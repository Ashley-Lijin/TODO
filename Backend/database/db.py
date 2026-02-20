from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
import os
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(os.getenv("DB_URL"))
Session = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
    