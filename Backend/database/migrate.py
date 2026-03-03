"""Run database migrations — safe to run repeatedly (IF NOT EXISTS)."""
from sqlalchemy import text
from database.db import engine

def run_migrations():
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE tasks
              ADD COLUMN IF NOT EXISTS dependencies VARCHAR(500),
              ADD COLUMN IF NOT EXISTS suggested_start_time TIME,
              ADD COLUMN IF NOT EXISTS suggested_priority VARCHAR(1),
              ADD COLUMN IF NOT EXISTS started_at TIMESTAMP;
        """))
        conn.execute(text("""
            ALTER TABLE archived_tasks
              ADD COLUMN IF NOT EXISTS started_at TIMESTAMP,
              ADD COLUMN IF NOT EXISTS actual_duration_minutes INTEGER,
              ADD COLUMN IF NOT EXISTS suggested_priority VARCHAR(1);
        """))
        conn.commit()
    print("✓ Migrations complete")

if __name__ == "__main__":
    run_migrations()
