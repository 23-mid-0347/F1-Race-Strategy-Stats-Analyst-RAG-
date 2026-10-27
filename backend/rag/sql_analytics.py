"""Parameterized SQL templates for common F1 statistics questions.

This deliberately does not convert arbitrary user text into executable SQL.
Add new approved query templates here as the project grows.
"""
from __future__ import annotations

import re

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from rag.config import DEFAULT_SEASON
from database.connection import get_engine
from database.models import Event, Season


def _season_from_question(question: str) -> int:
    match = re.search(r"\b(20\d{2})\b", question)
    return int(match.group(1)) if match else DEFAULT_SEASON


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _find_event(db: Session, season: int, question: str):
    q = f" {_normalize(question)} "
    rows = db.execute(
        select(Event.event_id, Event.event_name)
        .join(Season, Season.season_id == Event.season_id)
        .where(Season.year == season)
    ).all()
    for row in rows:
        name = _normalize(row.event_name)
        short_name = re.sub(r"\bgrand prix\b", "", name).strip()
        if (name and f" {name} " in q) or (short_name and f" {short_name} " in q):
            return row
        meaningful = [part for part in short_name.split() if part not in {"the", "gp"}]
        if len(meaningful) >= 1 and all(f" {part} " in q for part in meaningful):
            return row
    return None


def answer_stats(question: str) -> str | None:
    """Run a known safe query template; return None when unsupported."""
    q = question.lower()
    season = _season_from_question(question)
    engine = get_engine()

    with Session(engine) as db:
        event = _find_event(db, season, question)

        if "fastest lap" in q and event:
            row = db.execute(
                text("""
                    SELECT e.event_name, d.full_name, l.lap_number, l.lap_time_ms
                    FROM lap_times l
                    JOIN sessions s ON s.session_id = l.session_id
                    JOIN events e ON e.event_id = s.event_id
                    JOIN seasons se ON se.season_id = e.season_id
                    JOIN drivers d ON d.driver_id = l.driver_id
                    WHERE e.event_id = :event_id
                      AND se.year = :season
                      AND s.session_type = 'Race'
                      AND l.lap_time_ms IS NOT NULL
                    ORDER BY l.lap_time_ms ASC
                    LIMIT 1
                """), {"event_id": event.event_id, "season": season}
            ).first()
            if row is None:
                return f"No fastest-lap data is available for {event.event_name} in {season}."
            return (
                f"Fastest recorded lap at the {event.event_name} ({season}): "
                f"{row.full_name}, lap {row.lap_number}, {row.lap_time_ms / 1000:.3f} seconds."
            )

        # If a specific event is named, answer its winner from that event's result row
        # before considering season-wide win counts. This prevents a question such as
        # "Why did Verstappen win Singapore?" from receiving the entire season leaderboard.
        win_word = bool(re.search(r"\b(?:win|wins|won|winner|victory|victories)\b", q))
        aggregate_win_question = bool(
            re.search(r"\b(?:most|total|how many|number of|count of)\b.{0,35}\b(?:wins?|victories)\b", q)
            or re.search(r"\bdriver wins\b", q)
        )
        event_winner_question = bool(event and win_word and not aggregate_win_question)

        if event and (event_winner_question or "race result" in q):
            row = db.execute(
                text("""
                    SELECT e.event_name, d.full_name, c.name AS constructor_name
                    FROM results res
                    JOIN sessions s ON s.session_id = res.session_id
                    JOIN events e ON e.event_id = s.event_id
                    JOIN seasons se ON se.season_id = e.season_id
                    JOIN drivers d ON d.driver_id = res.driver_id
                    LEFT JOIN constructors c ON c.constructor_id = res.constructor_id
                    WHERE e.event_id = :event_id
                      AND se.year = :season
                      AND s.session_type = 'Race'
                      AND res.finish_position = 1
                    LIMIT 1
                """), {"event_id": event.event_id, "season": season}
            ).first()
            if row is None:
                return f"No race-winner result is available for {event.event_name} in {season}."
            return (
                f"EVENT-SPECIFIC RACE WINNER — {row.event_name} ({season}): "
                f"{row.full_name} ({row.constructor_name}). Use this event result to check "
                "any claim about who won this race; do not substitute season-wide win totals."
            )

        if ("constructor" in q or "team" in q) and any(term in q for term in ("standing", "points", "championship", "ranking")):
            rows = db.execute(
                text("""
                    SELECT c.name, SUM(res.points) AS total_points
                    FROM results res
                    JOIN constructors c ON c.constructor_id = res.constructor_id
                    JOIN sessions s ON s.session_id = res.session_id
                    JOIN events e ON e.event_id = s.event_id
                    JOIN seasons se ON se.season_id = e.season_id
                    WHERE se.year = :season
                    GROUP BY c.name
                    ORDER BY total_points DESC
                    LIMIT 10
                """), {"season": season}
            ).all()
            if not rows:
                return f"No constructor points were found for {season}."
            lines = [f"Constructor standings for {season} (Race + Sprint points):"]
            lines += [f"{i}. {r.name}: {float(r.total_points):g} points" for i, r in enumerate(rows, 1)]
            return "\n".join(lines)

        if "driver" in q and any(term in q for term in ("standing", "points", "championship", "ranking")):
            rows = db.execute(
                text("""
                    SELECT d.full_name, SUM(res.points) AS total_points
                    FROM results res
                    JOIN drivers d ON d.driver_id = res.driver_id
                    JOIN sessions s ON s.session_id = res.session_id
                    JOIN events e ON e.event_id = s.event_id
                    JOIN seasons se ON se.season_id = e.season_id
                    WHERE se.year = :season
                    GROUP BY d.full_name
                    ORDER BY total_points DESC
                    LIMIT 10
                """), {"season": season}
            ).all()
            if not rows:
                return f"No driver points were found for {season}."
            lines = [f"Driver standings for {season} (Race + Sprint points):"]
            lines += [f"{i}. {r.full_name}: {float(r.total_points):g} points" for i, r in enumerate(rows, 1)]
            return "\n".join(lines)

        if "podium" in q:
            rows = db.execute(
                text("""
                    SELECT d.full_name, COUNT(*) AS podiums
                    FROM results res
                    JOIN drivers d ON d.driver_id = res.driver_id
                    JOIN sessions s ON s.session_id = res.session_id
                    JOIN events e ON e.event_id = s.event_id
                    JOIN seasons se ON se.season_id = e.season_id
                    WHERE se.year = :season
                      AND s.session_type = 'Race'
                      AND res.finish_position BETWEEN 1 AND 3
                    GROUP BY d.full_name
                    ORDER BY podiums DESC, d.full_name
                    LIMIT 10
                """), {"season": season}
            ).all()
            if not rows:
                return f"No podium data was found for {season}."
            lines = [f"Driver podiums in {season} (Race sessions):"]
            lines += [f"{i}. {r.full_name}: {r.podiums} podiums" for i, r in enumerate(rows, 1)]
            return "\n".join(lines)

        if "win" in q or re.search(r"\bwon the most\b", q):
            rows = db.execute(
                text("""
                    SELECT d.full_name, COUNT(*) AS wins
                    FROM results res
                    JOIN drivers d ON d.driver_id = res.driver_id
                    JOIN sessions s ON s.session_id = res.session_id
                    JOIN events e ON e.event_id = s.event_id
                    JOIN seasons se ON se.season_id = e.season_id
                    WHERE se.year = :season
                      AND s.session_type = 'Race'
                      AND res.finish_position = 1
                    GROUP BY d.full_name
                    ORDER BY wins DESC, d.full_name
                    LIMIT 10
                """), {"season": season}
            ).all()
            if not rows:
                return f"No race-win data was found for {season}."
            lines = [f"Driver wins in {season} (Race sessions):"]
            lines += [f"{i}. {r.full_name}: {r.wins} wins" for i, r in enumerate(rows, 1)]
            return "\n".join(lines)

        if any(term in q for term in ("how many drivers", "number of drivers", "driver count")):
            count = db.execute(
                text("""
                    SELECT COUNT(DISTINCT res.driver_id)
                    FROM results res
                    JOIN sessions s ON s.session_id = res.session_id
                    JOIN events e ON e.event_id = s.event_id
                    JOIN seasons se ON se.season_id = e.season_id
                    WHERE se.year = :season AND s.session_type = 'Race'
                """), {"season": season}
            ).scalar_one()
            return f"There were {count} distinct race drivers in the loaded {season} season."

        if any(term in q for term in ("how many constructors", "number of constructors", "constructor count", "how many teams")):
            count = db.execute(
                text("""
                    SELECT COUNT(DISTINCT res.constructor_id)
                    FROM results res
                    JOIN sessions s ON s.session_id = res.session_id
                    JOIN events e ON e.event_id = s.event_id
                    JOIN seasons se ON se.season_id = e.season_id
                    WHERE se.year = :season AND s.session_type = 'Race'
                """), {"season": season}
            ).scalar_one()
            return f"There were {count} constructors represented in race results for {season}."

    return None
