from mcp.server.fastmcp import FastMCP
import requests
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

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

# ===== Phase 2: Task Estimation =====

@mcp.tool()
def start_task(task_id: int):
    """Start a task by setting its started_at timestamp. Call this when user begins working on a task."""
    res = requests.patch(f"{API}/tasks/{task_id}/start")
    return res.json()

@mcp.tool()
def get_estimation_accuracy():
    """Get estimation accuracy patterns by category. Shows avg estimated vs actual time and suggested multiplier."""
    res = requests.get(f"{API}/analytics/estimation-accuracy")
    return res.json()

# ===== Phase 3: Intelligent Prioritization =====

@mcp.tool()
def get_priority_suggestion(category: str, title: str, keyword: str = ""):
    """Get priority suggestion based on historical patterns in the category.
    Confidence: 'high' (10+ samples), 'medium' (4-9), 'low' (1-3), 'none' (0)"""
    res = requests.get(
        f"{API}/analytics/priority-patterns",
        params={"category": category, "keyword": keyword or title}
    )
    return res.json()

@mcp.tool()
def suggest_task_priority(task_id: int, suggested_priority: str):
    """Store a suggested priority for a task (S/A/B/C/D). Claude uses this when suggesting priorities."""
    res = requests.patch(f"{API}/tasks/{task_id}", json={"suggested_priority": suggested_priority})
    return res.json()

@mcp.tool()
def set_suggested_start_time(task_id: int, suggested_start_time: str):
    """Set Claude's suggested start time for a task (HH:MM:SS format)"""
    res = requests.patch(
        f"{API}/tasks/{task_id}/suggested_start",
        json={"suggested_start_time": suggested_start_time}
    )
    return res.json()

# ===== Phase 4: Task Dependencies & Completion Patterns =====

@mcp.tool()
def set_task_dependencies(task_id: int, depends_on: list[int]):
    """Set which tasks must be completed before this task can start"""
    res = requests.post(f"{API}/tasks/{task_id}/dependencies", json={"depends_on": depends_on})
    return res.json()

@mcp.tool()
def get_task_dependencies(task_id: int):
    """Get a task's dependencies and their completion status"""
    res = requests.get(f"{API}/tasks/{task_id}/dependencies")
    return res.json()

@mcp.tool()
def get_scheduling_context(start_date: str, end_date: str):
    """Get comprehensive scheduling context before planning the day. Returns:
    - completion_patterns: when tasks are typically completed by category
    - estimation_multipliers: time estimation accuracy by category
    - blocked_task_ids: tasks that are waiting on dependencies
    - calendar_free_slots: free time from integrated calendars (if configured)
    Call this BEFORE set_today_tasks to make informed scheduling decisions."""
    res = requests.get(
        f"{API}/analytics/scheduling-context",
        params={"start_date": start_date, "end_date": end_date}
    )
    return res.json()

# ===== Phase 5: Calendar Integration =====

@mcp.tool()
def configure_calendar(source_type: str, source_value: str, label: str = ""):
    """Configure a calendar source. source_type: 'url' or 'file', source_value: webcal:// URL or file path"""
    res = requests.post(
        f"{API}/analytics/calendar",
        json={"source_type": source_type, "source_value": source_value, "label": label}
    )
    return res.json()

@mcp.tool()
def list_calendars():
    """List all configured calendar sources"""
    res = requests.get(f"{API}/analytics/calendar")
    return res.json()

@mcp.tool()
def get_calendar_free_slots(start_date: str, end_date: str, work_start: str = "08:00", work_end: str = "22:00"):
    """Get free time slots from configured calendars within work hours (HH:MM format)"""
    res = requests.get(
        f"{API}/analytics/calendar-free-slots",
        params={
            "start_date": start_date,
            "end_date": end_date,
            "work_start": work_start,
            "work_end": work_end
        }
    )
    return res.json()

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport == "sse":
        mcp.run(transport="sse", host="0.0.0.0", port=8001)
    else:
        mcp.run(transport="stdio")