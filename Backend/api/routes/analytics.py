from fastapi import APIRouter, HTTPException, Query
from database.db import Session
from database.models import Task, ArchivedTask, CalendarConfig, PriorityRank
from pydantic import BaseModel
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Optional
from collections import Counter
import requests
from urllib.parse import urlparse
from pathlib import Path

router = APIRouter()

class CalendarConfigCreate(BaseModel):
    source_type: str  # "url" or "file"
    source_value: str  # webcal:// URL or file path
    label: Optional[str] = None

class SuggestedStartTimeRequest(BaseModel):
    suggested_start_time: str  # HH:MM:SS

# ===== Phase 2: Task Estimation =====

@router.get("/estimation-accuracy")
def get_estimation_accuracy():
    """Get estimation accuracy patterns across categories"""
    session = Session()
    archived = session.query(ArchivedTask).filter(
        ArchivedTask.actual_duration_minutes.isnot(None)
    ).all()

    accuracy_by_category = {}
    for task in archived:
        estimated_minutes = int(task.time_required_for_work.hour * 60 + task.time_required_for_work.minute)
        actual_minutes = task.actual_duration_minutes

        if task.category not in accuracy_by_category:
            accuracy_by_category[task.category] = {
                "estimated_minutes": [],
                "actual_minutes": []
            }

        accuracy_by_category[task.category]["estimated_minutes"].append(estimated_minutes)
        accuracy_by_category[task.category]["actual_minutes"].append(actual_minutes)

    result = {}
    for category, data in accuracy_by_category.items():
        avg_estimated = sum(data["estimated_minutes"]) / len(data["estimated_minutes"])
        avg_actual = sum(data["actual_minutes"]) / len(data["actual_minutes"])
        multiplier = avg_actual / avg_estimated if avg_estimated > 0 else 1.0

        result[category] = {
            "sample_size": len(data["estimated_minutes"]),
            "avg_estimated_minutes": round(avg_estimated, 1),
            "avg_actual_minutes": round(avg_actual, 1),
            "suggested_multiplier": round(multiplier, 2)
        }

    session.close()
    return {"accuracy_by_category": result}

# ===== Phase 3: Intelligent Prioritization =====

@router.get("/priority-patterns")
def get_priority_patterns(
    category: str = Query(...),
    keyword: Optional[str] = Query(None)
):
    """Get priority suggestions based on historical patterns"""
    session = Session()
    query = session.query(ArchivedTask).filter(ArchivedTask.category == category)

    if keyword:
        query = query.filter(
            (ArchivedTask.title.ilike(f"%{keyword}%")) |
            (ArchivedTask.description.ilike(f"%{keyword}%"))
        )

    tasks = query.all()
    session.close()

    if not tasks:
        return {
            "category": category,
            "suggested_priority": None,
            "confidence": "none",
            "sample_size": 0,
            "priority_distribution": {}
        }

    priorities = [task.priority.value for task in tasks]
    priority_counter = Counter(priorities)
    most_common_priority = priority_counter.most_common(1)[0][0]

    sample_size = len(tasks)
    if sample_size >= 10:
        confidence = "high"
    elif sample_size >= 4:
        confidence = "medium"
    elif sample_size >= 1:
        confidence = "low"
    else:
        confidence = "none"

    return {
        "category": category,
        "suggested_priority": most_common_priority,
        "confidence": confidence,
        "sample_size": sample_size,
        "priority_distribution": dict(priority_counter)
    }

@router.get("/completion-patterns")
def get_completion_patterns():
    """Get completion time patterns by category"""
    session = Session()
    archived = session.query(ArchivedTask).all()

    patterns_by_category = {}
    for task in archived:
        if task.category not in patterns_by_category:
            patterns_by_category[task.category] = []

        hour = task.completed_at.hour
        patterns_by_category[task.category].append(hour)

    result = {}
    for category, hours in patterns_by_category.items():
        hour_counter = Counter(hours)
        most_common_hour = hour_counter.most_common(1)[0][0] if hours else None

        result[category] = {
            "most_common_hour": most_common_hour,
            "hour_distribution": dict(hour_counter),
            "sample_size": len(hours)
        }

    session.close()
    return {"completion_patterns": result}

@router.get("/scheduling-context")
def get_scheduling_context(
    start_date: str = Query(...),  # YYYY-MM-DD
    end_date: str = Query(...)     # YYYY-MM-DD
):
    """Get comprehensive scheduling context: completion patterns, estimation accuracy, blocked tasks, and free calendar slots"""
    session = Session()

    # Get completion patterns
    archived = session.query(ArchivedTask).all()
    patterns_by_category = {}
    for task in archived:
        if task.category not in patterns_by_category:
            patterns_by_category[task.category] = []
        patterns_by_category[task.category].append(task.completed_at.hour)

    completion_patterns = {}
    for category, hours in patterns_by_category.items():
        hour_counter = Counter(hours)
        most_common_hour = hour_counter.most_common(1)[0][0] if hours else None
        completion_patterns[category] = {
            "most_common_hour": most_common_hour,
            "hour_distribution": dict(hour_counter)
        }

    # Get estimation accuracy
    archived_with_duration = session.query(ArchivedTask).filter(
        ArchivedTask.actual_duration_minutes.isnot(None)
    ).all()

    estimation_accuracy = {}
    for task in archived_with_duration:
        estimated_minutes = int(task.time_required_for_work.hour * 60 + task.time_required_for_work.minute)
        actual_minutes = task.actual_duration_minutes

        if task.category not in estimation_accuracy:
            estimation_accuracy[task.category] = {
                "estimated_minutes": [],
                "actual_minutes": []
            }

        estimation_accuracy[task.category]["estimated_minutes"].append(estimated_minutes)
        estimation_accuracy[task.category]["actual_minutes"].append(actual_minutes)

    estimation_multipliers = {}
    for category, data in estimation_accuracy.items():
        avg_estimated = sum(data["estimated_minutes"]) / len(data["estimated_minutes"])
        avg_actual = sum(data["actual_minutes"]) / len(data["actual_minutes"])
        multiplier = avg_actual / avg_estimated if avg_estimated > 0 else 1.0
        estimation_multipliers[category] = round(multiplier, 2)

    # Get blocked tasks
    all_tasks = session.query(Task).filter(Task.completed == False).all()
    blocked_tasks = []
    for task in all_tasks:
        if task.dependencies:
            dep_ids = [int(x.strip()) for x in task.dependencies.split(",") if x.strip()]
            blocked = False
            for dep_id in dep_ids:
                dep_task = session.query(Task).filter(Task.id == dep_id).first()
                if dep_task and not dep_task.completed:
                    blocked = True
                    break
            if blocked:
                blocked_tasks.append(task.id)

    # Get calendar free slots (Phase 5)
    calendar_free_slots = get_free_slots_internal(session, start_date, end_date)

    session.close()

    return {
        "completion_patterns": completion_patterns,
        "estimation_multipliers": estimation_multipliers,
        "blocked_task_ids": blocked_tasks,
        "calendar_free_slots": calendar_free_slots
    }

# ===== Phase 5: Calendar Integration =====

@router.post("/calendar")
def add_calendar_config(data: CalendarConfigCreate):
    """Add a calendar configuration"""
    session = Session()
    config = CalendarConfig(
        source_type=data.source_type,
        source_value=data.source_value,
        label=data.label
    )
    session.add(config)
    session.commit()
    config_id = config.id
    session.close()
    return {"success": True, "id": config_id}

@router.get("/calendar")
def list_calendar_configs():
    """List all calendar configurations"""
    session = Session()
    configs = session.query(CalendarConfig).all()
    result = [
        {
            "id": c.id,
            "source_type": c.source_type,
            "source_value": c.source_value,
            "label": c.label,
            "created_at": str(c.created_at),
            "last_synced_at": str(c.last_synced_at) if c.last_synced_at else None
        }
        for c in configs
    ]
    session.close()
    return result

@router.delete("/calendar/{config_id}")
def delete_calendar_config(config_id: int):
    """Delete a calendar configuration"""
    session = Session()
    config = session.query(CalendarConfig).filter(CalendarConfig.id == config_id).first()
    if not config:
        session.close()
        raise HTTPException(status_code=404, detail="Calendar config not found")

    session.delete(config)
    session.commit()
    session.close()
    return {"success": True}

@router.post("/calendar/{config_id}/test")
def test_calendar_config(config_id: int):
    """Test a calendar configuration by fetching and parsing"""
    session = Session()
    config = session.query(CalendarConfig).filter(CalendarConfig.id == config_id).first()
    if not config:
        session.close()
        raise HTTPException(status_code=404, detail="Calendar config not found")

    try:
        if config.source_type == "url":
            url = config.source_value.replace("webcal://", "https://")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        elif config.source_type == "file":
            with open(config.source_value, "rb") as f:
                response = f.read()
        else:
            session.close()
            raise HTTPException(status_code=400, detail="Invalid source type")

        # Try to parse as iCalendar
        try:
            from icalendar import Calendar
            if config.source_type == "url":
                cal = Calendar.from_ical(response.content)
            else:
                cal = Calendar.from_ical(response)

            event_count = 0
            for component in cal.walk():
                if component.name == "VEVENT":
                    event_count += 1

            config.last_synced_at = datetime.now()
            session.commit()
            session.close()

            return {"success": True, "event_count": event_count}
        except Exception as e:
            session.close()
            raise HTTPException(status_code=400, detail=f"Failed to parse iCalendar: {str(e)}")

    except requests.RequestException as e:
        session.close()
        raise HTTPException(status_code=400, detail=f"Failed to fetch calendar: {str(e)}")
    except FileNotFoundError:
        session.close()
        raise HTTPException(status_code=400, detail="Calendar file not found")

@router.get("/calendar-free-slots")
def get_calendar_free_slots(
    start_date: str = Query(...),  # YYYY-MM-DD
    end_date: str = Query(...),    # YYYY-MM-DD
    work_start: str = Query("08:00"),  # HH:MM
    work_end: str = Query("22:00")     # HH:MM
):
    """Get free time slots from calendar within work hours"""
    session = Session()
    free_slots = get_free_slots_internal(session, start_date, end_date, work_start, work_end)
    session.close()
    return {"free_slots": free_slots}

def get_free_slots_internal(session, start_date: str, end_date: str, work_start: str = "08:00", work_end: str = "22:00"):
    """Internal helper to compute free slots"""
    try:
        from icalendar import Calendar
    except ImportError:
        return []

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    work_start_h = int(work_start.split(":")[0])
    work_end_h = int(work_end.split(":")[0])

    configs = session.query(CalendarConfig).all()
    all_events = []

    for cfg in configs:
        try:
            if cfg.source_type == "url":
                url = cfg.source_value.replace("webcal://", "https://")
                response = requests.get(url, timeout=10)
                cal = Calendar.from_ical(response.content)
            elif cfg.source_type == "file":
                with open(cfg.source_value, "rb") as f:
                    cal = Calendar.from_ical(f.read())
            else:
                continue

            for component in cal.walk():
                if component.name == "VEVENT":
                    dtstart = component.get("DTSTART")
                    dtend = component.get("DTEND")
                    if dtstart and dtend:
                        dtstart_val = dtstart.dt
                        dtend_val = dtend.dt

                        # Normalize all-day events
                        if isinstance(dtstart_val, date) and not isinstance(dtstart_val, datetime):
                            dtstart_val = datetime(dtstart_val.year, dtstart_val.month, dtstart_val.day, 0, 0)
                        if isinstance(dtend_val, date) and not isinstance(dtend_val, datetime):
                            dtend_val = datetime(dtend_val.year, dtend_val.month, dtend_val.day, 23, 59)

                        all_events.append((dtstart_val, dtend_val))
        except Exception:
            continue

    # Compute free slots
    free_slots = []
    current = start

    while current < end:
        day_start = datetime(current.year, current.month, current.day, work_start_h, 0)
        day_end = datetime(current.year, current.month, current.day, work_end_h, 0)

        # Get events for this day
        day_events = []
        for evt_start, evt_end in all_events:
            # Check if event overlaps with work hours
            if evt_end > day_start and evt_start < day_end:
                # Clamp to work hours
                clamp_start = max(evt_start, day_start)
                clamp_end = min(evt_end, day_end)
                day_events.append((clamp_start, clamp_end))

        # Sort events by start time
        day_events.sort()

        # Find gaps
        gap_start = day_start
        for evt_start, evt_end in day_events:
            if evt_start > gap_start:
                gap_minutes = int((evt_start - gap_start).total_seconds() / 60)
                if gap_minutes >= 30:  # Only include gaps >= 30 minutes
                    free_slots.append({
                        "date": gap_start.strftime("%Y-%m-%d"),
                        "start": gap_start.strftime("%H:%M"),
                        "end": evt_start.strftime("%H:%M"),
                        "duration_minutes": gap_minutes
                    })
            gap_start = max(gap_start, evt_end)

        # Final gap
        if gap_start < day_end:
            gap_minutes = int((day_end - gap_start).total_seconds() / 60)
            if gap_minutes >= 30:
                free_slots.append({
                    "date": gap_start.strftime("%Y-%m-%d"),
                    "start": gap_start.strftime("%H:%M"),
                    "end": day_end.strftime("%H:%M"),
                    "duration_minutes": gap_minutes
                })

        current = current + timedelta(days=1)

    return free_slots
