from fastapi import APIRouter, HTTPException
from database.db import Session
from database.models import Task, TodayTask, ArchivedTask, PriorityRank
from pydantic import BaseModel
from datetime import datetime, date, time

router = APIRouter()

class TaskCreate(BaseModel):
    title: str
    description: str = ""
    due_date: str
    priority: str
    time_required: str
    category: str

class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    due_date: str | None = None
    priority: str | None = None
    time_required: str | None = None
    category: str | None = None

@router.get("/")
def get_all_tasks():
    session = Session()
    tasks = session.query(Task).order_by(Task.due_date).all()
    result = [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "due_date": str(t.due_date),
            "priority": t.priority.value,
            "time_required": str(t.time_required_for_work),
            "category": t.category,
            "completed": t.completed,
            "created_at": str(t.created_at)
        }
        for t in tasks
    ]
    session.close()
    return result

@router.get("/today")
def get_today_tasks():
    session = Session()
    today_tasks = (
        session.query(TodayTask)
        .filter(TodayTask.date == date.today())
        .order_by(TodayTask.order)
        .all()
    )
    result = [
        {
            "order": tt.order,
            "id": tt.task.id,
            "title": tt.task.title,
            "description": tt.task.description,
            "due_date": str(tt.task.due_date),
            "priority": tt.task.priority.value,
            "time_required": str(tt.task.time_required_for_work),
            "category": tt.task.category,
            "completed": tt.task.completed
        }
        for tt in today_tasks
    ]
    session.close()
    return result

@router.post("/")
def add_task(data: TaskCreate):
    session = Session()
    due = datetime.strptime(data.due_date, "%Y-%m-%d %H:%M:%S")
    h, m, s = map(int, data.time_required.split(":"))
    t = time(h, m, s)
    task = Task(
        title=data.title,
        description=data.description,
        due_date=due,
        priority=PriorityRank[data.priority],
        time_required_for_work=t,
        category=data.category
    )
    session.add(task)
    session.commit()
    session.close()
    return {"success": f"Task '{data.title}' added!"}

@router.delete("/{task_id}")
def delete_task(task_id: int):
    session = Session()
    task = session.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    session.query(TodayTask).filter(TodayTask.task_id == task_id).delete()
    session.delete(task)
    session.commit()
    session.close()
    return {"success": True}
@router.patch("/{task_id}/complete")
def complete_task(task_id: int):
    session = Session()
    task = session.query(Task).filter(Task.id == task_id).first()
    if not task:
        session.close()
        raise HTTPException(status_code=404, detail="Task not found")
    task.completed = not task.completed
    session.commit()
    completed = task.completed
    session.close()
    return {"success": True, "completed": completed}

@router.patch("/{task_id}")
def update_task(task_id: int, data: TaskUpdate):
    session = Session()
    task = session.query(Task).filter(Task.id == task_id).first()
    if not task:
        session.close()
        raise HTTPException(status_code=404, detail="Task not found")
    
    if data.title is not None:
        task.title = data.title
    if data.description is not None:
        task.description = data.description
    if data.due_date is not None:
        task.due_date = datetime.strptime(data.due_date, "%Y-%m-%d %H:%M:%S")
    if data.priority is not None:
        task.priority = PriorityRank[data.priority]
    if data.time_required is not None:
        h, m, s = map(int, data.time_required.split(":"))
        task.time_required_for_work = time(h, m, s)
    if data.category is not None:
        task.category = data.category

    session.commit()
    session.close()
    return {"success": True}

@router.get("/archived")
def get_archived_tasks():
    session = Session()
    tasks = session.query(ArchivedTask).order_by(ArchivedTask.completed_at.desc()).all()
    result = [
        {
            "id": t.id,
            "original_id": t.original_id,
            "title": t.title,
            "description": t.description,
            "due_date": str(t.due_date),
            "priority": t.priority.value,
            "time_required": str(t.time_required_for_work),
            "category": t.category,
            "created_at": str(t.created_at),
            "completed_at": str(t.completed_at)
        }
        for t in tasks
    ]
    session.close()
    return result

@router.post("/cleanup")
def cleanup_completed():
    """Archive completed tasks from previous days"""
    session = Session()
    completed_tasks = session.query(Task).filter(
        Task.completed == True,
    ).all()

    archived_count = 0
    for task in completed_tasks:
        # Only archive if it was in today_tasks from a previous day
        was_today = session.query(TodayTask).filter(
            TodayTask.task_id == task.id,
            TodayTask.date < date.today()
        ).first()

        # Or if it was completed but never added to today at all
        never_today = session.query(TodayTask).filter(
            TodayTask.task_id == task.id
        ).first() is None

        if was_today or never_today:
            archived = ArchivedTask(
                original_id=task.id,
                title=task.title,
                description=task.description,
                due_date=task.due_date,
                priority=task.priority,
                time_required_for_work=task.time_required_for_work,
                category=task.category,
                created_at=task.created_at,
                completed_at=datetime.now()
            )
            session.add(archived)
            session.query(TodayTask).filter(TodayTask.task_id == task.id).delete()
            session.delete(task)
            archived_count += 1

    session.commit()
    session.close()
    return {"success": True, "archived": archived_count}