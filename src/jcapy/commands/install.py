# SPDX-License-Identifier: Apache-2.0
import os
import shutil
import subprocess
import sys
import yaml
from rich.console import Console
from rich.prompt import Confirm
from jcapy.core.base import CommandBase

console = Console()

class InstallCommand(CommandBase):
    name = "install"
    description = "Install a skill from a GitHub URL"

    def setup_parser(self, parser):
        parser.add_argument("url", help="Git URL of the skill repository")

    def execute(self, args):
        """
        Installs a JCapy skill from a Git repository.
        Usage: jcapy install <git_url>
        """
        # We need to ensure the parser defines 'url'.
        if not hasattr(args, 'url') or not args.url:
            console.print("[red]Error: Please provide a Git URL.[/red]")
            return

        repo_url = args.url
        # Extract skill name from URL
        skill_name = repo_url.rstrip("/").split("/")[-1]
        if skill_name.endswith(".git"):
            skill_name = skill_name[:-4]

        install_base = os.path.expanduser("~/.jcapy/skills")
        install_dir = os.path.join(install_base, skill_name)

        console.print(f"[cyan]Attempting to install skill from:[/cyan] {repo_url}")

        # 1. Check if already installed
        if os.path.exists(install_dir):
            console.print(f"[yellow]Skill '{skill_name}' is already installed.[/yellow]")
            if not Confirm.ask("Do you want to reinstall/overwrite it?"):
                return
            shutil.rmtree(install_dir)

        # Ensure base skills dir exists
        os.makedirs(install_base, exist_ok=True)

        # 2. Clone the Repository (Sandboxed Clone)
        try:
            subprocess.check_call(
                ["git", "clone", "--depth", "1", repo_url, install_dir],
                stdout=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            console.print(f"[red]Failed to clone repository. Check URL and internet connection.[/red]")
            if os.path.exists(install_dir):
                shutil.rmtree(install_dir)
            return

        # 3. Verify Manifest (Security Policy Rule #1)
        manifest_path = os.path.join(install_dir, "jcapy.yaml")
        if not os.path.exists(manifest_path):
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

        console.print("\n[bold green]Skill Manifest Verified:[/bold green]")
        console.print(f"  Name: [cyan]{manifest.get('name', 'Unknown')}[/cyan]")
        console.print(f"  Version: {manifest.get('version', '0.0.0')}")
        console.print(f"  Description: {manifest.get('description', 'No description')}")
        console.print(f"  Permissions: {manifest.get('permissions', ['None'])}")

        if not Confirm.ask("\n[bold]Do you trust this skill and want to proceed?[/bold]"):
            console.print("[yellow]Installation aborted by user.[/yellow]")
            shutil.rmtree(install_dir)
            return

        # 5. Handle Dependencies (Security Policy Rule #3)
        req_path = os.path.join(install_dir, "requirements.txt")
        if os.path.exists(req_path):
            console.print(f"\n[yellow]This skill requires external Python packages.[/yellow]")
            if Confirm.ask("Install dependencies via pip?"):
                 try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_path])
                 except subprocess.CalledProcessError:
                     console.print("[red]Failed to install dependencies.[/red]")
                     console.print("[yellow]Skill installed, but might not work correctly.[/yellow]")

        console.print(f"\n[bold green]Success![/bold green] Skill '{skill_name}' installed.")
        console.print("Run [cyan]jcapy --help[/cyan] to see your new commands.")

# Maintain backward compatibility if needed, but we are switching to class-based.
run_install = None # Deprecated
