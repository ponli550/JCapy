# SPDX-License-Identifier: Apache-2.0
import os
import shutil
import subprocess
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from jcapy.core.base import CommandBase
from jcapy.config import load_config, DEFAULT_LIBRARY_PATH
from jcapy.utils.git_lib import get_git_remote_url
from jcapy.ui.theme import GLASS_STYLE, create_glass_panel

console = Console()

class DoctorCommand(CommandBase):
    """
    Diagnoses the health of JCapy, including local files, cloud connections, and telemetry.
    """
    name = "doctor"
    description = "Check system health"
    aliases = ["chk", "check"]

    def execute(self, args):
        console.print(Panel("[bold cyan]🩺 jcapy Doctor[/bold cyan]", box=GLASS_STYLE["box"], border_style=GLASS_STYLE["border_style"]))

        # 1. Core Health
        self.check_version()
        self.check_tools()
        self.check_local_storage()

        # 2. Telemetry Health
        self.check_telemetry()

        # 3. Cloud/Pro Health
        self.check_cloud_memory()

        # 4. Integrations
        self.check_integrations()

        # 5. Personas
        self.check_personas()

        # console.rule("[bold]Diagnosis Complete[/bold]")

    def check_version(self):
        # Assuming VERSION exists in jcapy.__init__ or similar, but user code said utils.updates
        try:
            from jcapy import __version__ as VERSION
        except ImportError:
            VERSION = "Unknown"

        console.print("\n[bold]📦 Core System[/bold]")
        console.print(f"  Version:   [green]v{VERSION}[/green]")
        console.print(f"  Python:    [cyan]{sys.version.split()[0]}[/cyan]")
        console.print(f"  Binary:    [dim]{sys.argv[0]}[/dim]")

    def check_tools(self):
        console.print("\n[bold]🛠  Tools[/bold]")
        tools = ["git", "node", "npm"]
        for tool in tools:
            if shutil.which(tool):
                console.print(f"  {tool:<10} [green]✔ Found[/green]")
            else:
                console.print(f"  {tool:<10} [red]✘ Missing[/red]")

    def check_local_storage(self):
        console.print("\n[bold]📂 Local Storage[/bold]")
        shadow_log = os.path.expanduser("~/.jcapy/shadow_log.jsonl")
        log_dir = os.path.dirname(shadow_log)

        # Check config files too
        cwd = os.getcwd()
        if os.path.exists(os.path.join(cwd, ".jcapyrc")):
             console.print(f"  .jcapyrc:  [green]Present[/green]")
        else:
             console.print(f"  .jcapyrc:  [yellow]Missing (Project Context)[/yellow]")

        if os.access(log_dir, os.W_OK):
            console.print(f"  Log Dir:   [green]Writable[/green]")
        else:
            console.print(f"  Log Dir:   [red]Permission Denied[/red] ({log_dir})")

    def check_telemetry(self):
        console.print("\n[bold]📡 Telemetry[/bold]")
        try:
            from jcapy.telemetry import get_telemetry
            t = get_telemetry()
            enabled = t.enabled
            status = "[green]Enabled[/green]" if enabled else "[yellow]Disabled (Opt-out)[/yellow]"
            console.print(f"  Status:    {status}")

            if enabled:
                ph_key = os.getenv("POSTHOG_API_KEY")
                k_status = "[green]Present[/green]" if ph_key else "[red]Missing[/red]"
                console.print(f"  PostHog:   {k_status}")
                console.print(f"  User ID:   [dim]{t.user_id[:8]}...[/dim]")
        except ImportError:
             console.print(f"  Status:    [red]Module Missing[/red]")

    def run_with_timeout(self, func, timeout=5):
        """Run a function with a timeout to prevent hanging."""
        import threading
        result = [None]
        exception = [None]

        def target():
            try:
                result[0] = func()
            except Exception as e:
                exception[0] = e

        t = threading.Thread(target=target)
        t.daemon = True
        t.start()
        t.join(timeout)

        if t.is_alive():
            raise TimeoutError("Check timed out (network issue?)")
        if exception[0]:
            raise exception[0]
        return result[0]

    def check_cloud_memory(self):
        console.print("\n[bold]🧠 Memory Bank[/bold]")
        provider = os.getenv("JCAPY_MEMORY_PROVIDER", "local")
        p_color = "green" if provider == "remote" else "cyan"
        console.print(f"  Provider:  [{p_color}]{provider.upper()}[/{p_color}]")

        if provider == "remote":
            try:
                import pinecone
                console.print("  Client:    [green]Installed[/green]")
            except ImportError:
                console.print("  Client:    [red]MISSING[/red] (Run `pip install 'jcapy[pro]'`)")
                return

            api_key = os.getenv("JCAPY_PINECONE_API_KEY")
            if api_key:
                console.print("  API Key:   [green]Found in Env[/green]")
                # Connectivity check
                try:
                   from pinecone import Pinecone
                   def check_pc():
                       pc = Pinecone(api_key=api_key)
                       # list_indexes is a network call
                       return pc.list_indexes()

                   self.run_with_timeout(check_pc, timeout=5)
                   console.print("  Connect:   [green]Healthy[/green]")
                except Exception as e:
                   console.print(f"  Connect:   [red]Failed ({e})[/red]")
            else:
                console.print("  API Key:   [red]Missing JCAPY_PINECONE_API_KEY[/red]")
        else:
            # Check Chroma
            try:
                import chromadb
                console.print("  ChromaDB:  [green]Installed[/green]")
            except ImportError:
                console.print("  ChromaDB:  [red]Missing[/red]")

    def check_integrations(self):
        console.print("\n[bold]🔗 Integrations[/bold]")
        cwd = os.getcwd()
        # Vercel
        v_status = "[green]Linked[/green]" if os.path.exists(os.path.join(cwd, ".vercel")) else "[dim]Not Linked[/dim]"
        console.print(f"  Vercel:    {v_status}")

        # Supabase
        s_linked = os.path.exists(os.path.join(cwd, "supabase", "config.toml"))
        s_status = "[green]Linked[/green]" if s_linked else "[dim]Not Linked[/dim]"
        console.print(f"  Supabase:  {s_status}")

    def check_personas(self):
        # Using GLASS_STYLE from theme.py
        p_table = Table(
            box=GLASS_STYLE["box"],
            border_style=GLASS_STYLE["border_style"],
            header_style=GLASS_STYLE["header_style"],
            expand=True
        )
        p_table.add_column("Persona", style="bold white")
        p_table.add_column("Path", style="dim white")
        p_table.add_column("Remote URL", style="dim cyan", overflow="ellipsis")
        p_table.add_column("Status", justify="center")

        config = load_config()
        personas = config.get("personas", {})
        if "programmer" not in personas:
             personas["programmer"] = {"path": DEFAULT_LIBRARY_PATH}

        for name, p_data in personas.items():
            path = p_data.get("path", "")
            exists = os.path.exists(path)

            remote_url_display = "[dim]Local Only[/dim]"
            if exists:
                url = get_git_remote_url(path)
                if url:
                    remote_url_display = url
                elif os.path.exists(os.path.join(path, ".git")):
                    remote_url_display = "[dim]No Remote[/dim]"
                else:
                    remote_url_display = "[bold red]LOCAL (No Git)[/bold red]"

            elif not exists:
                remote_url_display = "[bold red]MISSING[/bold red]"

            status = "[green]Active[/green]" if exists else "[bold red]MISSING[/bold red]"
            p_table.add_row(name, path, remote_url_display, status)

        console.print(create_glass_panel(p_table, title="[bold blue]Personas Diagnostic[/bold blue]"))

# Deprecated function entry point if still used elsewhere
def run_doctor():
    cmd = DoctorCommand()
    cmd.execute(None)
