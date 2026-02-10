import sys
import argparse
import os
from jcapy.config import get_active_library_path, get_current_persona_name, load_config, set_ux_preference, get_all_ux_preferences
from jcapy.utils.updates import check_for_framework_updates, get_update_status, VERSION
from jcapy.commands.frameworks import list_frameworks, harvest_framework, search_frameworks, open_framework, delete_framework, merge_frameworks, apply_framework
from jcapy.commands.brain import select_persona, open_brain_vscode, run_brainstorm_wizard, migrate_persona_libraries
from jcapy.commands.sync import sync_all_personas, push_all_personas
from jcapy.commands.project import init_project, deploy_project
from jcapy.commands.doctor import run_doctor
from jcapy.ui.ux.safety import get_undo_stack
from jcapy.ui.ux.hints import prompt_typo_correction, get_tutorial, JCAPY_COMMANDS
from jcapy.ui.ux.feedback import show_success, show_error

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
    """Render Rich Help Menu with Logo"""
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich.text import Text

        console = Console()
        app_update, framework_update = get_update_status()

#         # ASCII Logo (Rubik-style blocks)
#         logo = """
# [bold cyan]     ██  ██████  █████  ██████  ██    ██[/bold cyan]
# [bold blue]     ██ ██      ██   ██ ██   ██  ██  ██[/bold blue]
# [bold magenta]     ██ ██      ███████ ██████    ████[/bold magenta]
# [bold yellow]██   ██ ██      ██   ██ ██         ██[/bold yellow]
# [bold green] █████   ██████ ██   ██ ██         ██[/bold green]
# """
#         console.print(logo)

        # Tagline
        console.print("[bold white]One-Army Orchestrator[/bold white] [dim]• Build Like a Team of Ten[/dim]")
        console.print(f"[dim]v{VERSION} • {get_current_persona_name()}[/dim]\n")

        # Update Banner (App)
        if app_update:
            console.print(f"[bold green]🚀 jcapy Update Available: v{app_update}[/bold green]")
            console.print(f"[dim]Run 'brew upgrade jcapy' to update from v{VERSION}[/dim]")

        # Update Banner (Skills)
        if framework_update:
            console.print("[bold yellow]🌟 New framework updates available! Run 'jcapy sync' to upgrade your knowledge.[/bold yellow]")

        table = Table(show_header=True, header_style="bold magenta", box=None)
        table.add_column("Command", style="cyan", width=12)
        table.add_column("Alias", style="yellow", width=8)
        table.add_column("Description", style="white")

        table.add_row("manage", "tui", "Interactive Command Center [bold](Default)[/bold]")
        table.add_row("harvest", "new", "Wizard to extract new frameworks")
        table.add_row("list", "ls", "List all knowledge base frameworks")
        table.add_row("apply", "", "Deploy Framework (Executable Knowledge)")
        table.add_row("deploy", "", "Deploy pipeline (Grade-Aware)")
        table.add_row("search", "", "Fuzzy search by content")
        table.add_row("open", "", "Open framework in VS Code")
        table.add_row("delete", "rm", "Delete a framework")
        table.add_row("doctor", "chk", "Check system health")
        table.add_row("persona", "p", "Switch Persona")
        table.add_row("sync", "", "Update Framework Library (Git Sync)")
        table.add_row("push", "", "Upload Local Changes (Git Push)")
        table.add_row("brainstorm", "bs", "AI Refactor & Optimization")
        table.add_row("merge", "", "Create a Blueprint (Frontend + Backend)")
        table.add_row("init", "", "Scaffold new project structure")
        table.add_row("undo", "", "Undo last destructive action")
        table.add_row("tutorial", "", "Interactive onboarding guide")
        table.add_row("config", "", "Set preferences (theme, hints)")
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
    subparsers.add_parser("list", aliases=["ls"], help="List all harvested frameworks")

    harvest_parser = subparsers.add_parser("harvest", aliases=["new"], help="Interactive framework extraction wizard")
    harvest_parser.add_argument("--doc", help="Path to documentation file to auto-harvest from")
    harvest_parser.add_argument("doc_flag", nargs='?', help="Positional path to doc (optional)")

    # Search Command
    search_parser = subparsers.add_parser("search", help="Search frameworks by content")
    search_parser.add_argument("query", help="Keyword to search for")

    # Open Command
    open_parser = subparsers.add_parser("open", help="Open a framework in VS Code")
    open_parser.add_argument("name", help="Name of the framework to open (fuzzy match)")

    # Delete Command
    delete_parser = subparsers.add_parser("delete", aliases=["rm"], help="Delete a framework")
    delete_parser.add_argument("name", help="Name of the framework to delete")

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
    apply_parser.add_argument("name", help="Name of the framework to apply")
    apply_parser.add_argument("--dry-run", action="store_true", help="Preview commands without running")

    # Doctor Command
    subparsers.add_parser("doctor", aliases=["chk", "check"], help="Check system health")

    # Sync Command
    subparsers.add_parser("sync", help="Sync frameworks with remote library")

    # Push Command
    subparsers.add_parser("push", help="Push frameworks to remote library")

    # Brainstorm Command
    subparsers.add_parser("brainstorm", aliases=["bs"], help="AI Refactor & Optimization")

    # Help Command
    subparsers.add_parser("help", help="Show help message")

    # Undo Command
    undo_parser = subparsers.add_parser("undo", help="Undo last destructive action")
    undo_parser.add_argument("--list", action="store_true", dest="list_undo", help="List undo history")

    # Tutorial Command
    tutorial_parser = subparsers.add_parser("tutorial", help="Interactive onboarding")
    tutorial_parser.add_argument("--reset", action="store_true", help="Reset tutorial progress")

    # Config Command
    config_parser = subparsers.add_parser("config", help="Set or view preferences")
    config_parser.add_argument("action", nargs="?", choices=["set", "get", "list"], default="list", help="Action: set, get, or list")
    config_parser.add_argument("key_value", nargs="?", help="key=value for set, key for get")

    try:
        # Handling for no args
        if len(sys.argv) == 1:
            config_path = os.path.join(os.getcwd(), ".jcapyrc")
            global_config = os.path.expanduser("~/.jcapyrc")
            # If completely new user
            if not os.path.exists(config_path) and not os.path.exists(global_config):
                show_welcome()

            check_for_framework_updates()
            migrate_persona_libraries() # Auto-migrate

            # Cinematic intro for main TUI
            try:
                from jcapy.ui.animations import cinematic_intro, should_animate
                if should_animate():
                    cinematic_intro()
            except ImportError:
                pass

            # Default Flow: Select Persona -> Launches TUI
            select_persona()
            return

        # Handle custom version flag
        if "--version" in sys.argv or "-v" in sys.argv:
            print(f"jcapy v{VERSION}")
            return

        # Handle custom help flag
        if "-h" in sys.argv or "--help" in sys.argv:
            check_for_framework_updates()
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
            harvest_framework(doc_arg)
        elif cmd == "search":
            search_frameworks(args.query)
        elif cmd == "open":
            open_framework(args.name)
        elif cmd == "code":
            open_brain_vscode()
        elif cmd in ["delete", "rm"]:
            delete_framework(args.name)
        elif cmd in ["manage", "tui"]:
            from jcapy.ui.tui import run as run_tui
            run_tui(get_active_library_path())
        elif cmd in ["persona", "p"]:
            select_persona()
        elif cmd == "init":
            init_project()
        elif cmd == "merge":
            merge_frameworks()
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
            apply_framework(args.name, args.dry_run)
        elif cmd == "help":
            check_for_framework_updates()
            print_help()
        elif cmd == "undo":
            undo_stack = get_undo_stack()
            if getattr(args, 'list_undo', False):
                items = undo_stack.list_items()
                if not items:
                    print(f"{GREY}No undo history.{RESET}")
                else:
                    print(f"{CYAN}Undo History:{RESET}")
                    for i, item in enumerate(items, 1):
                        print(f"  {i}. {item.get('description', 'Unknown')} ({item.get('timestamp', '')[:16]})")
            else:
                restored = undo_stack.pop()
                if restored:
                    show_success(f"Restored: {restored.get('description', 'item')}")
                else:
                    show_error("Nothing to undo", hint="Run 'jcapy undo --list' to see history")
        elif cmd == "tutorial":
            tutorial = get_tutorial()
            if getattr(args, 'reset', False):
                tutorial.reset()
                show_success("Tutorial progress reset")
            else:
                # Cinematic intro for tutorial
                try:
                    from jcapy.ui.animations import cinematic_intro, should_animate
                    if should_animate():
                        cinematic_intro()
                except ImportError:
                    pass
                tutorial.run_interactive()
        elif cmd == "config":
            action = getattr(args, 'action', 'list')
            key_value = getattr(args, 'key_value', None)
            if action == "list":
                prefs = get_all_ux_preferences()
                print(f"{CYAN}UX Preferences:{RESET}")
                for k, v in prefs.items():
                    print(f"  {k}: {v}")
            elif action == "set" and key_value and "=" in key_value:
                key, value = key_value.split("=", 1)
                # Parse boolean values
                if value.lower() in ("true", "1", "yes"):
                    value = True
                elif value.lower() in ("false", "0", "no"):
                    value = False
                set_ux_preference(key.strip(), value)
                show_success(f"Set {key.strip()} = {value}")
            elif action == "get" and key_value:
                prefs = get_all_ux_preferences()
                print(f"{key_value}: {prefs.get(key_value, 'not set')}")
            else:
                print(f"{YELLOW}Usage: jcapy config set key=value | get key | list{RESET}")
        else:
            # Typo correction
            if args.command:
                corrected = prompt_typo_correction(args.command, JCAPY_COMMANDS)
                if corrected:
                    print(f"{GREY}Running: jcapy {corrected}{RESET}")
                    sys.argv[1] = corrected
                    main()  # Re-run with corrected command
                    return
            print_help()

    except KeyboardInterrupt:
        print(f"\n{RED}Aborted by user.{RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{RED}Unexpected Error: {e}{RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()
