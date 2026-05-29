"""
migrate.py — idempotent schema migration helper.

Applies any columns defined in SQLAlchemy models that are missing from the
live database without using Alembic.  Safe to run on every startup.
"""
from sqlalchemy import create_engine, inspect, text
import os

DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    raise RuntimeError("DATABASE_URL not set")

# ── Column additions that must always be present ──────────────────────────────
# Add new entries here whenever a model gains a new column.
REQUIRED_COLUMNS = [
    {
        "table": "classification_results",
        "column": "area_m2",
        "ddl": "ALTER TABLE classification_results ADD COLUMN area_m2 DOUBLE PRECISION",
    },
]

def run_migrations():
    engine = create_engine(DB_URL)
    insp = inspect(engine)

    for entry in REQUIRED_COLUMNS:
        table = entry["table"]
        col = entry["column"]

        # Check whether the column already exists
        existing_cols = [c["name"] for c in insp.get_columns(table)]
        if col not in existing_cols:
            print(f"[migrate] Adding missing column '{col}' to '{table}'...")
            with engine.begin() as conn:
                conn.execute(text(entry["ddl"]))
            print(f"[migrate] ✓ Done: {table}.{col}")
        else:
            print(f"[migrate] Column '{table}.{col}' already exists — skipping.")

    print("[migrate] Migration complete.")

if __name__ == "__main__":
    run_migrations()
