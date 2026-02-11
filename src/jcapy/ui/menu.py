import sys
import os
import termios
import tty

# Colors
CYAN = '\033[1;36m'
GREEN = '\033[1;32m'
GREY = '\033[0;90m'
WHITE = '\033[1;37m'
RESET = '\033[0m'

def get_key():
    """Captures a single keypress, handling arrow key escape sequences."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
        if ch == '\x1b':
            ch += sys.stdin.read(2)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    if ch == '\x03': raise KeyboardInterrupt
    return ch

def interactive_menu(prompt, options, default_index=0, return_char=False):
    """Renders an interactive menu handling arrow keys. Supports shortcuts."""
    current_row = default_index

    # Inverse Video for selection
    REVERSE = '\033[7m'

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')

        # Add a breathing room line if requested (or just default)
        print()
        print(f"{CYAN}{prompt}{RESET}")
        print("-----------------------------------------------------")

        for idx, option in enumerate(options):
            if idx == current_row:
                # Reverse Video Selection
                print(f"{REVERSE} {option} {RESET}")
            else:
                print(f"  {option}")

        print("-----------------------------------------------------")

        # Footer / Status Bar
        if return_char:
            # Button-like badges
            btn_c = f"{REVERSE} [C] Code {RESET}"
            btn_s = f"{REVERSE} [S] Sync All {RESET}"
            btn_p = f"{REVERSE} [P] Push Brain {RESET}"

            # Solid background footer
            footer_text = f" Use UP/DOWN to navigate, ENTER to select.  {btn_c} {btn_s} {btn_p} "
            # Use a background color for the whole line if possible, or just the text
            # For now, let's keep it simple with the badges, or usage of REVERSE for the whole bar if desired.
            # User asked for: "Use a solid background color (e.g., dark blue or grey) for the footer row"
            # Let's use GREY background if possible, or just REVERSE for the whole line.
            # \033[100m is bright black background (greyish)
            BG_GREY = '\033[100m'
            print(f"{BG_GREY}{WHITE}{footer_text:<80}{RESET}")
        else:
            print(f"{GREY}Use UP/DOWN arrows to navigate, ENTER to select.{RESET}")

        key = get_key()

        if key == '\x1b[A': # UP
            if current_row > 0:
                current_row -= 1
        elif key == '\x1b[B': # DOWN
            if current_row < len(options) - 1:
                current_row += 1
        elif key == '\r': # ENTER
            return (current_row, None) if return_char else current_row

        # Handle Shortcuts
        if return_char and key.lower() in ['c', 'p', 's']:
            return (current_row, key.lower())
