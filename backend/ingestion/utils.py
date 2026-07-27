import os
import fastf1
import pandas as pd
from sqlalchemy import text

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache")


def setup_fastf1_cache():
    os.makedirs(CACHE_DIR, exist_ok=True)
    fastf1.Cache.enable_cache(CACHE_DIR)


def upsert_season(conn, year: int) -> int:
    result = conn.execute(
        text("""
            INSERT INTO seasons (year)
            VALUES (:year)
            ON CONFLICT (year) DO UPDATE SET year = EXCLUDED.year
            RETURNING season_id
        """),
        {"year": year},
    )
    return result.scalar_one()


def upsert_circuit(conn, name: str, location: str, country: str) -> int:
    result = conn.execute(
        text("""
            INSERT INTO circuits (name, location, country)
            VALUES (:name, :location, :country)
            ON CONFLICT (name) DO UPDATE SET location = EXCLUDED.location, country = EXCLUDED.country
            RETURNING circuit_id
        """),
        {"name": name, "location": location, "country": country},
    )
    return result.scalar_one()


def upsert_event(conn, season_id: int, round_no: int, event_name: str, circuit_id: int, event_date) -> int:
    result = conn.execute(
        text("""
            INSERT INTO events (season_id, round, event_name, circuit_id, event_date)
            VALUES (:season_id, :round, :event_name, :circuit_id, :event_date)
            ON CONFLICT (season_id, round) DO UPDATE SET
                event_name = EXCLUDED.event_name,
                circuit_id = EXCLUDED.circuit_id,
                event_date = EXCLUDED.event_date
            RETURNING event_id
        """),
        {"season_id": season_id, "round": round_no, "event_name": event_name,
         "circuit_id": circuit_id, "event_date": event_date},
    )
    return result.scalar_one()


def upsert_session(conn, event_id: int, session_type: str, session_date) -> int:
    # COALESCE keeps the existing date if this call doesn't have one (e.g. fetch_results.py
    # re-touching a session fetch_schedule.py already dated correctly)
    result = conn.execute(
        text("""
            INSERT INTO sessions (event_id, session_type, session_date)
            VALUES (:event_id, :session_type, :session_date)
            ON CONFLICT (event_id, session_type) DO UPDATE
                SET session_date = COALESCE(EXCLUDED.session_date, sessions.session_date)
            RETURNING session_id
        """),
        {"event_id": event_id, "session_type": session_type, "session_date": session_date},
    )
    return result.scalar_one()


def get_season_id(conn, year: int):
    row = conn.execute(text("SELECT season_id FROM seasons WHERE year = :year"), {"year": year}).first()
    return row[0] if row else None


def get_event_id(conn, season_id: int, round_no: int):
    row = conn.execute(
        text("SELECT event_id FROM events WHERE season_id = :season_id AND round = :round"),
        {"season_id": season_id, "round": round_no},
    ).first()
    return row[0] if row else None


def upsert_driver(conn, code: str, full_name: str, nationality: str) -> int:
    result = conn.execute(
        text("""
            INSERT INTO drivers (driver_code, full_name, nationality)
            VALUES (:code, :full_name, :nationality)
            ON CONFLICT (driver_code) DO UPDATE SET full_name = EXCLUDED.full_name
            RETURNING driver_id
        """),
        {"code": code, "full_name": full_name, "nationality": nationality},
    )
    return result.scalar_one()


def upsert_constructor(conn, name: str) -> int:
    result = conn.execute(
        text("""
            INSERT INTO constructors (name)
            VALUES (:name)
            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
            RETURNING constructor_id
        """),
        {"name": name},
    )
    return result.scalar_one()


def insert_result(conn, session_id, driver_id, constructor_id, grid_pos, finish_pos, points, status):
    conn.execute(
        text("""
            INSERT INTO results (session_id, driver_id, constructor_id, grid_position, finish_position, points, status)
            VALUES (:session_id, :driver_id, :constructor_id, :grid_pos, :finish_pos, :points, :status)
            ON CONFLICT (session_id, driver_id) DO UPDATE SET
                constructor_id = EXCLUDED.constructor_id,
                grid_position = EXCLUDED.grid_position,
                finish_position = EXCLUDED.finish_position,
                points = EXCLUDED.points,
                status = EXCLUDED.status
        """),
        {"session_id": session_id, "driver_id": driver_id, "constructor_id": constructor_id,
         "grid_pos": grid_pos, "finish_pos": finish_pos, "points": points, "status": status},
    )

def safe_numeric(value):
    """Convert NaN to None so we store SQL NULL instead of a literal NaN in NUMERIC columns."""
    if value is None or (isinstance(value, float) and value != value):  # NaN check
        return None
    return value

def safe_int(value):
    """FastF1 sometimes returns NaN for DNS/DNF positions — convert cleanly or return None."""
    try:
        if value is None or (isinstance(value, float) and value != value):  # NaN check
            return None
        return int(value)
    except (ValueError, TypeError):
        return None

def ms_from_timedelta(td):
    """Convert a pandas Timedelta (or NaT/None) to integer milliseconds, or None."""
    if td is None or pd.isna(td):
        return None
    return int(td.total_seconds() * 1000)


def get_driver_id_by_code(conn, code: str):
    """Look up a driver already created by fetch_results.py. Returns None if not found."""
    row = conn.execute(
        text("SELECT driver_id FROM drivers WHERE driver_code = :code"), {"code": code}
    ).first()
    return row[0] if row else None


def insert_lap(conn, session_id, driver_id, lap_number, lap_time_ms, tire_compound):
    conn.execute(
        text("""
            INSERT INTO lap_times (session_id, driver_id, lap_number, lap_time_ms, tire_compound)
            VALUES (:session_id, :driver_id, :lap_number, :lap_time_ms, :tire_compound)
            ON CONFLICT (session_id, driver_id, lap_number) DO UPDATE SET
                lap_time_ms = EXCLUDED.lap_time_ms,
                tire_compound = EXCLUDED.tire_compound
        """),
        {"session_id": session_id, "driver_id": driver_id, "lap_number": lap_number,
         "lap_time_ms": lap_time_ms, "tire_compound": tire_compound},
    )


def insert_pit_stop(conn, session_id, driver_id, stop_number, lap, duration_ms):
    conn.execute(
        text("""
            INSERT INTO pit_stops (session_id, driver_id, stop_number, lap, duration_ms)
            VALUES (:session_id, :driver_id, :stop_number, :lap, :duration_ms)
            ON CONFLICT (session_id, driver_id, stop_number) DO UPDATE SET
                lap = EXCLUDED.lap,
                duration_ms = EXCLUDED.duration_ms
        """),
        {"session_id": session_id, "driver_id": driver_id, "stop_number": stop_number,
         "lap": lap, "duration_ms": duration_ms},
    )


def insert_stint(conn, session_id, driver_id, stint_number, compound, lap_start, lap_end):
    conn.execute(
        text("""
            INSERT INTO stints (session_id, driver_id, stint_number, compound, lap_start, lap_end)
            VALUES (:session_id, :driver_id, :stint_number, :compound, :lap_start, :lap_end)
            ON CONFLICT (session_id, driver_id, stint_number) DO UPDATE SET
                compound = EXCLUDED.compound,
                lap_start = EXCLUDED.lap_start,
                lap_end = EXCLUDED.lap_end
        """),
        {"session_id": session_id, "driver_id": driver_id, "stint_number": stint_number,
         "compound": compound, "lap_start": lap_start, "lap_end": lap_end},
    )


def insert_weather(conn, session_id, recorded_at, air_temp, track_temp, humidity, rainfall, wind_speed):
    conn.execute(
        text("""
            INSERT INTO weather (session_id, recorded_at, air_temp, track_temp, humidity, rainfall, wind_speed)
            VALUES (:session_id, :recorded_at, :air_temp, :track_temp, :humidity, :rainfall, :wind_speed)
            ON CONFLICT (session_id, recorded_at) DO UPDATE SET
                air_temp = EXCLUDED.air_temp,
                track_temp = EXCLUDED.track_temp,
                humidity = EXCLUDED.humidity,
                rainfall = EXCLUDED.rainfall,
                wind_speed = EXCLUDED.wind_speed
        """),
        {"session_id": session_id, "recorded_at": recorded_at, "air_temp": air_temp,
         "track_temp": track_temp, "humidity": humidity, "rainfall": rainfall, "wind_speed": wind_speed},
    )