"""
Visual Feedback Module - Spinners, progress bars, and status banners.
"""
import functools
from contextlib import contextmanager

# Try importing Rich
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.panel import Panel
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

# Fallback ANSI colors
CYAN = '\033[1;36m'
GREEN = '\033[1;32m'
YELLOW = '\033[1;33m'
RED = '\033[1;31m'
RESET = '\033[0m'
GREY = '\033[0;90m'

_console = Console() if HAS_RICH else None
_quiet_mode = False


def set_quiet_mode(quiet: bool):
    """Enable/disable quiet mode (suppresses non-essential output)."""
    global _quiet_mode
    _quiet_mode = quiet


def with_spinner(message: str):
    """
    Decorator to wrap a function with a Rich spinner.
    Falls back to simple print if Rich is unavailable.

    Usage:
        @with_spinner("Syncing skills...")
        def sync_all():
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if _quiet_mode:
                return func(*args, **kwargs)

            if HAS_RICH:
                with _console.status(f"[bold cyan]{message}[/bold cyan]", spinner="dots"):
                    return func(*args, **kwargs)
            else:
                print(f"{GREY}[...] {message}{RESET}")
                result = func(*args, **kwargs)
                print(f"{GREEN}[✓] Done{RESET}")
                return result
        return wrapper
    return decorator


@contextmanager
def progress_bar(title: str, total: int):
    """
    Context manager for multi-step progress bar.

    Usage:
        with progress_bar("Deploying", total=3) as update:
            update("Running tests...")
            update("Building...")
            update("Pushing...")
    """
    if _quiet_mode:
        yield lambda msg: None
        return

    if HAS_RICH:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=_console
        ) as progress:
            task = progress.add_task(f"[cyan]{title}[/cyan]", total=total)

            def update(step_msg: str):
                progress.update(task, advance=1, description=f"[cyan]{step_msg}[/cyan]")

            yield update
    else:
        current = [0]
        print(f"{CYAN}{title}{RESET}")

        def update(step_msg: str):
            current[0] += 1
            print(f"  [{current[0]}/{total}] {step_msg}")

        yield update
        print(f"{GREEN}[✓] Complete{RESET}")


def show_success(message: str, hint: str = None):
    """Display a success banner."""
    if _quiet_mode:
        return

    if HAS_RICH:
        panel = Panel(
            f"[bold green]✓[/bold green] {message}" + (f"\n[dim]{hint}[/dim]" if hint else ""),
            border_style="green"
        )
        _console.print(panel)
    else:
        print(f"\n{GREEN}✓ {message}{RESET}")
        if hint:
            print(f"  {GREY}{hint}{RESET}")


def show_error(message: str, hint: str = None):
    """Display an error banner."""
    if HAS_RICH:
        panel = Panel(
            f"[bold red]✗[/bold red] {message}" + (f"\n[dim]{hint}[/dim]" if hint else ""),
            border_style="red"
        )
        _console.print(panel)
    else:
        print(f"\n{RED}✗ {message}{RESET}")
        if hint:
            print(f"  {GREY}{hint}{RESET}")


def show_warning(message: str, hint: str = None):
    """Display a warning banner."""
    if _quiet_mode:
        return

    if HAS_RICH:
        panel = Panel(
            f"[bold yellow]⚠[/bold yellow] {message}" + (f"\n[dim]{hint}[/dim]" if hint else ""),
            border_style="yellow"
        )
        _console.print(panel)
    else:
        print(f"\n{YELLOW}⚠ {message}{RESET}")
        if hint:
            print(f"  {GREY}{hint}{RESET}")
