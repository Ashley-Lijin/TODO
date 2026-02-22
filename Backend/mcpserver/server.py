from mcp.server.fastmcp import FastMCP
import requests
import os

API = os.getenv("API_URL", "http://localhost:8000")

mcp = FastMCP(
    "smart-planner",
    host=os.getenv("FASTMCP_HOST", "127.0.0.1"),
    port=int(os.getenv("FASTMCP_PORT", "8001"))
)

@mcp.tool()
def get_all_tasks():
    """Get all pending tasks including carried over ones from previous days"""
    res = requests.get(f"{API}/tasks/")
    return res.json()

@mcp.tool()
def get_today_tasks():
    """Get today's tasks in the order Claude set"""
    res = requests.get(f"{API}/tasks/today")
    return res.json()

@mcp.tool()
def set_today_tasks(task_ids: list[int]):
    """Claude calls this to set today's tasks in order"""
    res = requests.post(f"{API}/tasks/today", json={"task_ids": task_ids})
    return res.json()

@mcp.tool()
def get_task_by_id(task_id: int):
    """Get a specific task by ID"""
    res = requests.get(f"{API}/tasks/{task_id}")
    return res.json()

@mcp.tool()
def mark_task_complete(task_id: int):
    """Mark a task as completed"""
    res = requests.patch(f"{API}/tasks/{task_id}/complete")
    return res.json()

@mcp.tool()
def add_task(title: str, description: str, due_date: str, priority: str, time_required: str, category: str):
    """Add a new task. due_date: YYYY-MM-DD HH:MM:SS, time_required: HH:MM:SS, priority: S/A/B/C/D"""
    res = requests.post(f"{API}/tasks/", json={
        "title": title,
        "description": description,
        "due_date": due_date,
        "priority": priority,
        "time_required": time_required,
        "category": category
    })
    return res.json()

@mcp.tool()
def update_task(task_id: int, title: str = None, description: str = None, due_date: str = None, priority: str = None, time_required: str = None, category: str = None):
    """Update any field of a task"""
    payload = {}
    if title: payload["title"] = title
    if description: payload["description"] = description
    if due_date: payload["due_date"] = due_date
    if priority: payload["priority"] = priority
    if time_required: payload["time_required"] = time_required
    if category: payload["category"] = category
    res = requests.patch(f"{API}/tasks/{task_id}", json=payload)
    return res.json()

@mcp.tool()
def delete_task(task_id: int):
    """Delete a task"""
    res = requests.delete(f"{API}/tasks/{task_id}")
    return res.json()

@mcp.tool()
def cleanup_completed_tasks():
    """Archive completed tasks from previous days - call this each morning before planning"""
    res = requests.post(f"{API}/tasks/cleanup")
    return res.json()

@mcp.tool()
def get_archived_tasks():
    """Get all completed and archived tasks"""
    res = requests.get(f"{API}/tasks/archived")
    return res.json()

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "sse")
    if transport == "sse":
        mcp.run(transport="sse")
    elif transport == "http":
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")