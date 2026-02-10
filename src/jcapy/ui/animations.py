"""
JCapy CLI Animations Module
Matrix rain → Logo crystallization → Cinematic intro
"""
import os
import sys
import time
import random
import shutil
import subprocess

# Sound events: matrix_start, logo_crystallize, ready
def play_audio(event):
    """Play a sound based on the UX audio_mode preference."""
    try:
        from jcapy.config import get_ux_preference
        mode = get_ux_preference("audio_mode")
        if mode == "muted" or not mode:
            return

        if mode == "beeps":
            # Simple terminal bell
            print('\a', end='', flush=True)
            return

        if mode == "voice":
            voices = {
                "matrix_start": "Initiating J Capy.",
                # "logo_crystallize": "Crystallizing knowledge.",
                "ready": "Welcome back $USER."
            }
            text = voices.get(event, "")
            if text:
                # Use macOS 'say' command
                subprocess.Popen(['say', '-v', 'Samantha', text])
            return

        if mode == "custom":
            # Use macOS 'afplay' with system sounds as default custom
            sounds = {
                "matrix_start": "/System/Library/Sounds/Tink.aiff",
                "logo_crystallize": "/System/Library/Sounds/Glass.aiff",
                "ready": "/System/Library/Sounds/Hero.aiff"
            }
            sound_path = sounds.get(event)
            if sound_path and os.path.exists(sound_path):
                subprocess.Popen(['afplay', sound_path])
            return

    except Exception:
        # Silently fail if something goes wrong with audio
        pass

# ANSI Colors
CYAN = '\033[1;36m'
GREEN = '\033[1;32m'
GREY = '\033[0;90m'
WHITE = '\033[1;37m'
RESET = '\033[0m'

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


def should_animate():
    """Check if animations should run"""
    if os.environ.get("JCAPY_REDUCED_MOTION"):
        return False
    if not sys.stdout.isatty():
        return False
    return True


def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def get_terminal_size():
    """Get terminal dimensions"""
    try:
        cols, rows = shutil.get_terminal_size()
        return cols, rows
    except:
        return 80, 24


def matrix_rain(duration=1.2, density=0.5):
    """Display matrix-style falling characters"""
    if not should_animate():
        return

    cols, rows = get_terminal_size()
    # Limit for performance
    cols = min(cols, 80)
    rows = min(rows, 20)

    # Initialize columns with random starting positions
    columns = [random.randint(-rows, 0) for _ in range(cols)]

    start_time = time.time()
    frame_count = 0

    try:
        # Hide cursor
        print('\033[?25l', end='', flush=True)

        while time.time() - start_time < duration:
            clear_screen()

            # Build frame
            grid = [[' ' for _ in range(cols)] for _ in range(rows)]

            for col_idx, pos in enumerate(columns):
                if 0 <= pos < rows:
                    # Head of the rain (bright)
                    char = random.choice(MATRIX_CHARS)
                    grid[pos][col_idx] = f"{GREEN}{char}{RESET}"

                # Trail (dimmer)
                for trail in range(1, 4):
                    trail_pos = pos - trail
                    if 0 <= trail_pos < rows:
                        char = random.choice(MATRIX_CHARS)
                        grid[trail_pos][col_idx] = f"{GREY}{char}{RESET}"

                # Move column down
                columns[col_idx] += 2

                # Reset if off screen
                if columns[col_idx] > rows + 5:
                    if random.random() < density:
                        columns[col_idx] = random.randint(-5, 0)

            # Render frame
            for row in grid:
                print(''.join(row))

            time.sleep(0.05)
            frame_count += 1

    finally:
        # Show cursor
        print('\033[?25h', end='', flush=True)


def crystallize_logo(duration=0.8):
    """Transition from noise to JCAPY logo"""
    if not should_animate():
        print_logo_instant()
        return

    cols, _ = get_terminal_size()
    logo_width = len(JCAPY_LOGO[0])
    padding = max(0, (cols - logo_width) // 2)

    frames = 8
    frame_duration = duration / frames

    try:
        print('\033[?25l', end='', flush=True)  # Hide cursor

        for frame in range(frames + 1):
            clear_screen()
            print()  # Top margin

            reveal_ratio = frame / frames

            for line in JCAPY_LOGO:
                result = []
                for i, char in enumerate(line):
                    if random.random() < reveal_ratio:
                        result.append(char)
                    else:
                        result.append(random.choice("░▒▓█ "))

                # Color transition: grey → cyan
                if reveal_ratio < 0.5:
                    color = GREY
                elif reveal_ratio < 0.8:
                    color = WHITE
                else:
                    color = CYAN

                print(' ' * padding + color + ''.join(result) + RESET)

            time.sleep(frame_duration)

        # Final clean logo
        clear_screen()
        print()
        for line in JCAPY_LOGO:
            print(' ' * padding + CYAN + line + RESET)

    finally:
        print('\033[?25h', end='', flush=True)  # Show cursor


def print_logo_instant():
    """Print logo without animation (fallback)"""
    cols, _ = get_terminal_size()
    logo_width = len(JCAPY_LOGO[0])
    padding = max(0, (cols - logo_width) // 2)

    print()
    for line in JCAPY_LOGO:
        print(' ' * padding + CYAN + line + RESET)


def typewriter(text, delay=0.03):
    """Print text one character at a time"""
    if not should_animate():
        print(text)
        return

    cols, _ = get_terminal_size()
    padding = max(0, (cols - len(text)) // 2)

    print(' ' * padding, end='', flush=True)
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()


def staggered_rows(rows, delay=0.08):
    """Print rows with staggered timing"""
    if not should_animate():
        for row in rows:
            print(row)
        return

    for row in rows:
        print(row)
        time.sleep(delay)


def cinematic_intro():
    """Full cinematic intro sequence: Matrix → Logo → Tagline"""
    if not should_animate():
        print_logo_instant()
        print()
        print(TAGLINE)
        return

    try:
        # Phase 1: Matrix rain
        play_audio("matrix_start")
        matrix_rain(duration=0.6)

        # Phase 2: Logo crystallization
        play_audio("logo_crystallize")
        crystallize_logo(duration=0.4)

        # Phase 3: Tagline
        time.sleep(0.2)
        typewriter(TAGLINE, delay=0.02)

        play_audio("ready")

        # Brief pause before menu
        time.sleep(0.3)

    except KeyboardInterrupt:
        clear_screen()
        print_logo_instant()


# For testing
if __name__ == "__main__":
    cinematic_intro()
    print("\n✅ Animation complete!")
