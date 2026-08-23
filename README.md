# F1 data pipeline — Week 1 (FastF1 → Postgres)

Loads race results (drivers, constructors, races, results) from FastF1 into a
Postgres database. Tested schema and insert logic locally — you only need to
run this against the real network on your own machine.

## Setup

1. **Make sure Postgres is running and create the database:**
   ```bash
   createdb f1_analytics
   ```

2. **Install Python dependencies** (Python 3.9+ recommended):
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your DB connection:**
   ```bash
   cp .env.example .env
   # then edit .env with your actual DB_USER / DB_PASSWORD if different from defaults
   ```

4. **Create the schema:**
   ```bash
   psql -d f1_analytics -f db/schema.sql
   ```

## Run

Test with a single round first — much faster than a whole season, and confirms
everything is wired up correctly:

```bash
python scripts/load_season.py 2023 --rounds 1
```

If that works, load a full season:

```bash
python scripts/load_season.py 2023
```

A full season is ~22-24 rounds. First run per session is slow (FastF1 has to
fetch and cache the data — expect a couple of minutes total); re-runs are much
faster because of the local cache in `fastf1_cache/`.

## Verify

```bash
psql -d f1db -c "
SELECT r.race_name, d.full_name, res.finish_position, res.points
FROM results res
JOIN races r ON r.race_id = res.race_id
JOIN drivers d ON d.driver_id = res.driver_id
WHERE r.season = 2023 AND r.round = 1
ORDER BY res.finish_position;
"
```

## Notes

- **Safe to re-run.** Every insert uses `ON CONFLICT` upserts, so running the
  script twice (or loading the same round again) won't create duplicates or
  error out.
- **If a round fails to load** (FastF1's backend is occasionally flaky for
  very recent races), the script logs it and moves to the next round instead
  of crashing.
- **Scope on purpose:** this loads results only — no lap times or pit stops
  yet. That matches the Week 1 build goal in the project plan. Add
  `lap_times` / `pit_stops` loading once your FastAPI + text-to-SQL layer is
  working end-to-end with this simpler data.
- Once this is loaded, your next step (per the plan) is writing the 5
  hardcoded SQL queries directly against this data before moving to FastAPI
  in Week 2.

Backend development in progress.