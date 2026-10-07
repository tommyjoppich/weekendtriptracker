"""Build REPORT.md, the map dashboard (docs/index.html) and deal alerts
from data/prices.csv.

Per destination:
  now      cheapest round trip on any upcoming weekend in the latest run
  typical  median of the "cheapest available" price across all runs
  low      all-time low seen
  swing    how much the price moves around (10th–90th percentile spread ÷ typical)
  vs       today's price vs typical (negative = cheaper than usual)
"""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

import config
from airports import AIRPORTS

ROOT = Path(__file__).parent
DATA = ROOT / "data"
ALERTED_CSV = ROOT / "data" / "alerted.csv"
REPORT = ROOT / "REPORT.md"
TEMPLATE = ROOT / "dashboard_template.html"
DASHBOARD = ROOT / "docs" / "index.html"
ALERT = ROOT / "alert.md"


def money(x) -> str:
    return "—" if x is None or pd.isna(x) else f"${x:,.0f}"


def wk_label(d: str) -> str:
    """Weekend key (Thursday) → 'Oct 8–11'."""
    a = datetime.fromisoformat(d)
    b = a + timedelta(days=(config.RETURN_WEEKDAY - a.weekday()) % 7)
    return f"{a:%b} {a.day}–{b.day}" if a.month == b.month else f"{a:%b} {a.day}–{b:%b} {b.day}"


def hour_txt(h: int) -> str:
    return f"{(h % 12) or 12} {'AM' if h < 12 else 'PM'}"


def trip_text() -> str:
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    parts = []
    for wd, lo, hi in config.DEPART_WINDOWS:
        if lo is not None and hi is not None:
            parts.append(f"{days[wd]} {hour_txt(lo)}–{hour_txt(hi + 1)}")
        elif lo is not None:
            parts.append(f"{days[wd]} after {hour_txt(lo)}")
        elif hi is not None:
            parts.append(f"{days[wd]} before {hour_txt(hi + 1)}")
        else:
            parts.append(f"{days[wd]} any time")
    return (f"Leave {' or '.join(parts)} · back {days[config.RETURN_WEEKDAY]} "
            f"by {hour_txt(config.RETURN_LATEST_ARRIVAL_HOUR + 1)}")


def pct(x) -> str:
    return "—" if x is None or pd.isna(x) else f"{x*100:+.0f}%"


def load():
    files = sorted(DATA.glob("prices-*.csv"))
    if not files:
        return None
    return pd.concat([pd.read_csv(f, dtype={"price": "float", "nonstop_price": "float"})
                      for f in files], ignore_index=True)


def summarize(df: pd.DataFrame) -> dict:
    runs = sorted(df["run_id"].unique())
    latest_run = runs[-1]
    latest = df[df["run_id"] == latest_run]
    # Thu-evening and Fri-daytime searches → keep the cheaper one per city per weekend
    ok = (df[df["status"] == "ok"].sort_values("price")
          .drop_duplicates(["run_id", "dest", "weekend"]).copy())
    ok["depart_date"] = ok["weekend"]
    ok_latest = ok[ok["run_id"] == latest_run]
    weekends = sorted(latest["weekend"].unique())

    per_run_min = ok.groupby(["dest", "run_id"])["price"].min().reset_index()
    typical_all = ok.groupby("dest")["price"].median()   # typical fare for any one weekend
    meta = {a[0]: a for a in AIRPORTS}

    dests = []
    for code, city, state, tier in AIRPORTS:
        series = per_run_min[per_run_min["dest"] == code].sort_values("run_id")["price"]
        now_rows = ok_latest[ok_latest["dest"] == code].sort_values("price")
        grid = {r.depart_date: (r.price, int(r.stops) if pd.notna(r.stops) else None, r.flight)
                for r in now_rows.itertuples()}
        entry = {"code": code, "city": city, "state": state, "tier": tier,
                 "now": None, "best_wk": None, "now_stops": None, "now_flight": None,
                 "typical": None, "low": None, "swing": None, "vs": None,
                 "series": [], "grid": {}, "runs": int(series.size),
                 "typ_wk": float(typical_all[code]) if code in typical_all else None}
        if not series.empty:
            typical = float(series.median())
            entry.update(
                typical=typical, low=float(series.min()),
                swing=float((series.quantile(.9) - series.quantile(.1)) / typical) if series.size >= 3 else None,
                series=[int(v) for v in series.tail(60)],
            )
        if not now_rows.empty:
            r = now_rows.iloc[0]
            entry.update(now=float(r["price"]), best_wk=r["depart_date"],
                         now_stops=int(r["stops"]), now_flight=r["flight"])
            if entry["typical"]:
                entry["vs"] = entry["now"] / entry["typical"] - 1
        entry["grid"] = {d: {"p": int(p), "s": s, "f": f} for d, (p, s, f) in grid.items()}
        dests.append(entry)

    # deals: latest-run fares well below that destination's own typical fare
    runs_per_dest = ok.groupby("dest")["run_id"].nunique()
    deals = []
    for r in ok_latest.itertuples():
        t = typical_all.get(r.dest)
        if t is None or runs_per_dest.get(r.dest, 0) < config.DEAL_MIN_CHECKS:
            continue
        if r.price <= t * (1 - config.DEAL_THRESHOLD) and \
                (config.DEAL_MAX_PRICE is None or r.price <= config.DEAL_MAX_PRICE):
            deals.append({"dest": r.dest, "city": meta[r.dest][1], "state": meta[r.dest][2],
                          "depart": r.depart_date, "return": r.return_date,
                          "price": int(r.price), "typical": float(t),
                          "off": 1 - r.price / t, "stops": int(r.stops), "flight": r.flight})
    # one entry per city (its best weekend), so an email isn't 8 rows of the same city
    best_by_dest = {}
    for d in sorted(deals, key=lambda d: d["price"]):
        if d["dest"] in best_by_dest:
            best_by_dest[d["dest"]]["more"] += 1
        else:
            best_by_dest[d["dest"]] = {**d, "more": 0}
    deals = sorted(best_by_dest.values(), key=lambda d: -d["off"])

    # which weekend is cheapest overall (each fare relative to its destination's typical)
    rel = ok_latest.assign(rel=ok_latest["price"] / ok_latest["dest"].map(typical_all))
    wk_rel = rel.groupby("depart_date")["rel"].median().reindex(weekends)

    ever_ok = set(ok["dest"].unique())
    not_served = [d for d in dests if d["code"] not in ever_ok and
                  (latest[latest["dest"] == d["code"]]["status"] == "none").any()]

    n_err = int((latest["status"] == "error").sum())
    return {
        "updated": latest["checked_at_local"].iloc[-1],
        "latest_run": latest_run, "n_runs": len(runs),
        "weekends": weekends,
        "weekend_rel": {d: (None if pd.isna(v) else float(v)) for d, v in wk_rel.items()},
        "dests": dests, "deals": deals,
        "not_served": [d["code"] for d in not_served],
        "deal_threshold": config.DEAL_THRESHOLD, "deal_min_checks": config.DEAL_MIN_CHECKS,
        "errors": n_err, "searches": int(len(latest)),
        "trip": trip_text(),
    }


def write_report(s: dict):
    priced = [d for d in s["dests"] if d["now"] is not None]
    lines = [
        "# 🗺️ United weekend trips from Chicago (ORD)",
        "",
        f"{s['trip']} · United only · regular Economy · next {len(s['weekends'])} weekends",
        f"_Updated {s['updated']} Chicago time · run {s['n_runs']} · "
        f"{s['searches']} searches this run_",
        "",
        "**📍 Interactive map:** see `docs/index.html` (link in README once GitHub Pages is on).",
        "",
    ]
    if s["searches"] and s["errors"] / s["searches"] > 0.2:
        lines += [f"> ⚠️ {s['errors']} of {s['searches']} searches failed this run — "
                  "Google may be throttling the bot. Occasional bad runs are normal.", ""]

    if s["n_runs"] < config.DEAL_MIN_CHECKS:
        lines += [f"> ⏳ Run {s['n_runs']} of the first {config.DEAL_MIN_CHECKS}: \"typical price\", "
                  "swings and deal alerts switch on after a couple of days of data.", ""]

    if s["deals"]:
        lines += ["## 🔥 Deals right now", "",
                  "| Destination | Weekend | Price | Typical | Off | Flight |", "|---|---|---|---|---|---|"]
        for d in s["deals"][:15]:
            lines.append(f"| {d['city']}, {d['state']} ({d['dest']}) | {wk_label(d['depart'])} | "
                         f"**{money(d['price'])}** | {money(d['typical'])} | {d['off']*100:.0f}% | "
                         f"{d['flight']} {'nonstop' if d['stops'] == 0 else str(d['stops']) + ' stop'}"
                         f"{' (+' + str(d['more']) + ' more weekend' + ('s' if d['more'] > 1 else '') + ')' if d['more'] else ''} |")
        lines.append("")

    lines += ["## 💸 Cheapest right now", "",
              "| # | Destination | Price | Best weekend | Leave | Stops | vs. typical |", "|---|---|---|---|---|---|---|"]
    for i, d in enumerate(sorted(priced, key=lambda d: d["now"])[:20], 1):
        lines.append(f"| {i} | {d['city']}, {d['state']} ({d['code']}) | **{money(d['now'])}** | "
                     f"{wk_label(d['best_wk'])} | {d['now_flight'].split('→')[0]} | {'nonstop' if d['now_stops'] == 0 else d['now_stops']} | "
                     f"{pct(d['vs'])} |")
    lines.append("")

    steady = [d for d in s["dests"] if d["typical"] is not None and d["runs"] >= 2]
    if steady:
        lines += ["## 🏆 Consistently cheap (lowest typical price)", "",
                  "| # | Destination | Typical | All-time low | Swing |", "|---|---|---|---|---|"]
        for i, d in enumerate(sorted(steady, key=lambda d: d["typical"])[:15], 1):
            sw = "—" if d["swing"] is None else f"±{d['swing']*50:.0f}%"
            lines.append(f"| {i} | {d['city']}, {d['state']} ({d['code']}) | {money(d['typical'])} | "
                         f"{money(d['low'])} | {sw} |")
        lines.append("")

    swingy = [d for d in steady if d["swing"] is not None]
    if swingy:
        lines += ["## 🎢 Biggest price swings (worth waiting for a dip)", "",
                  "| Destination | Typical | Low | Swing |", "|---|---|---|---|"]
        for d in sorted(swingy, key=lambda d: -d["swing"])[:10]:
            lines.append(f"| {d['city']}, {d['state']} ({d['code']}) | {money(d['typical'])} | "
                         f"{money(d['low'])} | ±{d['swing']*50:.0f}% |")
        lines.append("")

    wr = {k: v for k, v in s["weekend_rel"].items() if v is not None}
    if wr and s["n_runs"] >= 2:
        lines += ["## 📅 Cheapest weekends overall", "",
                  "_Each fare compared with that city's typical price, then averaged across all cities._", "",
                  "| Weekend | vs. typical |", "|---|---|"]
        for d, v in sorted(wr.items(), key=lambda kv: kv[1]):
            lines.append(f"| {wk_label(d)} | {pct(v - 1)} |")
        lines.append("")

    if s["not_served"]:
        lines += ["## 🚫 No United flights found", "",
                  "These returned no United flights matching your times. Swap them in `airports.py` "
                  "for a nearby airport United flies to: " + ", ".join(s["not_served"]), ""]

    lines.append("_Raw data: `data/prices-YYYY-MM.csv` — one row per destination × departure day × weekend × run._")
    REPORT.write_text("\n".join(lines) + "\n")


def write_dashboard(s: dict):
    if not TEMPLATE.exists():
        return
    DASHBOARD.parent.mkdir(exist_ok=True)
    data = json.dumps(s, separators=(",", ":"), default=float).replace("</", "<\\/")
    DASHBOARD.write_text(TEMPLATE.read_text().replace("/*__DATA__*/null", data))


def write_alert(s: dict) -> bool:
    if ALERT.exists():
        ALERT.unlink()
    if not s["deals"]:
        return False
    last = {}
    if ALERTED_CSV.exists():
        for r in csv.DictReader(ALERTED_CSV.open()):
            last[(r["dest"], r["depart"])] = int(r["price"])
    fresh = [d for d in s["deals"]
             if (d["dest"], d["depart"]) not in last or d["price"] <= last[(d["dest"], d["depart"])] - 10]
    if not fresh:
        return False
    new = not ALERTED_CSV.exists()
    with ALERTED_CSV.open("a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["run_id", "dest", "depart", "price"])
        if new:
            w.writeheader()
        for d in fresh:
            w.writerow({"run_id": s["latest_run"], "dest": d["dest"], "depart": d["depart"], "price": d["price"]})
    body = [f"New weekend deals from ORD (United, regular Economy · {s['trip']}):", "",
            "| Destination | Weekend | Price | Typical | Off |", "|---|---|---|---|---|"]
    for d in fresh[:20]:
        more = f" (+{d['more']} more weekend{'s' if d['more'] > 1 else ''})" if d["more"] else ""
        body.append(f"| {d['city']}, {d['state']} ({d['dest']}) | {wk_label(d['depart'])}{more} | "
                    f"**{money(d['price'])}** | {money(d['typical'])} | {d['off']*100:.0f}% |")
    body += ["", "Prices change fast — confirm in Chase Travel before booking."]
    ALERT.write_text("\n".join(body) + "\n")
    return True


def main():
    df = load()
    if df is None:
        print("No data yet.")
        return
    s = summarize(df)
    write_report(s)
    write_dashboard(s)
    alerted = write_alert(s)
    best = min((d for d in s["dests"] if d["now"]), key=lambda d: d["now"], default=None)
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a") as fh:
            fh.write(f"alert={'true' if alerted else 'false'}\n")
            fh.write(f"deals={len(s['deals'])}\n")
    print(f"{len(s['dests'])} destinations | deals: {len(s['deals'])} | "
          f"cheapest: {best['code'] + ' ' + money(best['now']) if best else '—'} | alert: {alerted}")


if __name__ == "__main__":
    main()
