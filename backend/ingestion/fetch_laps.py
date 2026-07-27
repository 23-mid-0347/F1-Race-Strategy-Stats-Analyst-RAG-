"""
Loads lap-by-lap timing data (lap_times table) for a season's races.
Requires fetch_schedule.py to have been run first. Run fetch_results.py
first too if possible, so drivers already exist with real names.

Usage:
    python ingestion/fetch_laps.py 2023
    python ingestion/fetch_laps.py 2023 --rounds 1,2
"""
import sys
import os
import argparse
import time

import fastf1

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_engine
from ingestion.utils import (
    setup_fastf1_cache, get_season_id, get_event_id, upsert_session,
    get_driver_id_by_code, upsert_driver, insert_lap, safe_int, ms_from_timedelta,
)


def load_round_laps(engine, year, round_no):
    print(f"  Loading laps for {year} round {round_no}...")
    try:
        session = fastf1.get_session(year, round_no, "R")
        session.load(laps=True, telemetry=False, weather=False, messages=False)
    except Exception as e:
        print(f"    Skipped — could not load session: {e}")
        return

    laps = session.laps
    if laps is None or laps.empty:
        print("    Skipped — no lap data available for this session yet.")
        return

    with engine.begin() as conn:
        season_id = get_season_id(conn, year)
        event_id = get_event_id(conn, season_id, round_no) if season_id else None
        if event_id is None:
            print(f"    ERROR: round {round_no} not found for {year} — run fetch_schedule.py {year} first.")
            return
        session_id = upsert_session(conn, event_id, session_type="Race", session_date=None)

        saved = 0
        for _, row in laps.iterrows():
            code = row.get("Driver")
            driver_id = get_driver_id_by_code(conn, code)
            if driver_id is None:
                driver_id = upsert_driver(conn, code=code, full_name="Unknown", nationality=None)

            lap_number = safe_int(row.get("LapNumber"))
            if lap_number is None:
                continue  # can't store a lap without a lap number

            insert_lap(
                conn,
                session_id=session_id,
                driver_id=driver_id,
                lap_number=lap_number,
                lap_time_ms=ms_from_timedelta(row.get("LapTime")),
                tire_compound=row.get("Compound"),
            )
            saved += 1

    print(f"    Saved {saved} laps.")


def main():
    parser = argparse.ArgumentParser(description="Load lap times for a season into Postgres.")
    parser.add_argument("year", type=int)
    parser.add_argument("--rounds", type=str, default=None,
                         help="Comma-separated rounds, e.g. 1,2,3. Default: whole season.")
    args = parser.parse_args()

    setup_fastf1_cache()
    engine = get_engine()

    schedule = fastf1.get_event_schedule(args.year)
    schedule = schedule[schedule["RoundNumber"] > 0]
    if args.rounds:
        wanted = {int(r) for r in args.rounds.split(",")}
        schedule = schedule[schedule["RoundNumber"].isin(wanted)]

    for _, event in schedule.iterrows():
        load_round_laps(engine, args.year, int(event["RoundNumber"]))
        time.sleep(1)

    print("Done.")


if __name__ == "__main__":
    main()