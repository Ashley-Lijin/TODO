from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime,Date, Time, Enum as SAEnum
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, date
from enum import Enum

Base = declarative_base()

class PriorityRank(Enum):
    S = "S"
    A = "A"
    B = "B"
    C = "C"
    D = "D"

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    due_date = Column(DateTime, nullable=False)
    priority = Column(SAEnum(PriorityRank), nullable=False, default=PriorityRank.B)
    time_required_for_work = Column(Time, nullable=False)
    completed = Column(Boolean, nullable=False, default=False)
    category = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    dependencies = Column(String(500), nullable=True)  # comma-sep task IDs, e.g. "3,7"
    suggested_start_time = Column(Time, nullable=True)  # Claude's suggested start time
    suggested_priority = Column(SAEnum(PriorityRank), nullable=True)
    started_at = Column(DateTime, nullable=True)  # set when user runs `todo start`

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', description='{self.description}', due date='{self.due_date}', time required for work='{self.time_required_for_work}', priority='{self.priority}', completed={self.completed}, category='{self.category}', created_at={self.created_at})>"
   
        
class TodayTask(Base):
    __tablename__ = "today_tasks"
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    date = Column(Date, nullable=False, default=date.today)
    order = Column(Integer, nullable=False)  # Claude decides the order
    task = relationship("Task")

    def __repr__(self):
        return f"<TodayTask(task_id={self.task_id}, order={self.order})>"

class ArchivedTask(Base):
    __tablename__ = "archived_tasks"
    id = Column(Integer, primary_key=True)
    original_id = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    due_date = Column(DateTime, nullable=False)
    priority = Column(SAEnum(PriorityRank), nullable=False)
    time_required_for_work = Column(Time, nullable=False)
    category = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=False, default=datetime.now)
    started_at = Column(DateTime, nullable=True)
    actual_duration_minutes = Column(Integer, nullable=True)  # (completed_at - started_at)
    suggested_priority = Column(SAEnum(PriorityRank), nullable=True)

    def __repr__(self):
        return f"<ArchivedTask(id={self.id}, title='{self.title}')>"

class CalendarConfig(Base):
    __tablename__ = "calendar_config"
    id = Column(Integer, primary_key=True)
    source_type = Column(String(10), nullable=False)   # "url" or "file"
    source_value = Column(String(1000), nullable=False) # webcal:// URL or file path
    label = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    last_synced_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<CalendarConfig(id={self.id}, label='{self.label}', type='{self.source_type}')>"