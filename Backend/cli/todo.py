import typer
import requests
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich import box
from datetime import datetime
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

app = typer.Typer()
console = Console()

API = os.getenv("API_URL", "http://localhost:8000")

PRIORITY_COLOR = {
    "S": "bold magenta",
    "A": "bold red",
    "B": "bold yellow",
    "C": "bold cyan",
    "D": "dim white",
}

@app.command()
def today():
    """Show today's tasks planned by Claude"""
    res = requests.get(f"{API}/tasks/today")
    tasks = res.json()

    if not tasks:
        console.print("[dim]No tasks planned for today. Ask Claude to plan your day![/dim]")
        return

    table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold")
    table.add_column("Id", style="dim", width=3)
    table.add_column("#", style="dim", width=3)
    table.add_column("Title", min_width=25)
    table.add_column("Priority", width=8)
    table.add_column("Time", width=8)
    table.add_column("Suggested Start", width=14)
    table.add_column("Due", width=16)
    table.add_column("Status", width=10)

    for t in tasks:
        due = datetime.strptime(t["due_date"], "%Y-%m-%d %H:%M:%S")
        overdue = due.date() < datetime.today().date() and not t["completed"]
        status = Text("✓ done", style="green") if t["completed"] else (
            Text("⚠ overdue", style="bold red") if overdue else Text("pending", style="dim")
        )
        title = Text(t["title"], style="strike dim" if t["completed"] else (
            "bold red" if overdue else "white"
        ))
        suggested_start = t.get("suggested_start_time", None)
        suggested_start_str = Text(suggested_start, style="dim cyan") if suggested_start else Text("—", style="dim")

        table.add_row(
            str(t["id"]),
            str(t['order']),
            title,
            Text(t["priority"], style=PRIORITY_COLOR.get(t["priority"], "white")),
            t["time_required"],
            suggested_start_str,
            due.strftime("%b %d %H:%M"),
            status
        )

    console.print(f"\n[bold]Today's Tasks[/bold] [dim]— {datetime.today().strftime('%A, %b %d')}[/dim]")
    console.print(table)


@app.command()
def ls():
    """List all pending tasks"""
    res = requests.get(f"{API}/tasks/")
    tasks = res.json()

    if not tasks:
        console.print("[dim]No tasks found.[/dim]")
        return

    table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold")
    table.add_column("ID", style="dim", width=4)
    table.add_column("Title", min_width=25)
    table.add_column("Priority", width=8)
    table.add_column("Time", width=8)
    table.add_column("Due", width=16)
    table.add_column("Category", width=12)
    table.add_column("Status", width=10)

    for t in tasks:
        due = datetime.strptime(t["due_date"], "%Y-%m-%d %H:%M:%S")
        overdue = due.date() < datetime.today().date() and not t["completed"]
        status = Text("✓ done", style="green") if t["completed"] else (
            Text("⚠ overdue", style="bold red") if overdue else Text("pending", style="dim")
        )
        title = Text(t["title"], style="strike dim" if t["completed"] else (
            "bold red" if overdue else "white"
        ))
        table.add_row(
            str(t["id"]),
            title,
            Text(t["priority"], style=PRIORITY_COLOR.get(t["priority"], "white")),
            t["time_required"],
            due.strftime("%b %d %H:%M"),
            Text(t["category"], style="dim cyan"),
            status
        )

    console.print(f"\n[bold]All Tasks[/bold] [dim]({len(tasks)} total)[/dim]")
    console.print(table)


@app.command()
def add(
    title: str = typer.Argument(..., help="Task title"),
    due: str = typer.Option(..., "--due", "-d", help="Due date YYYY-MM-DD HH:MM:SS"),
    priority: str = typer.Option("B", "--priority", "-p", help="S/A/B/C/D"),
    time: str = typer.Option("00:30:00", "--time", "-t", help="Time required HH:MM:SS"),
    category: str = typer.Option("Personal", "--category", "-c", help="Category"),
    description: str = typer.Option("", "--desc", help="Description"),
):
    """Add a new task"""
    res = requests.post(f"{API}/tasks/", json={
        "title": title,
        "description": description,
        "due_date": due,
        "priority": priority,
        "time_required": time,
        "category": category
    })
    if res.status_code == 200:
        console.print(f"[green]✓[/green] Task [bold]{title}[/bold] added!")
    else:
        console.print(f"[red]✗ Error:[/red] {res.text}")


@app.command()
def complete(task_id: int = typer.Argument(..., help="Task ID to complete")):
    """Mark a task as complete"""
    res = requests.patch(f"{API}/tasks/{task_id}/complete")
    if res.status_code == 200:
        console.print(f"[green]✓[/green] Task [bold]{task_id}[/bold] completed and archived!")
    else:
        console.print(f"[red]✗ Error:[/red] {res.text}")


@app.command()
def delete(task_id: int = typer.Argument(..., help="Task ID to delete")):
    """Delete a task"""
    confirm = typer.confirm(f"Delete task {task_id}?")
    if not confirm:
        console.print("[dim]Cancelled[/dim]")
        return
    res = requests.delete(f"{API}/tasks/{task_id}")
    if res.status_code == 200:
        console.print(f"[red]✓[/red] Task [bold]{task_id}[/bold] deleted!")
    else:
        console.print(f"[red]✗ Error:[/red] {res.text}")


@app.command()
def update(
    task_id: int = typer.Argument(..., help="Task ID to update"),
    title: str = typer.Option(None, "--title"),
    due: str = typer.Option(None, "--due", "-d"),
    priority: str = typer.Option(None, "--priority", "-p"),
    time: str = typer.Option(None, "--time", "-t"),
    category: str = typer.Option(None, "--category", "-c"),
    description: str = typer.Option(None, "--desc"),
):
    """Update a task's fields"""
    payload = {}
    if title: payload["title"] = title
    if due: payload["due_date"] = due
    if priority: payload["priority"] = priority
    if time: payload["time_required"] = time
    if category: payload["category"] = category
    if description: payload["description"] = description

    if not payload:
        console.print("[dim]Nothing to update — pass at least one option[/dim]")
        return

    res = requests.patch(f"{API}/tasks/{task_id}", json=payload)
    if res.status_code == 200:
        console.print(f"[green]✓[/green] Task [bold]{task_id}[/bold] updated!")
    else:
        console.print(f"[red]✗ Error:[/red] {res.text}")


@app.command()
def archived():
    """Show completed/archived tasks"""
    res = requests.get(f"{API}/tasks/archived")
    tasks = res.json()

    if not tasks:
        console.print("[dim]No archived tasks yet.[/dim]")
        return

    table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold")
    table.add_column("ID", style="dim", width=4)
    table.add_column("Title", min_width=25)
    table.add_column("Priority", width=8)
    table.add_column("Category", width=12)
    table.add_column("Est / Actual", width=12)
    table.add_column("Completed At", width=18)

    for t in tasks:
        completed_at = datetime.strptime(t["completed_at"], "%Y-%m-%d %H:%M:%S.%f")
        time_required = t.get("time_required", "0:00:00")
        actual_minutes = t.get("actual_duration_minutes")

        # Format Est / Actual
        if actual_minutes:
            est_mins = int(time_required.split(":")[0]) * 60 + int(time_required.split(":")[1])
            est_actual = f"{est_mins}m / {actual_minutes}m"
        else:
            est_mins = int(time_required.split(":")[0]) * 60 + int(time_required.split(":")[1])
            est_actual = f"{est_mins}m / —"

        table.add_row(
            str(t["original_id"]),
            Text(t["title"], style="dim"),
            Text(t["priority"], style=PRIORITY_COLOR.get(t["priority"], "white")),
            Text(t["category"], style="dim cyan"),
            Text(est_actual, style="dim"),
            completed_at.strftime("%b %d %H:%M")
        )

    console.print(f"\n[bold]Archived Tasks[/bold] [dim]({len(tasks)} completed)[/dim]")
    console.print(table)

@app.command()
def cleanup():
    """Archive yesterday's completed tasks"""
    res = requests.post(f"{API}/tasks/cleanup")
    data = res.json()
    if res.status_code == 200:
        console.print(f"[green]✓[/green] Archived [bold]{data['archived']}[/bold] completed tasks")
    else:
        console.print(f"[red]✗ Error:[/red] {res.text}")

# ===== Phase 2: Task Estimation =====

@app.command()
def start(task_id: int = typer.Argument(..., help="Task ID to start")):
    """Start a task (sets timer)"""
    res = requests.patch(f"{API}/tasks/{task_id}/start")
    if res.status_code == 200:
        data = res.json()
        started_at = data.get("started_at", "")
        time_str = started_at.split(" ")[1].split(".")[0] if started_at else ""
        console.print(f"[green]✓[/green] Timer started at [bold]{time_str}[/bold]")
    else:
        console.print(f"[red]✗ Error:[/red] {res.text}")

# ===== Phase 3: Intelligent Prioritization =====

@app.command()
def suggest(task_id: int = typer.Argument(..., help="Task ID to suggest priority for")):
    """Get Claude's priority suggestion for a task"""
    # First get the task
    res = requests.get(f"{API}/tasks/")
    tasks = res.json()
    task = next((t for t in tasks if t["id"] == task_id), None)

    if not task:
        console.print(f"[red]✗ Task {task_id} not found[/red]")
        return

    # Get priority suggestion
    res = requests.get(
        f"{API}/analytics/priority-patterns",
        params={"category": task["category"], "keyword": task["title"]}
    )
    if res.status_code == 200:
        data = res.json()
        suggested = data.get("suggested_priority")
        confidence = data.get("confidence", "none")
        sample_size = data.get("sample_size", 0)

        if suggested:
            console.print(f"[cyan]Suggested priority:[/cyan] [bold]{suggested}[/bold] ([dim]{confidence} confidence[/dim], based on {sample_size} similar tasks)")
        else:
            console.print(f"[dim]No suggestion available[/dim]")
    else:
        console.print(f"[red]✗ Error:[/red] {res.text}")

# ===== Phase 4: Task Dependencies =====

@app.command()
def deps(task_id: int = typer.Argument(..., help="Task ID to show dependencies for")):
    """Show a task's dependencies"""
    res = requests.get(f"{API}/tasks/{task_id}/dependencies")
    if res.status_code == 200:
        data = res.json()
        depends_on = data.get("depends_on", [])

        if not depends_on:
            console.print(f"[dim]Task {task_id} has no dependencies[/dim]")
            return

        console.print(f"\n[bold]Task {task_id} depends on:[/bold]")
        for dep in depends_on:
            status_icon = "✓" if dep["completed"] else "○"
            status_color = "green" if dep["completed"] else "dim"
            console.print(f"  [{status_color}]{status_icon}[/{status_color}] [bold]{dep['id']}[/bold] {dep['title']}")
    else:
        console.print(f"[red]✗ Error:[/red] {res.text}")

# ===== Phase 5: Calendar Integration =====

@app.command()
def calendar(
    subcommand: str = typer.Argument(..., help="add, list"),
    url: Optional[str] = typer.Option(None, "--url", help="Calendar URL (webcal://)"),
    file: Optional[str] = typer.Option(None, "--file", help="Calendar file path"),
    label: Optional[str] = typer.Option(None, "--label", "-l", help="Calendar label"),
):
    """Manage calendar integrations"""
    if subcommand == "add":
        if not url and not file:
            console.print("[red]✗ Provide either --url or --file[/red]")
            return

        source_type = "url" if url else "file"
        source_value = url or file

        res = requests.post(
            f"{API}/analytics/calendar",
            json={"source_type": source_type, "source_value": source_value, "label": label}
        )
        if res.status_code == 200:
            data = res.json()
            console.print(f"[green]✓[/green] Calendar added with ID [bold]{data.get('id')}[/bold]")
        else:
            console.print(f"[red]✗ Error:[/red] {res.text}")

    elif subcommand == "list":
        res = requests.get(f"{API}/analytics/calendar")
        if res.status_code == 200:
            configs = res.json()
            if not configs:
                console.print("[dim]No calendars configured[/dim]")
                return

            table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold")
            table.add_column("ID", style="dim", width=3)
            table.add_column("Label", min_width=15)
            table.add_column("Type", width=6)
            table.add_column("Source", min_width=30)

            for c in configs:
                table.add_row(
                    str(c["id"]),
                    c.get("label") or "—",
                    c["source_type"],
                    c["source_value"]
                )

            console.print(f"\n[bold]Calendars[/bold]")
            console.print(table)
        else:
            console.print(f"[red]✗ Error:[/red] {res.text}")

    else:
        console.print(f"[red]✗ Unknown subcommand: {subcommand}[/red]")

# ===== Phase 6: Insights =====

@app.command()
def insights():
    """Show estimation accuracy and completion patterns"""
    res = requests.get(f"{API}/analytics/estimation-accuracy")
    if res.status_code != 200:
        console.print(f"[red]✗ Error fetching insights[/red]")
        return

    accuracy_data = res.json().get("accuracy_by_category", {})

    if not accuracy_data:
        console.print("[dim]Not enough data to show insights yet. Complete more tasks![/dim]")
        return

    console.print(f"\n[bold]Estimation Accuracy[/bold]")
    table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold")
    table.add_column("Category", min_width=15)
    table.add_column("Estimated", width=12)
    table.add_column("Actual", width=12)
    table.add_column("Multiplier", width=12)
    table.add_column("Tasks", width=8)

    for category, stats in accuracy_data.items():
        est = stats.get("avg_estimated_minutes", 0)
        actual = stats.get("avg_actual_minutes", 0)
        multiplier = stats.get("suggested_multiplier", 1.0)
        sample = stats.get("sample_size", 0)

        table.add_row(
            category,
            f"{est:.0f}m",
            f"{actual:.0f}m",
            f"{multiplier}x" if multiplier != 1.0 else "1.0x",
            str(sample)
        )

    console.print(table)


if __name__ == "__main__":
    app()