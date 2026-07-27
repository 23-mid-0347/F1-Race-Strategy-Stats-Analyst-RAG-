"""
Loads weather readings (weather table) for a season's races.

Usage:
    python ingestion/fetch_weather.py 2023
    python ingestion/fetch_weather.py 2023 --rounds 1,2
"""
import sys
import os
import argparse
import time

import fastf1
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_engine
from ingestion.utils import setup_fastf1_cache, get_season_id, get_event_id, upsert_session, insert_weather


def load_round_weather(engine, year, round_no):
    print(f"  Loading weather for {year} round {round_no}...")
    try:
        session = fastf1.get_session(year, round_no, "R")
        session.load(laps=False, telemetry=False, weather=True, messages=False)
    except Exception as e:
        print(f"    Skipped — could not load session: {e}")
        return

    weather = session.weather_data
    if weather is None or weather.empty:
        print("    Skipped — no weather data available for this session yet.")
        return

    with engine.begin() as conn:
        season_id = get_season_id(conn, year)
        event_id = get_event_id(conn, season_id, round_no) if season_id else None
        if event_id is None:
            print(f"    ERROR: round {round_no} not found for {year} — run fetch_schedule.py {year} first.")
            return
        session_id = upsert_session(conn, event_id, session_type="Race", session_date=None)

        # FastF1 gives Time as a session-relative timedelta, not a wall-clock timestamp.
        # session.date is the session's real start time, so we add the two to reconstruct
        # an actual timestamp — approximate to the second, fine for trends/ordering.
        session_start = session.date

        saved = 0
        for _, row in weather.iterrows():
            elapsed = row.get("Time")
            recorded_at = (session_start + elapsed) if pd.notna(elapsed) else None

            insert_weather(
                conn,
                session_id=session_id,
                recorded_at=recorded_at,
                air_temp=row.get("AirTemp"),
                track_temp=row.get("TrackTemp"),
                humidity=row.get("Humidity"),
                rainfall=bool(row.get("Rainfall")) if pd.notna(row.get("Rainfall")) else None,
                wind_speed=row.get("WindSpeed"),
            )
            saved += 1

    print(f"    Saved {saved} weather readings.")


def main():
    parser = argparse.ArgumentParser(description="Load weather data for a season into Postgres.")
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
        load_round_weather(engine, args.year, int(event["RoundNumber"]))
        time.sleep(1)

    print("Done.")


if __name__ == "__main__":
    main()