# SPDX-License-Identifier: Apache-2.0
import os
import shutil
import subprocess
from rich.console import Console
from jcapy.core.base import CommandBase, ResultStatus, CommandResult


console = Console()

class EditCommand(CommandBase):
    name = "edit"
    description = "Edit a file in the terminal editor (suspend TUI)"
    aliases = ["e", "vi", "nano"]
    is_interactive = True

    def setup_parser(self, parser):
        parser.add_argument("filename", nargs="?", help="File to edit")

    def execute(self, args):
        filename = getattr(args, 'filename', None)

        # Prepare file
        if not filename:
             filename = "scratch.md"

        filepath = os.path.abspath(os.path.expanduser(filename))

        # 1. Try Neovim RPC first (Smart Edit)
        nvim_socket = os.environ.get("NVIM_LISTEN_ADDRESS") or os.environ.get("NVIM")
        if nvim_socket:
            try:
                import pynvim
                # Connect to the parent Neovim instance
                nvim = pynvim.attach('socket', path=nvim_socket)
                # Use 'drop' to open the file; it handles switching buffers or opening new ones nicely
                # Escape the path using Neovim's internal function to be safe
                escaped_path = nvim.call('fnameescape', filepath)
                nvim.command(f"drop {escaped_path}")

                return CommandResult(
                    status=ResultStatus.SUCCESS,
                    message=f"Opened '{filename}' in parent Neovim.",
                )
            except Exception as e:
                # If RPC fails (e.g., pynvim not installed or socket closed), strictly fall back
                pass

        # 2. Fallback: Standard TUI Suspension

        # Determine editor
        editor = os.environ.get("EDITOR", "nano")
        if not shutil.which(editor):
            # Fallback if preferred editor not found
            if shutil.which("nano"): editor = "nano"
            elif shutil.which("vim"): editor = "vim"
            elif shutil.which("vi"): editor = "vi"
            else:
                return CommandResult(
                    status=ResultStatus.FAILURE,
                    message="No suitable text editor found ($EDITOR, nano, vim, vi).",
                    error_code="NO_EDITOR"
                )

        # Suspend Curses TUI and run editor
        try:
            import curses
            # Replicating tui.py's edit_in_terminal logic:
            try:
                curses.def_prog_mode()
                curses.endwin()
                # Explicitly clear screen for the editor to have a clean slate - REMOVED
                # print("\033[H\033[J", end="", flush=True)
            except:
                pass

            subprocess.call([editor, filepath])

            try:
                # Clear again before returning to TUI to avoid artifacts - REMOVED
                # print("\033[H\033[J", end="", flush=True)
                curses.reset_prog_mode()
                pass
            except:
                pass

            return CommandResult(
                status=ResultStatus.SUCCESS,
                message=f"Edited '{filename}'.",
            )

        except Exception as e:
            return CommandResult(
                status=ResultStatus.FAILURE,
                message=f"Failed to launch editor: {e}",
                error_code="EDITOR_ERROR"
            )
