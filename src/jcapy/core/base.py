# SPDX-License-Identifier: Apache-2.0
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional


# ---------------------------------------------------------------------------
# Command Result Contract
# ---------------------------------------------------------------------------

class ResultStatus(Enum):
    """Unified status for every command execution."""
    SUCCESS = "success"
    WARNING = "warning"
    FAILURE = "failure"
    PENDING = "pending"


@dataclass
class CommandResult:
    """
    The universal contract between command logic and its consumers (CLI / TUI).

    CLI reads `message` and `logs`.
    TUI reads those AND `data`, `ui_hint`, `duration`, etc.
    """
    status: ResultStatus = ResultStatus.SUCCESS
    message: str = ""                # Primary summary for the user
    data: Any = None                 # Structured data for widgets (Dict, List, …)
    ui_hint: Optional[str] = None    # e.g. "refresh_tree", "open_screen:harvest"
    logs: list[str] = field(default_factory=list)
    duration: float = 0.0            # Execution time in seconds
    error_code: Optional[str] = None # For specific error-handling logic
    silent: bool = False             # If True, TUI won't show a toast


# ---------------------------------------------------------------------------
# Command Base Class
# ---------------------------------------------------------------------------

class CommandBase(ABC):
    """
    Abstract Base Class for JCapy Commands.
    Enforces a consistent structure for all commands.
    """
    name: str = ""
    description: str = ""
    aliases: List[str] = []

    def setup_parser(self, parser):
        """Optional: Configure argparse parser."""
        pass

    @abstractmethod
    def execute(self, args):
        """Main execution logic."""
        pass

