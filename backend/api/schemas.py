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