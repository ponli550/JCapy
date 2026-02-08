import sys
import argparse
import os
from jcapy.config import get_active_library_path, get_current_persona_name, load_config
from jcapy.utils.updates import check_for_skill_updates, get_update_status, VERSION
from jcapy.commands.skills import list_skills, harvest_skill, search_skills, open_skill, delete_skill, merge_skills, apply_skill
from jcapy.commands.brain import select_persona, open_brain_vscode, run_brainstorm_wizard, migrate_persona_libraries
from jcapy.commands.sync import sync_all_personas, push_all_personas
from jcapy.commands.project import init_project, deploy_project
from jcapy.commands.doctor import run_doctor

# ANSI Colors
CYAN = '\033[1;36m'
GREEN = '\033[1;32m'
YELLOW = '\033[1;33m'
MAGENTA = '\033[1;35m'
BLUE = '\033[1;34m'
WHITE = '\033[1;37m'
RED = '\033[1;31m'
RESET = '\033[0m'
GREY = '\033[0;90m'

def print_help():
    """Render Rich Help Menu"""
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel

        console = Console()
        app_update, skill_update = get_update_status()

        # Update Banner (App)
        if app_update:
            console.print(f"\n[bold green]🚀 jcapy Update Available: v{app_update}[/bold green]")
            console.print(f"[dim]Run 'brew upgrade jcapy' to update from v{VERSION}[/dim]")

        # Update Banner (Skills)
        if skill_update:
            console.print("\n[bold yellow]🌟 New skill updates available! Run 'jcapy sync' to upgrade your knowledge.[/bold yellow]")

        # Header
        console.print(Panel.fit("[bold cyan]🤖 jcapy CLI[/bold cyan] - One-Army Orchestrator", border_style="blue"))
        console.print(f"[dim]Active Persona: {get_current_persona_name()}[/dim]")

        table = Table(show_header=True, header_style="bold magenta", box=None)
        table.add_column("Command", style="cyan", width=12)
        table.add_column("Alias", style="yellow", width=8)
        table.add_column("Description", style="white")

        table.add_row("manage", "tui", "Interactive Command Center [bold](Default)[/bold]")
        table.add_row("harvest", "new", "Wizard to extract new skills")
        table.add_row("list", "ls", "List all knowledge base skills")
        table.add_row("apply", "", "Inject Skill (Executable Knowledge)")
        table.add_row("deploy", "", "Deploy pipeline (Grade-Aware)")
        table.add_row("search", "", "Fuzzy search by content")
        table.add_row("open", "", "Open skill in VS Code")
        table.add_row("delete", "rm", "Delete a skill")
        table.add_row("doctor", "chk", "Check system health")
        table.add_row("persona", "p", "Switch Persona")
        table.add_row("sync", "", "Update Skill Library (Git Sync)")
        table.add_row("push", "", "Upload Local Changes (Git Push)")
        table.add_row("brainstorm", "bs", "AI Refactor & Optimization")
        table.add_row("merge", "", "Create a Blueprint (Frontend + Backend)")
        table.add_row("init", "", "Scaffold new project structure")
        table.add_row("help", "", "Show this help screen")

        console.print(table)
        console.print("\n[grey50]Run 'jcapy <command> -h' for specific arguments.[/grey50]")

    except ImportError:
        print("Rich not installed. Run 'pip install rich'")

def show_welcome():
    print(f"{CYAN}Welcome to jcapy!{RESET}")
    print("Initializing your environment...")

def main():
    parser = argparse.ArgumentParser(description=f"# jcapy Core - The One-Army Orchestrator\n# Version: {VERSION}", add_help=False)
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Subcommands with Aliases
    subparsers.add_parser("list", aliases=["ls"], help="List all harvested skills")

    harvest_parser = subparsers.add_parser("harvest", aliases=["new"], help="Interactive skill extraction wizard")
    harvest_parser.add_argument("--doc", help="Path to documentation file to auto-harvest from")
    harvest_parser.add_argument("doc_flag", nargs='?', help="Positional path to doc (optional)")

    # Search Command
    search_parser = subparsers.add_parser("search", help="Search skills by content")
    search_parser.add_argument("query", help="Keyword to search for")

    # Open Command
    open_parser = subparsers.add_parser("open", help="Open a skill in VS Code")
    open_parser.add_argument("name", help="Name of the skill to open (fuzzy match)")

    # Delete Command
    delete_parser = subparsers.add_parser("delete", aliases=["rm"], help="Delete a skill")
    delete_parser.add_argument("name", help="Name of the skill to delete")

    # Code Command (New)
    subparsers.add_parser("code", help="Open jcapy Brain in VS Code")

    # Manage Command (TUI)
    subparsers.add_parser("manage", aliases=["tui"], help="Interactive TUI Manager")

    # Persona Command
    subparsers.add_parser("persona", aliases=["p"], help="Switch Persona")

    # Init Command
    subparsers.add_parser("init", help="Scaffold One-Army Project")

    # Deploy Command
    subparsers.add_parser("deploy", help="Deploy Project")

    # Merge Command
    subparsers.add_parser("merge", help="Merge Skills into Blueprint")

    # Apply Command
    apply_parser = subparsers.add_parser("apply", help="Apply Skill (Executable Knowledge)")
    apply_parser.add_argument("name", help="Name of the skill to apply")
    apply_parser.add_argument("--dry-run", action="store_true", help="Preview commands without running")

    # Doctor Command
    subparsers.add_parser("doctor", aliases=["chk", "check"], help="Check system health")

    # Sync Command
    subparsers.add_parser("sync", help="Sync skills with remote library")

    # Push Command
    subparsers.add_parser("push", help="Push skills to remote library")

    # Brainstorm Command
    subparsers.add_parser("brainstorm", aliases=["bs"], help="AI Refactor & Optimization")

    # Help Command
    subparsers.add_parser("help", help="Show help message")

    try:
        # Handling for no args
        if len(sys.argv) == 1:
            config_path = os.path.join(os.getcwd(), ".jcapyrc")
            global_config = os.path.expanduser("~/.jcapyrc")
            # If completely new user
            if not os.path.exists(config_path) and not os.path.exists(global_config):
                show_welcome()

            check_for_skill_updates()
            migrate_persona_libraries() # Auto-migrate
            # Default Flow: Select Persona -> Launches TUI
            select_persona()
            return

        # Handle custom version flag
        if "--version" in sys.argv or "-v" in sys.argv:
            print(f"jcapy v{VERSION}")
            return

        # Handle custom help flag
        if "-h" in sys.argv or "--help" in sys.argv:
            check_for_skill_updates()
            print_help()
            return

        try:
            # Argparse doesn't handle aliases by default in older python versions,
            # but we assume 3.8+ behavior where it mostly works or we rely on explicit mapping if needed.
            # However, standard argparse aliases param requires Python 3.7+.
            args = parser.parse_args()
        except argparse.ArgumentError:
            print_help()
            return

        # Command Router
        cmd = args.command

        if cmd in ["list", "ls"]:
            # TUI List
            from jcapy.ui.tui import run as run_tui
            run_tui(get_active_library_path())
        elif cmd in ["harvest", "new"]:
            doc_arg = args.doc if args.doc else getattr(args, 'doc_flag', None)
            harvest_skill(doc_arg)
        elif cmd == "search":
            search_skills(args.query)
        elif cmd == "open":
            open_skill(args.name)
        elif cmd == "code":
            open_brain_vscode()
        elif cmd in ["delete", "rm"]:
            delete_skill(args.name)
        elif cmd in ["manage", "tui"]:
            from jcapy.ui.tui import run as run_tui
            run_tui(get_active_library_path())
        elif cmd in ["persona", "p"]:
            select_persona()
        elif cmd == "init":
            init_project()
        elif cmd == "merge":
            merge_skills()
        elif cmd == "deploy":
            deploy_project()
        elif cmd in ["doctor", "chk", "check"]:
            run_doctor()
        elif cmd in ["brainstorm", "bs"]:
            run_brainstorm_wizard()
        elif cmd == "sync":
            sync_all_personas()
        elif cmd == "push":
            push_all_personas()
        elif cmd == "apply":
            apply_skill(args.name, args.dry_run)
        elif cmd == "help":
            check_for_skill_updates()
            print_help()
        else:
            print_help()

    except KeyboardInterrupt:
        print(f"\n{RED}Aborted by user.{RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{RED}Unexpected Error: {e}{RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()
