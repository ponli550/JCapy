# SPDX-License-Identifier: Apache-2.0
import os
import shutil
import subprocess
import sys
import yaml
from pathlib import Path
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table
from jcapy.core.base import CommandBase

console = Console()

class InstallCommand(CommandBase):
    name = "install"
    description = "Install a skill from a GitHub URL with isolated dependencies"

    def setup_parser(self, parser):
        parser.add_argument("url", help="Git URL of the skill repository")
        parser.add_argument("--no-sandbox", action="store_true", 
                          help="Install dependencies to system Python (not recommended)")
        parser.add_argument("--sandbox", action="store_true", 
                          help="Force sandboxed installation (default for skills with requirements)")

    def execute(self, args):
        """
        Installs a JCapy skill from a Git repository.
        Usage: jcapy install <git_url>
        
        Features:
        - Manifest verification (security)
        - Consent-based installation
        - Isolated dependency sandboxing (prevents dependency hell)
        """
        if not hasattr(args, 'url') or not args.url:
            console.print("[red]Error: Please provide a Git URL.[/red]")
            return

        repo_url = args.url
        # Extract skill name from URL
        skill_name = repo_url.rstrip("/").split("/")[-1]
        if skill_name.endswith(".git"):
            skill_name = skill_name[:-4]

        install_base = Path.home() / ".jcapy" / "skills"
        install_dir = install_base / skill_name

        console.print(f"[cyan]Attempting to install skill from:[/cyan] {repo_url}")

        # 1. Check if already installed
        if install_dir.exists():
            console.print(f"[yellow]Skill '{skill_name}' is already installed.[/yellow]")
            if not Confirm.ask("Do you want to reinstall/overwrite it?"):
                return
            
            # Remove old installation and sandbox
            shutil.rmtree(install_dir)
            sandbox_dir = Path.home() / ".jcapy" / "sandboxes" / skill_name
            if sandbox_dir.exists():
                shutil.rmtree(sandbox_dir)

        # Ensure base skills dir exists
        install_base.mkdir(parents=True, exist_ok=True)

        # 2. Clone the Repository
        try:
            subprocess.check_call(
                ["git", "clone", "--depth", "1", repo_url, str(install_dir)],
                stdout=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            console.print(f"[red]Failed to clone repository. Check URL and internet connection.[/red]")
            if install_dir.exists():
                shutil.rmtree(install_dir)
            return

        # 3. Verify Manifest (Security Policy Rule #1)
        manifest_path = install_dir / "jcapy.yaml"
        if not manifest_path.exists():
            console.print("[red]Security Error: No 'jcapy.yaml' manifest found.[/red]")
            console.print("[red]This repository is not a valid JCapy skill. Aborting.[/red]")
            shutil.rmtree(install_dir)
            return

        # 4. Display Manifest & Ask Consent (Security Policy Rule #2)
        try:
            with open(manifest_path, "r") as f:
                manifest = yaml.safe_load(f)
        except Exception as e:
            console.print(f"[red]Error parsing manifest: {e}[/red]")
            shutil.rmtree(install_dir)
            return

        # Display manifest info
        self._display_manifest(manifest)

        if not Confirm.ask("\n[bold]Do you trust this skill and want to proceed?[/bold]"):
            console.print("[yellow]Installation aborted by user.[/yellow]")
            shutil.rmtree(install_dir)
            return

        # 5. Handle Dependencies with Sandboxing
        req_path = install_dir / "requirements.txt"
        has_requirements = req_path.exists()
        
        if has_requirements:
            deps = self._parse_requirements(req_path)
            
            console.print(f"\n[yellow]This skill requires {len(deps)} external package(s):[/yellow]")
            self._display_dependencies(deps)
            
            use_sandbox = not args.no_sandbox
            
            if use_sandbox:
                console.print("\n[cyan]📦 Installing in isolated sandbox...[/cyan]")
                success = self._install_with_sandbox(skill_name, req_path)
            else:
                console.print("\n[yellow]⚠️  Installing to system Python (may cause conflicts)[/yellow]")
                success = self._install_system(req_path)
            
            if not success:
                console.print("[yellow]Skill installed, but dependencies may not work correctly.[/yellow]")
        else:
            console.print("\n[dim]No additional dependencies required.[/dim]")

        console.print(f"\n[bold green]Success![/bold green] Skill '{skill_name}' installed.")
        console.print("Run [cyan]jcapy --help[/cyan] to see your new commands.")

    def _display_manifest(self, manifest: dict):
        """Display skill manifest in a formatted table."""
        table = Table(title="Skill Manifest", show_header=False, box=None)
        table.add_column("Field", style="cyan")
        table.add_column("Value")
        
        table.add_row("Name", manifest.get('name', 'Unknown'))
        table.add_row("Version", manifest.get('version', '0.0.0'))
        table.add_row("Description", manifest.get('description', 'No description'))
        
        permissions = manifest.get('permissions', ['None'])
        if isinstance(permissions, list):
            permissions = ", ".join(permissions)
        table.add_row("Permissions", permissions)
        
        console.print(table)

    def _display_dependencies(self, deps: list):
        """Display dependencies in a formatted table."""
        table = Table(show_header=True, box=None)
        table.add_column("Package", style="cyan")
        table.add_column("Version Constraint")
        
        for dep in deps[:10]:  # Show first 10
            name, version = self._parse_dep_string(dep)
            table.add_row(name, version or "latest")
        
        if len(deps) > 10:
            table.add_row(f"... and {len(deps) - 10} more", "")
        
        console.print(table)

    def _parse_requirements(self, req_path: Path) -> list:
        """Parse requirements.txt file."""
        deps = []
        try:
            with open(req_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        deps.append(line)
        except Exception:
            pass
        return deps

    def _parse_dep_string(self, dep: str) -> tuple:
        """Parse a dependency string into name and version."""
        for op in [">=", "<=", "==", "~=", ">", "<", "!="]:
            if op in dep:
                parts = dep.split(op, 1)
                return parts[0].strip(), op + parts[1].strip()
        return dep, None

    def _install_with_sandbox(self, skill_name: str, req_path: Path) -> bool:
        """Install dependencies in an isolated sandbox."""
        try:
            from jcapy.core.sandbox_manager import get_sandbox_manager
            
            manager = get_sandbox_manager()
            
            # Create isolated venv for this skill
            sandbox = manager.create_sandbox(skill_name)
            
            # Install dependencies
            success = manager.install_dependencies(
                skill_name,
                requirements=[],
                requirements_file=req_path
            )
            
            if success:
                deps_info = manager.get_dependency_info(skill_name)
                console.print(f"[green]✅ Installed {len(deps_info)} packages in isolated environment[/green]")
                console.print(f"[dim]   Sandbox: {sandbox.venv_path}[/dim]")
            
            return success
            
        except ImportError:
            console.print("[yellow]Sandbox manager not available, falling back to system install[/yellow]")
            return self._install_system(req_path)

    def _install_system(self, req_path: Path) -> bool:
        """Install dependencies to system Python."""
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-r", str(req_path)],
                stdout=subprocess.DEVNULL
            )
            return True
        except subprocess.CalledProcessError:
            return False


# For backward compatibility
run_install = None