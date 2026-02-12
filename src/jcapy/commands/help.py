import os
import sys
import tty
import termios
import select
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.text import Text
from jcapy.ui.theme import GLASS_STYLE, create_glass_panel

# Centralized metadata for all JCapy commands
HELP_REGISTRY = {
    "manage": {
        "title": "🖥️ Manage (TUI)",
        "aliases": ["tui"],
        "usage": "jcapy manage",
        "description": "The command center for JCapy. Launches an interactive dashboard where you can browse your library, switch personas, and monitor system health in real-time.",
        "tips": "This is the default command when running 'jcapy' without arguments."
    },
    "harvest": {
        "title": "🌾 Harvest",
        "aliases": ["new"],
        "usage": "jcapy harvest [--auto <path>] [<doc_path>]",
        "description": "Extracts reusable skills and frameworks into your library. You can harvest manually from a document or use the --auto flag for AI-powered 'Ghost Extraction'.",
        "tips": "Ghost-Extraction (--auto) requires an LLM API key configured via 'jcapy config set-key'."
    },
    "list": {
        "title": "📋 List",
        "aliases": ["ls"],
        "usage": "jcapy list",
        "description": "Displays a categorized view of all skills and frameworks currently stored in your active persona's library.",
        "tips": "Use the arrow keys and 'Enter' to open/edit a framework directly from the list."
    },
    "doctor": {
        "title": "🩺 Doctor",
        "aliases": ["chk", "check"],
        "usage": "jcapy doctor",
        "description": "Performs a deep diagnostic of your environment. Checks for required tools (Git, Node), local configurations (.jcapyrc), and AI provider API keys.",
        "tips": "If JCapy is acting strange, 'jcapy doctor' is your first line of defense."
    },
    "map": {
        "title": "🗺️ Map",
        "aliases": [],
        "usage": "jcapy map [<path>]",
        "description": "Analyzes a project directory using AI to identify high-value patterns suitable for harvesting into JCapy skills.",
        "tips": "Run this in the root of a successful project to find the components worth saving for your library."
    },
    "apply": {
        "title": "🚀 Apply",
        "aliases": [],
        "usage": "jcapy apply <framework_name>",
        "description": "Deploys a stored skill or framework into your current project. This is 'Executable Knowledge' in action.",
        "tips": "Fuzzy matching is supported, so 'jcapy apply auth' works even if the full name is 'firebase-auth-skill'."
    },
    "deploy": {
        "title": "🚢 Deploy",
        "aliases": [],
        "usage": "jcapy deploy",
        "description": "Executes a Grade-Aware deployment pipeline. The behavior (testing, security, linting) is dictated by the project grade set during 'jcapy init'.",
        "tips": "Grade A projects are strict, while Grade C projects skip most checks for rapid prototyping."
    },
    "search": {
        "title": "🔍 Search",
        "aliases": [],
        "usage": "jcapy search <query>",
        "description": "Fuzzy search through your entire knowledge base by command, title, or content.",
        "tips": "Great for finding that one obscure helper you harvested 3 months ago."
    },
    "open": {
        "title": "📂 Open",
        "aliases": [],
        "usage": "jcapy open <framework_name>",
        "description": "Opens a specific framework file in VS Code for manual editing.",
        "tips": "Ensures you always have easy access to the source of your skills."
    },
    "delete": {
        "title": "🗑️ Delete",
        "aliases": ["rm"],
        "usage": "jcapy delete <framework_name>",
        "description": "Permanently removes a framework from your library.",
        "tips": "Danger: This action cannot be undone unless you have a Git remote configured for your persona."
    },
    "persona": {
        "title": "👤 Persona",
        "aliases": ["p"],
        "usage": "jcapy persona [<name>]",
        "description": "Switches your active persona. Each persona has its own isolated library of skills and frameworks.",
        "tips": "Use this to separate your 'Frontend Specialist' skills from your 'DevOps Engineer' skills."
    },
    "sync": {
        "title": "🔄 Sync",
        "aliases": [],
        "usage": "jcapy sync",
        "description": "Pulls the latest updates for all your personas from their respective Git remotes.",
        "tips": "Essential for keeping your knowledge base synchronized across different machines."
    },
    "push": {
        "title": "⬆️ Push",
        "aliases": [],
        "usage": "jcapy push",
        "description": "Uploads all your local skill updates to their configured Git remotes.",
        "tips": "Run this after harvesting new value to ensure your backup and team are updated."
    },
    "brainstorm": {
        "title": "🧠 Brainstorm",
        "aliases": ["bs"],
        "usage": "jcapy brainstorm",
        "description": "Launches an AI wizard to help refine project designs, architect features, or optimize existing code.",
        "tips": "Adopt the 'One-Army' mindset: design for a team of ten, build as an individual."
    },
    "merge": {
        "title": "🧬 Merge (Blueprint)",
        "aliases": [],
        "usage": "jcapy merge",
        "description": "Creates a unified 'Blueprint' project structure, typically combining Frontend and Backend frameworks into a high-performance monorepo.",
        "tips": "The core of the JCapy rapid-start philosophy."
    },
    "init": {
        "title": "🏗️ Init",
        "aliases": [],
        "usage": "jcapy init",
        "description": "Scaffolds a new project using the 'One-Army' protocol, setting up documentation, grading, and folder structures.",
        "tips": "Always start a new project with 'jcapy init' for maximum orchestrator compatibility."
    },
    "fix": {
        "title": "🩹 Fix",
        "aliases": [],
        "usage": "jcapy fix <file> <instruction>",
        "description": "AI-powered tactical code fixing. Point it at a bug or a missing feature, and it will iterate until it's right.",
        "tips": "Provide clear, concise instructions for the best results."
    },
    "explore": {
        "title": "🛸 Explore",
        "aliases": [],
        "usage": "jcapy explore <topic>",
        "description": "Autonomous research agent. It will browse, search, and draft a new skill based on a topic you specify.",
        "tips": "Perfect for learning new libraries or patterns while you sleep."
    },
    "undo": {
        "title": "⏪ Undo",
        "aliases": [],
        "usage": "jcapy undo [--list]",
        "description": "Reverts the last destructive action (like an accidental delete or an AI fix gone wrong).",
        "tips": "Uses the JCapy Undo Stack for safe experimentation."
    },
    "tutorial": {
        "title": "🎓 Tutorial",
        "aliases": [],
        "usage": "jcapy tutorial [--reset]",
        "description": "Launches an interactive onboarding guide to help you master the JCapy orchestrator.",
        "tips": "A must-run for anyone new to the One-Army workflow."
    },
    "config": {
        "title": "⚙️ Config",
        "aliases": [],
        "usage": "jcapy config {list,set,get,set-key}",
        "description": "Manages your UX preferences (animations, hints) and securely stores your AI API keys.",
        "tips": "Use 'set-key' to enable all Agentic AI features."
    }
}

def get_key():
    """Captures a single keypress without blocking (non-buffered)."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        if select.select([sys.stdin], [], [], 0.1)[0]:
            ch = sys.stdin.read(1)
            if ch == '\x1b': # Escape sequence
                ch += sys.stdin.read(2)
            return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return None

def make_layout(selected_index):
    """Creates the 1:3 split layout for the Help Explorer."""
    layout = Layout()
    layout.split_row(
        Layout(name="sidebar", size=25),
        Layout(name="content")
    )

    # Sidebar: Command List
    commands = list(HELP_REGISTRY.keys())
    sidebar_content = Text()
    for i, cmd in enumerate(commands):
        style = "bold cyan reverse" if i == selected_index else "white"
        sidebar_content.append(f" {cmd.ljust(20)}\n", style=style)

    layout["sidebar"].update(create_glass_panel(sidebar_content, title="Commands"))

    # Content Area
    current_cmd = commands[selected_index]
    meta = HELP_REGISTRY[current_cmd]

    content_text = Text()
    content_text.append(f"\n {meta['title']}\n", style="bold magenta")
    if meta['aliases']:
        content_text.append(f" Aliases: {', '.join(meta['aliases'])}\n", style="dim yellow")

    content_text.append(f"\n Usage:\n", style="bold cyan")
    content_text.append(f"   {meta['usage']}\n", style="green")

    content_text.append(f"\n Description:\n", style="bold cyan")
    content_text.append(f"   {meta['description']}\n", style="white")

    content_text.append(f"\n Pro-Tips:\n", style="bold yellow")
    content_text.append(f"   {meta['tips']}\n", style="dim italic")

    layout["content"].update(create_glass_panel(content_text, title="Manual"))

    return layout

def run_interactive_help():
    """The main TUI Help loop."""
    console = Console()
    selected_index = 0
    commands = list(HELP_REGISTRY.keys())

    with Live(make_layout(selected_index), console=console, screen=True, auto_refresh=False) as live:
        while True:
            key = get_key()
            if key == 'q' or key == '\x1b': # q or Escape
                break
            elif key == '\x1b[A': # Up arrow
                selected_index = (selected_index - 1) % len(commands)
                live.update(make_layout(selected_index), refresh=True)
            elif key == '\x1b[B': # Down arrow
                selected_index = (selected_index + 1) % len(commands)
                live.update(make_layout(selected_index), refresh=True)

            # Brief sleep to prevent CPU spiking
            import time
            time.sleep(0.01)
