"""
ClaudeForge CLI using Typer.
Provides command-line interface for workflow management.
"""

import os
import sys
from typing import Optional

import httpx
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

app = typer.Typer(
    name="claudeforge",
    help="ClaudeForge - Spec-Driven AI Agent Framework",
    add_completion=False,
)
console = Console()

API_BASE = os.getenv("API_URL", "http://localhost:8000")


def get_api_url(endpoint: str) -> str:
    """Get full API URL for an endpoint."""
    return f"{API_BASE}{endpoint}"


@app.command()
def start(
    project: str = typer.Argument(..., help="Project name"),
    feature_desc: str = typer.Argument(..., help="Feature description"),
    auto_approve: bool = typer.Option(
        True, "--auto-approve/--manual", help="Auto-approve phases"
    ),
):
    """Start a new workflow for a feature."""
    console.print(Panel.fit(
        f"[bold blue]Starting ClaudeForge Workflow[/bold blue]\n\n"
        f"Project: [green]{project}[/green]\n"
        f"Feature: [yellow]{feature_desc}[/yellow]",
        border_style="blue",
    ))

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Initiating workflow...", total=None)

            response = httpx.post(
                get_api_url("/api/agents/start"),
                json={"project": project, "feature_desc": feature_desc},
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                feat_id = data.get("feat_id")
                progress.update(task, description=f"Workflow started: {feat_id}")

                console.print(f"\n[green]Workflow started successfully![/green]")
                console.print(f"Feature ID: [bold]{feat_id}[/bold]")
                console.print(f"\nMonitor progress:")
                console.print(f"  Dashboard: http://localhost:5050/specs/{feat_id}")
                console.print(f"  CLI: claudeforge status {feat_id}")
            else:
                console.print(f"[red]Error: {response.text}[/red]")
                raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Connection error: {e}[/red]")
        console.print("Make sure the ClaudeForge API is running.")
        raise typer.Exit(1)


@app.command()
def status(
    feat_id: Optional[str] = typer.Argument(
        None, help="Feature ID to check (optional)"
    ),
):
    """Check workflow status."""
    try:
        if feat_id:
            # Get specific workflow status
            response = httpx.get(
                get_api_url(f"/api/agents/status/{feat_id}"),
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                progress_pct = data.get("progress", 0) * 100

                table = Table(title=f"Workflow Status: {feat_id}")
                table.add_column("Property", style="cyan")
                table.add_column("Value", style="green")

                table.add_row("Status", data.get("status", "unknown"))
                table.add_row("Current Phase", data.get("current_phase", "unknown"))
                table.add_row("Progress", f"{progress_pct:.0f}%")

                console.print(table)

                # Show recent logs
                logs = data.get("logs", [])
                if logs:
                    console.print("\n[bold]Recent Logs:[/bold]")
                    for log in logs[-10:]:
                        console.print(f"  • {log}")
            else:
                console.print(f"[red]Feature not found: {feat_id}[/red]")
                raise typer.Exit(1)
        else:
            # List running workflows
            response = httpx.get(
                get_api_url("/api/agents/running"),
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                running = data.get("running", [])

                if running:
                    table = Table(title="Running Workflows")
                    table.add_column("Feature ID", style="cyan")
                    table.add_column("Status", style="green")

                    for fid in running:
                        table.add_row(fid, "running")

                    console.print(table)
                else:
                    console.print("[yellow]No running workflows[/yellow]")
            else:
                console.print(f"[red]Error: {response.text}[/red]")

    except httpx.RequestError as e:
        console.print(f"[red]Connection error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def projects():
    """List all projects."""
    try:
        response = httpx.get(
            get_api_url("/api/projects/list"),
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            project_list = data.get("projects", [])

            if project_list:
                table = Table(title="Registered Projects")
                table.add_column("Name", style="cyan")
                table.add_column("Path", style="blue")
                table.add_column("Status", style="green")

                for proj in project_list:
                    table.add_row(
                        proj.get("name", ""),
                        proj.get("path", ""),
                        proj.get("status", "active"),
                    )

                console.print(table)
            else:
                console.print("[yellow]No projects registered[/yellow]")
                console.print("Mount projects to /projects/ and they will be auto-detected.")
        else:
            console.print(f"[red]Error: {response.text}[/red]")

    except httpx.RequestError as e:
        console.print(f"[red]Connection error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def verify():
    """Verify ClaudeForge health."""
    console.print("[bold]ClaudeForge Health Check[/bold]\n")

    checks = [
        ("API", "/health"),
    ]

    all_ok = True
    for name, endpoint in checks:
        try:
            response = httpx.get(get_api_url(endpoint), timeout=5)
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "ok")
                console.print(f"[green]✓[/green] {name}: {status}")

                if name == "API":
                    db_status = data.get("database", "unknown")
                    console.print(f"  Database: {db_status}")
            else:
                console.print(f"[red]✗[/red] {name}: HTTP {response.status_code}")
                all_ok = False
        except httpx.RequestError as e:
            console.print(f"[red]✗[/red] {name}: Connection failed")
            all_ok = False

    # Check environment
    console.print("\n[bold]Environment:[/bold]")
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if api_key and api_key.startswith("sk-"):
        console.print("[green]✓[/green] ANTHROPIC_API_KEY: configured")
    else:
        console.print("[red]✗[/red] ANTHROPIC_API_KEY: not set")
        all_ok = False

    if all_ok:
        console.print("\n[green]All checks passed![/green]")
    else:
        console.print("\n[red]Some checks failed.[/red]")
        raise typer.Exit(1)


@app.command()
def logs(
    feat_id: str = typer.Argument(..., help="Feature ID"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow logs"),
    lines: int = typer.Option(50, "--lines", "-n", help="Number of lines"),
):
    """View logs for a workflow."""
    try:
        response = httpx.get(
            get_api_url(f"/api/agents/status/{feat_id}"),
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            logs_list = data.get("logs", [])[-lines:]

            console.print(f"[bold]Logs for {feat_id}:[/bold]\n")
            for log in logs_list:
                console.print(f"  {log}")

            if follow:
                console.print("\n[yellow]Following logs... (Ctrl+C to stop)[/yellow]")
                # Note: Real implementation would use WebSocket
                console.print("[dim]WebSocket follow not implemented in CLI[/dim]")
        else:
            console.print(f"[red]Feature not found: {feat_id}[/red]")
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Connection error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def approve(
    feat_id: str = typer.Argument(..., help="Feature ID"),
    phase: str = typer.Argument(..., help="Phase to approve"),
    comment: str = typer.Option("", "--comment", "-c", help="Approval comment"),
):
    """Approve a workflow phase."""
    try:
        response = httpx.post(
            get_api_url("/api/specs/approve"),
            json={
                "feat_id": feat_id,
                "phase": phase,
                "action": "approve",
                "comment": comment,
            },
            timeout=10,
        )

        if response.status_code == 200:
            console.print(f"[green]Phase '{phase}' approved for {feat_id}[/green]")
        else:
            console.print(f"[red]Error: {response.text}[/red]")
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Connection error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def reject(
    feat_id: str = typer.Argument(..., help="Feature ID"),
    phase: str = typer.Argument(..., help="Phase to reject"),
    comment: str = typer.Option("", "--comment", "-c", help="Rejection comment"),
):
    """Reject a workflow phase."""
    try:
        response = httpx.post(
            get_api_url("/api/specs/approve"),
            json={
                "feat_id": feat_id,
                "phase": phase,
                "action": "reject",
                "comment": comment,
            },
            timeout=10,
        )

        if response.status_code == 200:
            console.print(f"[yellow]Phase '{phase}' rejected for {feat_id}[/yellow]")
        else:
            console.print(f"[red]Error: {response.text}[/red]")
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Connection error: {e}[/red]")
        raise typer.Exit(1)


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
