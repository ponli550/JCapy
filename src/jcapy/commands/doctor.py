import os
import shutil
import subprocess
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from jcapy.config import load_config, DEFAULT_LIBRARY_PATH
from jcapy.utils.git_lib import get_git_remote_url
# We can't reuse the old renderer directly for Rich components, but we can adapt logic.
# The request specifically asked for "Glass Box" UI in doctor.py using jcapy.ui.theme

# Import the theme we created earlier to ensure consistency
from jcapy.ui.theme import GLASS_STYLE, create_glass_panel

console = Console()

def check_k8s_connection():
    """Checks if kubectl can connect to a running cluster"""
    try:
        subprocess.check_output(["kubectl", "cluster-info"], stderr=subprocess.STDOUT, timeout=5)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False

def check_system(full_scan=True):
    """Performs system health checks. Returns a dict of results."""
    results = {
        "tools": {},
        "config": {},
        "integrations": {},
        "installation": {},
        "all_passed": True
    }

    # 0. Check Installation (Homebrew)
    results["installation"]["Homebrew Managed"] = False
    if shutil.which("brew"):
        try:
            # Check if jcapy is in brew list
            res = subprocess.run(["brew", "list", "--formula"], capture_output=True, text=True)
            if "jcapy" in res.stdout:
                results["installation"]["Homebrew Managed"] = True
        except:
            pass

    # Path of executable
    results["installation"]["Binary Path"] = sys.argv[0]

    # 1. Check Tools
    tools = ["git", "node", "npm"]
    for tool in tools:
        if shutil.which(tool):
            results["tools"][tool] = True
        else:
            results["tools"][tool] = False
            results["all_passed"] = False

    # 2. Check Config
    cwd = os.getcwd()
    results["config"][".jcapyrc"] = os.path.exists(os.path.join(cwd, ".jcapyrc"))
    results["config"][".env"] = os.path.exists(os.path.join(cwd, ".env"))

    # We don't fail just because .jcapyrc is missing in CWD, as we might be outside a project
    # But for the purpose of a "Project Doctor", it might be relevant.
    # The original code set all_passed=False if .jcapyrc missing.
    if not results["config"][".jcapyrc"]:
        # Only affect all_passed if we are strictly checking project context?
        # Retaining original logic:
        results["all_passed"] = False

    results["integrations"]["Vercel Linked"] = os.path.exists(os.path.join(cwd, ".vercel"))
    results["integrations"]["Supabase Linked"] = os.path.exists(os.path.join(cwd, "supabase", "config.toml")) or os.path.exists(os.path.join(cwd, "supabase", "config.json"))

    # 4. Check AI Keys
    results["ai_keys"] = {}
    from jcapy.config import get_api_key
    for p in ["gemini", "openai", "deepseek"]:
        key = get_api_key(p)
        results["ai_keys"][p] = True if key else False

    # 5. Check Blueprint (Merge) - simplified local config load
    config_data = {}
    if results["config"][".jcapyrc"]:
        try:
             with open(os.path.join(cwd, ".jcapyrc"), 'r') as f:
                 import json
                 config_data = json.load(f)
        except: pass

    if config_data.get("type") == "blueprint":
        if "frontend" in config_data:
            fe_path = os.path.join(cwd, "apps/web")
            if not os.path.exists(fe_path):
                results["integrations"]["Frontend (Blueprint)"] = False
                results["all_passed"] = False
            else:
                 results["integrations"]["Frontend (Blueprint)"] = True

        if "backend" in config_data:
             be_path = os.path.join(cwd, "apps/api")
             if not os.path.exists(be_path):
                 results["integrations"]["Backend (Blueprint)"] = False
                 results["all_passed"] = False
             else:
                 results["integrations"]["Backend (Blueprint)"] = True

    return results

def run_doctor():
    """CLI Command: Check system health"""
    # Use Glass Box Styling for the main title?
    # Original used console.print("[bold cyan]🩺 jcapy Doctor[/bold cyan]")
    # We will wrap the whole thing or sections in Glass Panels.

    console.print(Panel("[bold cyan]🩺 jcapy Doctor[/bold cyan]", box=GLASS_STYLE["box"], border_style=GLASS_STYLE["border_style"]))

    results = check_system()

    # Installation Table
    table = Table(show_header=False, box=None)
    table.add_column("Item")
    table.add_column("Status")

    console.print("\n[bold]📦 Installation[/bold]")
    is_brew = results["installation"]["Homebrew Managed"]
    brew_status = "[green]Yes (Brew)[/green]" if is_brew else "[yellow]Manual Symlink[/yellow]"
    table.add_row("  Managed", brew_status)
    table.add_row("  Binary", f"[dim]{results['installation']['Binary Path']}[/dim]")
    console.print(table)

    # Tools Table
    table = Table(show_header=False, box=None)
    table.add_column("Item")
    table.add_column("Status")

    console.print("\n[bold]🛠  Tools[/bold]")
    for tool, passed in results["tools"].items():
        icon = "[green]✔[/green]" if passed else "[red]✘[/red]"
        msg = f"[dim]Found[/dim]" if passed else "[red]Missing[/red]"
        table.add_row(f"  {tool}", f"{icon}  {msg}")
    console.print(table)

    # Config Table
    table = Table(show_header=False, box=None)
    table.add_column("Item")
    table.add_column("Status")

    console.print("\n[bold]📂 Configuration[/bold]")
    for conf, passed in results["config"].items():
        icon = "[green]✔[/green]" if passed else "[yellow]![/yellow]"
        msg = f"[dim]Present[/dim]" if passed else "[yellow]Missing[/yellow]"
        table.add_row(f"  {conf}", f"{icon}  {msg}")
    console.print(table)

    # Integrations
    table = Table(show_header=False, box=None)
    table.add_column("Item")
    table.add_column("Status")

    console.print("\n[bold]🔗 Integrations[/bold]")
    for integ, passed in results["integrations"].items():
        icon = "[green]✔[/green]" if passed else "[yellow]![/yellow]"
        msg = f"[dim]Linked[/dim]" if passed else "[yellow]Not Linked[/yellow]"
        table.add_row(f"  {integ}", f"{icon}  {msg}")
    console.print(table)

    # AI Keys Table
    table = Table(show_header=False, box=None)
    table.add_column("Item", width=15)
    table.add_column("Status")

    console.print("\n[bold]🤖 AI Agentic Keys[/bold]")
    for provider, passed in results.get("ai_keys", {}).items():
        icon = "[green]✔[/green]" if passed else "[red]![/red]"
        msg = f"[dim]Configured[/dim]" if passed else "[red]Missing[/red]"
        table.add_row(f"  {provider.capitalize()}", f"{icon}  {msg}")
    console.print(table)

    # Personas Integrity Check (The Main Event for Refactor)
    # Using GLASS_STYLE from theme.py

    p_table = Table(
        box=GLASS_STYLE["box"],
        border_style=GLASS_STYLE["border_style"],
        header_style=GLASS_STYLE["header_style"],
        expand=True
    )
    p_table.add_column("Persona", style="bold white")
    p_table.add_column("Path", style="dim white")
    p_table.add_column("Remote URL", style="dim cyan", overflow="ellipsis")
    p_table.add_column("Status", justify="center")

    config = load_config()
    personas = config.get("personas", {})
    if "programmer" not in personas:
         personas["programmer"] = {"path": DEFAULT_LIBRARY_PATH}

    for name, p_data in personas.items():
        path = p_data.get("path", "")
        exists = os.path.exists(path)

        remote_url_display = "[dim]Local Only[/dim]"
        if exists:
            # Modified to use git_lib helper
            url = get_git_remote_url(path)
            if url:
                remote_url_display = url
            else:
                 # Check if it IS a git repo but no remote, or not a git repo?
                 # git_lib returns None for both.
                 if os.path.exists(os.path.join(path, ".git")):
                     remote_url_display = "[dim]No Remote[/dim]"
                 else:
                     remote_url_display = "[bold red]LOCAL (No Git)[/bold red]"

        elif not exists:
            remote_url_display = "[bold red]MISSING[/bold red]"

        if exists:
            status = "[green]Active[/green]"
        else:
            status = "[bold red]MISSING[/bold red]"
            results["all_passed"] = False # Fail doctor if brain is missing

        p_table.add_row(name, path, remote_url_display, status)

    # Wrap in Glass Panel as requested
    console.print(create_glass_panel(p_table, title="[bold blue]JCapy Diagnostic[/bold blue]"))

    # Recovery Hint for Missing Personas
    for name, p_data in personas.items():
        path = p_data.get("path", "")
        if not os.path.exists(path):
             console.print(f"\n[red]⚠️  Critical: Persona '{name}' is missing its library at {path}[/red]")
             console.print(f"   [yellow]→ If you have a backup/remote, run:[/yellow] git clone <url> {path}")
             console.print(f"   [yellow]→ Or run:[/yellow] jcapy sync (if remote was configured)")

    if not results["all_passed"]:
         console.print("\n[yellow]⚠️  Issues detected. Run 'jcapy init' or install missing tools.[/yellow]")
    else:
         console.print("\n[green]✨ System Healthy. Ready to deploy.[/green]")

if __name__ == "__main__":
    run_doctor()
