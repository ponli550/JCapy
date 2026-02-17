import curses
import time
import random
import sys
from jcapy.ui.animations import MATRIX_CHARS, JCAPY_LOGO, TAGLINE, play_audio

class Animation:
    """Base class/Utils for TUI animations."""
    @staticmethod
    def typewriter(window, y, x, text, delay=0.02, color=None):
        """Types text character by character."""
        h, w = window.getmaxyx()
        for i, char in enumerate(text):
            if x + i >= w - 1: break
            try:
                if color:
                    window.addstr(y, x + i, char, color)
                else:
                    window.addstr(y, x + i, char)
                window.refresh()
                time.sleep(delay)
            except: pass

    @staticmethod
    def fade_in_text(window, y, x, text, delay=0.05):
        """Simulates a fade-in (requires color capability, usually just delays drawing)."""
        # True fade-in in terminal is hard without palette manipulation.
        # We simulate visual build-up.
        window.addstr(y, x, text, curses.A_DIM)
        window.refresh()
        time.sleep(delay)
        window.addstr(y, x, text, curses.A_NORMAL)
        window.refresh()

class StartupSequence:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.h, self.w = stdscr.getmaxyx()
        # Initialize colors if not already
        if curses.has_colors():
            try:
                curses.start_color()
                curses.use_default_colors()
                curses.init_pair(10, curses.COLOR_CYAN, -1)   # Logo
                curses.init_pair(11, curses.COLOR_GREEN, -1)  # Success
                curses.init_pair(12, curses.COLOR_YELLOW, -1) # Warning/Loading
                curses.init_pair(13, curses.COLOR_WHITE, -1)  # White text
                # Grey is tricky in standard curses, usually just DIM
            except: pass

    def play(self):
        """Executes the full cinematic startup sequence."""
        self.stdscr.clear()
        curses.curs_set(0)

        # 1. Matrix Rain Effect
        play_audio("matrix_start")
        self._matrix_rain(duration=1.2)

        # 2. Logo Crystallization (The Reveal)
        play_audio("logo_crystallize")
        self.stdscr.clear()
        self._crystallize_logo(duration=0.8)

        # 3. Tagline
        play_audio("ready")
        self._draw_tagline()

        # 4. System Checks (Brief)
        self._run_system_checks()

        # 5. Fade out
        time.sleep(0.4)
        self.stdscr.clear()
        self.stdscr.refresh()

    def _matrix_rain(self, duration):
        """Matrix rain using shared constants."""
        end_time = time.time() + duration
        columns = [random.randint(-self.h, 0) for _ in range(self.w)]

        while time.time() < end_time:
            self.stdscr.erase() # Clear is expensive, erase is better? Or manual
            # For performance in Curses, full redraw every frame is heavy.
            # We'll just draw columns.

            for x, y in enumerate(columns):
                if 0 <= y < self.h:
                     try:
                        char = random.choice(MATRIX_CHARS)
                        self.stdscr.addstr(y, x, char, curses.color_pair(11) | curses.A_BOLD)
                        # Trail
                        if y - 1 >= 0:
                            self.stdscr.addstr(y - 1, x, random.choice(MATRIX_CHARS), curses.color_pair(11) | curses.A_DIM)
                        if y - 2 >= 0:
                            self.stdscr.addstr(y - 2, x, " ", curses.color_pair(11)) # Clear tail
                     except: pass

                columns[x] += 1
                if columns[x] > self.h + 2:
                    if random.random() > 0.95: columns[x] = 0

            self.stdscr.refresh()
            time.sleep(0.05)
            # Exit on key press
            self.stdscr.timeout(0)
            if self.stdscr.getch() != -1: break
            self.stdscr.timeout(-1)

    def _crystallize_logo(self, duration=0.8):
        """Curses adaptation of crystallization effect."""
        frames = 8
        frame_delay = duration / frames

        start_y = max(1, (self.h // 2) - len(JCAPY_LOGO) - 2)
        center_x = self.w // 2

        for frame in range(frames + 1):
            reveal_ratio = frame / frames

            for i, line in enumerate(JCAPY_LOGO):
                start_x = center_x - (len(line) // 2)
                display_line = ""
                attr = curses.A_NORMAL

                if reveal_ratio < 0.5:
                    attr = curses.A_DIM
                elif reveal_ratio > 0.8:
                    attr = curses.color_pair(10) | curses.A_BOLD # Cyan

                for char in line:
                    if char == " ":
                        display_line += " "
                        continue

                    if random.random() < reveal_ratio:
                        display_line += char
                    else:
                        display_line += random.choice("░▒▓█")

                try:
                    self.stdscr.addstr(start_y + i, start_x, display_line, attr)
                except: pass

            self.stdscr.refresh()
            time.sleep(frame_delay)

    def _draw_tagline(self):
        """Types out the tagline."""
        start_y = (self.h // 2) + 2
        center_x = self.w // 2
        start_x = center_x - (len(TAGLINE) // 2)

        Animation.typewriter(self.stdscr, start_y, start_x, TAGLINE, delay=0.03, color=curses.color_pair(13) | curses.A_BOLD)
        time.sleep(0.5)

    def _run_system_checks(self):
        """Simulates loading bars and checks."""
        # Simplified checks since we have a rich intro now
        checks = [
            ("Initializing Neural Core...", 0.1),
            ("Connecting to Brain...", 0.1),
        ]

        start_y = (self.h // 2) + 4
        center_x = self.w // 2

        for i, (msg, delay) in enumerate(checks):
             # Just flash them quickly
             start_x = center_x - (len(msg) // 2)
             try:
                 self.stdscr.addstr(start_y, 0, " " * (self.w - 1)) # Clear line
                 self.stdscr.addstr(start_y, start_x, msg, curses.color_pair(12))
                 self.stdscr.refresh()
                 time.sleep(delay)
             except: pass

class Spinner:
    """Simple frame-based spinner for TUI."""
    FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    def __init__(self):
        self.idx = 0
        self.last_update = time.time()
        self.interval = 0.1

    def next(self):
        """Returns current frame automatically advanced by time."""
        if time.time() - self.last_update > self.interval:
            self.idx = (self.idx + 1) % len(self.FRAMES)
            self.last_update = time.time()
        return self.FRAMES[self.idx]

class Throbber:
    """Returns a color attribute that pulses between normal and bright/dim."""
    def __init__(self, base_color_pair, interval=0.8):
        self.base = base_color_pair
        self.interval = interval
        self.start_time = time.time()

    def current_attr(self):
        """Returns blinking attribute based on sine wave or simple toggle."""
        # Simple toggle for Curses (Full RGB fading needs 256 colors remapping)
        elapsed = time.time() - self.start_time
        phase = (elapsed % self.interval) / self.interval

        if phase < 0.5:
             return self.base | curses.A_BOLD
        else:
             return self.base | curses.A_DIM
