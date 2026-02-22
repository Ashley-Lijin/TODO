from database.db import Session, init_db
from database.models import Task, PriorityRank
from datetime import datetime, time

init_db()
session = Session()

# Add a sample task
new_task = [Task(
    title="Make an gust invitation for SCIFA '26",
    description="make an guest invitation for SCIFA '26 using liquid glass",
    due_date=datetime(2026, 2, 22, 22, 30, 0),
    priority=PriorityRank.A,
    time_required_for_work=time(1, 00, 0),
    completed=False,
    category="College"
),
Task(
    title="Make an Promo Vidoe for SCIFA '26",
    description="Make an catchy 20-30 sec promo video for SCIFA '26",
    due_date=datetime(2026, 2, 22, 22, 30, 0),
    priority=PriorityRank.B,
    time_required_for_work=time(1, 30, 0),
    completed=False,
    category="College"
),
Task(
    title="make an ranking system in excel and paper version for judge",
    description="",
    due_date=datetime(2026, 2, 24, 22, 30, 0),
    priority=PriorityRank.A,
    time_required_for_work=time(0, 50, 0),
    completed=False,
    category="College"
),
]
session.add_all(new_task)
session.commit()


def update_task(task_id, **kwargs):
    task = session.query(Task).filter(Task.id == task_id).first()
    if not task:
        print(f"Task {task_id} not found")
        return
    for key, value in kwargs.items():
        setattr(task, key, value)
    session.commit()
    print(f"Task {task_id} updated!")


# update_task(1, completed=True)

# Query all tasks
tasks = session.query(Task).all()
print(tasks)