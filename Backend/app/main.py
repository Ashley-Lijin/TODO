from database.db import Session, init_db
from database.models import Task, PriorityRank
from datetime import datetime, time

init_db()
session = Session()

# # Add a sample task
# new_task = Task(
#     title="Clean mac storage",
#     description="clean the macs downloads folder and clear cache",
#     due_date=datetime(2026, 2, 22, 22, 30, 0),
#     priority=PriorityRank.C,
#     time_required_for_work=time(0, 10, 0),
#     completed=False,
#     catagory="Work"
# )
# session.add(new_task)
# session.commit()


def update_task(task_id, **kwargs):
    task = session.query(Task).filter(Task.id == task_id).first()
    if not task:
        print(f"Task {task_id} not found")
        return
    for key, value in kwargs.items():
        setattr(task, key, value)
    session.commit()
    print(f"Task {task_id} updated!")


update_task(1, completed=True)

# Query all tasks
tasks = session.query(Task).all()
print(tasks)