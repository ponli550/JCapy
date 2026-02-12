import curses
from jcapy.ui.ux.hints import JCAPY_COMMANDS

class CommandBar:
    """Handles the persistent modal command bar in the TUI footer."""

    def __init__(self):
        self.buffer = ""
        self.cursor_pos = 0
        self.history = []
        self.commands = sorted(JCAPY_COMMANDS)

    def clear(self):
        self.buffer = ""
        self.cursor_pos = 0

    def handle_key(self, key, mode):
        """Processes key input for COMMAND and INSERT modes."""
        if key in [10, 13]: # Enter
            cmd = self.buffer.strip()
            self.history.append(cmd)
            # self.clear() # Let the caller decide when to clear
            return "EXECUTE"

        elif key in [8, 127, curses.KEY_BACKSPACE]:
            if len(self.buffer) > 0:
                self.buffer = self.buffer[:-1]
                self.cursor_pos = max(0, self.cursor_pos - 1)

        elif key == 9: # Tab (Completion)
            return self.complete()

        elif 32 <= key <= 126:
            self.buffer += chr(key)
            self.cursor_pos += 1

        return "CONTINUE"

    def complete(self):
        """Simple prefix-based tab completion."""
        if not self.buffer:
            return "CONTINUE"

        matches = [c for c in self.commands if c.startswith(self.buffer)]
        if len(matches) == 1:
            self.buffer = matches[0]
            self.cursor_pos = len(self.buffer)
        elif len(matches) > 1:
            # Common prefix logic could go here, for now just cycle or leave
            pass
        return "CONTINUE"

    def render(self, stdscr, mode, h, w, COLOR_HIGHLIGHT, COLOR_SUBTITLE):
        """Renders the command bar at the bottom of the screen."""
        mode_str = f"-- {mode} --"
        prefix = ":" if mode == "COMMAND" else "/" if mode == "INSERT" else ""

        # Clear the line first
        stdscr.move(h - 1, 0)
        stdscr.clrtoeol()

        try:
            # Draw Mode
            stdscr.attron(curses.color_pair(COLOR_HIGHLIGHT))
            stdscr.addstr(h - 1, 2, mode_str)
            stdscr.attroff(curses.color_pair(COLOR_HIGHLIGHT))

            # Draw Prefix + Buffer
            input_text = f" {prefix}{self.buffer}"
            stdscr.attron(curses.color_pair(COLOR_SUBTITLE))
            stdscr.addstr(h - 1, 2 + len(mode_str) + 1, input_text)
            stdscr.attroff(curses.color_pair(COLOR_SUBTITLE))

            # Show cursor if in active mode
            if mode in ["COMMAND", "INSERT"]:
                curses.curs_set(1)
                stdscr.move(h - 1, 2 + len(mode_str) + 1 + len(prefix) + len(self.buffer))
            else:
                curses.curs_set(0)

        except curses.error:
            pass
