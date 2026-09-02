import sys
import os
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas import (
    HealthResponse, ConstructorStanding, DriverWinCount, DriverPodiumCount, FastestLap,
    DriverDetail, DriverStats, EventSummary, PaginatedEvents, RaceResultRow, EventResults,
)

app = FastAPI(title="F1 Analytics API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "unreachable"
    return HealthResponse(status="ok", database=db_status)


@app.get("/constructors/standings", response_model=list[ConstructorStanding])
def constructor_standings(
    season: Optional[int] = Query(None, description="Filter to one season, e.g. 2023. Omit for all seasons combined."),
    db: Session = Depends(get_db),
):
    rows = db.execute(text("""
        SELECT c.name, SUM(res.points) AS total_points
        FROM results res
        JOIN constructors c ON c.constructor_id = res.constructor_id
        JOIN sessions s ON s.session_id = res.session_id
        JOIN events e ON e.event_id = s.event_id
        JOIN seasons se ON se.season_id = e.season_id
        WHERE (CAST(:season AS INTEGER) IS NULL OR se.year = CAST(:season AS INTEGER))
        GROUP BY c.name
        ORDER BY total_points DESC
    """), {"season": season}).all()
    return [ConstructorStanding(name=r.name, total_points=float(r.total_points)) for r in rows]


@app.get("/drivers/wins", response_model=list[DriverWinCount])
def driver_wins(
    season: Optional[int] = Query(None, description="Filter to one season, e.g. 2023. Omit for all seasons combined."),
    db: Session = Depends(get_db),
):
    rows = db.execute(text("""
        SELECT d.full_name, COUNT(*) AS wins
        FROM results res
        JOIN drivers d ON d.driver_id = res.driver_id
        JOIN sessions s ON s.session_id = res.session_id
        JOIN events e ON e.event_id = s.event_id
        JOIN seasons se ON se.season_id = e.season_id
        WHERE res.finish_position = 1 AND s.session_type = 'Race'
          AND (CAST(:season AS INTEGER) IS NULL OR se.year = CAST(:season AS INTEGER))
        GROUP BY d.full_name
        ORDER BY wins DESC
    """), {"season": season}).all()
    return [DriverWinCount(full_name=r.full_name, wins=r.wins) for r in rows]


@app.get("/drivers/podiums", response_model=list[DriverPodiumCount])
def driver_podiums(
    season: Optional[int] = Query(None, description="Filter to one season, e.g. 2023. Omit for all seasons combined."),
    db: Session = Depends(get_db),
):
    rows = db.execute(text("""
        SELECT d.full_name, COUNT(*) AS podiums
        FROM results res
        JOIN drivers d ON d.driver_id = res.driver_id
        JOIN sessions s ON s.session_id = res.session_id
        JOIN events e ON e.event_id = s.event_id
        JOIN seasons se ON se.season_id = e.season_id
        WHERE res.finish_position BETWEEN 1 AND 3 AND s.session_type = 'Race'
          AND (CAST(:season AS INTEGER) IS NULL OR se.year = CAST(:season AS INTEGER))
        GROUP BY d.full_name
        ORDER BY podiums DESC
    """), {"season": season}).all()
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


@app.get("/drivers/{driver_id}", response_model=DriverDetail)
def get_driver(driver_id: int, db: Session = Depends(get_db)):
    row = db.execute(text("""
        SELECT driver_id, driver_code, full_name, nationality, date_of_birth
        FROM drivers WHERE driver_id = :driver_id
    """), {"driver_id": driver_id}).first()

    if row is None:
        raise HTTPException(status_code=404, detail=f"No driver found with driver_id {driver_id}")

    return DriverDetail(
        driver_id=row.driver_id, driver_code=row.driver_code, full_name=row.full_name,
        nationality=row.nationality, date_of_birth=row.date_of_birth,
    )


@app.get("/drivers/{driver_id}/stats", response_model=DriverStats)
def get_driver_stats(
    driver_id: int,
    season: Optional[int] = Query(None, description="Filter to one season, e.g. 2023. Omit for career totals."),
    db: Session = Depends(get_db),
):
    driver = db.execute(
        text("SELECT driver_id, full_name FROM drivers WHERE driver_id = :driver_id"),
        {"driver_id": driver_id},
    ).first()
    if driver is None:
        raise HTTPException(status_code=404, detail=f"No driver found with driver_id {driver_id}")

    row = db.execute(text("""
        SELECT
            COUNT(*) FILTER (WHERE s.session_type = 'Race') AS races,
            COUNT(*) FILTER (WHERE res.finish_position = 1 AND s.session_type = 'Race') AS wins,
            COUNT(*) FILTER (WHERE res.finish_position BETWEEN 1 AND 3 AND s.session_type = 'Race') AS podiums,
            COUNT(*) FILTER (WHERE res.grid_position = 1 AND s.session_type = 'Race') AS poles,
            COUNT(*) FILTER (
                WHERE res.status NOT IN ('Finished') AND res.status NOT LIKE '%Lap%' AND s.session_type = 'Race'
            ) AS dnfs,
            ROUND(AVG(res.finish_position) FILTER (WHERE s.session_type = 'Race'), 2) AS avg_finish
        FROM results res
        JOIN sessions s ON s.session_id = res.session_id
        JOIN events e ON e.event_id = s.event_id
        JOIN seasons se ON se.season_id = e.season_id
        WHERE res.driver_id = :driver_id AND (CAST(:season AS INTEGER) IS NULL OR se.year = CAST(:season AS INTEGER))
    """), {"driver_id": driver_id, "season": season}).first()

    return DriverStats(
        driver_id=driver.driver_id, full_name=driver.full_name, season=season,
        races=row.races, wins=row.wins, podiums=row.podiums, poles=row.poles,
        dnfs=row.dnfs, avg_finish=float(row.avg_finish) if row.avg_finish is not None else None,
    )


@app.get("/events", response_model=PaginatedEvents)
def list_events(
    season: Optional[int] = Query(None, description="Filter to one season, e.g. 2023. Omit for all seasons."),
    limit: int = Query(20, ge=1, le=100, description="Max results per page (1-100)."),
    offset: int = Query(0, ge=0, description="Number of results to skip, for paging."),
    db: Session = Depends(get_db),
):
    total = db.execute(text("""
        SELECT COUNT(*)
        FROM events e
        JOIN seasons se ON se.season_id = e.season_id
        WHERE (CAST(:season AS INTEGER) IS NULL OR se.year = CAST(:season AS INTEGER))
    """), {"season": season}).scalar_one()

    rows = db.execute(text("""
        SELECT e.event_id, se.year AS season, e.round, e.event_name, c.name AS circuit_name, e.event_date
        FROM events e
        JOIN seasons se ON se.season_id = e.season_id
        LEFT JOIN circuits c ON c.circuit_id = e.circuit_id
        WHERE (CAST(:season AS INTEGER) IS NULL OR se.year = CAST(:season AS INTEGER))
        ORDER BY se.year, e.round
        LIMIT :limit OFFSET :offset
    """), {"season": season, "limit": limit, "offset": offset}).all()

    items = [
        EventSummary(
            event_id=r.event_id, season=r.season, round=r.round,
            event_name=r.event_name, circuit_name=r.circuit_name, event_date=r.event_date,
        )
        for r in rows
    ]
    return PaginatedEvents(total=total, limit=limit, offset=offset, items=items)


@app.get("/events/{event_id}/results", response_model=EventResults)
def get_event_results(event_id: int, db: Session = Depends(get_db)):
    event = db.execute(text("""
        SELECT e.event_id, e.event_name, e.round, se.year AS season
        FROM events e
        JOIN seasons se ON se.season_id = e.season_id
        WHERE e.event_id = :event_id
    """), {"event_id": event_id}).first()

    if event is None:
        raise HTTPException(status_code=404, detail=f"No event found with event_id {event_id}")

    rows = db.execute(text("""
        SELECT res.finish_position, res.grid_position, d.driver_code, d.full_name,
               c.name AS constructor_name, res.points, res.status
        FROM results res
        JOIN sessions s ON s.session_id = res.session_id
        JOIN drivers d ON d.driver_id = res.driver_id
        LEFT JOIN constructors c ON c.constructor_id = res.constructor_id
        WHERE s.event_id = :event_id AND s.session_type = 'Race'
        ORDER BY res.finish_position ASC NULLS LAST
    """), {"event_id": event_id}).all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"Event {event_id} exists but has no Race results loaded yet.",
        )

    results = [
        RaceResultRow(
            finish_position=r.finish_position, grid_position=r.grid_position,
            driver_code=r.driver_code, full_name=r.full_name,
            constructor_name=r.constructor_name,
            points=float(r.points) if r.points is not None else 0.0,
            status=r.status,
        )
        for r in rows
    ]

    return EventResults(
        event_id=event.event_id, event_name=event.event_name,
        season=event.season, round=event.round, results=results,
    )