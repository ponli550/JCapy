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
from jcapy.utils.updates import VERSION
from jcapy.ui.ux.command_bar import CommandBar

import threading
import queue
import shutil
import re
import itertools
from collections import deque
from .intelligence import AutonomousObserver

JCAPY_LOGO = [
    r"      _  _____               ",
    r"     | |/ ____|              ",
    r"     | | |     __ _ _ __  _   _ ",
    r" _   | | |    / _` | '_ \| | | |",
    r"| |__| | |___| (_| | |_) | |_| |",
    r" \____/ \_____\__,_| .__/ \__, |",
    r"                   | |     __/ |",
    r"                   |_|    |___/ "
]

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
        self.full_output = deque(maxlen=5000)
        self.lock = threading.Lock()

    def start(self, cmd_str):
        self.command = cmd_str
        self.is_running = True
        self.exit_code = None
        self.output_queue = queue.Queue()
        # self.full_output = deque(maxlen=5000) # Maintain history unless explicitly cleared

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
                        with self.lock:
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

# Colors (initialized in main)
COLOR_DEFAULT = 1
COLOR_HIGHLIGHT = 2
COLOR_TITLE = 3
COLOR_SUBTITLE = 4
COLOR_DIM = 5
COLOR_SUCCESS = 6
COLOR_WARNING = 7

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

def get_actionable_matches(text):
    """Detects IDs, Pod names, and IPs in the provided text."""
    patterns = [
        r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', # UUID
        r'pod-[a-z0-9-]+', # K8s Pods (Guess)
        r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b' # IP
    ]
    matches = []
    for p in patterns:
        for m in re.finditer(p, text):
            matches.append((m.start(), m.end(), m.group()))
    return matches

def draw_header(stdscr, w):
    """Draws a persistent header with persona and path info."""
    persona = get_current_persona_name().upper()
    path = get_active_library_path().replace(os.path.expanduser("~"), "~")

    stdscr.attron(curses.color_pair(COLOR_TITLE) | curses.A_BOLD)
    stdscr.addstr(0, 0, " " * w) # Clear line
    stdscr.addstr(0, 2, f"👤 OPERATING AS: {persona}")
    stdscr.addstr(0, w - len(path) - 4, f"📂 {path} ")
    stdscr.attroff(curses.color_pair(COLOR_TITLE) | curses.A_BOLD)

def draw_stream_pane(stdscr, y, x, w, h, proc, scroll_idx, focus, selection, observer=None, cursor_pos=(0, 0)):
    """Draws the persistent log stream pane on the right."""
    try:
        win = curses.newwin(h, w, y, x)
        win.attron(curses.color_pair(COLOR_TITLE))
        win.box()

        # Stream Heartbeat Indicator
        hb_char = "●" if not selection else "⏸"
        hb_color = COLOR_SUCCESS if (not selection and proc.is_running) else (COLOR_WARNING if selection else COLOR_DIM)
        win.addstr(0, w - 4, f" {hb_char} ", curses.color_pair(hb_color) | curses.A_BOLD)

        # Tier 1 (System) Alerts: Blinking Line
        if observer:
            sys_alerts = observer.get_latest_alerts(tier=1)
            if sys_alerts:
                # Use a blinking effect (simplified as Bold Highlight for now)
                alert_msg = f" 🔥 SYSTEM ALERT: {sys_alerts[-1].message} "
                win.addstr(0, (w - len(alert_msg)) // 2, alert_msg, curses.color_pair(COLOR_WARNING) | curses.A_BOLD)

        status = "[PAUSED]" if selection else ("[STREAMING]" if proc.is_running else "[IDLE]")
        color = COLOR_HIGHLIGHT if selection else (COLOR_TITLE if proc.is_running else COLOR_DEFAULT)
        win.attron(curses.color_pair(color))
        win.addstr(0, 2, f" STREAM {status} ", curses.A_BOLD)
        win.attroff(curses.color_pair(color))

        # Render output from circular buffer
        with proc.lock:
            total_lines = len(proc.full_output)
            max_content_h = h - 2
            start_idx = max(0, total_lines - max_content_h - scroll_idx)
            end_idx = min(total_lines, start_idx + max_content_h)
            # Use islice for O(K) slice instead of O(N) list conversion
            display_lines = list(itertools.islice(proc.full_output, start_idx, end_idx))

        max_content_w = w - 4
        for i, line in enumerate(display_lines):
            if i >= max_content_h: break
            clean_line = strip_ansi(line)[:max_content_w].replace('\n', '').replace('\r', '')

            # Categorized Colors for Stream
            matches = get_actionable_matches(clean_line)
            last_pos = 0

            # Decide base color for the line (Dimmed for standard logs)
            base_attr = curses.color_pair(COLOR_DIM)
            if "SUCCESS" in clean_line.upper() or "DONE" in clean_line.upper():
                base_attr = curses.color_pair(COLOR_SUCCESS)
            elif "ERROR" in clean_line.upper() or "FAILED" in clean_line.upper():
                base_attr = curses.color_pair(COLOR_WARNING) | curses.A_BOLD

            for m_start, m_end, m_text in matches:
                win.addstr(i + 1, 2 + last_pos, clean_line[last_pos:m_start], base_attr)
                win.addstr(i + 1, 2 + m_start, m_text, curses.color_pair(COLOR_HIGHLIGHT) | curses.A_BOLD)
                last_pos = m_end
            win.addstr(i + 1, 2 + last_pos, clean_line[last_pos:], base_attr)

            # Draw Selection Cursor
            if selection and cursor_pos[0] == i:
                win.attron(curses.A_REVERSE)
                char = clean_line[cursor_pos[1]] if cursor_pos[1] < len(clean_line) else ' '
                win.addstr(i + 1, 2 + cursor_pos[1], char)
                win.attroff(curses.A_REVERSE)

        win.refresh()
    except Exception as e:
        pass

def draw_lazy_dashboard(stdscr, selected_idx, version, skill_count):
    """Draws a clean, centered dashboard inspired by LazyVim."""
    h, w = stdscr.getmaxyx()
    win = curses.newwin(h, w, 0, 0) # Full screen overlay (minus command bar space if needed)
    win.attron(curses.color_pair(COLOR_DEFAULT))

    # 1. Logo (Centered)
    logo_height = len(JCAPY_LOGO)
    start_y = max(1, (h // 2) - logo_height - 6) # Push up slightly

    for i, line in enumerate(JCAPY_LOGO):
        # Pulsing effect based on time? For now, static or simple cycle
        color = COLOR_TITLE
        win.addstr(start_y + i, (w - len(line)) // 2, line, curses.color_pair(color) | curses.A_BOLD)

    # 2. Menu Items
    menu_y = start_y + logo_height + 2

    options = [
        {"key": "f", "label": "Find Skill",     "icon": "🔍"},
        {"key": "n", "label": "New Skill",      "icon": "📄"},
        {"key": "p", "label": "Map Project",    "icon": "🗺️ "},
        {"key": "s", "label": "Semantic Search","icon": "🧠"},
        {"key": "r", "label": "Recent Skills",  "icon": "clock"}, # Icon encoding issue? Use text
        {"key": "c", "label": "Config",         "icon": "⚙️ "},
        {"key": "q", "label": "Quit",           "icon": "🚪"},
    ]

    max_label_len = max(len(o['label']) for o in options)
    menu_width = 30 # Approx width for centering
    menu_start_x = (w - menu_width) // 2

    current_y = menu_y
    for idx, opt in enumerate(options):
        is_selected = (idx == selected_idx)

        # Icon + Label
        prefix = f" {opt['icon']} {opt['label']}"
        # Padding for alignment
        padding = " " * (menu_width - len(prefix) - 5)
        # Shortcut key
        suffix = f"{opt['key']} "

        full_line = f"{prefix}{padding}{suffix}"

        attr = curses.color_pair(COLOR_HIGHLIGHT) | curses.A_BOLD if is_selected else curses.color_pair(COLOR_DEFAULT)

        win.addstr(current_y, (w - len(full_line)) // 2, full_line, attr)
        current_y += 1

    # 3. Footer Stats
    footer_text = f"⚡ jcapy loaded {skill_count} skills • v{version}"
    win.addstr(h - 2, (w - len(footer_text)) // 2, footer_text, curses.color_pair(COLOR_DIM))

    win.refresh()

# Legacy alias if needed, but we will update run() to use this
def draw_dashboard(*args, **kwargs): pass

def draw_config_panel(stdscr, active_persona, personas_data, selected_idx=0):
    """Draws the premium Identity & Configuration panel."""
    h, w = stdscr.getmaxyx()
    win = curses.newwin(h - 2, w, 1, 0)
    win.attron(curses.color_pair(COLOR_DEFAULT))
    win.box()

    # 1. Hero Logo (Centered)
    logo_y = 2
    for i, line in enumerate(JCAPY_LOGO):
        # Pulsing color simulation: Title for logo
        win.addstr(logo_y + i, (w - len(line)) // 2, line, curses.color_pair(COLOR_TITLE) | curses.A_BOLD)

    # 2. Whoami Section (Centered Badge)
    whoami_y = logo_y + len(JCAPY_LOGO) + 2
    user_name = os.environ.get('USER', 'OPERATOR').upper()
    label = f" 👤 [ IDENTITY: {user_name} ] "
    win.addstr(whoami_y, (w - len(label)) // 2, label, curses.color_pair(COLOR_HIGHLIGHT) | curses.A_REVERSE)

    # 3. Persona Management
    win.addstr(whoami_y + 3, 4, " ⚙️  PERSONA MANAGEMENT ", curses.color_pair(COLOR_SUBTITLE) | curses.A_BOLD)

    for idx, p in enumerate(personas_data):
        is_active = p['name'].lower() == active_persona.lower()
        is_selected = (idx == selected_idx)

        marker = "▶" if is_active else " "

        # Color logic: Highlight for hovered, Success for active, Default for others
        if is_selected:
            attr = curses.color_pair(COLOR_HIGHLIGHT) | curses.A_BOLD
        elif is_active:
            attr = curses.color_pair(COLOR_SUCCESS) | curses.A_BOLD
        else:
            attr = curses.color_pair(COLOR_DEFAULT)

        # Display Name and Path
        name_str = p['name'].capitalize()
        path_str = p.get('path', '').replace(os.path.expanduser("~"), "~")
        win.addstr(whoami_y + 5 + idx, 6, f"{marker} {name_str:<15} {path_str:<40}", attr)

    # 4. Instructions (Footer)
    win.addstr(h - 5, (w - 60) // 2, "[j/k] Navigate  [ENTER] Select  [a] Add  [d] Delete  [:q] Exit", curses.color_pair(COLOR_DIM))
    win.refresh()

LEADER_MAP = {
    'd': 'doctor',
    's': 'sync',
    'p': 'push',
    'h': 'harvest',
    'l': 'list',
    'm': 'manage',
    'i': 'init',
    'D': 'deploy',
    'U': 'persona',
    '?': 'help'
}

def draw_leader_menu(stdscr):
    """Draws the quick-action leader menu overlay."""
    h, w = stdscr.getmaxyx()
    box_h, box_w = 14, 42
    box_y, box_x = (h - box_h) // 2, (w - box_w) // 2

    try:
        win = curses.newwin(box_h, box_w, box_y, box_x)
        win.attron(curses.color_pair(COLOR_HIGHLIGHT))
        win.box()
        win.attron(curses.color_pair(COLOR_TITLE) | curses.A_BOLD)
        win.addstr(0, (box_w - 18) // 2, " ⚡ POWER MAGIC ⚡ ")
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
            win.addstr(2 + i, 4, f"[ {key} ] ", curses.color_pair(COLOR_HIGHLIGHT))
            win.addstr(2 + i, 10, desc, curses.color_pair(COLOR_DEFAULT))

        win.addstr(box_h - 2, (box_w - 18) // 2, "[Esc] to cancel", curses.color_pair(COLOR_SUBTITLE))
        win.refresh()
        return win
    except:
        return None

def draw_dual_pane(stdscr, selected_idx, skills, filter_text, width=None):
    h, w_full = stdscr.getmaxyx()
    w = width if width else w_full
    left_w = int(w * 0.45)
    right_w = w - left_w

    # Left Pane: Frameworks/Skills
    try:
        left_win = curses.newwin(h - 2, left_w, 1, 0)
        left_win.attron(curses.color_pair(COLOR_DEFAULT))
        left_win.box()
        left_win.addstr(0, 2, " FRAMEWORKS ", curses.color_pair(COLOR_TITLE) | curses.A_BOLD)

        max_items = h - 4
        start_idx = max(0, selected_idx - max_items // 2)

        for i in range(len(skills)):
            if i < start_idx: continue
            if i >= start_idx + max_items: break

            attr = curses.color_pair(COLOR_HIGHLIGHT) if i == selected_idx else curses.A_NORMAL
            locked = "🔒" if skills[i].get('locked') else "  "
            name = skills[i]['name'][:left_w-8]

            y_pos = i - start_idx + 1
            left_win.addstr(y_pos, 2, f"{locked} {name}", attr)
        left_win.refresh()
    except: pass

    # Right Pane: Preview
    try:
        right_win = curses.newwin(h - 2, right_w, 1, left_w)
        right_win.attron(curses.color_pair(COLOR_DEFAULT))
        right_win.box()
        right_win.addstr(0, 2, " PREVIEW ", curses.color_pair(COLOR_TITLE) | curses.A_BOLD)

        if skills and selected_idx < len(skills):
            with open(skills[selected_idx]['path'], 'r') as f:
                raw_content = f.read()

            # Simple cleanup for preview
            clean_lines = []
            for line in raw_content.splitlines():
                if "jcapy:EXEC" in line: continue
                if "---" in line and len(clean_lines) < 5: continue # Skip yaml frontmatter
                clean_lines.append(line.rstrip())

            for i, line in enumerate(clean_lines[:h-4]):
                display_line = line[:right_w-4]
                # Basic "highlighting"
                color = curses.color_pair(COLOR_SUBTITLE) if line.startswith("#") else curses.color_pair(COLOR_DEFAULT)
                right_win.addstr(i + 1, 2, display_line, color)
        right_win.refresh()
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

    # Clear terminal for a clean interactive experience
    print("\033[H\033[J", end="")
    print(f"\n{COLOR_TITLE}[jcapy] Operating as: {get_current_persona_name().upper()}{RESET}")
    print(f"{COLOR_TITLE}[jcapy] Executing: {cmd}{RESET}\n")
    try:
        subprocess.call(f"{exe} {cmd}", shell=True)
        print(f"\n{COLOR_SUBTITLE}[jcapy] Finished. Press ENTER to return to Cockpit.{RESET}")
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

    # New QoL Colors: Subtle Gray for logs, Green/Yellow for status
    curses.init_pair(COLOR_DIM, 242 if curses.can_change_color() else curses.COLOR_WHITE, -1)
    curses.init_pair(COLOR_SUCCESS, curses.COLOR_GREEN, -1)
    curses.init_pair(COLOR_WARNING, curses.COLOR_RED, -1)

    curses.curs_set(0)

    # State
    current_library_path = initial_library_path
    view_mode, edit_mode = "dashboard", "NORMAL"
    view_focus = "PILOT" # PILOT or STREAM
    selection_mode = False
    stream_scroll_idx = 0
    cmd_bar = CommandBar()
    dash_idx, list_row, filter_text = 0, 0, ""
    active_proc = ProcessManager()

    # Phase 2: Autonomous Intelligence Observer
    observer = AutonomousObserver(active_proc)
    observer.start()
    # stdscr.observer = observer # REMOVED: Curses windows don't allow arbitrary attributes

    stdscr.timeout(50)  # Snappier polling (50ms)

    # Mock/Load Data
    config = load_config()
    personas = config.get("personas", {"programmer": {"path": "/Users/irfanali/.jcapy/library"}})

    def refresh_data():
        nonlocal personas
        cfg = load_config()
        personas = cfg.get("personas", {"programmer": {"path": "/Users/irfanali/.jcapy/library"}})
        stats = []
        from jcapy.utils.git_lib import get_git_status
        for name, data in personas.items():
            path = data.get('path', '')
            sync_info, pending = get_git_status(path)
            status = f"🛠️ {pending} Pending" if pending > 0 else "✅ Synced"
            stats.append({
                "name": name,
                "path": path,
                "status": status,
                "count": 0 # Placeholder for skill count if we want it later
            })
        stats.sort(key=lambda x: x['name'])
        return stats, []

    p_stats, recent_files = refresh_data()

    def heuristic_search(stdscr, query):
        """Perform semantic search using MemoryBank."""
        try:
            from jcapy.memory import MemoryBank, get_active_library_path
            bank = MemoryBank()
            if bank.collection.count() == 0:
                 # Auto-sync on first use if empty
                 bank.sync_library(get_active_library_path())

            results = bank.recall(query, n_results=10)
            seen = set()
            skills = []

            for res in results:
                name = res['metadata']['name']
                if name not in seen:
                    skills.append({'name': name, 'path': res['metadata']['source']})
                    seen.add(name)
            return skills
        except:
             return []

    def fuzzy_search_ids(stdscr, proc):
        """Pops up a fuzzy finder for all actionable IDs in the buffer."""
        lines = list(proc.full_output)
        all_ids = set()
        for line in lines[-500:]:
            matches = get_actionable_matches(strip_ansi(line))
            for _, _, text in matches:
                all_ids.add(text)

        sorted_ids = sorted(list(all_ids))
        if not sorted_ids: return None

        h, w = stdscr.getmaxyx()
        box_h, box_w = min(15, len(sorted_ids) + 4), 60
        win = curses.newwin(box_h, box_w, (h-box_h)//2, (w-box_w)//2)
        win.box()
        win.addstr(1, 2, " FUZZY SEARCH IDs ", curses.color_pair(COLOR_TITLE) | curses.A_BOLD)

        sel_idx = 0
        while True:
            for i, item in enumerate(sorted_ids[:box_h-4]):
                attr = curses.color_pair(COLOR_HIGHLIGHT) if i == sel_idx else curses.color_pair(COLOR_DEFAULT)
                win.addstr(3 + i, 4, item[:box_w-8], attr)

            win.refresh()
            k = stdscr.getch()
            if k == ord('\n') or k == 13:
                return sorted_ids[sel_idx]
            elif k == 27: # ESC
                stdscr.clear(); stdscr.refresh()
                return None
            elif k in [curses.KEY_UP, ord('k')]:
                sel_idx = max(0, sel_idx - 1)
            elif k in [curses.KEY_DOWN, ord('j')]:
                sel_idx = min(len(sorted_ids) - 1, box_h - 5, sel_idx + 1)
        return None

    def update_global_persona(name):
        """Updates the current_persona in global config"""
        try:
            from jcapy.config import save_config
            cfg = load_config()
            cfg["current_persona"] = name
            save_config(cfg)
        except: pass

    selection_cursor = [0, 0] # [y, x] relative to viewport
    config_idx = 0

    try:
        while True:
            h, w = stdscr.getmaxyx()
            pilot_w = int(w * 0.35)
            stream_w = w - pilot_w

            # Draw Global Header
            draw_header(stdscr, w)

            # Ensure scroll index doesn't exceed buffer
            max_scroll = max(0, len(active_proc.full_output) - (h - 3))
            stream_scroll_idx = min(stream_scroll_idx, max_scroll)

            if view_mode == "dashboard":
                current_skills = get_skills(current_library_path)
                draw_lazy_dashboard(stdscr, dash_idx, VERSION, len(current_skills))
            elif view_mode == "config":
                # Get current persona name from config for highlighting
                active_persona_name = load_config().get("current_persona", "programmer")
                draw_config_panel(stdscr, active_persona_name, p_stats, selected_idx=config_idx)
            else:
                if filter_text.startswith("?"):
                    # Semantic Search
                    skills = heuristic_search(stdscr, filter_text[1:].strip())
                else:
                    # String Search
                    skills = [s for s in get_skills(current_library_path) if filter_text.lower() in s['name'].lower()]

                draw_dual_pane(stdscr, list_row, skills, filter_text, width=pilot_w)

            # Draw the stream (Hidden in Dashboard for clean aesthetic)
            if view_mode != "dashboard":
                draw_stream_pane(stdscr, 1, pilot_w, stream_w, h-2, active_proc, stream_scroll_idx, view_focus == "STREAM", selection_mode, observer=observer, cursor_pos=tuple(selection_cursor))

            # Removed redundant Process HUD
            # if active_proc.is_running or active_proc.exit_code is not None:
            #    draw_process_hud(stdscr, active_proc)

            # Tier 2 (Hint) Teaser in Command Bar area
            hints = observer.get_latest_alerts(tier=2)
            if hints and not selection_mode:
                stdscr.addstr(h-1, w-25, f" ⚡ Suggestion [H] ", curses.color_pair(COLOR_HIGHLIGHT) | curses.A_BOLD)

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
                # Selection mode toggle
                if key == ord('['):
                    selection_mode = not selection_mode
                    view_focus = "STREAM" if selection_mode else "PILOT"
                    continue

                # Tab to toggle focus
                if key == ord('\t'):
                    view_focus = "STREAM" if view_focus == "PILOT" else "PILOT"
                    continue

                # Ctrl+G Fuzzy ID Search
                if key == 7: # Ctrl+G
                    target_id = fuzzy_search_ids(stdscr, active_proc)
                    if target_id:
                        # Default to list/explore for selected ID
                        execute_interactive_command(stdscr, f"apply logs --id {target_id}")
                        p_stats, recent_files = refresh_data()
                    continue

                # Selection Mode Navigation
                if selection_mode and view_focus == "STREAM":
                    content_h = h - 2
                    max_y = min(content_h - 1, len(active_proc.full_output) - 1)

                    if key in [curses.KEY_UP, ord('k')]:
                        if selection_cursor[0] > 0: selection_cursor[0] -= 1
                        else: stream_scroll_idx = min(max_scroll, stream_scroll_idx + 1)
                    elif key in [curses.KEY_DOWN, ord('j')]:
                        if selection_cursor[0] < max_y: selection_cursor[0] += 1
                        else: stream_scroll_idx = max(0, stream_scroll_idx - 1)
                    elif key in [curses.KEY_LEFT, ord('h')]:
                        selection_cursor[1] = max(0, selection_cursor[1] - 1)
                    elif key in [curses.KEY_RIGHT, ord('l')]:
                        selection_cursor[1] += 1 # Bound check during draw
                    elif key == ord('g'):
                        stream_scroll_idx = max_scroll; selection_cursor[0] = 0
                    elif key == ord('G'):
                        stream_scroll_idx = 0; selection_cursor[0] = max_y

                    # Action Dispatcher (Prototypes)
                    elif key in [ord('L'), ord('R')]:
                        # Extract string under cursor
                        lines = list(active_proc.full_output)
                        total_lines = len(lines)
                        start_idx = max(0, total_lines - content_h - stream_scroll_idx)
                        line_idx = start_idx + selection_cursor[0]

                        if line_idx < total_lines:
                            clean_line = strip_ansi(lines[line_idx])
                            matches = get_actionable_matches(clean_line)
                            target_id = None
                            for m_start, m_end, m_text in matches:
                                if m_start <= selection_cursor[1] <= m_end:
                                    target_id = m_text
                                    break

                            if target_id:
                                action = "logs" if key == ord('L') else "restart"
                                # For R (Root), we handoff to Pilot
                                if key == ord('R'):
                                    selection_mode = False
                                    view_focus = "PILOT"
                                    execute_interactive_command(stdscr, f"apply {action} --id {target_id}")
                                    p_stats, recent_files = refresh_data()
                                else:
                                    # For L (Live/Quick-Look), show transient popup
                                    stdscr.addstr(h-1, 0, f" [FETCHING LOGS FOR {target_id}...] ", curses.color_pair(COLOR_HIGHLIGHT))
                                    stdscr.refresh()

                                    try:
                                        exe = "jcapy" if shutil.which("jcapy") else sys.executable + " -m jcapy"
                                        # Fetch last 20 lines
                                        cmd = f"{exe} logs --id {target_id} --limit 20"
                                        raw_out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
                                        display_output_panel(stdscr, f"QUICK LOOK: {target_id}", raw_out)
                                    except Exception as e:
                                        display_output_panel(stdscr, "Quick Look Error", str(e))

                                    stdscr.clear(); stdscr.refresh()

                    continue

                # [H] Heuristic Menu for Application Skills
                if key == ord('H'):
                    hints = observer.get_latest_alerts(tier=2)
                    if hints:
                        # Draw a simple choice menu
                        box_h, box_w = min(12, len(hints) + 4), 60
                        win = curses.newwin(box_h, box_w, (h-box_h)//2, (w-box_w)//2)
                        win.box()
                        win.attron(curses.color_pair(COLOR_HIGHLIGHT))
                        win.box()
                        win.addstr(1, 2, " 🧠 HEURISTIC ENGINE (Suggestions) ", curses.color_pair(COLOR_TITLE) | curses.A_BOLD)

                        # Show only unique suggestions
                        unique_hints = []
                        seen_cmds = set()
                        for h_alert in reversed(hints):
                            if h_alert.action_cmd not in seen_cmds:
                                unique_hints.append(h_alert)
                                seen_cmds.add(h_alert.action_cmd)

                        sel_h_idx = 0
                        while True:
                            for i, h_alert in enumerate(unique_hints[:box_h-4]):
                                attr = curses.color_pair(COLOR_HIGHLIGHT) if i == sel_h_idx else curses.color_pair(COLOR_DEFAULT)
                                win.addstr(3 + i, 4, f"• {h_alert.suggestion[:box_w-10]}", attr)

                            win.refresh()
                            hk = stdscr.getch()
                            if hk == ord('\n') or hk == 13:
                                selected_alert = unique_hints[sel_h_idx]
                                execute_interactive_command(stdscr, selected_alert.action_cmd)
                                p_stats, recent_files = refresh_data()
                                break
                            elif hk == 27: break
                            elif hk in [curses.KEY_UP, ord('k')]: sel_h_idx = max(0, sel_h_idx - 1)
                            elif hk in [curses.KEY_DOWN, ord('j')]: sel_h_idx = min(len(unique_hints)-1, sel_h_idx + 1)

                        stdscr.clear(); stdscr.refresh()
                    continue
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
                    # Vertical Navigation (LazyVim Style)
                    if key in [curses.KEY_UP, ord('k')]: dash_idx = max(0, dash_idx - 1) # 0 to 6
                    elif key in [curses.KEY_DOWN, ord('j')]: dash_idx = min(6, dash_idx + 1)

                    # Execute Selection (Enter)
                    elif key in [10, 13]:
                        if dash_idx == 0: # Find (Fuzzy)
                            view_mode = "list"; edit_mode = "INSERT"; cmd_bar.clear(); filter_text = ""
                        elif dash_idx == 1: # New (Harvest)
                            execute_interactive_command(stdscr, "harvest")
                            p_stats, recent_files = refresh_data()
                        elif dash_idx == 2: # Map Project
                            execute_interactive_command(stdscr, "map")
                        elif dash_idx == 3: # Semantic Search
                            view_mode = "list"; edit_mode = "INSERT"; cmd_bar.clear(); filter_text = "?"
                        elif dash_idx == 4: # Recent (List)
                            view_mode = "list"
                        elif dash_idx == 5: # Config
                            view_mode = "config"
                        elif dash_idx == 6: # Quit
                            break

                    # Shortcuts
                    elif key == ord('f'): view_mode = "list"; edit_mode = "INSERT"; cmd_bar.clear(); filter_text = ""
                    elif key == ord('n'): execute_interactive_command(stdscr, "harvest"); p_stats, recent_files = refresh_data()
                    elif key == ord('p'): execute_interactive_command(stdscr, "map")
                    elif key == ord('s'): view_mode = "list"; edit_mode = "INSERT"; cmd_bar.clear(); filter_text = "?"
                    elif key == ord('r'): view_mode = "list"
                    elif key == ord('c'): view_mode = "config"
                    elif key in [ord('q'), ord('Q')]: break

                    elif key == ord(':'): edit_mode = "COMMAND"; cmd_bar.clear()
                    elif key == ord(' '): # Power Magic Leader
                        win = draw_leader_menu(stdscr)
                        if win:
                            stdscr.timeout(-1)
                            action_key = stdscr.getch()
                            stdscr.timeout(100)
                            if 0 <= action_key <= 1114111 and chr(action_key) in LEADER_MAP:
                                cmd = LEADER_MAP[chr(action_key)]
                                if cmd == "manage": view_mode = "dashboard"
                                elif cmd == "list": view_mode = "list"
                                elif cmd in ["harvest", "sync", "push", "init", "deploy", "persona"]:
                                    execute_interactive_command(stdscr, cmd)
                                else:
                                    active_proc.start(cmd)
                            del win
                elif view_mode == "config":
                    if key in [curses.KEY_UP, ord('k')]: config_idx = max(0, config_idx - 1)
                    elif key in [curses.KEY_DOWN, ord('j')]: config_idx = min(len(p_stats)-1, config_idx + 1)
                    elif key in [10, 13]: # ENTER
                        persona_name = p_stats[config_idx]['name']
                        current_library_path = personas[persona_name]['path']
                        update_global_persona(persona_name)
                        view_mode = "list"
                    elif key == ord(':'): edit_mode = "COMMAND"; cmd_bar.clear()
                    elif key == 27: view_mode = "dashboard"
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
                                elif cmd in ["harvest", "sync", "push", "init", "deploy", "persona"]:
                                    execute_interactive_command(stdscr, cmd)
                                    p_stats, recent_files = refresh_data()
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
                            if cmd in ["config", "settings", "whoami"]:
                                view_mode = "config"
                            elif cmd == "dashboard":
                                view_mode = "dashboard"
                            elif cmd == "list":
                                view_mode = "list"
                            elif cmd == "q":
                                break
                            else:
                                try:
                                    base_cmd = cmd.split()[0]
                                    if base_cmd in ["harvest", "sync", "push", "init", "deploy", "persona"]:
                                        execute_interactive_command(stdscr, cmd)
                                        p_stats, recent_files = refresh_data()
                                    else:
                                        active_proc.start(cmd)
                                except Exception as e:
                                    display_output_panel(stdscr, "Error", str(e))
                        edit_mode = "NORMAL"; cmd_bar.clear()
    finally:
        observer.stop()

def run(library_path):
    curses.wrapper(main, library_path)

if __name__ == "__main__":
    run("/Users/irfanali/.jcapy/library")
