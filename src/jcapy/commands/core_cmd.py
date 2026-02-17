# SPDX-License-Identifier: Apache-2.0
import os
from rich.console import Console
from jcapy.ui.ux.safety import get_undo_stack
from jcapy.ui.ux.feedback import show_success, show_error
from jcapy.ui.ux.hints import get_tutorial
from jcapy.config import get_active_library_path

console = Console()

def setup_undo(parser):
    parser.add_argument("--list", action="store_true", dest="list_undo", help="List undo history")

def run_undo(args):
    undo_stack = get_undo_stack()
    if getattr(args, 'list_undo', False):
        items = undo_stack.list_items()
        if not items:
            console.print(f"[grey50]No undo history.[/grey50]")
        else:
            console.print(f"[bold cyan]Undo History:[/bold cyan]")
            for i, item in enumerate(items, 1):
                print(f"  {i}. {item.get('description', 'Unknown')} ({item.get('timestamp', '')[:16]})")
    else:
        restored = undo_stack.pop()
        if restored:
            show_success(f"Restored: {restored.get('description', 'item')}")
        else:
            show_error("Nothing to undo", hint="Run 'jcapy undo --list' to see history")

def setup_tutorial(parser):
    parser.add_argument("--reset", action="store_true", help="Reset tutorial progress")

def run_tutorial(args):
    tutorial = get_tutorial()
    if getattr(args, 'reset', False):
        tutorial.reset()
        show_success("Tutorial progress reset")
    else:
        try:
            from jcapy.ui.animations import cinematic_intro, should_animate
            if should_animate():
                cinematic_intro()
        except ImportError: pass
        tutorial.run_interactive()

def run_suggest(args):
    console.print(f"[bold cyan]🤖 jcapy Recommendations:[/bold cyan]")
    lib_path = get_active_library_path()
    has_files = False
    for r, d, f in os.walk(lib_path):
        if any(k.endswith('.md') for k in f):
            has_files = True
            break

    if not has_files:
        console.print(f"  • [green]jcapy harvest[/green]: Start building your knowledge base.")
        console.print(f"  • [green]jcapy init[/green]: Create a new project structure.")
    else:
        try:
            from jcapy.utils.git_lib import get_git_status
            _, pending = get_git_status(lib_path)
            if pending > 0:
                console.print(f"  • [green]jcapy push[/green]: You have {pending} uncommitted changes.")
        except: pass
        console.print(f"  • [green]jcapy list[/green]: Browse your library.")
        console.print(f"  • [green]jcapy manage[/green]: Open the Dashboard.")
    console.print(f"  • [green]jcapy doctor[/green]: Verify system health.")

def run_tui(args=None, start_screen="dashboard"):
    # If args is a namespace (from argparse), check if it has start_screen
    if args and hasattr(args, 'screen'):
        start_screen = args.screen

    # We are switching to the Textual App (App.py) as the primary TUI
    # The old curses TUI is in jcapy.ui.tui.run

    # Try to launch Textual App first
    try:
        from jcapy.ui.app import JCapyApp
        app = JCapyApp(start_screen=start_screen)
        app.run()
    except Exception as e:
        # Fallback or error logging
        print(f"Error launching TUI: {e}")
        # import traceback
        # traceback.print_exc()
