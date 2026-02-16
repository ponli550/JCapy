# Design: Hybrid TUI/CLI "Polymorphic" Architecture

This document outlines the technical design for JCapy's transition from a standard CLI to a hybrid "Polymorphic" tool that provides a seamless experience between the system terminal and a rich interactive dashboard.

## Overview

The goal is to enable a single codebase to support:
1. **System Terminal Execution**: Stateless, pipe-friendly, and fast.
2. **Dashboard Integrated Execution**: Stateful, interactive, and visually rich.

We achieve this using a **Controller-View** pattern with an **Incremental Bridge** (Adapter) for legacy commands.

## 1. The Contract: `CommandResult`

Every command execution (modern or legacy) must eventually return a `CommandResult`.

```python
from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum

class ResultStatus(Enum):
    SUCCESS = "success"
    WARNING = "warning"
    FAILURE = "failure"
    PENDING = "pending"

@dataclass
class CommandResult:
    status: ResultStatus = ResultStatus.SUCCESS
    message: str = ""                # Primary summary for the user
    data: Any = None                 # Structured data for widgets (e.g., Dict, List)
    ui_hint: Optional[str] = None    # e.g., "refresh_tree", "focus_logs"
    logs: list[str] = field(default_factory=list)
    duration: float = 0.0            # Execution time in seconds
    error_code: Optional[str] = None # For specific error handling logic
    silent: bool = False             # If true, TUI won't show a toast for success
```

## 2. The Bridge: `CommandAdapter`

To support existing `print()`-based commands, the dispatcher wraps them in a capture-layer.

```python
def execute(self, command_name: str, args: list) -> CommandResult:
    command_fn = self.get_handler(command_name)
    start_time = time.time()
    stdout_capture = io.StringIO()

    try:
        # Force Rich to include ANSI codes even when redirected
        # This ensures the TUI renders colors correctly
        with contextlib.redirect_stdout(stdout_capture):
            result = command_fn(args)

            # MODERN: Command already returns structured data
            if isinstance(result, CommandResult):
                if not result.duration:
                    result.duration = time.time() - start_time
                return result

            # LEGACY: Wrap the printed output
            return CommandResult(
                status=ResultStatus.SUCCESS,
                message=f"Command '{command_name}' finished.",
                logs=[stdout_capture.getvalue()],
                duration=time.time() - start_time
            )
    except Exception as e:
        return CommandResult(
            status=ResultStatus.FAILURE,
            message=f"Error: {str(e)}",
            logs=[stdout_capture.getvalue()],
            duration=time.time() - start_time,
            error_code=type(e).__name__
        )
```

## 3. The View: `UIDispatcher`

The Textual-based Dashboard maintains a worker that routes results to widgets.

```python
@work(thread=True)
def run_command(self, command_str: str) -> None:
    # 1. Execute via Shared Engine
    result: CommandResult = registry.execute_string(command_str)

    # 2. Update Terminal Log (The "Both" strategy)
    self.call_from_thread(self.log_to_terminal, result)

    # 3. Handle UI Hints
    if result.ui_hint:
        self.call_from_thread(self.handle_ui_hint, result)

    # 4. Global Fallback: Toast Notifications
    if not result.silent and result.message:
        self.notify(result.message, severity=result.status.value)

def handle_ui_hint(self, result: CommandResult) -> None:
    hint = result.ui_hint
    if hint == "refresh_tree":
        self.query_one("#project-tree").reload_data(result.data)
    elif hint.startswith("open_screen:"):
        self.push_screen(hint.split(":")[1])
```

## Phase 1: Implementation Plan
1. **Core**: Implement `CommandResult` and `ResultStatus` in `src/jcapy/core/base.py`.
2. **Registry**: Refactor `CommandRegistry.execute` in `src/jcapy/core/plugins.py` to use the adapter pattern.
3. **TUI**: Update `JCapyApp.run_command` in `src/jcapy/ui/app.py` to handle the new result objects.
4. **Verification**: Wrap the `doctor` command as the first legacy pilot.
