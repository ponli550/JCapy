import curses
import os
import shutil
import subprocess
import io
import stat
import sys
import time
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from jcapy.config import load_config, JCAPY_HOME, get_current_persona_name, get_active_library_path
from jcapy.utils.git_lib import get_git_status
from jcapy.ui.ux.command_bar import CommandBar

import threading
import queue

# ANSI Colors for terminal escape fallbacks
CYAN = '\033[1;36m'
GREEN = '\033[1;32m'
YELLOW = '\033[1;33m'
RESET = '\033[0m'
COLOR_TITLE = CYAN
COLOR_SUBTITLE = YELLOW

class ProcessManager:
    """Manages background subprocess execution with real-time output capturing."""
    def __init__(self):
        self.process = None
        self.output_queue = queue.Queue()
        self.is_running = False
        self.exit_code = None
        self.command = ""
        self.full_output = []

    def start(self, cmd_str):
        self.command = cmd_str
        self.is_running = True
        self.exit_code = None
        self.output_queue = queue.Queue()
        self.full_output = []

        def run_proc():
            exe = "jcapy" if shutil.which("jcapy") else sys.executable + " -m jcapy"
            try:
                # Use stdbuf or similar if possible, but Popen with bufsize=1 works for line-buffering
                self.process = subprocess.Popen(
                    f"{exe} {cmd_str}",
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )

                if self.process.stdout:
                    for line in self.process.stdout:
                        self.output_queue.put(line)
                        self.full_output.append(line)

                self.process.wait()
                self.exit_code = self.process.returncode
            except Exception as e:
                err_msg = f"Error: {e}\n"
                self.output_queue.put(err_msg)
                self.full_output.append(err_msg)
            finally:
                self.is_running = False

        self.thread = threading.Thread(target=run_proc, daemon=True)
        self.thread.start()

    def kill(self):
        if self.process:
            try:
                # Kill the process group if possible to ensure children die
                import signal
                os.kill(self.process.pid, signal.SIGTERM)
            except:
                self.process.terminate()
            self.is_running = False

# Colors (initialized in run)
COLOR_DEFAULT = 1
COLOR_HIGHLIGHT = 2
COLOR_TITLE = 3
COLOR_SUBTITLE = 4

def is_locked(path):
    try:
        st = os.stat(path)
        return bool(st.st_flags & stat.UF_IMMUTABLE)
    except Exception: return False

def toggle_lock(path):
    locked = is_locked(path)
    flag = 'nouchg' if locked else 'uchg'
    try:
        subprocess.call(['chflags', flag, path])
        return not locked
    except Exception: return locked

def get_skills(library_path):
    skills = []
    if not os.path.exists(library_path): return skills
    for root, dirs, files in os.walk(library_path):
        for f in files:
            if f.endswith(".md") and f != "TEMPLATE_SKILL.md":
                abs_path = os.path.join(root, f)
                domain = os.path.basename(root)
                if root == library_path: domain = "root"
                skills.append({"name": f, "path": abs_path, "domain": domain, "locked": is_locked(abs_path)})
    skills.sort(key=lambda x: (x['domain'], x['name']))
    return skills

def draw_dashboard(stdscr, selected_idx, personas_data, recent_files):
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    title = f" Who is operating right now? (Current: {get_current_persona_name().upper()}) "
    try:
        stdscr.attron(curses.color_pair(COLOR_TITLE) | curses.A_BOLD)
        stdscr.addstr(1, (w - len(title)) // 2, title)
        stdscr.attroff(curses.color_pair(COLOR_TITLE) | curses.A_BOLD)
    except: pass

    y_start, col_width, margin = 4, 25, 2
    current_x = margin
    for idx, p in enumerate(personas_data):
        if current_x + col_width > w: break
        is_selected = (idx == selected_idx)
        attr = curses.color_pair(COLOR_HIGHLIGHT) if is_selected else curses.color_pair(COLOR_DEFAULT) | curses.A_BOLD
        try:
            stdscr.addstr(y_start, current_x, f"┌{'─'*(col_width-2)}┐", attr)
            stdscr.addstr(y_start+1, current_x, f"│ {p['name'].capitalize():<{col_width-4}} │", attr)
            stdscr.addstr(y_start+2, current_x, f"├{'─'*(col_width-2)}┤", attr)
            stdscr.addstr(y_start+5, current_x, f"└{'─'*(col_width-2)}┘", attr)
        except: pass
        current_x += col_width + margin
    stdscr.refresh()

LEADER_MAP = {
    'd': 'doctor',
    's': 'sync',
    'p': 'push',
    'h': 'harvest',
    'l': 'list',
    'm': 'manage',
    'i': 'init',
    'D': 'deploy',
    '?': 'help'
}

def draw_leader_menu(stdscr):
    """Draws the quick-action leader menu overlay."""
    h, w = stdscr.getmaxyx()
    box_h, box_w = 14, 40
    box_y, box_x = (h - box_h) // 2, (w - box_w) // 2

    try:
        win = curses.newwin(box_h, box_w, box_y, box_x)
        win.box()
        win.attron(curses.color_pair(COLOR_TITLE) | curses.A_BOLD)
        win.addstr(1, (box_w - 14) // 2, " POWER MAGIC ")
        win.attroff(curses.color_pair(COLOR_TITLE) | curses.A_BOLD)

        actions = [
            ("d", "Doctor (Health)"),
            ("s", "Sync (Pull)"),
            ("p", "Push (Publish)"),
            ("h", "Harvest (Skill)"),
            ("l", "List (Library)"),
            ("m", "Manage (Dash)"),
            ("i", "Init (Project)"),
            ("D", "Deploy (Prod)"),
            ("?", "Help (TUI)")
        ]

        for i, (key, desc) in enumerate(actions):
            win.addstr(3 + i, 4, f"[ {key} ] ", curses.color_pair(COLOR_HIGHLIGHT))
            win.addstr(3 + i, 10, desc, curses.color_pair(COLOR_DEFAULT))

        win.addstr(box_h - 2, (box_w - 18) // 2, "[Esc] to cancel", curses.color_pair(COLOR_SUBTITLE))
        win.refresh()
        return win
    except:
        return None

def draw_dual_pane(stdscr, selected_idx, skills, filter_text):
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    left_w = int(w * 0.3)
    right_w = w - left_w
    try:
        left_win = stdscr.subwin(h - 2, left_w, 1, 0)
        left_win.box()
        left_win.addstr(0, 2, " FRAMEWORKS ", curses.color_pair(COLOR_TITLE))
        max_items = h - 4
        start_idx = max(0, selected_idx - max_items + 1)
        for i in range(start_idx, min(len(skills), start_idx + max_items)):
            attr = curses.color_pair(COLOR_HIGHLIGHT) if i == selected_idx else curses.A_NORMAL
            display_name = ("🔒 " if skills[i].get('locked') else "  ") + skills[i]['name'][:left_w-6]
            left_win.addstr(i - start_idx + 1, 2, display_name, attr)
    except: pass

    try:
        right_win = stdscr.subwin(h - 2, right_w, 1, left_w)
        right_win.box()
        right_win.addstr(0, 2, " PREVIEW ", curses.color_pair(COLOR_TITLE))
        if skills and selected_idx < len(skills):
            with open(skills[selected_idx]['path'], 'r') as f:
                lines = f.readlines()
            for i, line in enumerate(lines[:h-4]):
                right_win.addstr(i + 1, 2, line.rstrip()[:right_w-4])
    except: pass

def strip_ansi(text):
    """Removes ANSI escape sequences from text."""
    import re
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def draw_process_hud(stdscr, active_proc):
    """Draws a real-time output panel for a running background process."""
    if not active_proc.is_running and active_proc.exit_code is None:
        return

    h, w = stdscr.getmaxyx()
    box_h, box_w = min(h - 4, 20), min(w - 10, 100)
    box_y, box_x = (h - box_h) // 2, (w - box_w) // 2

    f = io.StringIO()
    console = Console(file=f, force_terminal=True, color_system=None, width=box_w - 4)

    # Filter and format lines
    output_lines = [strip_ansi(line) for line in active_proc.full_output]
    content = "".join(output_lines[-(box_h-4):])

    status_text = "[bold yellow]Running...[/bold yellow]"
    if not active_proc.is_running:
        color = "green" if active_proc.exit_code == 0 else "red"
        status_text = f"[bold {color}]Finished ({active_proc.exit_code})[/bold {color}]"

    console.print(Panel(
        Text(content),
        title=f" [bold magenta]Master Key: {active_proc.command}[/bold magenta] ",
        subtitle=f" {status_text} | [dim]SPACE to control / any key to close[/dim] ",
        border_style="magenta"
    ))

    lines = strip_ansi(f.getvalue()).splitlines()
    try:
        win = curses.newwin(box_h, box_w, box_y, box_x)
        win.attron(curses.color_pair(COLOR_DEFAULT))
        for i, line in enumerate(lines[:box_h]):
             try: win.addstr(i, 0, line[:box_w-1])
             except: pass
        win.refresh()
        del win
    except: pass

def display_output_panel(stdscr, cmd_name, output):
    """Renders a floating Rich panel with command output, stripped of ANSI."""
    h, w = stdscr.getmaxyx()
    box_h, box_w = min(h - 4, 30), min(w - 10, 110)
    box_y, box_x = (h - box_h) // 2, (w - box_w) // 2
    f = io.StringIO()
    # Use color_system=None to prevent Rich from generating its own ANSI codes
    console = Console(file=f, force_terminal=True, color_system=None, width=box_w - 4)

    # Pre-strip the output so Rich doesn't try to parse existing ANSI as text
    clean_output = strip_ansi(output)

    console.print(Panel(Text(clean_output), title=f" [bold cyan]{cmd_name}[/bold cyan] ", border_style="magenta", subtitle=" [dim]Any key to dismiss[/dim] "))

    # Final strip of the rendered panel just in case
    lines = strip_ansi(f.getvalue()).splitlines()

    try:
        win = curses.newwin(box_h, box_w, box_y, box_x)
        win.attron(curses.color_pair(COLOR_DEFAULT))
        for i, line in enumerate(lines[:box_h]):
             try: win.addstr(i, 0, line[:box_w-1])
             except: pass
        win.refresh()
        stdscr.getch()
        del win
    except: pass

def action_menu(stdscr, skill, library_path):
    options = ["Edit (VS Code)", "Move", "Delete", "Cancel"]
    selected_idx = 0
    while True:
        h, w = stdscr.getmaxyx()
        try:
            win = curses.newwin(10, 50, (h-10)//2, (w-50)//2)
            win.box()
            win.addstr(1, 2, f"Action: {skill['name']}", curses.color_pair(COLOR_TITLE))
            for idx, opt in enumerate(options):
                attr = curses.color_pair(COLOR_HIGHLIGHT) if idx == selected_idx else curses.color_pair(COLOR_DEFAULT)
                win.addstr(3 + idx, 4, f"> {opt}" if idx == selected_idx else f"  {opt}", attr)
            win.refresh()
        except: pass
        key = stdscr.getch()
        if key == curses.KEY_UP and selected_idx > 0: selected_idx -= 1
        elif key == curses.KEY_DOWN and selected_idx < len(options) - 1: selected_idx += 1
        elif key in [10, 13]:
            if selected_idx == 0: subprocess.call(['code', skill['path']])
            elif selected_idx == 3: return
            return "refresh"

def edit_in_terminal(stdscr, path):
    editor = os.environ.get('EDITOR', 'nano')
    if not shutil.which(editor): editor = 'vim'
    curses.def_prog_mode()
    curses.endwin()
    try: subprocess.call([editor, path])
    except: pass
    curses.reset_prog_mode()
    stdscr.clear()
    stdscr.refresh()
    curses.doupdate()

def execute_interactive_command(stdscr, cmd):
    """Temporarily exits curses to run an interactive JCapy command."""
    exe = "jcapy" if shutil.which("jcapy") else sys.executable + " -m jcapy"
    curses.def_prog_mode()
    curses.endwin()

    print(f"\n{COLOR_TITLE}[jcapy] Executing interactive command: {cmd}{RESET}\n")
    try:
        # Connect directly to the terminal's stdin/stdout
        subprocess.call(f"{exe} {cmd}", shell=True)
        print(f"\n{COLOR_SUBTITLE}[jcapy] Execution finished. Press ENTER to return to TUI.{RESET}")
        input()
    except Exception as e:
        print(f"Error: {e}")
        input("Press ENTER to continue...")

    curses.reset_prog_mode()
    stdscr.clear()
    stdscr.refresh()
    curses.doupdate()

def main(stdscr, initial_library_path):
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(COLOR_DEFAULT, curses.COLOR_WHITE, -1)
    curses.init_pair(COLOR_HIGHLIGHT, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(COLOR_TITLE, curses.COLOR_CYAN, -1)
    curses.init_pair(COLOR_SUBTITLE, curses.COLOR_YELLOW, -1)
    curses.curs_set(0)

    # State
    current_library_path = initial_library_path
    view_mode, edit_mode = "dashboard", "NORMAL"
    cmd_bar = CommandBar()
    dash_idx, list_row, filter_text = 0, 0, ""
    active_proc = ProcessManager()
    stdscr.timeout(100)  # Polling interval (100ms)

    # Mock/Load Data
    config = load_config()
    personas = config.get("personas", {"programmer": {"path": "/Users/irfanali/.jcapy/library"}})

    def refresh_data():
        stats = []
        for name in personas: stats.append({"name": name, "count": 0})
        return stats, []

    p_stats, recent_files = refresh_data()

    while True:
        h, w = stdscr.getmaxyx()
        if view_mode == "dashboard":
            draw_dashboard(stdscr, dash_idx, p_stats, recent_files)
        else:
            skills = [s for s in get_skills(current_library_path) if filter_text.lower() in s['name'].lower()]
            draw_dual_pane(stdscr, list_row, skills, filter_text)

        # Draw Background Process HUD if active
        if active_proc.is_running or active_proc.exit_code is not None:
            draw_process_hud(stdscr, active_proc)

        cmd_bar.render(stdscr, edit_mode, h, w, COLOR_HIGHLIGHT, COLOR_SUBTITLE)
        key = stdscr.getch()

        # Handle "any key to dismiss" for finished process
        if not active_proc.is_running and active_proc.exit_code is not None and key != -1:
            active_proc.exit_code = None
            active_proc.full_output = []
            stdscr.clear()
            continue

        if key == -1: continue # No input, just loop for refresh

        if edit_mode == "NORMAL":
            # Master Key Interception: Space while process is running
            if key == ord(' ') and active_proc.is_running:
                # Master Control Menu
                box_h, box_w = 10, 50
                win = curses.newwin(box_h, box_w, (h-box_h)//2, (w-box_w)//2)
                win.box()
                win.addstr(1, 2, " MASTER KEY (Power Magic) ", curses.color_pair(COLOR_TITLE) | curses.A_BOLD)
                win.addstr(3, 4, "[k] Kill Process", curses.color_pair(COLOR_DEFAULT))
                win.addstr(4, 4, "[x] Background (Hide HUD)", curses.color_pair(COLOR_DEFAULT))
                win.addstr(5, 4, "[any] Continue watching", curses.color_pair(COLOR_DEFAULT))
                win.refresh()

                stdscr.timeout(-1) # Wait for master choice
                m_key = stdscr.getch()
                stdscr.timeout(100) # Restore polling

                if m_key == ord('k'): active_proc.kill()
                elif m_key == ord('x'): active_proc.exit_code = None # Hide panel
                del win
                stdscr.clear()
                continue

            if view_mode == "dashboard":
                if key in [curses.KEY_LEFT, ord('h')]: dash_idx = max(0, dash_idx - 1)
                elif key in [curses.KEY_RIGHT, ord('l')]: dash_idx = min(len(p_stats)-1, dash_idx + 1)
                elif key in [10, 13]:
                    current_library_path = personas[p_stats[dash_idx]['name']]['path']
                    view_mode = "list"
                elif key == ord(':'): edit_mode = "COMMAND"; cmd_bar.clear()
                elif key == ord('/'): edit_mode = "INSERT"; view_mode = "list"; cmd_bar.clear(); filter_text = ""
                elif key == ord(' '): # Power Magic Leader
                    win = draw_leader_menu(stdscr)
                    if win:
                        stdscr.timeout(-1) # Wait for subcommand
                        action_key = stdscr.getch()
                        stdscr.timeout(100) # Restore polling

                        if 0 <= action_key <= 1114111 and chr(action_key) in LEADER_MAP:
                            cmd = LEADER_MAP[chr(action_key)]
                            if cmd == "manage": view_mode = "dashboard"
                            elif cmd == "list": view_mode = "list"
                            elif cmd in ["harvest", "sync", "push", "init", "deploy"]:
                                execute_interactive_command(stdscr, cmd)
                            else:
                                active_proc.start(cmd)
                        del win
                elif key in [ord('q'), ord('Q')]: break
            else:
                if key in [curses.KEY_UP, ord('k')]: list_row = max(0, list_row - 1)
                elif key in [curses.KEY_DOWN, ord('j')]: list_row += 1
                elif key == ord(':'): edit_mode = "COMMAND"; cmd_bar.clear()
                elif key == ord('/'): edit_mode = "INSERT"; cmd_bar.clear(); filter_text = ""
                elif key == ord(' '): # Power Magic Leader
                    win = draw_leader_menu(stdscr)
                    if win:
                        stdscr.timeout(-1) # Wait for subcommand
                        action_key = stdscr.getch()
                        stdscr.timeout(100) # Restore polling

                        if 0 <= action_key <= 1114111 and chr(action_key) in LEADER_MAP:
                            cmd = LEADER_MAP[chr(action_key)]
                            if cmd == "manage": view_mode = "dashboard"
                            elif cmd == "list": view_mode = "list"
                            elif cmd in ["harvest", "sync", "push", "init", "deploy"]:
                                execute_interactive_command(stdscr, cmd)
                            else:
                                active_proc.start(cmd)
                        del win
                elif key == 27: view_mode = "dashboard"
                elif key in [10, 13] and skills: action_menu(stdscr, skills[list_row], current_library_path)

        elif edit_mode == "INSERT":
            if key == 27: edit_mode = "NORMAL"
            else:
                res = cmd_bar.handle_key(key, edit_mode)
                filter_text = cmd_bar.buffer
                if res == "EXECUTE": edit_mode = "NORMAL"

        elif edit_mode == "COMMAND":
            if key == 27: edit_mode = "NORMAL"; cmd_bar.clear()
            else:
                res = cmd_bar.handle_key(key, edit_mode)
                if res == "EXECUTE":
                    cmd = cmd_bar.buffer.strip()
                    if cmd:
                        try:
                            base_cmd = cmd.split()[0]
                            if base_cmd in ["harvest", "sync", "push", "init", "deploy"]:
                                execute_interactive_command(stdscr, cmd)
                            else:
                                active_proc.start(cmd)
                        except Exception as e:
                             display_output_panel(stdscr, "Error", str(e))
                    edit_mode = "NORMAL"; cmd_bar.clear()

def run(library_path):
    curses.wrapper(main, library_path)

if __name__ == "__main__":
    run("/Users/irfanali/.jcapy/library")
