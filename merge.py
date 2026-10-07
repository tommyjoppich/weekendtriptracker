"""Combine the shard files from the parallel GitHub jobs into data/prices-YYYY-MM.csv."""

import csv
import sys
from pathlib import Path

from tracker import DATA, FIELDS


def main(shard_dir: str = "out"):
    files = sorted(Path(shard_dir).glob("*.csv"))
    rows = []
    for f in files:
        rows += list(csv.DictReader(f.open()))
    if not rows:
        print("No shard results to merge.")
        return
    DATA.mkdir(exist_ok=True)
    by_month = {}
    for r in rows:
        by_month.setdefault(r["run_id"][:7], []).append(r)
    for month, rs in by_month.items():
        path = DATA / f"prices-{month}.csv"
        new = not path.exists()
        with path.open("a", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            if new:
                w.writeheader()
            w.writerows(rs)
    ok = sum(r["status"] == "ok" for r in rows)
    print(f"Merged {len(files)} shard files: {len(rows)} searches, {ok} prices.")


if __name__ == "__main__":
    main(*sys.argv[1:])
