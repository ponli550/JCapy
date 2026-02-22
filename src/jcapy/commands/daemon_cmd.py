# SPDX-License-Identifier: Apache-2.0
"""
JCapy Daemon Commands

CLI commands for managing the JCapy daemon:
- Start/stop daemon
- Check daemon status
- View logs
- Health checks
"""

import os
import sys
import argparse
import subprocess
import signal
import time
from pathlib import Path
from datetime import datetime

# ANSI Colors
CYAN = '\033[1;36m'
GREEN = '\033[1;32m'
YELLOW = '\033[1;33m'
RED = '\033[1;31m'
BOLD = '\033[1m'
RESET = '\033[0m'
GREY = '\033[0;90m'

# Default paths
DEFAULT_PID_FILE = Path.home() / '.jcapy' / 'daemon.pid'
DEFAULT_LOG_FILE = Path.home() / '.jcapy' / 'logs' / 'daemon.log'
DEFAULT_PORT = 8080


def get_pid_file() -> Path:
    """Get the PID file path"""
    return Path(os.environ.get('JCAPY_PID_FILE', DEFAULT_PID_FILE))


def get_log_file() -> Path:
    """Get the log file path"""
    return Path(os.environ.get('JCAPY_LOG_DIR', Path.home() / '.jcapy' / 'logs')) / 'daemon.log'


def is_daemon_running() -> bool:
    """Check if daemon is running"""
    pid_file = get_pid_file()
    
    if not pid_file.exists():
        return False
    
    try:
        with open(pid_file) as f:
            pid = int(f.read().strip())
        
        # Check if process exists
        os.kill(pid, 0)
        return True
    except (ValueError, ProcessLookupError, PermissionError):
        return False


def get_daemon_pid() -> int | None:
    """Get the daemon PID if running"""
    if not is_daemon_running():
        return None
    
    try:
        with open(get_pid_file()) as f:
            return int(f.read().strip())
    except (ValueError, FileNotFoundError):
        return None


def cmd_start(args):
    """Start the JCapy daemon"""
    if is_daemon_running():
        print(f"{YELLOW}Daemon is already running{RESET}")
        pid = get_daemon_pid()
        print(f"  PID: {pid}")
        print(f"  Use 'jcapy daemon stop' to stop it first")
        return
    
    port = args.port or DEFAULT_PORT
    
    print(f"{CYAN}Starting JCapy Daemon...{RESET}")
    
    # Ensure directories exist
    pid_file = get_pid_file()
    log_file = get_log_file()
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Start daemon process
    try:
        # Use subprocess to start daemon in background
        cmd = [
            sys.executable, '-m', 'jcapy.daemon.server',
            '--port', str(port),
            '--host', '0.0.0.0'
        ]
        
        # Start as background process
        with open(log_file, 'a') as log:
            log.write(f"\n{'='*60}\n")
            log.write(f"JCapy Daemon starting at {datetime.now().isoformat()}\n")
            log.flush()
            
            process = subprocess.Popen(
                cmd,
                stdout=log,
                stderr=log,
                start_new_session=True  # Detach from terminal
            )
        
        # Write PID file
        with open(pid_file, 'w') as f:
            f.write(str(process.pid))
        
        # Wait a moment and verify
        time.sleep(1)
        
        if is_daemon_running():
            print(f"{GREEN}✓ Daemon started successfully{RESET}")
            print(f"  PID: {process.pid}")
            print(f"  Port: {port}")
            print(f"  Control Plane: http://localhost:{port}")
            print(f"  Health Check: http://localhost:{port}/health")
            print(f"  Logs: {log_file}")
        else:
            print(f"{RED}✗ Daemon failed to start{RESET}")
            print(f"  Check logs: {log_file}")
            
    except Exception as e:
        print(f"{RED}Error starting daemon: {e}{RESET}")


def cmd_stop(args):
    """Stop the JCapy daemon"""
    if not is_daemon_running():
        print(f"{YELLOW}Daemon is not running{RESET}")
        return
    
    pid = get_daemon_pid()
    print(f"{CYAN}Stopping JCapy Daemon (PID: {pid})...{RESET}")
    
    try:
        # Send SIGTERM
        os.kill(pid, signal.SIGTERM)
        
        # Wait for process to stop
        for _ in range(10):
            time.sleep(0.5)
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                break
        else:
            # Force kill if still running
            print(f"{YELLOW}Daemon didn't stop gracefully, forcing...{RESET}")
            os.kill(pid, signal.SIGKILL)
        
        # Clean up PID file
        pid_file = get_pid_file()
        if pid_file.exists():
            pid_file.unlink()
        
        print(f"{GREEN}✓ Daemon stopped{RESET}")
        
    except ProcessLookupError:
        print(f"{YELLOW}Daemon process not found{RESET}")
        # Clean up stale PID file
        pid_file = get_pid_file()
        if pid_file.exists():
            pid_file.unlink()
    except Exception as e:
        print(f"{RED}Error stopping daemon: {e}{RESET}")


def cmd_restart(args):
    """Restart the JCapy daemon"""
    print(f"{CYAN}Restarting JCapy Daemon...{RESET}")
    
    # Stop if running
    if is_daemon_running():
        cmd_stop(args)
        time.sleep(1)
    
    # Start
    cmd_start(args)


def cmd_status(args):
    """Check daemon status"""
    print(f"\n{BOLD}JCapy Daemon Status{RESET}")
    print("-" * 40)
    
    if is_daemon_running():
        pid = get_daemon_pid()
        print(f"  Status: {GREEN}● Running{RESET}")
        print(f"  PID: {pid}")
        
        # Try to get status from daemon
        try:
            import urllib.request
            import json
            
            with urllib.request.urlopen('http://localhost:8080/api/status', timeout=2) as response:
                status = json.loads(response.read().decode())
                
                print(f"  Uptime: {status.get('uptime_human', 'unknown')}")
                print(f"  Tasks Completed: {status.get('tasks_completed', 0)}")
                print(f"  Version: {status.get('version', 'unknown')}")
                print(f"  Last Activity: {status.get('last_activity', 'unknown')}")
        except Exception:
            print(f"  {GREY}(Could not fetch detailed status){RESET}")
        
        print(f"  Control Plane: http://localhost:8080")
    else:
        print(f"  Status: {RED}○ Stopped{RESET}")
    
    print()


def cmd_logs(args):
    """View daemon logs"""
    log_file = get_log_file()
    
    if not log_file.exists():
        print(f"{YELLOW}No log file found: {log_file}{RESET}")
        return
    
    lines = args.lines or 50
    
    print(f"{CYAN}Last {lines} lines of daemon logs:{RESET}")
    print("-" * 60)
    
    try:
        # Use tail-like behavior
        result = subprocess.run(
            ['tail', '-n', str(lines), str(log_file)],
            capture_output=True, text=True
        )
        print(result.stdout)
    except Exception:
        # Fallback to reading file
        with open(log_file) as f:
            all_lines = f.readlines()
            for line in all_lines[-lines:]:
                print(line.rstrip())


def cmd_health(args):
    """Run daemon health check"""
    try:
        from jcapy.daemon.health import HealthChecker
        
        checker = HealthChecker()
        checker.print_report()
    except ImportError:
        print(f"{RED}Health checker module not available{RESET}")
        print("Running basic health check...")
        
        # Basic health check via HTTP
        try:
            import urllib.request
            import json
            
            with urllib.request.urlopen('http://localhost:8080/health', timeout=5) as response:
                health = json.loads(response.read().decode())
                
                print(f"\n{GREEN}✓ Daemon is healthy{RESET}")
                print(f"  Status: {health.get('status')}")
                print(f"  Version: {health.get('version')}")
        except Exception as e:
            print(f"\n{RED}✗ Daemon health check failed: {e}{RESET}")


def register_parser(subparsers):
    """Register daemon commands with the argument parser"""
    
    # Main daemon command
    daemon_parser = subparsers.add_parser(
        'daemon',
        help='Manage JCapy background daemon',
        description='Start, stop, and manage the JCapy daemon service'
    )
    
    daemon_subparsers = daemon_parser.add_subparsers(
        dest='daemon_command',
        help='Daemon commands'
    )
    
    # Start
    start_parser = daemon_subparsers.add_parser(
        'start',
        help='Start the daemon'
    )
    start_parser.add_argument(
        '--port', '-p',
        type=int,
        default=DEFAULT_PORT,
        help=f'Port to listen on (default: {DEFAULT_PORT})'
    )
    start_parser.set_defaults(func=cmd_start)
    
    # Stop
    stop_parser = daemon_subparsers.add_parser(
        'stop',
        help='Stop the daemon'
    )
    stop_parser.set_defaults(func=cmd_stop)
    
    # Restart
    restart_parser = daemon_subparsers.add_parser(
        'restart',
        help='Restart the daemon'
    )
    restart_parser.add_argument('--port', '-p', type=int, default=DEFAULT_PORT)
    restart_parser.set_defaults(func=cmd_restart)
    
    # Status
    status_parser = daemon_subparsers.add_parser(
        'status',
        help='Check daemon status'
    )
    status_parser.set_defaults(func=cmd_status)
    
    # Logs
    logs_parser = daemon_subparsers.add_parser(
        'logs',
        help='View daemon logs'
    )
    logs_parser.add_argument(
        '--lines', '-n',
        type=int,
        default=50,
        help='Number of lines to show (default: 50)'
    )
    logs_parser.add_argument(
        '--follow', '-f',
        action='store_true',
        help='Follow log output'
    )
    logs_parser.set_defaults(func=cmd_logs)
    
    # Health
    health_parser = daemon_subparsers.add_parser(
        'health',
        help='Run daemon health check'
    )
    health_parser.set_defaults(func=cmd_health)
    
    return daemon_parser