"""Request and response schemas for the AI Analyst endpoint."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class AnalystRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


class AnalystSource(BaseModel):
    title: str
    source_url: HttpUrl
    event_name: str | None = None
    season: int | None = None
    distance: float | None = None


class AnalystResponse(BaseModel):
    answer: str
    route: Literal["stats", "narrative", "hybrid"]
    sources: list[AnalystSource] = Field(default_factory=list)
