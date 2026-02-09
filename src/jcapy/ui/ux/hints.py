"""
Discoverability Module - Typo correction, contextual hints, tutorials.
"""
import os
import json
import difflib
from pathlib import Path

# ANSI colors
CYAN = '\033[1;36m'
YELLOW = '\033[1;33m'
RESET = '\033[0m'
GREY = '\033[0;90m'
BOLD = '\033[1m'

TUTORIAL_FILE = os.path.expanduser("~/.jcapy/tutorial.json")
HINTS_ENABLED_KEY = "hints"

# Available commands for typo matching
JCAPY_COMMANDS = [
    "list", "ls", "harvest", "new", "search", "open", "delete", "rm",
    "code", "manage", "tui", "persona", "p", "init", "deploy", "merge",
    "apply", "doctor", "chk", "check", "sync", "push", "brainstorm", "bs",
    "help", "undo", "tutorial", "config"
]


def suggest_command(typo: str, commands: list = None, threshold: int = 2) -> list:
    """
    Suggest closest matching commands for a typo.
    Uses difflib with cutoff based on Levenshtein-like distance.

    Returns list of up to 3 suggestions.
    """
    if commands is None:
        commands = JCAPY_COMMANDS

    # Get close matches (cutoff 0.6 is roughly edit distance of 2 for short strings)
    matches = difflib.get_close_matches(typo.lower(), commands, n=3, cutoff=0.6)
    return matches


def prompt_typo_correction(typo: str, commands: list = None) -> str | None:
    """
    Prompt user if they meant a different command.
    Returns the corrected command or None.
    """
    suggestions = suggest_command(typo, commands)

    if not suggestions:
        return None

    if len(suggestions) == 1:
        response = input(f"{YELLOW}❓ Did you mean '{suggestions[0]}'? [Y/n]: {RESET}").strip().lower()
        if response in ('', 'y', 'yes'):
            return suggestions[0]
    else:
        print(f"{YELLOW}❓ Did you mean one of these?{RESET}")
        for i, s in enumerate(suggestions, 1):
            print(f"  {i}. {s}")
        response = input(f"{GREY}Enter number or press Enter to cancel: {RESET}").strip()
        if response.isdigit() and 1 <= int(response) <= len(suggestions):
            return suggestions[int(response) - 1]

    return None


def show_hint(message: str, context: str = None):
    """
    Display a contextual hint message.
    Respects hints config setting.
    """
    from jcapy.config import load_config

    config = load_config()
    if not config.get(HINTS_ENABLED_KEY, True):
        return

    prefix = f"[{context}] " if context else ""
    print(f"\n{CYAN}💡 Tip:{RESET} {prefix}{message}\n")


class Tutorial:
    """Interactive onboarding tutorial for new users."""

    STEPS = [
        {
            "id": "welcome",
            "message": "Welcome to jcapy! Let's get you started.",
            "action": None
        },
        {
            "id": "harvest",
            "message": "First, let's create a skill. Run: jcapy harvest",
            "action": "harvest"
        },
        {
            "id": "list",
            "message": "Great! Now view your skills with: jcapy list",
            "action": "list"
        },
        {
            "id": "persona",
            "message": "Switch personas with: jcapy persona",
            "action": "persona"
        },
        {
            "id": "complete",
            "message": "🎉 You're all set! Run 'jcapy help' for more commands.",
            "action": None
        }
    ]

    def __init__(self):
        self._ensure_file()

    def _ensure_file(self):
        """Create tutorial state file if it doesn't exist."""
        os.makedirs(os.path.dirname(TUTORIAL_FILE), exist_ok=True)
        if not os.path.exists(TUTORIAL_FILE):
            self._save_state({"completed": [], "current_step": 0, "finished": False})

    def _load_state(self) -> dict:
        """Load tutorial state."""
        try:
            with open(TUTORIAL_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"completed": [], "current_step": 0, "finished": False}

    def _save_state(self, state: dict):
        """Save tutorial state."""
        with open(TUTORIAL_FILE, 'w') as f:
            json.dump(state, f, indent=2)

    def is_finished(self) -> bool:
        """Check if tutorial is complete."""
        return self._load_state().get("finished", False)

    def get_current_step(self) -> dict | None:
        """Get the current tutorial step."""
        state = self._load_state()
        if state.get("finished"):
            return None

        idx = state.get("current_step", 0)
        if idx < len(self.STEPS):
            return self.STEPS[idx]
        return None

    def advance(self) -> dict | None:
        """Advance to next step. Returns new step or None if finished."""
        state = self._load_state()
        idx = state.get("current_step", 0)

        if idx < len(self.STEPS) - 1:
            state["current_step"] = idx + 1
            state["completed"].append(self.STEPS[idx]["id"])
            self._save_state(state)
            return self.STEPS[idx + 1]
        else:
            state["finished"] = True
            self._save_state(state)
            return None

    def reset(self):
        """Reset tutorial progress."""
        self._save_state({"completed": [], "current_step": 0, "finished": False})

    def run_interactive(self):
        """Run the interactive tutorial."""
        print(f"\n{CYAN}{'='*50}{RESET}")
        print(f"{BOLD}🎓 jcapy Tutorial{RESET}")
        print(f"{CYAN}{'='*50}{RESET}\n")

        while True:
            step = self.get_current_step()
            if step is None:
                print(f"{CYAN}Tutorial complete! You're ready to use jcapy.{RESET}")
                break

            step_num = self._load_state().get("current_step", 0) + 1
            total = len(self.STEPS)

            print(f"[{step_num}/{total}] {step['message']}")

            if step.get("action"):
                response = input(f"{GREY}Press Enter after running the command (or 'skip' to skip): {RESET}").strip()
                if response.lower() == 'skip':
                    pass
            else:
                input(f"{GREY}Press Enter to continue...{RESET}")

            next_step = self.advance()
            if next_step:
                print(f"\n{CYAN}✓ Step complete!{RESET}\n")
            else:
                print()


# Singleton instance
_tutorial = None

def get_tutorial() -> Tutorial:
    """Get the singleton Tutorial instance."""
    global _tutorial
    if _tutorial is None:
        _tutorial = Tutorial()
    return _tutorial
