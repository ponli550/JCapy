from rich import box
from rich.panel import Panel
from rich.style import Style

GLASS_STYLE = {
    "box": box.ROUNDED,
    "border_style": "cyan",
    "header_style": "bold blue",
    "title_align": "left",
}

THEMES = {
    "default": {
        "background": "#1e1e1e",
        "surface": "#252526",
        "panel": "#252526",
        "border": "#3c3c3c",
        "accent": "#007acc",
        "text": "#d4d4d4",
        "success": "#4caf50",
        "warning": "#ff9800",
        "error": "#f44336",
    },
    "dracula": {
        "background": "#282a36",
        "surface": "#44475a",
        "panel": "#282a36",
        "border": "#6272a4",
        "accent": "#bd93f9", # Purple
        "text": "#f8f8f2",
        "success": "#50fa7b",
        "warning": "#ffb86c",
        "error": "#ff5555",
    },
    "matrix": {
        "background": "#000000",
        "surface": "#0d0d0d",
        "panel": "#001100",
        "border": "#003300",
        "accent": "#00ff00",
        "text": "#00cc00",
        "success": "#00ff00",
        "warning": "#ccff00",
        "error": "#ff0000",
    },
    "midnight": {
        "background": "#02040a",
        "surface": "#0d1117",
        "panel": "#161b22",
        "border": "#30363d",
        "accent": "#58a6ff", # GitHub Blue
        "text": "#c9d1d9",
        "success": "#238636",
        "warning": "#d29922",
        "error": "#f85149",
    },
    "architect": {
        "background": "#001a33", # Blueprint Dark Blue
        "surface": "#002b4d",
        "panel": "#003d66",
        "border": "#00ccff",
        "accent": "#00ffff", # Cyan highlight
        "text": "#e6f7ff",
        "success": "#33ff99",
        "warning": "#ffff66",
        "error": "#ff3366",
    }
}

def create_glass_panel(renderable, title: str | None = None) -> Panel:
    """Creates a standardized Glass Box Panel."""
    return Panel(
        renderable,
        title=title,
        box=GLASS_STYLE["box"],
        border_style=GLASS_STYLE["border_style"],
    )

