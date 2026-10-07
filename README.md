# 🗺️ United Weekend Fare Tracker (from Chicago ORD)

A free bot that checks United round-trip fares from O'Hare to **70 airports**
(United's ~50 biggest US destinations plus at least one airport in every state
United serves) for each of the **next 10 weekends**, twice a day.

It builds:

- **An interactive map dashboard**: US map colored by the cheapest fare to each
  state, a sortable table of every city with price trends, and a
  weekend-by-city grid showing which weekends are cheap.
- **REPORT.md**: cheapest right now, consistently cheap cities, biggest price
  swings, cheapest weekends overall.
- **Deal emails** when a city drops 20%+ below its *own* typical price.

**Search settings:** United only · regular Economy (no Basic, matching what Chase
Travel sells) · 1 adult
- **Leave ORD** any time from **Thursday 6 PM to Friday 6 PM**
- **Return Sunday**, landing back at ORD **by 10 PM**

That's two searches per city per weekend (Thursday evening + Friday daytime), and
the bot keeps whichever is cheaper. About 1,400 searches per run, split across
**4 GitHub machines running at the same time** so each run finishes in ~20 minutes
and no single machine hits Google too hard.

**Cost: $0** on GitHub's free tier.

---

## Setup (about 10 minutes)

### 1. Create a new **public** repository
**+** (top right) → **New repository** → name it `weekend-tracker` → choose
**Public** → **Create repository**.

> Why public? GitHub's free plan only hosts the map page (GitHub Pages) for public
> repos, and public repos get unlimited Actions minutes. This bot uses 4 machines ×
> ~20 min × 2 runs a day, well over a private repo's free 2,000 min/month.
> Nothing in the repo is personal; it's just fare data.

### 2. Upload the files
1. Unzip `weekend-tracker.zip` and open the `weekend-tracker` folder.
2. On your repo page: **uploading an existing file** (or **Add file → Upload files**).
3. Drag in everything inside the folder: `airports.py`, `analyze.py`, `config.py`,
   `tracker.py`, `merge.py`, `requirements.txt`, `dashboard_template.html`,
   `README.md`, and the `docs` folder.
4. **Commit changes**.

### 3. Add the workflow file (the schedule)
The hidden `.github` folder usually won't drag-and-drop, so create it by hand:
1. **Add file → Create new file**.
2. Name it exactly: `.github/workflows/weekend.yml`
3. Open `weekend.yml` from the unzipped folder (it's inside `.github/workflows/`;
   show hidden files to see it) in Notepad or TextEdit, copy everything, and paste.
4. **Commit changes**.

### 4. Let the bot save data
**Settings → Actions → General → Workflow permissions → Read and write permissions → Save.**

### 5. Turn on the map page
**Settings → Pages** → under *Build and deployment*, Source: **Deploy from a branch**
→ Branch: **main**, folder: **/docs** → **Save**.

After a minute the page shows your link, something like
`https://YOUR-USERNAME.github.io/weekend-tracker/`. Bookmark it on your phone.

### 6. Run it once
**Actions → Track weekend fares → Run workflow → Run workflow.**
It takes **about 20–25 minutes**. You'll see 4 "track" jobs run side by side, then a
"publish" job that combines them.
When it's green, refresh your map link and open **REPORT.md**.

After that it runs automatically around **7:45 AM and 6:45 PM** Chicago time.

---

## What to expect over time

| When | What you'll see |
|---|---|
| After run 1 | Today's cheapest fares, map, every-weekend grid |
| After ~2 days (4 runs) | "Typical price" per city, price swings, **deal emails start** |
| After 1–2 weeks | Reliable "consistently cheap" ranking and trend lines |

## Changing settings

**`config.py`**
- `DEPART_WINDOWS`: when you can leave, e.g. `(3, 18, None)` = Thursday after 6 PM
- `RETURN_WEEKDAY` / `RETURN_LATEST_ARRIVAL_HOUR`: when you need to be back
- `WEEKENDS_AHEAD`: how many weekends to track (more = longer runs)
- `DEAL_THRESHOLD`: `0.20` = email when 20% below typical
- `DEAL_MAX_PRICE`: e.g. `250` to only email deals under $250

**`airports.py`**: add or remove destinations, one line each.

> Changing the weekend shape or times mid-way mixes old and new prices. If you do,
> delete the files in `data/` to start fresh.

## Things to know

- **Prices come from Google Flights**, not Chase. United's Economy cash fares
  should match Chase Travel closely, but always confirm in Chase before booking.
- **"No United flights found"**: if an airport shows up in that list, United
  doesn't fly there at your times. Swap it in `airports.py` for a nearby airport.
- **Delaware** has no United service; Philadelphia (PHL) covers it.
  **Illinois** is skipped since it's home.
- **Occasional failed searches are normal.** If the report warns that lots
  failed, Google throttled that run; the next one usually recovers. If every run
  fails for a day, update the version in `requirements.txt` to the newest
  [fast-flights](https://pypi.org/project/fast-flights/) release.
- Scheduled runs can start 5–30 minutes late. That's GitHub's free scheduler.

## Files

| File | What it does |
|---|---|
| `tracker.py` | Searches every airport × weekend (each machine does a quarter) |
| `merge.py` | Combines the 4 machines' results into `data/prices-YYYY-MM.csv` |
| `analyze.py` | Builds `REPORT.md`, the map page, and deal alerts |
| `dashboard_template.html` | Design of the map page (data gets filled in each run) |
| `docs/index.html` | The live map page GitHub Pages serves |
| `airports.py` / `config.py` | What to track |
| `.github/workflows/weekend.yml` | Runs it twice a day on 4 machines in parallel |
