"""
Accessibility Module - Themes, screen reader support, reduced motion.
"""
import os
import sys

# Theme definitions with WCAG AA compliant contrast ratios
THEMES = {
    "default": {
        "primary": '\033[1;36m',      # Cyan
        "success": '\033[1;32m',      # Green
        "warning": '\033[1;33m',      # Yellow
        "error": '\033[1;31m',        # Red
        "muted": '\033[0;90m',        # Grey
        "text": '\033[0m',            # Default
        "highlight": '\033[1;35m',    # Magenta
        "reset": '\033[0m'
    },
    "high-contrast": {
        "primary": '\033[1;97m',      # Bright white
        "success": '\033[1;92m',      # Bright green
        "warning": '\033[1;93m',      # Bright yellow
        "error": '\033[1;91m',        # Bright red
        "muted": '\033[0;37m',        # Light grey
        "text": '\033[1;97m',         # Bright white
        "highlight": '\033[1;95m',    # Bright magenta
        "reset": '\033[0m'
    },
    "monochrome": {
        "primary": '\033[1m',         # Bold
        "success": '\033[1m',         # Bold
        "warning": '\033[4m',         # Underline
        "error": '\033[7m',           # Reverse
        "muted": '\033[2m',           # Dim
        "text": '\033[0m',            # Default
        "highlight": '\033[1;4m',     # Bold + Underline
        "reset": '\033[0m'
    }
}

_current_theme = "default"


def set_theme(theme_name: str) -> bool:
    """Set the current color theme."""
    global _current_theme
    if theme_name in THEMES:
        _current_theme = theme_name
        return True
    return False


def get_theme() -> str:
    """Get the current theme name."""
    return _current_theme


def get_color(name: str) -> str:
    """Get ANSI color code for the current theme."""
    theme = THEMES.get(_current_theme, THEMES["default"])
    return theme.get(name, theme["text"])


def load_theme_from_config():
    """Load theme preference from config file."""
    global _current_theme
    try:
        from jcapy.config import load_config
        config = load_config()
        theme = config.get("theme", "default")
        if theme in THEMES:
            _current_theme = theme
    except ImportError:
        pass


def is_reduced_motion() -> bool:
    """
    Check if reduced motion is preferred.
    Checks config setting and system environment.
    """
    # Check config
    try:
        from jcapy.config import load_config
        config = load_config()
        if config.get("reduced_motion", False):
            return True
    except ImportError:
        pass

    # Check macOS system preference via environment
    # JCAPY_REDUCED_MOTION can be set by users
    if os.environ.get("JCAPY_REDUCED_MOTION", "").lower() in ("1", "true", "yes"):
        return True

    # Check NO_COLOR environment variable (common accessibility standard)
    if os.environ.get("NO_COLOR"):
        return True

    return False


def announce(message: str, urgent: bool = False):
    """
    Announce a message for screen readers.

    Uses ANSI OSC sequences for terminal accessibility.
    Falls back to stderr print for urgent messages.
    """
    # Check if in accessible mode
    if not _is_accessible_mode():
        return

    if urgent:
        # Write to stderr for immediate attention
        print(f"[ANNOUNCE] {message}", file=sys.stderr)

    # OSC 777 is used by some terminals for notifications
    # This is a best-effort approach for terminal accessibility
    try:
        if sys.stdout.isatty():
            # OSC 52 / 777 escape sequences for terminal notifications
            # Note: Support varies by terminal emulator
            sys.stdout.write(f"\033]777;notify;jcapy;{message}\033\\")
            sys.stdout.flush()
    except Exception:
        pass


def _is_accessible_mode() -> bool:
    """Check if accessible mode is enabled."""
    # VoiceOver on macOS sets these
    if os.environ.get("VOICEOVER_RUNNING"):
        return True

    # Explicit setting
    if os.environ.get("JCAPY_ACCESSIBLE", "").lower() in ("1", "true", "yes"):
        return True

    # Check config
    try:
        from jcapy.config import load_config
        config = load_config()
        return config.get("accessible", False)
    except ImportError:
        return False


def get_spinner_style() -> str:
    """Get appropriate spinner style based on reduced motion setting."""
    if is_reduced_motion():
        return "static"  # Use [...] instead of animated spinner
    return "dots"


def format_for_screen_reader(text: str) -> str:
    """
    Format text to be more screen-reader friendly.
    Removes emojis and decorative characters.
    """
    import re
    # Remove emojis and special characters that might not read well
    # Keep alphanumeric, basic punctuation, and spaces
    cleaned = re.sub(r'[^\w\s\-.,!?:;()\[\]\'\"]+', '', text)
    return cleaned.strip()


# Initialize theme from config on module load
load_theme_from_config()
