from fastapi import APIRouter, HTTPException
from database.db import Session
from database.models import Task, TodayTask, ArchivedTask, PriorityRank
from pydantic import BaseModel
from datetime import datetime, date, time
from typing import List

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
    suggested_priority: str | None = None

class TodayTasksSet(BaseModel):
    task_ids: list[int]

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
            "completed": tt.task.completed,
            "suggested_start_time": str(tt.task.suggested_start_time) if tt.task.suggested_start_time else None
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
    if data.suggested_priority is not None:
        task.suggested_priority = PriorityRank[data.suggested_priority]

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
            actual_duration_minutes = None
            if task.started_at:
                actual_duration_minutes = int((datetime.now() - task.started_at).total_seconds() / 60)

            archived = ArchivedTask(
                original_id=task.id,
                title=task.title,
                description=task.description,
                due_date=task.due_date,
                priority=task.priority,
                time_required_for_work=task.time_required_for_work,
                category=task.category,
                created_at=task.created_at,
                completed_at=datetime.now(),
                started_at=task.started_at,
                actual_duration_minutes=actual_duration_minutes,
                suggested_priority=task.suggested_priority
            )
            session.add(archived)
            session.query(TodayTask).filter(TodayTask.task_id == task.id).delete()
            session.delete(task)
            archived_count += 1

    session.commit()
    session.close()
    return {"success": True, "archived": archived_count}

# Mcp

@router.patch("/{task_id}/start")
def start_task(task_id: int):
    """Start a task by setting started_at timestamp"""
    session = Session()
    task = session.query(Task).filter(Task.id == task_id).first()
    if not task:
        session.close()
        raise HTTPException(status_code=404, detail="Task not found")

    task.started_at = datetime.now()
    started_at = task.started_at
    session.commit()
    session.close()
    return {"success": True, "started_at": str(started_at)}

@router.patch("/{task_id}/suggested_start")
def set_suggested_start_time(task_id: int, data: dict):
    """Set suggested start time for a task"""
    session = Session()
    task = session.query(Task).filter(Task.id == task_id).first()
    if not task:
        session.close()
        raise HTTPException(status_code=404, detail="Task not found")

    suggested_start_time = data.get("suggested_start_time")
    if not suggested_start_time:
        session.close()
        raise HTTPException(status_code=400, detail="suggested_start_time required")

    h, m, s = map(int, suggested_start_time.split(":"))
    task.suggested_start_time = time(h, m, s)
    session.commit()
    session.close()
    return {"success": True}

@router.post("/{task_id}/dependencies")
def set_task_dependencies(task_id: int, data: dict):
    """Set task dependencies"""
    session = Session()
    task = session.query(Task).filter(Task.id == task_id).first()
    if not task:
        session.close()
        raise HTTPException(status_code=404, detail="Task not found")

    depends_on = data.get("depends_on", [])

    # Validate all dependency IDs exist
    for dep_id in depends_on:
        dep_task = session.query(Task).filter(Task.id == dep_id).first()
        if not dep_task:
            session.close()
            raise HTTPException(status_code=400, detail=f"Task {dep_id} not found")

    task.dependencies = ",".join(map(str, depends_on)) if depends_on else None
    session.commit()
    session.close()
    return {"success": True}

@router.get("/{task_id}/dependencies")
def get_task_dependencies(task_id: int):
    """Get task dependencies with completion status"""
    session = Session()
    task = session.query(Task).filter(Task.id == task_id).first()
    if not task:
        session.close()
        raise HTTPException(status_code=404, detail="Task not found")

    depends_on = []
    if task.dependencies:
        dep_ids = [int(x.strip()) for x in task.dependencies.split(",") if x.strip()]
        for dep_id in dep_ids:
            dep_task = session.query(Task).filter(Task.id == dep_id).first()
            if dep_task:
                depends_on.append({
                    "id": dep_task.id,
                    "title": dep_task.title,
                    "completed": dep_task.completed
                })

    session.close()
    return {
        "task_id": task_id,
        "depends_on": depends_on
    }

@router.post("/today")
def set_today_tasks(data: TodayTasksSet):
    session = Session()
    session.query(TodayTask).filter(TodayTask.date == date.today()).delete()
    session.commit()
    for order, task_id in enumerate(data.task_ids, start=1):
        task = session.query(Task).filter(Task.id == task_id, Task.completed == False).first()
        if not task:
            continue
        today_task = TodayTask(task_id=task_id, date=date.today(), order=order)
        session.add(today_task)
    session.commit()
    session.close()
    return {"success": True, "count": len(data.task_ids)}

