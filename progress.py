"""
Etap C deliverable: one-shot progress summary across every translation
CSV in the project (ui.csv, achievements.csv, items.csv, and the 69
per-speaker files under csv/dialogue/), replacing the ad hoc "run a
python -c one-liner" progress check done after every block so far.

    python progress.py
    python progress.py --dialogue-detail

Counts rows by status (new/translated/review/kept) per file and prints
a totals table. --dialogue-detail also breaks csv/dialogue/ down by
speaker (uses csv/dialogue/_index.csv for the file list).
"""
import argparse
import csv
from pathlib import Path

csv.field_size_limit(10_000_000)

ROOT = Path(__file__).resolve().parent
STATUSES = ["new", "translated", "review", "kept"]


def count_file(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    counts = {s: 0 for s in STATUSES}
    for r in rows:
        counts[r.get("status", "new")] = counts.get(r.get("status", "new"), 0) + 1
    counts["total"] = len(rows)
    counts["done"] = counts["translated"] + counts["review"] + counts["kept"]
    return counts


def fmt_row(label: str, c: dict) -> str:
    pct = (c["done"] / c["total"] * 100) if c["total"] else 0.0
    return (f"{label:22s} {c['done']:6d}/{c['total']:<6d} ({pct:5.1f}%)  "
            f"new={c['new']:<6d} translated={c['translated']:<6d} review={c['review']:<5d} kept={c['kept']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dialogue-detail", action="store_true",
                     help="also break csv/dialogue/ down per speaker")
    args = ap.parse_args()

    print("=== Основной корпус ===")
    main_totals = {s: 0 for s in STATUSES}
    main_totals["total"] = main_totals["done"] = 0
    for name in ["ui.csv", "achievements.csv", "items.csv"]:
        path = ROOT / "csv" / name
        if not path.exists():
            continue
        c = count_file(path)
        print(fmt_row(name, c))
        for k in STATUSES + ["total", "done"]:
            main_totals[k] += c[k]
    print(fmt_row("ИТОГО (основной)", main_totals))

    dialogue_dir = ROOT / "csv" / "dialogue"
    if dialogue_dir.is_dir():
        print()
        print("=== dialogue.csv (по персонажам) ===")
        dlg_totals = {s: 0 for s in STATUSES}
        dlg_totals["total"] = dlg_totals["done"] = 0
        per_file = []
        for path in sorted(dialogue_dir.glob("*.csv")):
            if path.name == "_index.csv":
                continue
            c = count_file(path)
            per_file.append((path.stem, c))
            for k in STATUSES + ["total", "done"]:
                dlg_totals[k] += c[k]

        if args.dialogue_detail:
            for name, c in sorted(per_file, key=lambda x: -x[1]["total"]):
                print(fmt_row(name, c))
        print(fmt_row("ИТОГО (dialogue)", dlg_totals))

        print()
        grand = {k: main_totals[k] + dlg_totals[k] for k in STATUSES + ["total", "done"]}
        print(fmt_row("ВСЕГО ПРОЕКТ", grand))
    else:
        print()
        print("(csv/dialogue/ не найден — запустите scripts/split_dialogue.py)")


if __name__ == "__main__":
    main()
