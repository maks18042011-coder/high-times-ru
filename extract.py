"""
Stage 1 deliverable: extract translatable strings from a *copy* of the game's
SQLite text databases (./work/SqlText/*.sq) into intermediate CSVs.

Never touches the original game install. Never writes a machine translation —
the `target` column is always left empty for a human/translation-memory step.

Usage:
    python extract.py [--work-dir work/SqlText] [--out-dir csv]
"""
import argparse
import csv
import re
import sqlite3
from pathlib import Path

DEFAULT_WORK_DIR = Path(__file__).resolve().parent / "work" / "SqlText"
DEFAULT_OUT_DIR = Path(__file__).resolve().parent / "csv"

CSV_FIELDS = ["id", "file", "context", "source", "target", "status", "max_len"]

# Tokens containing this substring (case-insensitive) go to achievements.csv
# instead of ui.csv. Found by inspecting real TOKEN values in localized.sq
# (lz_achievement_title_1, lz_achievement_unlocked, ...).
ACHIEVEMENT_HINT = re.compile(r"achiev", re.IGNORECASE)

# Heuristic for recipes.sq 'name' values that look like internal scene-linked
# presets (e.g. "Adam Arc 1 Scene 1 Custom") rather than real player-facing
# menu items (e.g. "Boston Cream"). Not a hard classifier — flagged in
# `context` for human triage, nothing is dropped.
INTERNAL_PRESET_HINT = re.compile(r"\bArc \d+\b.*\b(Scene|Context) \d+\b")


def connect_ro(path: Path) -> sqlite3.Connection:
    """Open a SQLite file strictly read-only, refusing to create/modify it."""
    if not path.exists():
        raise FileNotFoundError(f"expected a copy of the game DB at {path}")
    return sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)


def token_context(token: str | None, sep: str = "_") -> str:
    if not token:
        return ""
    parts = token.split(sep)
    if len(parts) >= 3:
        return parts[1]
    return token


def extract_localized_texts(db_path: Path, achievements: bool) -> list[dict]:
    """Shared extractor for vntext.sq and localized.sq (same table shape).

    Uses `rowid` as the stable key (not TOKEN): vntext.sq declares TOKEN as
    PRIMARY KEY but that's a separate unique index, not the rowid alias
    (only INTEGER PRIMARY KEY would be); localized.sq's TOKEN is *not*
    unique at all (1 duplicate found). rowid is unique and stable in both.
    """
    con = connect_ro(db_path)
    rows = con.execute("SELECT rowid, TOKEN, EN FROM localized_texts").fetchall()
    con.close()

    out = []
    dbname = db_path.name
    for rowid, token, en in rows:
        is_achiev = bool(ACHIEVEMENT_HINT.search(token or ""))
        if is_achiev != achievements:
            continue
        source = en or ""
        out.append(
            {
                "id": f"{dbname}#{rowid}",
                "file": dbname,
                "context": token_context(token),
                "source": source,
                "target": "",
                "status": "new",
                "max_len": len(source),
            }
        )
    return out


def extract_recipes(db_path: Path) -> list[dict]:
    """recipes.sq has NO per-language columns (single-language table) —
    see NOTES.md for why that breaks the 'overwrite DE' strategy used
    elsewhere. Extracted here anyway so the data is visible for review;
    build.py currently refuses to write it back until that's resolved.
    """
    con = connect_ro(db_path)
    rows = con.execute("SELECT rowid, name, description FROM recipes").fetchall()
    con.close()

    out = []
    dbname = db_path.name
    for rowid, name, description in rows:
        if name and INTERNAL_PRESET_HINT.search(name):
            # scene-linked internal preset (e.g. "Adam Arc 1 Scene 1 Custom"),
            # not a player-facing menu item — excluded per Stage 1 review.
            continue
        if name:
            out.append(
                {
                    "id": f"{dbname}#{rowid}#name",
                    "file": dbname,
                    "context": "recipe:name:menu-item",
                    "source": name,
                    "target": "",
                    "status": "new",
                    "max_len": len(name),
                }
            )
        if description:
            out.append(
                {
                    "id": f"{dbname}#{rowid}#description",
                    "file": dbname,
                    "context": "recipe:description",
                    "source": description,
                    "target": "",
                    "status": "new",
                    "max_len": len(description),
                }
            )
    return out


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = ap.parse_args()

    dialogue = extract_localized_texts(args.work_dir / "vntext.sq", achievements=False)
    ui = extract_localized_texts(args.work_dir / "localized.sq", achievements=False)
    achievements = extract_localized_texts(args.work_dir / "localized.sq", achievements=True)
    items = extract_recipes(args.work_dir / "recipes.sq")

    write_csv(dialogue, args.out_dir / "dialogue.csv")
    write_csv(ui, args.out_dir / "ui.csv")
    write_csv(achievements, args.out_dir / "achievements.csv")
    write_csv(items, args.out_dir / "items.csv")

    print(f"dialogue.csv:     {len(dialogue)} rows")
    print(f"ui.csv:           {len(ui)} rows")
    print(f"achievements.csv: {len(achievements)} rows")
    print(f"items.csv:        {len(items)} rows")


if __name__ == "__main__":
    main()
