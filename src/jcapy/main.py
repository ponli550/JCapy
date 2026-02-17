# SPDX-License-Identifier: Apache-2.0
import sys
import argparse
import os
import time
from jcapy.config import get_active_library_path, get_current_persona_name, load_config
from jcapy.utils.updates import check_for_framework_updates, get_update_status, VERSION
from jcapy.ui.ux.hints import prompt_typo_correction, get_tutorial, JCAPY_COMMANDS
from jcapy.core.plugins import get_registry
from jcapy.core.bootstrap import register_core_commands

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
        console = Console()
        app_update, framework_update = get_update_status()

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

def main():
    # 1. Initialize Registry
    registry = get_registry()

    # 2. Register Core Commands
    register_core_commands(registry)

    # 3. Load External Plugins
    # 3. Load External Plugins
    registry.load_plugins()

    # Load Example Local Plugins (for dev/test)
    # Ideally config.get("plugin_paths")
    registry.load_local_plugins("examples/skills")

    # Load User Plugins
    registry.load_local_plugins(os.path.expanduser("~/.jcapy/skills"))

    parser = argparse.ArgumentParser(description=f"# jcapy Core - The One-Army Orchestrator\n# Version: {VERSION}", add_help=True)
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # 4. Configure Parsers from Registry
    registry.configure_parsers(subparsers)

    try:
        # Handling for no args
        if len(sys.argv) == 1:
            # Check for standard config file
            from jcapy.config import CONFIG_PATH

            # If completely new user (no config exists)
            if not os.path.exists(CONFIG_PATH):
                # 1. First-time Setup Welcome
                try:
                    from jcapy.ui.animations import should_animate, typewriter_print
                    if should_animate():
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
                 # Standard Flow for returning users:
                 # The TUI JCapyApp now handles the cinematic startup internally.
                 pass

            from jcapy.commands.brain import ensure_operator_identity
            ensure_operator_identity()

            check_for_framework_updates()

            # Default Flow: Dashboard directly (User Request)
            from jcapy.commands.brain import migrate_persona_libraries
            migrate_persona_libraries()

            try:
                from jcapy.ui.app import JCapyApp
                app = JCapyApp()
                app.run()
            except ImportError as e:
                # Provide a much more helpful error message for missing TUI dependencies
                print(f"\n❌ Dashboard Error: {e}")
                if "textual" in str(e):
                    print("💡 Missing 'textual' library. Dashboard requires it.")
                    print("👉 Run: pip install textual")
                else:
                    print("💡 A required dependency for the UI is missing.")

                print("\n🔧 Environment Check:")
                print(f"   Python:  {sys.executable}")
                print("   Tip:     If you have a virtual environment, make sure it's activated.")
                print("            Try: source .venv/bin/activate && jcapy")
            except Exception as e:
                print(f"\n💥 Unexpected TUI Crash: {e}")
                import traceback
                traceback.print_exc()
            return

        # Handle custom version flag
        if "--version" in sys.argv or "-v" in sys.argv:
            print(f"jcapy v{VERSION}")
            return

        # Handle custom help flag - only for global help/updates check
        if len(sys.argv) == 2 and sys.argv[1] in ["-h", "--help"]:
            check_for_framework_updates()
            print_help()
            return

        try:
            args = parser.parse_args()
        except argparse.ArgumentError:
            print_help()
            return

        if hasattr(args, 'func'):
            result = args.func(args)

            # Legacy/Modern Bridge: Handle CommandResult
            # If a command returns a result object, we should render it for CLI users
            # Most legacy commands return None and print directly
            if result:
                try:
                    from jcapy.core.base import CommandResult, ResultStatus
                    if isinstance(result, CommandResult):
                        # Print logs first (so message is at bottom)
                        for log in result.logs:
                             if log.strip(): print(log.strip())

                        # Print Message (if significant)
                        if result.message and not result.silent:
                            color = GREEN if result.status == ResultStatus.SUCCESS else RED
                            if result.status == ResultStatus.WARNING: color = YELLOW
                            print(f"{color}{result.message}{RESET}")

                        if result.status == ResultStatus.FAILURE:
                            sys.exit(1)
                except ImportError:
                    pass # Should not happen if core is loaded
            return

        # Typo correction or help
        if getattr(args, 'command', None):
            known_commands = list(registry.get_commands().keys())
            corrected = prompt_typo_correction(args.command, known_commands)
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
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
