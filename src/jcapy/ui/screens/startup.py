from textual.screen import Screen
from textual.widgets import Static
from textual.app import ComposeResult
from textual import on
import random
import time
from rich.text import Text
from rich.style import Style

# Matrix characters
MATRIX_CHARS = "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓ0123456789"

JCAPY_LOGO = [
    "     ██  ██████  █████  ██████  ██    ██",
    "     ██ ██      ██   ██ ██   ██  ██  ██ ",
    "     ██ ██      ███████ ██████    ████  ",
    "██   ██ ██      ██   ██ ██         ██   ",
    " █████   ██████ ██   ██ ██         ██   ",
]

TAGLINE = "One-Army Orchestrator • Build Like a Team of Ten"

class StartupScreen(Screen):
    """Cinematic startup screen with Matrix rain and logo crystallization."""

    def __init__(self, next_screen: str = "dashboard", **kwargs):
        super().__init__(**kwargs)
        self.next_screen = next_screen
        self.anim_interval = None

    def compose(self) -> ComposeResult:
        yield Static(id="animation-surface")

    def on_mount(self) -> None:
        self.start_time = time.time()
        self.phase = "RAIN"
        self.cols = 0
        self.rows = 0
        self.columns_data = []

        # Audio
        try:
            from jcapy.ui.animations import play_audio
            play_audio("matrix_start")
        except:
            pass

        # Start animation loop
        self.anim_interval = self.set_interval(0.05, self.update_animation)

    def update_animation(self) -> None:
        try:
            surface = self.query_one("#animation-surface", Static)
        except:
            if self.anim_interval:
                self.anim_interval.stop()
            return

        elapsed = time.time() - self.start_time

        # Update dimensions if needed
        self.cols = self.size.width
        self.rows = self.size.height

        if not self.columns_data or len(self.columns_data) != self.cols:
            self.columns_data = [random.randint(-self.rows, 0) for _ in range(self.cols)]

        if elapsed < 0.8:
            self.phase = "RAIN"
            surface.update(self.get_rain_frame())
        elif elapsed < 1.7:
            if self.phase == "RAIN":
                self.phase = "CRYSTALLIZE"
                try:
                    from jcapy.ui.animations import play_audio
                    play_audio("logo_crystallize")
                except:
                    pass

            progress = (elapsed - 0.8) / 0.9
            surface.update(self.get_crystallize_frame(progress))
        else:
            self.phase = "DONE"
            # Final check - push audio ready
            try:
                from jcapy.ui.animations import play_audio
                play_audio("ready")
            except:
                pass

            # Switch to final target
            if self.anim_interval:
                self.anim_interval.stop()
            self.app.switch_screen(self.next_screen)

    def get_rain_frame(self) -> Text:
        final_text = Text()
        grid = [[" " for _ in range(self.cols)] for _ in range(self.rows)]

        # We simulate multiple "drops" per column for higher density
        for col_idx, pos in enumerate(self.columns_data):
            if 0 <= pos < self.rows:
                grid[pos][col_idx] = random.choice(MATRIX_CHARS)
                # Small trail
                if pos > 0: grid[pos-1][col_idx] = random.choice(MATRIX_CHARS)
                if pos > 1: grid[pos-2][col_idx] = random.choice(MATRIX_CHARS)

            # Random speed variation
            self.columns_data[col_idx] += random.choice([1, 2])
            if self.columns_data[col_idx] > self.rows:
                self.columns_data[col_idx] = random.randint(-15, 0)

        for r in range(self.rows):
            row_text = Text()
            for c in range(self.cols):
                char = grid[r][c]
                if char != " ":
                    # Variegated green styles
                    style = random.choice(["bold green", "green", "dim green"])
                    row_text.append(char, style=style)
                else:
                    row_text.append(" ")
            final_text.append(row_text)
            final_text.append("\n")

        return final_text

    def get_crystallize_frame(self, progress: float) -> Text:
        final_text = Text()

        # Vertical centering
        logo_height = len(JCAPY_LOGO)
        top_padding = max(0, (self.rows - logo_height) // 2)

        for _ in range(top_padding):
            final_text.append(" " * self.cols + "\n")

        logo_width = len(JCAPY_LOGO[0])
        left_padding = max(0, (self.cols - logo_width) // 2)

        # Color based on progress: grey -> white -> cyan
        if progress < 0.4:
            color = "#444444"
        elif progress < 0.7:
            color = "#888888"
        elif progress < 0.9:
            color = "#ffffff"
        else:
            color = "bold cyan"

        # Glitch amplitude decreases as progress increases
        glitch_chance = max(0, 0.2 * (1.0 - progress))

        for line in JCAPY_LOGO:
            row = Text(" " * left_padding)
            for char in line:
                if random.random() < progress:
                    # Occasional "bad bit" glitch
                    if char != " " and random.random() < glitch_chance:
                        row.append(random.choice("░▒▓█"), style="white")
                    else:
                        row.append(char, style=color)
                else:
                    # Rain characters still falling through the reveal
                    if random.random() < 0.1:
                        row.append(random.choice(MATRIX_CHARS), style="dim green")
                    else:
                        row.append(random.choice("░▒▓ "), style="#222222")
            final_text.append(row)
            final_text.append("\n")

        if progress > 0.7:
            tag_progress = (progress - 0.7) / 0.3
            tag_padding = max(0, (self.cols - len(TAGLINE)) // 2)
            final_text.append("\n")
            # Fade in tagline
            tag_color = "#666666" if tag_progress < 0.5 else "dim white"
            final_text.append(" " * tag_padding + TAGLINE, style=tag_color)

        return final_text

    CSS = """
    StartupScreen {
        background: #000000;
        align: center middle;
    }
    #animation-surface {
        width: 100%;
        height: 100%;
        content-align: center middle;
    }
    """
