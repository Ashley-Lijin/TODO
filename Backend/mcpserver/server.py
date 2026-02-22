from mcp.server.fastmcp import FastMCP
from database.db import Session, init_db
from database.models import Task, TodayTask, PriorityRank
from datetime import datetime, date

init_db()

mcp = FastMCP("smart-planner")

@mcp.tool()
def get_all_tasks():
    """Get all pending tasks including carried over ones from previous days"""
    session = Session()
    tasks = session.query(Task).filter(Task.completed == False).all()
    result = []
    for t in tasks:
        yesterday_missed = session.query(TodayTask).filter(
            TodayTask.task_id == t.id,
            TodayTask.date < date.today()
        ).first()
        result.append({
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "due_date": str(t.due_date),
            "priority": t.priority.value,
            "time_required": str(t.time_required_for_work),
            "category": t.category,
            "carried_over": yesterday_missed is not None
        })
    session.close()
    return result

@mcp.tool()
def get_today_tasks():
    """Get today's tasks in the order Claude set"""
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

@mcp.tool()
def set_today_tasks(task_ids: list[int]):
    """Claude calls this to set today's tasks in order"""
    session = Session()
    session.query(TodayTask).filter(TodayTask.date == date.today()).delete()
    session.commit()
    for order, task_id in enumerate(task_ids, start=1):
        task = session.query(Task).filter(Task.id == task_id, Task.completed == False).first()
        if not task:
            continue
        today_task = TodayTask(task_id=task_id, date=date.today(), order=order)
        session.add(today_task)
    session.commit()
    session.close()
    return {"success": f"{len(task_ids)} tasks set for today"}

@mcp.tool()
def get_task_by_id(task_id: int):
    """Get a specific task by ID"""
    session = Session()
    t = session.query(Task).filter(Task.id == task_id).first()
    if not t:
        session.close()
        return {"error": "Task not found"}
    result = {
        "id": t.id,
        "title": t.title,
        "description": t.description,
        "due_date": str(t.due_date),
        "priority": t.priority.value,
        "time_required": str(t.time_required_for_work),
        "category": t.category,
        "completed": t.completed
    }
    session.close()
    return result

@mcp.tool()
def mark_task_complete(task_id: int):
    """Mark a task as completed"""
    session = Session()
    task = session.query(Task).filter(Task.id == task_id).first()
    if not task:
        session.close()
        return {"error": "Task not found"}
    task.completed = True
    session.commit()
    title = task.title
    session.close()
    return {"success": f"Task '{title}' marked as complete"}

@mcp.tool()
def add_task(title: str, description: str, due_date: str, priority: str, time_required: str, category: str):
    """Add a new task. due_date: YYYY-MM-DD HH:MM:SS, time_required: HH:MM:SS, priority: S/A/B/C/D"""
    from datetime import time
    session = Session()
    due = datetime.strptime(due_date, "%Y-%m-%d %H:%M:%S")
    h, m, s = map(int, time_required.split(":"))
    t = time(h, m, s)
    task = Task(
        title=title,
        description=description,
        due_date=due,
        priority=PriorityRank[priority],
        time_required_for_work=t,
        category=category
    )
    session.add(task)
    session.commit()
    session.close()
    return {"success": f"Task '{title}' added!"}

@mcp.tool()
def cleanup_completed_tasks():
    """Archive completed tasks from previous days - call this each morning"""
    import os
    import requests
    api_url = os.getenv("API_URL", "http://localhost:8000")
    res = requests.post(f"{api_url}/tasks/cleanup")
    return res.json()

if __name__ == "__main__":
    import os
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport == "sse":
        mcp.run(transport="sse", host="0.0.0.0", port=8001)
    else:
        mcp.run(transport="stdio")