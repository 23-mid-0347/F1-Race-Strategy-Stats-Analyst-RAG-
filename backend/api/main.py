import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas import (
    HealthResponse, ConstructorStanding, DriverWinCount, DriverPodiumCount, FastestLap,
)

app = FastAPI(title="F1 Analytics API", version="0.1.0")


@app.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "unreachable"
    return HealthResponse(status="ok", database=db_status)


@app.get("/constructors/standings", response_model=list[ConstructorStanding])
def constructor_standings(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT c.name, SUM(res.points) AS total_points
        FROM results res
        JOIN constructors c ON c.constructor_id = res.constructor_id
        GROUP BY c.name
        ORDER BY total_points DESC
    """)).all()
    return [ConstructorStanding(name=r.name, total_points=float(r.total_points)) for r in rows]


@app.get("/drivers/wins", response_model=list[DriverWinCount])
def driver_wins(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT d.full_name, COUNT(*) AS wins
        FROM results res
        JOIN drivers d ON d.driver_id = res.driver_id
        JOIN sessions s ON s.session_id = res.session_id
        WHERE res.finish_position = 1 AND s.session_type = 'Race'
        GROUP BY d.full_name
        ORDER BY wins DESC
    """)).all()
    return [DriverWinCount(full_name=r.full_name, wins=r.wins) for r in rows]


@app.get("/drivers/podiums", response_model=list[DriverPodiumCount])
def driver_podiums(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT d.full_name, COUNT(*) AS podiums
        FROM results res
        JOIN drivers d ON d.driver_id = res.driver_id
        JOIN sessions s ON s.session_id = res.session_id
        WHERE res.finish_position BETWEEN 1 AND 3 AND s.session_type = 'Race'
        GROUP BY d.full_name
        ORDER BY podiums DESC
    """)).all()
    return [DriverPodiumCount(full_name=r.full_name, podiums=r.podiums) for r in rows]


@app.get("/sessions/{session_id}/fastest-lap", response_model=FastestLap)
def fastest_lap(session_id: int, db: Session = Depends(get_db)):
    row = db.execute(text("""
        SELECT e.event_name, d.full_name, l.lap_number, l.lap_time_ms
        FROM lap_times l
        JOIN sessions s ON s.session_id = l.session_id
        JOIN events e ON e.event_id = s.event_id
        JOIN drivers d ON d.driver_id = l.driver_id
        WHERE l.session_id = :session_id
        ORDER BY l.lap_time_ms ASC
        LIMIT 1
    """), {"session_id": session_id}).first()

    if row is None:
        raise HTTPException(status_code=404, detail=f"No lap data found for session_id {session_id}")

    return FastestLap(
        event_name=row.event_name, full_name=row.full_name,
        lap_number=row.lap_number, lap_time_ms=row.lap_time_ms,
    )