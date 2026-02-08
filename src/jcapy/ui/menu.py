import sys
import os
import termios
import tty

# Colors
CYAN = '\033[1;36m'
GREEN = '\033[1;32m'
GREY = '\033[0;90m'
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

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"\n{CYAN}{prompt}{RESET}")
        print("-----------------------------------------------------")

        for idx, option in enumerate(options):
            if idx == current_row:
                print(f"{GREEN}> {option}{RESET}")
            else:
                print(f"  {option}")

        print("-----------------------------------------------------")
        print(f"{GREY}Use UP/DOWN arrows to navigate, ENTER to select.{RESET}")
        if return_char:
             print(f"{GREY}[C] Code | [S] Sync All | [P] Push Brain{RESET}")

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
