import sys
import argparse
import os
from jcapy.config import get_active_library_path, get_current_persona_name, load_config, set_ux_preference, get_all_ux_preferences
from jcapy.utils.updates import check_for_framework_updates, get_update_status, VERSION
from jcapy.commands.frameworks import list_frameworks, harvest_framework, search_frameworks, open_framework, delete_framework, merge_frameworks, apply_framework
from jcapy.commands.brain import select_persona, open_brain_vscode, run_brainstorm_wizard, migrate_persona_libraries
from jcapy.commands.sync import sync_all_personas, push_all_personas
from jcapy.commands.project import init_project, deploy_project, map_project_patterns
from jcapy.commands.doctor import run_doctor
from jcapy.commands.edit import rapid_fix
from jcapy.commands.research import autonomous_explore
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
BOLD = '\033[1m'
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

        from jcapy.commands.help import run_interactive_help
        run_interactive_help()
        console.print("\n[grey50]Run 'jcapy <command> -h' for specific arguments.[/grey50]")

    except ImportError:
        print("Rich not installed. Run 'pip install rich'")

def show_welcome():
    print(f"{CYAN}Welcome to jcapy!{RESET}")
    print("Initializing your environment...")

def main():
    parser = argparse.ArgumentParser(description=f"# jcapy Core - The One-Army Orchestrator\n# Version: {VERSION}", add_help=True)
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Subcommands with Aliases
    subparsers.add_parser("list", aliases=["ls"], help="List all harvested frameworks")

    # Harvest Command
    harvest_parser = subparsers.add_parser("harvest", aliases=["new"], help="Extract current code into a reusable skill")
    harvest_parser.add_argument("--doc", help="Path to existing documentation to parse")
    harvest_parser.add_argument("--auto", help="Path to file to automatically extract a skill from")
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
    persona_parser = subparsers.add_parser("persona", aliases=["p"], help="Switch Persona")
    persona_parser.add_argument("name", nargs="?", help="Name of the persona to switch to")

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

    # Suggest Command
    subparsers.add_parser("suggest", help="Recommend next best actions")

    # Help Command
    subparsers.add_parser("help", help="Show help message")

    # MCP Command
    subparsers.add_parser("mcp", help="Start JCapy MCP Server (Stdio)")

    # Undo Command
    undo_parser = subparsers.add_parser("undo", help="Undo last destructive action")
    undo_parser.add_argument("--list", action="store_true", dest="list_undo", help="List undo history")

    # Recall Command (Phase 4: Memory)
    recall_parser = subparsers.add_parser("recall", help="Semantic Search (Vector Memory)")
    recall_parser.add_argument("query", nargs="+", help="Natural language query")

    # Fix Command
    fix_parser = subparsers.add_parser("fix", help="Rapid tactical code fix")
    fix_parser.add_argument("file", help="Path to file to fix")
    fix_parser.add_argument("instruction", help="Instruction for the fix")
    fix_parser.add_argument("--diag", help="LSP diagnostic context (error messages)")

    # Explore Command
    explore_parser = subparsers.add_parser("explore", help="Autonomous research & draft skill")
    explore_parser.add_argument("topic", help="Topic to research")

    # Map Command
    map_parser = subparsers.add_parser("map", help="Analyze project for harvesting candidates")
    map_parser.add_argument("path", nargs="?", default=".", help="Project path to map")

    # Tutorial Command
    tutorial_parser = subparsers.add_parser("tutorial", help="Interactive onboarding")
    tutorial_parser.add_argument("--reset", action="store_true", help="Reset tutorial progress")

    # Config Command
    config_parser = subparsers.add_parser("config", help="Manage UX preferences and keys")
    config_subparsers = config_parser.add_subparsers(dest="action")
    config_subparsers.add_parser("list", help="List all preferences")

    set_key_parser = config_subparsers.add_parser("set-key", help="Set AI Provider API Key")
    set_key_parser.add_argument("provider", choices=["gemini", "openai", "deepseek"], help="AI Provider name")

    config_get_parser = config_subparsers.add_parser("get", help="Get a preference")
    config_get_parser.add_argument("key_value", help="Key name")

    config_set_parser = config_subparsers.add_parser("set", help="Set a preference")
    config_set_parser.add_argument("key_value", help="key=value")

    try:
        # Handling for no args
        if len(sys.argv) == 1:
            # Check for standard config file
            from jcapy.config import CONFIG_PATH
            print(f"DEBUG: CONFIG_PATH='{CONFIG_PATH}'")
            print(f"DEBUG: Checking {CONFIG_PATH}, exists={os.path.exists(CONFIG_PATH)}")
            print("DEBUG: Calling ensure_operator_identity...")
            ensure_operator_identity()
            sys.exit("DEBUG EXIT - After ensure_operator_identity")

            # If completely new user (no config exists)
            print(f"DEBUG: Checking {CONFIG_PATH}, exists={os.path.exists(CONFIG_PATH)}")
            if not os.path.exists(CONFIG_PATH):
                # 1. Animations: Matrix Rain + Crystallizing Logo
                try:
                    from jcapy.ui.animations import cinematic_intro, should_animate, typewriter_print
                    if should_animate():
                        # cinematic_intro()
                        pass
                        print("\n")
                        typewriter_print(f"{CYAN}Welcome to JCapy.{RESET}", speed=0.08)
                        time.sleep(0.5)
                        typewriter_print(f"{GREY}Your personal AI Architect.{RESET}", speed=0.05)
                        time.sleep(1)
                except ImportError:
                    pass

                # 2. Admin Setup: "Who is operating right now?"
                from jcapy.commands.brain import setup_initial_persona
                setup_initial_persona()

                # 3. Tutorial: Interactive Guide
                tutorial = get_tutorial()
                tutorial.run_interactive()

            else:
                 # Standard Intro for returning users
                 try:
                    from jcapy.ui.animations import cinematic_intro, should_animate
                    if should_animate():
                        cinematic_intro()
                 except ImportError:
                    pass

            # 2a. Security Check (ensure identity is known on updates)
            from jcapy.commands.brain import ensure_operator_identity
            print("DEBUG: Calling ensure_operator_identity...")
            ensure_operator_identity()

            check_for_framework_updates()
            migrate_persona_libraries() # Auto-migrate

            # Default Flow: Dashboard directly (User Request)
            # select_persona() <--- Skipped in favor of valid dashboard
            from jcapy.ui.tui import run as run_tui
            run_tui(get_active_library_path())
            return

        # Handle custom version flag
        if "--version" in sys.argv or "-v" in sys.argv:
            print(f"jcapy v{VERSION}")
            return

        # Handle custom help flag - only for global help
        if len(sys.argv) == 2 and sys.argv[1] in ["-h", "--help"]:
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
            harvest_framework(doc_arg, auto_path=args.auto)
        elif cmd == "search":
            search_frameworks(args.query)
        elif cmd == "code":
            open_brain_vscode()
        elif cmd in ["delete", "rm"]:
            delete_framework(args.name)
        elif cmd in ["manage", "tui"]:
            from jcapy.ui.tui import run as run_tui
            run_tui(get_active_library_path())
        elif cmd in ["persona", "p"]:
            select_persona(getattr(args, 'name', None))
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
        elif cmd == "fix":
            rapid_fix(args.file, args.instruction, diagnostics=args.diag)
        elif cmd == "explore":
            autonomous_explore(args.topic)
        elif cmd == "mcp":
            from jcapy.mcp.server import run_mcp_server
            run_mcp_server()
        elif cmd == "map":
            map_project_patterns(args.path)
        elif cmd == "recall":
            # 1. Initialize Memory
            try:
                from jcapy.memory import MemoryBank
                bank = MemoryBank()

                # Check if we need to sync (simplistic check: if empty)
                if bank.collection.count() == 0:
                    print(f"{YELLOW}🧠 Initializing Memory Bank (First Run)...{RESET}")
                    bank.sync_library(get_active_library_path())

                query = " ".join(args.query)
                print(f"{CYAN}🔍 Recalling knowledge related to: '{query}'...{RESET}")

                results = bank.recall(query, n_results=5)

                if not results:
                    print(f"{GREY}No relevant memories found.{RESET}")
                else:
                    for i, res in enumerate(results, 1):
                        meta = res['metadata']
                        score = res['distance'] # Lower is better in Chroma usually
                        similarity = (1 - score) * 100 # Rough approx
                        print(f"\n{i}. {BOLD}{meta['name']}{RESET} ( Relevance: {similarity:.1f}% )")
                        print(f"   Shape: {meta['source']}")
                        # print(f"   Excerpt: {res['content'][:100]}...")
            except ImportError:
                print(f"{RED}Error: 'chromadb' not installed. Run 'pip install chromadb' first.{RESET}")
            except Exception as e:
                print(f"{RED}Memory Error: {e}{RESET}")
        elif cmd == "suggest":
            # Suggestion Logic
            print(f"{CYAN}🤖 jcapy Recommendations:{RESET}")
            lib_path = get_active_library_path()

            # 1. Harvest Check
            has_files = False
            for r, d, f in os.walk(lib_path):
                if any(k.endswith('.md') for k in f):
                    has_files = True
                    break

            if not has_files:
                print(f"  • {GREEN}jcapy harvest{RESET}: Start building your knowledge base.")
                print(f"  • {GREEN}jcapy init{RESET}: Create a new project structure.")
            else:
                # 2. Sync Check
                try:
                    from jcapy.utils.git_lib import get_git_status
                    _, pending = get_git_status(lib_path)
                    if pending > 0:
                        print(f"  • {GREEN}jcapy push{RESET}: You have {pending} uncommitted changes.")
                except: pass

                print(f"  • {GREEN}jcapy list{RESET}: Browse your library.")
                print(f"  • {GREEN}jcapy manage{RESET}: Open the Dashboard.")

            # General
            print(f"  • {GREEN}jcapy doctor{RESET}: Verify system health.")

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
            if action == "list":
                prefs = get_all_ux_preferences()
                print(f"{CYAN}UX Preferences:{RESET}")
                for k, v in prefs.items():
                    print(f"  {k}: {v}")
            elif action == "set-key":
                # Secure prompt for key
                from rich.prompt import Prompt
                provider = args.provider
                key = Prompt.ask(f"Enter {provider.capitalize()} API Key", password=True)
                if key:
                    from jcapy.config import set_api_key
                    success, msg = set_api_key(provider, key)
                    if success:
                        show_success(msg)
                        print(f"{GREY}Tip: Run 'jcapy doctor' to verify.{RESET}")
                    else:
                        show_error(msg)
                else:
                    print(f"{YELLOW}Key entry cancelled.{RESET}")
            elif action == "set":
                key_value = getattr(args, 'key_value', None)
                if key_value and "=" in key_value:
                    key, value = key_value.split("=", 1)
                    # Parse boolean values
                    if value.lower() in ("true", "1", "yes"):
                        value = True
                    elif value.lower() in ("false", "0", "no"):
                        value = False
                    set_ux_preference(key.strip(), value)
                    show_success(f"Set {key.strip()} = {value}")
                else:
                    print(f"{YELLOW}Usage: jcapy config set key=value{RESET}")
            elif action == "get":
                key_value = getattr(args, 'key_value', None)
                if key_value:
                    config = load_config()
                    prefs = get_all_ux_preferences()
                    # Check root first, then UX
                    val = config.get(key_value) or prefs.get(key_value, 'not set')
                    print(f"{key_value}: {val}")
                else:
                    print(f"{YELLOW}Usage: jcapy config get key{RESET}")
            else:
                print(f"{YELLOW}Usage: jcapy config set-key [provider] | set key=value | get key | list{RESET}")
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
