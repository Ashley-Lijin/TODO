from sqlalchemy import Column, Integer, String, Boolean, DateTime, Time, Enum as SAEnum
from sqlalchemy.orm import declarative_base
from datetime import datetime
from enum import Enum

Base = declarative_base()

class PriorityRank(Enum):
    S = 10
    A = 7
    B = 5
    C = 3
    D = 1

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    due_date = Column(DateTime, nullable=False)
    priority = Column(SAEnum(PriorityRank), nullable=False, default=PriorityRank.B)
    time_required_for_work = Column(Time, nullable=False)
    completed = Column(Boolean, nullable=False, default=False)
    catagory = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now())

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', description='{self.description}', due date='{self.due_date}', time required for work='{self.time_required_for_work}', priority='{self.priority}', completed={self.completed}, catagory='{self.catagory}', created_at={self.created_at})>"