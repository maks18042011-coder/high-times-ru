"""
Stage 4 deliverable: assemble a patched localized.sq/recipes.sq/vntext.sq
from one or more translation CSVs.

    python build.py --input csv/ui.csv --input csv/achievements.csv
    python build.py --input csv/items.csv --db recipes.sq
    python build.py --input-dir csv/dialogue --db vntext.sq
    python build.py --input csv/ui.csv --marker

Multiple CSVs can feed the same DB (e.g. ui.csv + achievements.csv both
target localized.sq; the 69 per-speaker files under csv/dialogue/ all
target vntext.sq -- see glossary.md / Etap C). Pass --input repeatedly
and/or --input-dir for a whole folder of CSVs (every *.csv in the folder
except _index.csv). Rows are merged across all given inputs; the same
`id` appearing in two inputs with two different non-empty targets aborts
the build (ambiguous source of truth), matching a row already accepted.

Logic (per the pilot-patch brief):
  - rows present in the input(s) with a non-empty `target` -> DE = target
    (wrapped in a [Ж]...[rowid] marker if --marker is passed)
  - every other row of the same DB table -> DE = EN (the game has no
    auto-fallback to EN when DE is empty/NULL, see NOTES.md "Этап 2")

Only ever reads work/SqlText/*.sq (a copy) and writes into work/build/...
(also a copy). Never touches the original game install.

A validator runs before any row is accepted: source and target must carry
the same inline markup ({...} interpolation, [...] BBCode, <...> TMP rich
text tags, literal \\n escapes) or the whole build is aborted -- no partial
writes.
"""
import argparse
import csv
import re
import shutil
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORK_SQLTEXT = ROOT / "work" / "SqlText"
BUILD_DIR = ROOT / "work" / "build"

# same patterns catalogued in NOTES.md's markup inventory (Stage 1, item 3)
MARKUP_PATTERNS = {
    "curly": re.compile(r"\{[^{}]*\}"),
    "square": re.compile(r"\[[^\[\]]*\]"),
    "angle": re.compile(r"</?[a-zA-Z][^<>]*>"),
    "newline_escape": re.compile(r"\\n"),
}


class ValidationError(Exception):
    pass


class BuildAbort(Exception):
    pass


def extract_markup(text: str) -> dict:
    return {name: sorted(pat.findall(text)) for name, pat in MARKUP_PATTERNS.items()}


def validate_row(row_id: str, source: str, target: str) -> None:
    src_markup = extract_markup(source)
    tgt_markup = extract_markup(target)
    if src_markup != tgt_markup:
        diffs = []
        for name in MARKUP_PATTERNS:
            if src_markup[name] != tgt_markup[name]:
                diffs.append(f"{name}: source={src_markup[name]!r} target={tgt_markup[name]!r}")
        raise ValidationError(f"{row_id}: markup mismatch -- " + "; ".join(diffs))
    real_nl_src = source.count("\n")
    real_nl_tgt = target.count("\n")
    if real_nl_src != real_nl_tgt:
        raise ValidationError(
            f"{row_id}: line-break count mismatch (source={real_nl_src}, target={real_nl_tgt})"
        )


def collect_input_csvs(inputs: list[Path], input_dirs: list[Path]) -> list[Path]:
    csvs = list(inputs)
    for d in input_dirs:
        if not d.is_dir():
            raise BuildAbort(f"--input-dir not a directory: {d}")
        csvs.extend(sorted(p for p in d.glob("*.csv") if p.name != "_index.csv"))
    if not csvs:
        raise BuildAbort("no input CSVs given (use --input and/or --input-dir)")
    return csvs


def load_translations(input_csvs: list[Path], db_name: str) -> dict[int, tuple[str, str]]:
    """Returns {rowid: (source, target)} merged across all `input_csvs` for
    rows that belong to `db_name` and have a non-empty target. Raises
    ValidationError/BuildAbort (aborting the whole build) on the first
    markup mismatch or cross-file id conflict found."""
    translations: dict[int, tuple[str, str]] = {}
    seen_in: dict[int, str] = {}
    for input_csv in input_csvs:
        with open(input_csv, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r.get("file") != db_name:
                    continue
                target = r.get("target") or ""
                if not target.strip():
                    continue
                row_id = r["id"]
                try:
                    rowid = int(row_id.split("#", 1)[1])
                except (IndexError, ValueError):
                    raise BuildAbort(f"malformed id in {input_csv.name}: {row_id!r}")
                source = r.get("source") or ""
                validate_row(row_id, source, target)
                if rowid in translations and translations[rowid] != (source, target):
                    raise BuildAbort(
                        f"{row_id}: conflicting translations in {seen_in[rowid]} and {input_csv.name}"
                    )
                translations[rowid] = (source, target)
                seen_in[rowid] = input_csv.name
    return translations


def build_one(input_csvs: list[Path], db_name: str, marker: bool, out_root: Path) -> tuple[int, int]:
    src_db = WORK_SQLTEXT / db_name
    if not src_db.exists():
        raise BuildAbort(f"expected a working copy at {src_db} (never the original game folder)")

    translations = load_translations(input_csvs, db_name)

    out_dir = out_root / "High Times_Data" / "StreamingAssets" / "SqlText"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_db = out_dir / db_name
    shutil.copy2(src_db, out_db)

    con = sqlite3.connect(str(out_db))
    rows = con.execute("SELECT rowid, EN, DE FROM localized_texts").fetchall()

    updates = []
    n_translated = 0
    n_fallback = 0
    for rowid, en, de in rows:
        if rowid in translations:
            _, target = translations[rowid]
            text = f"[Ж]{target}[{rowid}]" if marker else target
            n_translated += 1
        else:
            # No auto-fallback to EN in-game (Stage 2 finding) -- write it
            # explicitly so untranslated rows show English, not blank/error.
            text = en or ""
            n_fallback += 1
        updates.append((text, rowid))

    con.executemany("UPDATE localized_texts SET DE = ? WHERE rowid = ?", updates)
    con.commit()
    con.close()
    return n_translated, n_fallback


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", action="append", type=Path, default=[],
                     help="translation CSV, e.g. csv/ui.csv (repeatable)")
    ap.add_argument("--input-dir", action="append", type=Path, default=[],
                     help="directory of translation CSVs, e.g. csv/dialogue (repeatable; skips _index.csv)")
    ap.add_argument("--marker", action="store_true", help="wrap translated strings in [Ж]text[rowid]")
    ap.add_argument("--db", default="localized.sq", help="which working-copy DB to build (default: localized.sq)")
    args = ap.parse_args()

    variant = "marker" if args.marker else "plain"
    out_root = BUILD_DIR / variant

    try:
        input_csvs = collect_input_csvs(args.input, args.input_dir)
        n_translated, n_fallback = build_one(input_csvs, args.db, args.marker, out_root)
    except (ValidationError, BuildAbort) as e:
        print(f"[ABORTED] {e}")
        raise SystemExit(1)

    print(f"[{variant}] built {out_root / 'High Times_Data' / 'StreamingAssets' / 'SqlText' / args.db}")
    print(f"  translated (from {len(input_csvs)} input CSV(s)): {n_translated}")
    print(f"  EN fallback (no auto-fallback in-game, written explicitly): {n_fallback}")


if __name__ == "__main__":
    main()
