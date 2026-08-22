from functools import lru_cache
from sqlalchemy.orm import sessionmaker, Session

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_engine


@lru_cache
def _get_session_factory():
    """Engine + sessionmaker are built once and cached — not recreated per request."""
    engine = get_engine()
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """FastAPI dependency: yields a DB session, always closes it after the request."""
    SessionLocal = _get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()