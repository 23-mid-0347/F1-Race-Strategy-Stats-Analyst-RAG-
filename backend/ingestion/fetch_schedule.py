"""
Populates seasons, circuits, events, and sessions from FastF1's event schedule.
Run this BEFORE fetch_results.py — results attach to the sessions this creates.

Usage:
    python ingestion/fetch_schedule.py 2023
"""
import sys
import os
import argparse

import fastf1

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_engine
from ingestion.utils import setup_fastf1_cache, upsert_season, upsert_circuit, upsert_event, upsert_session


def main():
    parser = argparse.ArgumentParser(description="Load an F1 season's schedule (events + sessions) into Postgres.")
    parser.add_argument("year", type=int)
    args = parser.parse_args()

    setup_fastf1_cache()
    engine = get_engine()

    schedule = fastf1.get_event_schedule(args.year)
    schedule = schedule[schedule["RoundNumber"] > 0]  # round 0 is pre-season testing, skip it

    with engine.begin() as conn:
        season_id = upsert_season(conn, args.year)

        for _, event in schedule.iterrows():
            circuit_id = upsert_circuit(
                conn,
                name=event["Location"],       # FastF1's schedule doesn't expose an official circuit
                location=event["Location"],   # name, so we use Location (e.g. "Sakhir", "Monza") as the
                country=event["Country"],     # closest available stand-in for now
            )
            event_id = upsert_event(
                conn,
                season_id=season_id,
                round_no=int(event["RoundNumber"]),
                event_name=event["EventName"],
                circuit_id=circuit_id,
                event_date=event["EventDate"].date(),
            )

            for n in range(1, 6):
                session_name = event.get(f"Session{n}")
                session_date = event.get(f"Session{n}Date")
                if not session_name or session_name != session_name:  # skip missing/NaN
                    continue
                upsert_session(conn, event_id, session_type=session_name, session_date=session_date)

            print(f"  Loaded schedule for round {int(event['RoundNumber'])}: {event['EventName']}")

    print("Done.")


if __name__ == "__main__":
    main()