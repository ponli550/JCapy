"""
JCapy Scroll Pager Module
User-controlled scrollable output for long content
"""
import os
import sys
import shutil


def get_terminal_size():
    """Get terminal dimensions"""
    try:
        cols, rows = shutil.get_terminal_size()
        return cols, rows
    except:
        return 80, 24


def paged_output(content, title=None):
    """
    Display content with scroll controls.
    For non-interactive terminals, prints all at once.

    Args:
        content: String or list of lines to display
        title: Optional header title
    """
    if not sys.stdout.isatty():
        # Non-interactive: print all
        if title:
            print(f"\n{title}")
            print("-" * 40)
        if isinstance(content, list):
            print('\n'.join(content))
        else:
            print(content)
        return

    # Convert to lines
    if isinstance(content, str):
        lines = content.split('\n')
    else:
        lines = list(content)

    cols, rows = get_terminal_size()
    page_size = rows - 4  # Leave room for header/footer

    if len(lines) <= page_size:
        # Content fits on one screen - no paging needed
        if title:
            print(f"\n{title}")
            print("-" * min(40, cols))
        for line in lines:
            print(line)
        return

    # Paged display
    current_line = 0
    total_lines = len(lines)

    try:
        import tty
        import termios

        old_settings = termios.tcgetattr(sys.stdin)
        tty.setraw(sys.stdin.fileno())

        while current_line < total_lines:
            # Clear and display page
            os.system('clear')

            if title:
                print(f"\r{title}")
                print("\r" + "-" * min(40, cols))

            # Show current page
            end_line = min(current_line + page_size, total_lines)
            for i in range(current_line, end_line):
                print(f"\r{lines[i]}")

            # Footer
            remaining = total_lines - end_line
            if remaining > 0:
                print(f"\r\n\033[90m--- {remaining} more lines | ↓/Space: more | q: quit ---\033[0m", end='', flush=True)
            else:
                print(f"\r\n\033[90m--- End | q: quit ---\033[0m", end='', flush=True)

            # Read key
            key = sys.stdin.read(1)

            if key in ('q', 'Q', '\x03'):  # q or Ctrl+C
                break
            elif key in (' ', '\n', 'j', '\x1b'):  # Space, Enter, j, or arrow
                if key == '\x1b':  # Arrow key prefix
                    sys.stdin.read(2)  # Consume [A/B/C/D
                current_line += page_size // 2  # Scroll half page
            elif key == 'k':  # Scroll up
                current_line = max(0, current_line - page_size // 2)

        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        os.system('clear')

    except (ImportError, termios.error):
        # Fallback: simple pagination with input()
        simple_pager(lines, title, page_size)


def simple_pager(lines, title=None, page_size=20):
    """Simple pager using input() - works everywhere"""
    current = 0
    total = len(lines)

    print()
    if title:
        print(title)
        print("-" * 40)

    while current < total:
        end = min(current + page_size, total)

        for i in range(current, end):
            print(lines[i])

        if end < total:
            remaining = total - end
            try:
                response = input(f"\033[90m--- {remaining} more | Enter: continue | q: quit ---\033[0m ")
                if response.lower() == 'q':
                    break
            except (EOFError, KeyboardInterrupt):
                break

        current = end


def scrollable_menu(options, title="Select an option", selected=0):
    """
    Display a scrollable menu that fits terminal height.
    Returns selected index.
    """
    cols, rows = get_terminal_size()
    visible_count = min(len(options), rows - 6)
    scroll_offset = 0

    if not sys.stdout.isatty():
        # Non-interactive fallback
        print(title)
        for i, opt in enumerate(options):
            print(f"  {i+1}. {opt}")
        try:
            choice = int(input("Select: ")) - 1
            return max(0, min(choice, len(options) - 1))
        except:
            return 0

    try:
        import tty
        import termios

        old_settings = termios.tcgetattr(sys.stdin)
        tty.setraw(sys.stdin.fileno())
        print('\033[?25l', end='')  # Hide cursor

        while True:
            os.system('clear')
            print(f"\r{title}")
            print("\r" + "-" * min(40, cols))

            # Ensure selected is visible
            if selected < scroll_offset:
                scroll_offset = selected
            elif selected >= scroll_offset + visible_count:
                scroll_offset = selected - visible_count + 1

            # Display visible options
            for i in range(scroll_offset, min(scroll_offset + visible_count, len(options))):
                if i == selected:
                    print(f"\r\033[1;36m> {options[i]}\033[0m")
                else:
                    print(f"\r  {options[i]}")

            # Scroll indicators
            if scroll_offset > 0:
                print("\r\033[90m  ↑ more above\033[0m")
            if scroll_offset + visible_count < len(options):
                print("\r\033[90m  ↓ more below\033[0m")

            print(f"\r\n\033[90mUse ↑/↓ to navigate, Enter to select\033[0m", end='', flush=True)

            # Read input
            key = sys.stdin.read(1)

            if key == '\x1b':  # Arrow key
                sys.stdin.read(1)  # [
                arrow = sys.stdin.read(1)
                if arrow == 'A':  # Up
                    selected = max(0, selected - 1)
                elif arrow == 'B':  # Down
                    selected = min(len(options) - 1, selected + 1)
            elif key in ('\r', '\n'):  # Enter
                break
            elif key in ('q', '\x03'):  # q or Ctrl+C
                selected = -1
                break

        print('\033[?25h', end='')  # Show cursor
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        os.system('clear')
        return selected

    except (ImportError, termios.error):
        # Fallback
        print('\033[?25h', end='')
        print(title)
        for i, opt in enumerate(options):
            print(f"  {i+1}. {opt}")
        try:
            choice = int(input("Select: ")) - 1
            return max(0, min(choice, len(options) - 1))
        except:
            return 0


# For testing
if __name__ == "__main__":
    # Test paged output
    test_content = [f"Line {i}: This is test content for the pager" for i in range(50)]
    paged_output(test_content, title="Test Pager")

    # Test scrollable menu
    options = [f"Option {i}" for i in range(20)]
    selected = scrollable_menu(options, "Test Menu")
    print(f"Selected: {selected}")
