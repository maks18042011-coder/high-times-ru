"""
Etap C deliverable: standalone validator, reusable across ui.csv,
achievements.csv, items.csv, and the 69 per-speaker files under
csv/dialogue/. Meant to run right after any translation pass, the same
checks that were done ad hoc (inline, one-off scripts) for every block
of ui.csv this project has done so far -- now consolidated into one
tool instead of hand-rolling it per block.

    python validate.py --input csv/ui.csv
    python validate.py --input-dir csv/dialogue
    python validate.py --input csv/ui.csv --input csv/achievements.csv --input csv/items.csv --input-dir csv/dialogue

Checks (source vs target, only rows with status in translated/review/kept):
  1. Markup parity: {...} interpolation, [...] BBCode, <...> TMP rich
     text tags -- same multiset in source and target (build.py's own
     pre-write check, reused here so problems surface before a build
     attempt, not during one).
  2. Newline parity: same count of literal \\n.
  3. Boolean literals (AND/OR/NOT) inside {...}/[...] blocks must be
     copied byte-for-byte, never translated (NOTES.md, "Инвентаризация
     разметки" -- these are GOLD-Parser conditional expressions, not
     prose).
  4. Length budget: target must not exceed source length by more than
     15% (source <=15 chars) or 25% (source >15 chars). Reported as a
     warning, not an error -- single dictionary-word tag rows
     (ttext_*/colors:/tastes:/etc, see NOTES.md block 33) are a known,
     accepted exception category and always will exceed this.
  5. Glossary drift: if a row's source contains one of glossary.md's
     English proper nouns (character/place names kept untranslated by
     project convention), warn if that exact substring is missing from
     the target -- catches accidental transliteration/translation of a
     name that should have stayed in Latin script.

Exit code is non-zero only for hard errors (1-3); length-budget and
glossary findings are warnings and don't fail the run (pass --strict to
promote warnings to errors, e.g. for a final pre-build gate).
"""
import argparse
import csv
import re
from pathlib import Path

csv.field_size_limit(10_000_000)

ROOT = Path(__file__).resolve().parent

MARKUP_PATTERNS = {
    "curly": re.compile(r"\{[^{}]*\}"),
    "square": re.compile(r"\[[^\[\]]*\]"),
    "angle": re.compile(r"</?[a-zA-Z][^<>]*>"),
}
BOOLEAN_IN_BRACKETS = re.compile(r"[{\[][^{}\[\]]*\b(AND|OR|NOT)\b[^{}\[\]]*[\]}]")

# Proper nouns established as "kept in English" project-wide (glossary.md +
# NOTES.md precedent). Not exhaustive -- extend as more names get confirmed.
GLOSSARY_NAMES = [
    "San Mazo", "Attleset", "Monumento", "San Juanico",
    "Connor Collins", "MJ Hayes", "Lucy Dee", "Stacy Ortiz",
    "Emmette Meine", "Harry Yen", "Riri", "Kyle Hill", "Zoey Belladonna",
    "Jojo", "Zone Hayes", "Dexie Dean", "Emma Meine", "Adam LaChance",
    "Sally Divine", "Cody Yen", "Detective Fox", "Nova", "Debora",
    "Billie", "Elisa Stern", "Hugo Stern", "Sam Camarillo", "Dakota",
    "Queen Adarna", "Tim Dunham", "Beck Geller",
]


def extract_markup(text: str) -> dict:
    return {name: sorted(pat.findall(text)) for name, pat in MARKUP_PATTERNS.items()}


def collect_input_csvs(inputs: list[Path], input_dirs: list[Path]) -> list[Path]:
    csvs = list(inputs)
    for d in input_dirs:
        if not d.is_dir():
            raise SystemExit(f"--input-dir not a directory: {d}")
        csvs.extend(sorted(p for p in d.glob("*.csv") if p.name != "_index.csv"))
    if not csvs:
        raise SystemExit("no input CSVs given (use --input and/or --input-dir)")
    return csvs


def validate_file(path: Path, strict: bool) -> tuple[int, int, int]:
    """Returns (n_checked, n_errors, n_warnings)."""
    n_checked = 0
    n_errors = 0
    n_warnings = 0
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    for r in rows:
        if r.get("status") not in ("translated", "review", "kept"):
            continue
        rid = r["id"]
        source = r.get("source") or ""
        target = r.get("target") or ""
        n_checked += 1

        src_markup = extract_markup(source)
        tgt_markup = extract_markup(target)
        if src_markup != tgt_markup:
            for name in MARKUP_PATTERNS:
                if src_markup[name] != tgt_markup[name]:
                    print(f"[ERROR] {path.name} {rid}: {name} markup mismatch -- "
                          f"source={src_markup[name]!r} target={tgt_markup[name]!r}")
            n_errors += 1
            continue

        if source.count("\n") != target.count("\n"):
            print(f"[ERROR] {path.name} {rid}: newline count mismatch "
                  f"(source={source.count(chr(10))}, target={target.count(chr(10))})")
            n_errors += 1
            continue

        src_bool = sorted(BOOLEAN_IN_BRACKETS.findall(source))
        if src_bool:
            tgt_bool_blocks = MARKUP_PATTERNS["curly"].findall(target) + MARKUP_PATTERNS["square"].findall(target)
            src_bool_blocks = [b for b in (MARKUP_PATTERNS["curly"].findall(source) + MARKUP_PATTERNS["square"].findall(source))
                                if BOOLEAN_IN_BRACKETS.match(b)]
            missing = [b for b in src_bool_blocks if b not in tgt_bool_blocks]
            if missing:
                print(f"[ERROR] {path.name} {rid}: AND/OR/NOT boolean block(s) not copied verbatim: {missing}")
                n_errors += 1
                continue

        src_len = len(source)
        if src_len:
            delta = (len(target) - src_len) / src_len * 100
            cap = 15 if src_len <= 15 else 25
            if delta > cap:
                level = "ERROR" if strict else "WARN"
                print(f"[{level}] {path.name} {rid}: length budget +{delta:.1f}% (cap {cap}%) "
                      f"src={source!r} tgt={target!r}")
                if strict:
                    n_errors += 1
                else:
                    n_warnings += 1

        for name in GLOSSARY_NAMES:
            if name in source and name not in target:
                level = "ERROR" if strict else "WARN"
                print(f"[{level}] {path.name} {rid}: glossary name {name!r} present in source but missing from target")
                if strict:
                    n_errors += 1
                else:
                    n_warnings += 1

    return n_checked, n_errors, n_warnings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", action="append", type=Path, default=[])
    ap.add_argument("--input-dir", action="append", type=Path, default=[])
    ap.add_argument("--strict", action="store_true", help="promote length-budget/glossary warnings to errors")
    args = ap.parse_args()

    csvs = collect_input_csvs(args.input, args.input_dir)

    total_checked = total_errors = total_warnings = 0
    for path in csvs:
        n_checked, n_errors, n_warnings = validate_file(path, args.strict)
        total_checked += n_checked
        total_errors += n_errors
        total_warnings += n_warnings

    print()
    print(f"checked {total_checked} rows across {len(csvs)} file(s): "
          f"{total_errors} error(s), {total_warnings} warning(s)")
    if total_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
