"""Check United round-trip prices from ORD to the airports in airports.py for each
of the next N weekends.

Weekend = leave Thursday after 6 PM or Friday before 6 PM, return Sunday landing
at ORD by 10 PM. That's two searches per airport per weekend (Thu and Fri).

On GitHub the airport list is split across 4 machines running at the same time
("shards"), and merge.py combines their results afterwards.

    python tracker.py                         # all airports, write to data/
    python tracker.py --shard 0 --of 4 --out out/shard-0.csv
"""

from __future__ import annotations

import argparse
import csv
import os
import random
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import config
from airports import AIRPORTS

ROOT = Path(__file__).parent
DATA = ROOT / "data"
FIELDS = [
    "run_id", "checked_at_local", "dest", "city", "state", "tier",
    "weekend", "depart_date", "depart_day", "return_date", "status", "price",
    "nonstop_price", "stops", "flight", "num_options", "error",
]
DAY = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
GIVE_UP_AFTER = 40           # consecutive failures → assume blocked, stop this run


def upcoming_weekends(today: date, n: int):
    """Next n weekends: list of (weekend_key, [(depart_date, earliest, latest), ...], return_date).
    weekend_key is the date of the first departure day (Thursday)."""
    first_wd = config.DEPART_WINDOWS[0][0]
    d = today
    while d.weekday() != first_wd:
        d += timedelta(days=1)
    out = []
    for i in range(n):
        anchor = d + timedelta(weeks=i)
        windows = [(anchor + timedelta(days=(wd - first_wd) % 7), lo, hi)
                   for wd, lo, hi in config.DEPART_WINDOWS]
        ret = anchor + timedelta(days=(config.RETURN_WEEKDAY - first_wd) % 7)
        # skip departure days already in the past
        windows = [w for w in windows if w[0] >= today]
        if windows:
            out.append((anchor, windows, ret))
    return out


def build_query(dest: str, out: date, lo, hi, back: date):
    from fast_flights import FlightQuery, Passengers, create_query
    legs = [
        FlightQuery(date=out.isoformat(), from_airport=config.ORIGIN, to_airport=dest,
                    airlines=[config.AIRLINE_CODE],
                    earliest_departure_hour=lo, latest_departure_hour=hi),
        FlightQuery(date=back.isoformat(), from_airport=dest, to_airport=config.ORIGIN,
                    airlines=[config.AIRLINE_CODE],
                    latest_arrival_hour=config.RETURN_LATEST_ARRIVAL_HOUR),
    ]
    return create_query(
        flights=legs, seat=config.SEAT, trip="round-trip",
        passengers=Passengers(adults=config.ADULTS), currency=config.CURRENCY,
        language="en-US", exclude_basic_economy=config.EXCLUDE_BASIC_ECONOMY,
    )


def fetch(dest, out, lo, hi, back):
    from fast_flights import get_flights
    q = build_query(dest, out, lo, hi, back)
    try:
        return get_flights(q)
    except Exception:
        time.sleep(8)                 # one retry after a short pause
        return get_flights(q)


def united_options(results, lo, hi) -> list[dict]:
    opts = []
    for f in results or []:
        if not f.flights or not f.price:
            continue
        names = f.airlines or []
        if not names or not all(config.AIRLINE_NAME.lower() in n.lower() for n in names):
            continue
        first, last = f.flights[0], f.flights[-1]
        h = first.departure.time[0]
        if (lo is not None and h < lo) or (hi is not None and h > hi):
            continue
        opts.append({
            "price": int(f.price),
            "stops": len(f.flights) - 1,
            "time": f"{h:02d}:{first.departure.time[1]:02d}",
            "arr": f"{last.arrival.time[0]:02d}:{last.arrival.time[1]:02d}",
        })
    return sorted(opts, key=lambda o: o["price"])


def run(fetcher=fetch, now: datetime | None = None, sleep=time.sleep,
        airports=None, out_path: Path | None = None, run_id: str | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    local = now.astimezone(ZoneInfo(config.TIMEZONE))
    run_id = run_id or os.environ.get("RUN_ID") or now.strftime("%Y-%m-%dT%H:%MZ")
    airports = AIRPORTS if airports is None else airports
    weekends = upcoming_weekends(local.date(), config.WEEKENDS_AHEAD)
    out_path = out_path or DATA / f"prices-{run_id[:7]}.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    new = not out_path.exists()
    ok = fails = streak = 0
    with out_path.open("a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        if new:
            w.writeheader()
        for code, city, state, tier in airports:
            for anchor, windows, back in weekends:
                for out, lo, hi in windows:
                    row = {"run_id": run_id, "checked_at_local": local.strftime("%Y-%m-%d %H:%M"),
                           "dest": code, "city": city, "state": state, "tier": tier,
                           "weekend": anchor.isoformat(), "depart_date": out.isoformat(),
                           "depart_day": DAY[out.weekday()], "return_date": back.isoformat()}
                    try:
                        opts = united_options(fetcher(code, out, lo, hi, back), lo, hi)
                        streak = 0                   # Google answered; not blocked
                        if not opts:
                            raise LookupError("no matching United flights")
                        ns = [o for o in opts if o["stops"] == 0]
                        row.update(status="ok", price=opts[0]["price"],
                                   nonstop_price=ns[0]["price"] if ns else "",
                                   stops=opts[0]["stops"],
                                   flight=f"{DAY[out.weekday()]} {opts[0]['time']}→{opts[0]['arr']}",
                                   num_options=len(opts), error="")
                        ok += 1
                    except Exception as e:
                        if not isinstance(e, LookupError):
                            streak += 1
                        row.update(status="none" if isinstance(e, LookupError) else "error",
                                   price="", nonstop_price="", stops="", flight="",
                                   num_options=0, error=str(e)[:160])
                        fails += 1
                    w.writerow(row)
                    if streak >= GIVE_UP_AFTER:
                        print(f"{streak} failures in a row — Google is probably blocking; stopping early.",
                              file=sys.stderr)
                        return ok
                    if streak == 15:
                        sleep(90)                    # long pause, then keep trying
                    sleep(random.uniform(*config.DELAY_RANGE))
            fh.flush()
            print(f"{code}: done", flush=True)
    print(f"Done: {ok} prices, {fails} misses ({len(airports)} airports × {len(weekends)} weekends)")
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--of", type=int, default=1)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    run(airports=AIRPORTS[a.shard::a.of], out_path=a.out)
