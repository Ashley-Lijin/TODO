from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from .models import Base
import os
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(os.getenv("DB_URL"))
Session = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)

    # Add columns that may be missing on older deployments
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