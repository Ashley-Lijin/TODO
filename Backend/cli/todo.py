import typer
import requests
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich import box
from datetime import datetime

app = typer.Typer()
console = Console()

API = "http://localhost:8000"

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
        table.add_row(
            str(t["id"]),
            str(t['order']),
            title,
            Text(t["priority"], style=PRIORITY_COLOR.get(t["priority"], "white")),
            t["time_required"],
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
    table.add_column("Completed At", width=18)

    for t in tasks:
        completed_at = datetime.strptime(t["completed_at"], "%Y-%m-%d %H:%M:%S.%f")
        table.add_row(
            str(t["original_id"]),
            Text(t["title"], style="dim"),
            Text(t["priority"], style=PRIORITY_COLOR.get(t["priority"], "white")),
            Text(t["category"], style="dim cyan"),
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


if __name__ == "__main__":
    app()