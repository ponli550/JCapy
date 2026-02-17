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
        "background": "#0a0f14",
        "surface": "#161b22",
        "panel": "#1b2128",
        "border": "#30363d",
        "accent": "#2f81f7",
        "text": "#c9d1d9",
        "success": "#3fb950",
        "warning": "#d29922",
        "error": "#f85149",
        "boost": "#1f242c",
    },
    "dracula": {
        "background": "#21222c",
        "surface": "#282a36",
        "panel": "#44475a",
        "border": "#6272a4",
        "accent": "#bd93f9",
        "text": "#f8f8f2",
        "success": "#50fa7b",
        "warning": "#ffb86c",
        "error": "#ff5555",
        "boost": "#2d2f3b",
    },
    "matrix": {
        "background": "#000000",
        "surface": "#0a0a0a",
        "panel": "#001a00",
        "border": "#003b00",
        "accent": "#00ff41",
        "text": "#00dd00",
        "success": "#00ff7f",
        "warning": "#d4ff00",
        "error": "#ff0000",
        "boost": "#002200",
    },
    "midnight": {
        "background": "#010409",
        "surface": "#0d1117",
        "panel": "#161b22",
        "border": "#30363d",
        "accent": "#58a6ff",
        "text": "#f0f6fc",
        "success": "#238636",
        "warning": "#d29922",
        "error": "#f85149",
        "boost": "#121d2f",
    },
    "architect": {
        "background": "#011627", # Deep Night Blue
        "surface": "#0b2942",
        "panel": "#1d3b53",
        "border": "#00d1ff", # Tech Cyan
        "accent": "#7fdbca", # Teal-Cyan highlight
        "text": "#d6deeb",
        "success": "#addb67",
        "warning": "#ecc48d",
        "error": "#ef5350",
        "boost": "#012a4a",
    },
    "neon": {
        "background": "#0d0221", # Deep Purple Black
        "surface": "#240b36",
        "panel": "#2d0b5a",
        "border": "#c31432", # Neon Red
        "accent": "#00f2fe", # Cyan Glow
        "text": "#e0e0e0",
        "success": "#00ff00",
        "warning": "#faff00",
        "error": "#ff00ff",
        "boost": "#1a082d",
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

