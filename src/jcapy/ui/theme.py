from rich import box
from rich.panel import Panel
from rich.style import Style

GLASS_STYLE = {
    "box": box.ROUNDED,
    "border_style": "cyan",
    "header_style": "bold blue",
    "title_align": "left",
}

def create_glass_panel(renderable, title: str | None = None) -> Panel:
    """Creates a standardized Glass Box Panel."""
    return Panel(
        renderable,
        title=title,
        box=GLASS_STYLE["box"],
        border_style=GLASS_STYLE["border_style"],
        # header_style is used in table headers, but for Panel titles we rely on rich's default title styling unless overridden
        # We can bake the title style into the title string if needed, or just let it be.
        # For this implementation, we'll keep it simple to match the requested style dictionary usage.
    )
