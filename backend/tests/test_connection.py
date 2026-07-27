"""
Quick manual check that the DB connection and env config are working.
Run: python tests/test_connection.py
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database.connection import get_engine


def main():
    engine = get_engine()
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version();")).scalar()
        db_name = conn.execute(text("SELECT current_database();")).scalar()
        print(f"✓ Connected to PostgreSQL database '{db_name}'")
        print(version)


if __name__ == "__main__":
    main()