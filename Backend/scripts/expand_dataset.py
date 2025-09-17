"""
Expand the `Backend/data/pnw.csv` file to at least N rows by duplicating and
jittering existing rows.

Usage:
    python Backend/scripts/expand_dataset.py --count 100

This script will back up the original `pnw.csv` to `pnw.csv.bak` before
overwriting.
"""

import argparse
import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "pnw.csv"
BACKUP = DATA.with_suffix(".csv.bak")

CATEGORIES = [
    "Mountain",
    "Lake",
    "Park",
    "Gorge",
    "Climbing",
    "Island",
    "Beach",
    "Trail",
    "Forest",
    "Desert",
]

parser = argparse.ArgumentParser()
parser.add_argument("--count", type=int, default=100, help="Target minimum row count")
args = parser.parse_args()


def read_rows(path: Path):
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        return list(r)


def write_rows(path: Path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def expand(rows, target):
    out = []
    n = len(rows)
    idx = 1
    i = 0
    while len(out) < target:
        base = rows[i % n].copy()
        # new id
        base["id"] = str(idx)
        # append suffix to name to make unique-ish
        base["name"] = f"{base.get('name','')}_{idx}"
        # jitter lat/lon slightly within ~0.05 deg (~3 miles)
        try:
            lat = float(base["lat"])
            lon = float(base["lon"])
            lat += random.uniform(-0.05, 0.05)
            lon += random.uniform(-0.05, 0.05)
            base["lat"] = f"{lat:.6f}"
            base["lon"] = f"{lon:.6f}"
        except Exception:
            pass
        # ensure elevation exists
        if not base.get("elevation"):
            base["elevation"] = "0"
        # category: cycle through list
        base["category"] = CATEGORIES[(idx - 1) % len(CATEGORIES)]
        # timezone and state left as-is
        out.append(base)
        idx += 1
        i += 1
    return out


def main():
    if not DATA.exists():
        print(f"Data file not found: {DATA}")
        return
    rows = read_rows(DATA)
    if len(rows) >= args.count:
        print(f"Already {len(rows)} rows >= target {args.count}; no change.")
        return
    # backup
    if not BACKUP.exists():
        DATA.replace(BACKUP)
        print(f"Backed up original to {BACKUP}")
        # read from backup path for original rows
        rows = read_rows(BACKUP)
    expanded = expand(rows, args.count)
    fieldnames = rows[0].keys()
    write_rows(DATA, expanded, fieldnames)
    print(f"Wrote {len(expanded)} rows to {DATA}")


if __name__ == "__main__":
    main()
