from jcapy.utils.updates import VERSION, get_update_status
from rich.console import Console

def run_version(args):
    """Displays JCapy version and update status."""
    console = Console()
    app_update, skill_update = get_update_status()

    console.print(f"[bold cyan]JCapy[/][dim] v{VERSION}[/dim]")

    if app_update:
        console.print(f"[bold green]🚀 Update Available: v{app_update}[/bold green]")
        console.print(f"[dim]Run 'brew upgrade jcapy' to update.[/dim]")
    else:
        console.print("[dim]You are on the latest version.[/dim]")

    if skill_update:
        console.print("[bold yellow]🌟 Skill updates available. Run 'jcapy sync' to upgrade.[/bold yellow]")

    return None
