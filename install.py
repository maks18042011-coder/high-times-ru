"""
Stage 4 deliverable: install / uninstall a built patch onto a *copy* of the
game. Never has a default target path -- you must always pass --target-dir
explicitly, and it is checked against the one original-install path this
project has ever touched, as a last-resort safety net (see --target-dir
help below for why that's not a substitute for you picking the right path).

Install:
    python install.py --target-dir "D:\\...\\game_copy" [--marker] [--yes]

Uninstall (restores everything from the backup this same script made):
    python install.py --target-dir "D:\\...\\game_copy" --uninstall [--yes]
"""
import argparse
import json
import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD_DIR = ROOT / "work" / "build"
BACKUP_DIR = ROOT / "backup"

# Optional last-resort trip-wire: set HT_ORIGINAL_PATH to your original
# (non-copy) game install and this script will refuse to write there.
# Passing any other path is YOUR responsibility to have verified is a copy;
# this check does not replace that.
KNOWN_ORIGINAL_PATH = os.environ.get("HT_ORIGINAL_PATH", "")


def localAppData_low_dir() -> Path:
    import os

    return Path(os.environ["USERPROFILE"]) / "AppData" / "LocalLow" / "Yangyang Mobile" / "High Times"


def resolve_and_guard_target(target_dir: str) -> Path:
    target = Path(target_dir).resolve()
    if KNOWN_ORIGINAL_PATH and str(target).lower() == str(Path(KNOWN_ORIGINAL_PATH).resolve()).lower():
        raise SystemExit(
            f"[REFUSED] --target-dir resolves to the known ORIGINAL game install:\n"
            f"  {target}\n"
            f"This script will never write there. Point it at a copy instead."
        )
    exe = target / "High Times.exe"
    sqltext = target / "High Times_Data" / "StreamingAssets" / "SqlText"
    if not exe.exists() or not sqltext.exists():
        raise SystemExit(
            f"[REFUSED] {target} doesn't look like a High Times install "
            f"(missing 'High Times.exe' or 'High Times_Data\\StreamingAssets\\SqlText')."
        )
    return target


def confirm(target: Path, skip: bool) -> None:
    print(f"Target: {target}")
    print(
        "NOTE: this game's save-data cache (AppData\\LocalLow\\Yangyang Mobile\\High Times) "
        "is shared machine-wide by *any* copy of the game with this name/publisher, not just "
        "this folder -- installing here will also affect that shared cache. See NOTES.md."
    )
    if skip:
        return
    answer = input("Proceed? [y/N] ").strip().lower()
    if answer not in ("y", "yes"):
        raise SystemExit("Aborted by user.")


def backup_file(path: Path, backup_root: Path, rel_label: str) -> Path | None:
    if not path.exists():
        return None
    dest = backup_root / rel_label
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dest)
    return dest


def ensure_full_localLow_backup() -> Path | None:
    """
    A.4: on the very FIRST install this script ever runs on this machine,
    back up the ENTIRE LocalLow\\Yangyang Mobile\\High Times folder --
    saves, settings, everything -- before touching anything in it. This is
    a whole-folder safety net layered on top of (not instead of) the
    surgical per-file backup/restore in do_install/do_uninstall, because
    that folder is shared between this copy and the original install (or
    any other copy) -- see NOTES.md "Этап 2 -- LocalLow cache".

    Never deletes or modifies the source folder; only ever copies it.
    Runs at most once (checked via a marker file) so repeat installs don't
    re-copy tens of MB of save data every time.
    """
    ll_dir = localAppData_low_dir()
    if not ll_dir.exists():
        print(f"[i] no LocalLow folder at {ll_dir} yet -- nothing to full-backup.")
        return None

    marker = BACKUP_DIR / "localLow_full_backup_done.json"
    if marker.exists():
        info = json.loads(marker.read_text(encoding="utf-8"))
        print(f"[i] full LocalLow backup already made once, at {info['backup']} ({info['timestamp']}) -- not repeating.")
        return Path(info["backup"])

    print(
        "[!] WARNING: AppData\\LocalLow\\Yangyang Mobile\\High Times is shared by "
        "ANY copy of this game on this machine (including the original install) -- "
        "it holds saves and settings, not just our cache files. Making a one-time "
        "full backup of the whole folder before this or any future install touches it."
    )
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = BACKUP_DIR / f"localLow_full_{stamp}"
    shutil.copytree(ll_dir, dest)
    marker.write_text(
        json.dumps({"timestamp": stamp, "backup": str(dest), "source": str(ll_dir)}, indent=2),
        encoding="utf-8",
    )
    print(f"[*] full LocalLow backup: {dest}")
    return dest


# Every DB this project might have a built patch for. Originally only
# localized.sq was ever patched (dialogue.csv/vntext.sq was permanently
# out of scope) -- that restriction was explicitly lifted, so vntext.sq
# is now installed the same way, whenever a build for it actually exists.
# recipes.sq listed for completeness (items.csv target) even though no
# build.py run against it has happened yet as of this script version.
PATCHABLE_DBS = ["localized.sq", "vntext.sq", "recipes.sq"]


def do_install(target: Path, marker: bool, skip_confirm: bool) -> None:
    variant = "marker" if marker else "plain"
    build_sqltext = BUILD_DIR / variant / "High Times_Data" / "StreamingAssets" / "SqlText"
    patch_dbs = [db for db in PATCHABLE_DBS if (build_sqltext / db).exists()]
    if not patch_dbs:
        raise SystemExit(
            f"[REFUSED] no built patch found under {build_sqltext} -- run build.py first "
            f"(--marker to match)."
        )

    confirm(target, skip_confirm)
    ensure_full_localLow_backup()

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = BACKUP_DIR / f"install_{stamp}"
    manifest = {
        "timestamp": stamp,
        "target": str(target),
        "variant": variant,
        "streaming_assets_backups": {},
        "localLow_backups": [],
    }

    target_sqltext = target / "High Times_Data" / "StreamingAssets" / "SqlText"
    ll_dir = localAppData_low_dir()

    for db_name in patch_dbs:
        patch_db = build_sqltext / db_name

        # 1) back up + overwrite StreamingAssets/SqlText/<db_name>
        target_db = target_sqltext / db_name
        backed_up = backup_file(target_db, backup_root, f"StreamingAssets_SqlText/{db_name}")
        manifest["streaming_assets_backups"][db_name] = str(backed_up) if backed_up else None
        shutil.copy2(patch_db, target_db)
        print(f"[*] patched {target_db}")

        # 2) LocalLow cache: back up + overwrite ONLY the cache file for
        #    this same db_name, if it already exists there. Never touch
        #    State/, Log/, Player*.log, and never delete the LocalLow
        #    folder itself (hard rule). Any db_name NOT in patch_dbs is
        #    left completely alone in the cache too -- we only ever touch
        #    a cache file for a DB we're actually patching this run.
        if ll_dir.exists():
            cache_file = ll_dir / db_name
            if cache_file.exists():
                backed_up = backup_file(cache_file, backup_root, f"LocalLow_cache/{db_name}")
                manifest["localLow_backups"].append({"name": db_name, "backup": str(backed_up)})
                shutil.copy2(patch_db, cache_file)
                print(f"[*] patched cached copy at {cache_file}")
            else:
                print(f"[i] no cached {db_name} at {ll_dir} yet -- nothing to patch there, it'll be populated fresh from StreamingAssets on first launch.")
        else:
            print(f"[i] no LocalLow cache dir found at {ll_dir} yet (game likely never run from here) -- nothing to patch there, it'll be populated fresh from StreamingAssets on first launch.")

    manifest_path = backup_root / "manifest.json"
    backup_root.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[*] backup + manifest: {backup_root}")
    print(f"[*] install complete ({variant} variant, {', '.join(patch_dbs)}). To undo: python install.py --target-dir \"{target}\" --uninstall")


def find_latest_manifest(target: Path) -> Path:
    candidates = []
    for d in BACKUP_DIR.glob("install_*"):
        mf = d / "manifest.json"
        if mf.exists():
            try:
                data = json.loads(mf.read_text(encoding="utf-8"))
            except Exception:
                continue
            if Path(data.get("target", "")).resolve() == target:
                candidates.append((d.name, mf))
    if not candidates:
        raise SystemExit(f"[REFUSED] no install backup found for target {target} under {BACKUP_DIR}")
    candidates.sort()
    return candidates[-1][1]


def do_uninstall(target: Path, skip_confirm: bool) -> None:
    manifest_path = find_latest_manifest(target)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    print(f"[*] restoring from {manifest_path}")

    if not skip_confirm:
        answer = input(f"Restore {target} from this backup? [y/N] ").strip().lower()
        if answer not in ("y", "yes"):
            raise SystemExit("Aborted by user.")

    sa_backups = manifest.get("streaming_assets_backups")
    if sa_backups is None:
        # backwards compatibility with manifests written before multi-DB support
        legacy = manifest.get("streaming_assets_backup")
        sa_backups = {"localized.sq": legacy} if legacy else {}
    for db_name, sa_backup in sa_backups.items():
        if not sa_backup:
            continue
        dest = target / "High Times_Data" / "StreamingAssets" / "SqlText" / db_name
        shutil.copy2(sa_backup, dest)
        print(f"[*] restored {dest}")

    ll_dir = localAppData_low_dir()
    for entry in manifest.get("localLow_backups", []):
        dest = ll_dir / entry["name"]
        if Path(entry["backup"]).exists():
            shutil.copy2(entry["backup"], dest)
            print(f"[*] restored cached {dest}")

    print("[*] uninstall complete -- State/, Log/, Player*.log and everything else were never touched.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--target-dir",
        required=True,
        help="path to a COPY of the game install (never defaults; refused if it matches the known original path)",
    )
    ap.add_argument("--marker", action="store_true", help="install the [Ж]...[rowid]-marked patch instead of the plain one")
    ap.add_argument("--uninstall", action="store_true", help="restore target-dir (and the shared LocalLow cache) from the backup this script made")
    ap.add_argument("--yes", action="store_true", help="skip the interactive confirmation prompt")
    args = ap.parse_args()

    target = resolve_and_guard_target(args.target_dir)

    if args.uninstall:
        do_uninstall(target, args.yes)
    else:
        do_install(target, args.marker, args.yes)


if __name__ == "__main__":
    main()
