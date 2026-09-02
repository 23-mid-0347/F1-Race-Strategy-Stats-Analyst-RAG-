from typing import Optional
from datetime import date
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    database: str


class ConstructorStanding(BaseModel):
    name: str
    total_points: float


class DriverWinCount(BaseModel):
    full_name: str
    wins: int


class DriverPodiumCount(BaseModel):
    full_name: str
    podiums: int


class FastestLap(BaseModel):
    event_name: str
    full_name: str
    lap_number: int
    lap_time_ms: int


class DriverDetail(BaseModel):
    driver_id: int
    driver_code: str
    full_name: str
    nationality: Optional[str] = None
    date_of_birth: Optional[date] = None


class DriverStats(BaseModel):
    driver_id: int
    full_name: str
    season: Optional[int] = None
    races: int
    wins: int
    podiums: int
    poles: int
    dnfs: int
    avg_finish: Optional[float] = None


class EventSummary(BaseModel):
    event_id: int
    season: int
    round: int
    event_name: str
    circuit_name: Optional[str] = None
    event_date: Optional[date] = None


class PaginatedEvents(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[EventSummary]


class RaceResultRow(BaseModel):
    finish_position: Optional[int] = None
    grid_position: Optional[int] = None
    driver_code: str
    full_name: str
    constructor_name: Optional[str] = None
    points: float
    status: Optional[str] = None


class EventResults(BaseModel):
    event_id: int
    event_name: str
    season: int
    round: int
    results: list[RaceResultRow]