# SPDX-License-Identifier: Apache-2.0
"""
System Stats Widget for JCapy TUI

Displays real-time system metrics (CPU, Memory, Tasks, Uptime)
"""

import os
import psutil
from datetime import datetime
from textual.widget import Widget
from textual.widgets import Static
from textual.containers import Horizontal, Vertical
from textual.app import ComposeResult
from textual.reactive import reactive
from rich.panel import Panel
from rich.text import Text
from rich.progress import Bar


class SystemStatsWidget(Widget):
    """Real-time system statistics widget."""
    
    cpu_percent = reactive(0.0)
    memory_percent = reactive(0.0)
    memory_used = reactive("0 MB")
    tasks_count = reactive(0)
    uptime_seconds = reactive(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_time = datetime.now()
        self.widget_name = "SystemStats"
    
    def on_mount(self) -> None:
        """Initialize widget and start periodic updates."""
        self.highlighted = False
        self.update_stats()
        # Update every 2 seconds
        self.set_interval(2.0, self.update_stats)
    
    def toggle_highlight(self, active: bool) -> None:
        """Toggle edit mode highlight."""
        self.highlighted = active
        self.refresh()
    
    def update_stats(self) -> None:
        """Update system statistics."""
        try:
            # CPU
            self.cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory
            mem = psutil.virtual_memory()
            self.memory_percent = mem.percent
            self.memory_used = f"{mem.used // (1024*1024)} MB"
            
            # Uptime
            elapsed = datetime.now() - self.start_time
            self.uptime_seconds = int(elapsed.total_seconds())
            
            # Tasks (from daemon state if available)
            try:
                from jcapy.daemon.server import state
                self.tasks_count = state.tasks_completed
            except:
                self.tasks_count = 0
                
        except Exception as e:
            # Fallback if psutil not available
            self.cpu_percent = 0.0
            self.memory_percent = 0.0
            self.memory_used = "N/A"
    
    def format_uptime(self) -> str:
        """Format uptime as human readable."""
        seconds = self.uptime_seconds
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    
    def render(self) -> Panel:
        """Render the widget."""
        content = Text()
        
        # CPU
        content.append("\n ")
        content.append("🖥️  CPU", style="bold cyan")
        content.append(f"  {self.cpu_percent:.1f}%", style="bold white")
        content.append("\n ")
        bar_filled = int(self.cpu_percent / 5)
        bar_empty = 20 - bar_filled
        content.append("█" * bar_filled, style="cyan")
        content.append("░" * bar_empty, style="dim")
        
        # Memory
        content.append("\n\n ")
        content.append("💾  RAM", style="bold green")
        content.append(f"  {self.memory_percent:.1f}%", style="bold white")
        content.append(f" ({self.memory_used})", style="dim")
        content.append("\n ")
        bar_filled = int(self.memory_percent / 5)
        bar_empty = 20 - bar_filled
        content.append("█" * bar_filled, style="green")
        content.append("░" * bar_empty, style="dim")
        
        # Tasks & Uptime
        content.append("\n\n ")
        content.append("📋  Tasks", style="bold yellow")
        content.append(f"   {self.tasks_count}", style="bold white")
        
        content.append("\n ")
        content.append("⏱️  Uptime", style="bold magenta")
        content.append(f" {self.format_uptime()}", style="bold white")
        
        border_color = "green" if self.highlighted else "blue"
        return Panel(
            content,
            title="📊 System Stats",
            border_style=border_color,
            padding=(0, 1)
        )


class ConnectionStatusWidget(Widget):
    """Shows ZMQ/WebSocket connection status."""
    
    zmq_status = reactive("OFFLINE")
    web_status = reactive("OFFLINE")
    clients_count = reactive(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.widget_name = "ConnectionStatus"
    
    def on_mount(self) -> None:
        """Initialize widget."""
        self.highlighted = False
        self.update_status()
        self.set_interval(5.0, self.update_status)
    
    def toggle_highlight(self, active: bool) -> None:
        self.highlighted = active
        self.refresh()
    
    def update_status(self) -> None:
        """Check connection status."""
        try:
            from jcapy.core.zmq_publisher import get_zmq_bridge
            bridge = get_zmq_bridge()
            if bridge and bridge.is_running:
                self.zmq_status = "ONLINE"
            else:
                self.zmq_status = "OFFLINE"
        except:
            self.zmq_status = "OFFLINE"
        
        # Web status (check if bridge server is running)
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', 8000))
            sock.close()
            self.web_status = "ONLINE" if result == 0 else "OFFLINE"
        except:
            self.web_status = "OFFLINE"
    
    def render(self) -> Panel:
        content = Text()
        
        # ZMQ Status
        zmq_color = "green" if self.zmq_status == "ONLINE" else "red"
        content.append("\n ")
        content.append("🔌 ZMQ Bridge", style="bold white")
        content.append(f"  {self.zmq_status}", style=f"bold {zmq_color}")
        
        # WebSocket Status
        web_color = "green" if self.web_status == "ONLINE" else "red"
        content.append("\n ")
        content.append("🌐 WebSocket", style="bold white")
        content.append(f"   {self.web_status}", style=f"bold {web_color}")
        
        border_color = "green" if self.highlighted else "cyan"
        return Panel(
            content,
            title="🔗 Connections",
            border_style=border_color,
            padding=(0, 1)
        )


# Register widgets
try:
    from jcapy.ui.widgets.dashboard_widgets import WidgetRegistry
    WidgetRegistry.register("SystemStats", SystemStatsWidget, "Real-time CPU/Memory/Tasks", "small", "System")
    WidgetRegistry.register("ConnectionStatus", ConnectionStatusWidget, "ZMQ/Web Connection Status", "small", "System")
except ImportError:
    pass