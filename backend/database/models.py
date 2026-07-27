from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import String, Integer, Numeric, Date, DateTime, Boolean, ForeignKey, UniqueConstraint, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Driver(Base):
    __tablename__ = "drivers"

    driver_id: Mapped[int] = mapped_column(primary_key=True)
    driver_code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    nationality: Mapped[Optional[str]] = mapped_column(String)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date)

    results: Mapped[List["Result"]] = relationship(back_populates="driver")


class Constructor(Base):
    __tablename__ = "constructors"

    constructor_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    nationality: Mapped[Optional[str]] = mapped_column(String)

    results: Mapped[List["Result"]] = relationship(back_populates="constructor")


class Circuit(Base):
    __tablename__ = "circuits"

    circuit_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String)
    country: Mapped[Optional[str]] = mapped_column(String)

    events: Mapped[List["Event"]] = relationship(back_populates="circuit")


class Season(Base):
    __tablename__ = "seasons"

    season_id: Mapped[int] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)

    events: Mapped[List["Event"]] = relationship(back_populates="season")


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (UniqueConstraint("season_id", "round"),)

    event_id: Mapped[int] = mapped_column(primary_key=True)
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.season_id"), nullable=False)
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    event_name: Mapped[str] = mapped_column(String, nullable=False)
    circuit_id: Mapped[Optional[int]] = mapped_column(ForeignKey("circuits.circuit_id"))
    event_date: Mapped[Optional[date]] = mapped_column(Date)

    season: Mapped["Season"] = relationship(back_populates="events")
    circuit: Mapped[Optional["Circuit"]] = relationship(back_populates="events")
    sessions: Mapped[List["Session"]] = relationship(back_populates="event", cascade="all, delete-orphan")
    documents: Mapped[List["Document"]] = relationship(back_populates="event")


class Session(Base):
    __tablename__ = "sessions"
    __table_args__ = (UniqueConstraint("event_id", "session_type"),)

    session_id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.event_id", ondelete="CASCADE"), nullable=False)
    session_type: Mapped[str] = mapped_column(String, nullable=False)  # 'FP1','FP2','FP3','Q','SQ','R'
    session_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    event: Mapped["Event"] = relationship(back_populates="sessions")
    results: Mapped[List["Result"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    lap_times: Mapped[List["LapTime"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    pit_stops: Mapped[List["PitStop"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    stints: Mapped[List["Stint"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    weather_readings: Mapped[List["Weather"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class Result(Base):
    __tablename__ = "results"
    __table_args__ = (UniqueConstraint("session_id", "driver_id"),)

    result_id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.session_id", ondelete="CASCADE"), nullable=False)
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.driver_id"), nullable=False)
    constructor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("constructors.constructor_id"))
    grid_position: Mapped[Optional[int]] = mapped_column(Integer)
    finish_position: Mapped[Optional[int]] = mapped_column(Integer)
    points: Mapped[Optional[Decimal]] = mapped_column(Numeric)
    status: Mapped[Optional[str]] = mapped_column(String)

    session: Mapped["Session"] = relationship(back_populates="results")
    driver: Mapped["Driver"] = relationship(back_populates="results")
    constructor: Mapped[Optional["Constructor"]] = relationship(back_populates="results")


class LapTime(Base):
    __tablename__ = "lap_times"
    __table_args__ = (UniqueConstraint("session_id", "driver_id", "lap_number"),)

    lap_id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.session_id", ondelete="CASCADE"), nullable=False)
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.driver_id"), nullable=False)
    lap_number: Mapped[int] = mapped_column(Integer, nullable=False)
    lap_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    tire_compound: Mapped[Optional[str]] = mapped_column(String)

    session: Mapped["Session"] = relationship(back_populates="lap_times")


class PitStop(Base):
    __tablename__ = "pit_stops"
    __table_args__ = (UniqueConstraint("session_id", "driver_id", "stop_number"),)

    pit_stop_id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.session_id", ondelete="CASCADE"), nullable=False)
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.driver_id"), nullable=False)
    stop_number: Mapped[int] = mapped_column(Integer, nullable=False)
    lap: Mapped[Optional[int]] = mapped_column(Integer)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)

    session: Mapped["Session"] = relationship(back_populates="pit_stops")


class Stint(Base):
    __tablename__ = "stints"
    __table_args__ = (UniqueConstraint("session_id", "driver_id", "stint_number"),)

    stint_id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.session_id", ondelete="CASCADE"), nullable=False)
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.driver_id"), nullable=False)
    stint_number: Mapped[int] = mapped_column(Integer, nullable=False)
    compound: Mapped[Optional[str]] = mapped_column(String)
    lap_start: Mapped[Optional[int]] = mapped_column(Integer)
    lap_end: Mapped[Optional[int]] = mapped_column(Integer)

    session: Mapped["Session"] = relationship(back_populates="stints")


class Weather(Base):
    __tablename__ = "weather"
    __table_args__ = (UniqueConstraint("session_id", "recorded_at"),)

    weather_id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.session_id", ondelete="CASCADE"), nullable=False)
    recorded_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    air_temp: Mapped[Optional[Decimal]] = mapped_column(Numeric)
    track_temp: Mapped[Optional[Decimal]] = mapped_column(Numeric)
    humidity: Mapped[Optional[Decimal]] = mapped_column(Numeric)
    rainfall: Mapped[Optional[bool]] = mapped_column(Boolean)
    wind_speed: Mapped[Optional[Decimal]] = mapped_column(Numeric)

    session: Mapped["Session"] = relationship(back_populates="weather_readings")


class Document(Base):
    __tablename__ = "documents"

    doc_id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[Optional[int]] = mapped_column(ForeignKey("events.event_id"))
    source_url: Mapped[Optional[str]] = mapped_column(Text)
    title: Mapped[Optional[str]] = mapped_column(String)
    content_type: Mapped[Optional[str]] = mapped_column(String)
    scraped_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    event: Mapped[Optional["Event"]] = relationship(back_populates="documents")
    embeddings: Mapped[List["EmbeddingMetadata"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class EmbeddingMetadata(Base):
    __tablename__ = "embeddings_metadata"
    __table_args__ = (UniqueConstraint("doc_id", "chunk_index"),)

    embedding_id: Mapped[int] = mapped_column(primary_key=True)
    doc_id: Mapped[int] = mapped_column(ForeignKey("documents.doc_id", ondelete="CASCADE"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text_preview: Mapped[Optional[str]] = mapped_column(Text)
    vector_db_id: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    document: Mapped["Document"] = relationship(back_populates="embeddings")