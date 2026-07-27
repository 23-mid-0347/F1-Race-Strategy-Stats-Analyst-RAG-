"""
Loads Race session results for a season into Postgres.
Requires fetch_schedule.py to have been run first for the same season —
this looks up existing events/sessions rather than creating new ones.

Usage:
    python ingestion/fetch_results.py 2023
    python ingestion/fetch_results.py 2023 --rounds 1,2
"""
import sys
import os
import argparse
import time

import fastf1

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_engine
from ingestion.utils import (
    safe_numeric, setup_fastf1_cache, get_season_id, get_event_id, upsert_session,
    upsert_driver, upsert_constructor, insert_result, safe_int,
)


def load_round_results(engine, year, round_no):
    print(f"  Loading results for {year} round {round_no}...")
    try:
        session = fastf1.get_session(year, round_no, "R")
        session.load(laps=False, telemetry=False, weather=False, messages=False)
    except Exception as e:
        print(f"    Skipped — could not load session: {e}")
        return

    results = session.results
    if results is None or results.empty:
        print("    Skipped — no results available for this session yet.")
        return

    with engine.begin() as conn:
        season_id = get_season_id(conn, year)
        if season_id is None:
            print(f"    ERROR: season {year} not found — run fetch_schedule.py {year} first.")
            return

        event_id = get_event_id(conn, season_id, round_no)
        if event_id is None:
            print(f"    ERROR: round {round_no} not found for {year} — run fetch_schedule.py {year} first.")
            return

        session_id = upsert_session(conn, event_id, session_type="Race", session_date=None)

        for _, row in results.iterrows():
            driver_id = upsert_driver(
                conn,
                code=row.get("Abbreviation") or str(row.get("DriverNumber")),
                full_name=row.get("FullName") or row.get("BroadcastName") or "Unknown",
                nationality=row.get("CountryCode"),
            )
            constructor_id = upsert_constructor(conn, name=row.get("TeamName") or "Unknown")

            insert_result(
                conn,
                session_id=session_id,
                driver_id=driver_id,
                constructor_id=constructor_id,
                grid_pos=safe_int(row.get("GridPosition")),
                finish_pos=safe_int(row.get("Position")),
                points=safe_numeric(row.get("Points")),
                status=row.get("Status"),
            )

    print(f"    Saved {len(results)} results.")


def main():
    parser = argparse.ArgumentParser(description="Load race results for a season into Postgres.")
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
        load_round_results(engine, args.year, int(event["RoundNumber"]))
        time.sleep(1)

    print("Done.")


if __name__ == "__main__":
    main()