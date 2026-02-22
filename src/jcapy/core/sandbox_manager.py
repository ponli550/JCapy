# SPDX-License-Identifier: Apache-2.0
"""
Plugin Sandbox Manager - Isolated Virtual Environments for Skills

This module provides dependency isolation for installed skills by creating
a separate virtual environment per skill, preventing "dependency hell" when
different skills require different versions of the same package.
"""
import os
import subprocess
import sys
import venv
import shutil
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass
from rich.console import Console

console = Console()

@dataclass
class SkillSandbox:
    """Represents an isolated environment for a skill."""
    name: str
    path: Path
    venv_path: Path
    python_path: Path
    pip_path: Path
    active: bool = False
    
    @property
    def site_packages(self) -> Path:
        """Get the site-packages directory for this sandbox."""
        if sys.platform == "win32":
            return self.venv_path / "Lib" / "site-packages"
        else:
            # Linux/macOS: lib/pythonX.Y/site-packages
            py_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
            return self.venv_path / "lib" / py_version / "site-packages"


class SandboxManager:
    """
    Manages isolated virtual environments for JCapy skills.
    
    Each skill gets its own venv in ~/.jcapy/sandboxes/<skill_name>/
    This prevents dependency conflicts between skills.
    """
    
    SANDBOX_DIR = Path.home() / ".jcapy" / "sandboxes"
    
    def __init__(self):
        self.SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
        self._sandboxes: Dict[str, SkillSandbox] = {}
        self._load_existing_sandboxes()
    
    def _load_existing_sandboxes(self):
        """Load metadata for existing sandboxes."""
        if not self.SANDBOX_DIR.exists():
            return
        
        for skill_dir in self.SANDBOX_DIR.iterdir():
            if skill_dir.is_dir() and (skill_dir / "pyvenv.cfg").exists():
                sandbox = self._create_sandbox_object(skill_dir.name)
                self._sandboxes[skill_dir.name] = sandbox
    
    def _create_sandbox_object(self, name: str) -> SkillSandbox:
        """Create a SkillSandbox object for an existing venv."""
        venv_path = self.SANDBOX_DIR / name
        
        if sys.platform == "win32":
            python_path = venv_path / "Scripts" / "python.exe"
            pip_path = venv_path / "Scripts" / "pip.exe"
        else:
            python_path = venv_path / "bin" / "python"
            pip_path = venv_path / "bin" / "pip"
        
        return SkillSandbox(
            name=name,
            path=self.SANDBOX_DIR / name,
            venv_path=venv_path,
            python_path=python_path,
            pip_path=pip_path
        )
    
    def create_sandbox(self, skill_name: str) -> SkillSandbox:
        """
        Create a new isolated virtual environment for a skill.
        
        Args:
            skill_name: Name of the skill to create sandbox for
            
        Returns:
            SkillSandbox object for the new environment
        """
        if skill_name in self._sandboxes:
            console.print(f"[yellow]Sandbox for '{skill_name}' already exists[/yellow]")
            return self._sandboxes[skill_name]
        
        venv_path = self.SANDBOX_DIR / skill_name
        
        console.print(f"[cyan]Creating isolated environment for {skill_name}...[/cyan]")
        
        # Create venv with system site packages for base JCapy access
        builder = venv.EnvBuilder(
            system_site_packages=True,  # Allow access to JCapy's packages
            clear=False,
            symlinks=True,
            upgrade=True,
            with_pip=True
        )
        
        builder.create(str(venv_path))
        
        sandbox = self._create_sandbox_object(skill_name)
        self._sandboxes[skill_name] = sandbox
        
        console.print(f"[green]✅ Created sandbox: {venv_path}[/green]")
        
        return sandbox
    
    def get_sandbox(self, skill_name: str) -> Optional[SkillSandbox]:
        """Get sandbox for a skill if it exists."""
        return self._sandboxes.get(skill_name)
    
    def install_dependencies(
        self, 
        skill_name: str, 
        requirements: List[str],
        requirements_file: Optional[Path] = None
    ) -> bool:
        """
        Install dependencies into a skill's sandbox.
        
        Args:
            skill_name: Name of the skill
            requirements: List of pip requirements strings (e.g., ["numpy>=1.0", "pandas"])
            requirements_file: Path to requirements.txt file (alternative to list)
            
        Returns:
            True if installation succeeded
        """
        sandbox = self.get_sandbox(skill_name)
        if not sandbox:
            console.print(f"[red]No sandbox found for '{skill_name}'[/red]")
            return False
        
        if not sandbox.pip_path.exists():
            console.print(f"[red]pip not found in sandbox: {sandbox.pip_path}[/red]")
            return False
        
        console.print(f"[cyan]Installing dependencies for {skill_name}...[/cyan]")
        
        cmd = [str(sandbox.pip_path), "install", "--quiet"]
        
        if requirements_file and requirements_file.exists():
            cmd.extend(["-r", str(requirements_file)])
        else:
            cmd.extend(requirements)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                console.print(f"[green]✅ Dependencies installed for {skill_name}[/green]")
                return True
            else:
                console.print(f"[red]Failed to install dependencies: {result.stderr}[/red]")
                return False
                
        except subprocess.TimeoutExpired:
            console.print(f"[red]Installation timed out for {skill_name}[/red]")
            return False
        except Exception as e:
            console.print(f"[red]Error installing dependencies: {e}[/red]")
            return False
    
    def run_in_sandbox(
        self, 
        skill_name: str, 
        command: List[str],
        cwd: Optional[Path] = None
    ) -> subprocess.CompletedProcess:
        """
        Run a command in a skill's sandbox environment.
        
        Args:
            skill_name: Name of the skill
            command: Command and arguments to run
            cwd: Working directory for the command
            
        Returns:
            CompletedProcess result
        """
        sandbox = self.get_sandbox(skill_name)
        if not sandbox:
            raise ValueError(f"No sandbox found for '{skill_name}'")
        
        # Set up environment to use sandbox's Python
        env = os.environ.copy()
        env["VIRTUAL_ENV"] = str(sandbox.venv_path)
        env["PATH"] = str(sandbox.venv_path / "bin") + ":" + env.get("PATH", "")
        
        # Run with sandbox's Python
        full_cmd = [str(sandbox.python_path)] + command
        
        return subprocess.run(
            full_cmd,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True
        )
    
    def list_sandboxes(self) -> List[SkillSandbox]:
        """List all sandboxes."""
        return list(self._sandboxes.values())
    
    def remove_sandbox(self, skill_name: str) -> bool:
        """
        Remove a skill's sandbox.
        
        Args:
            skill_name: Name of the skill
            
        Returns:
            True if sandbox was removed
        """
        sandbox = self._sandboxes.pop(skill_name, None)
        if not sandbox:
            return False
        
        try:
            shutil.rmtree(sandbox.venv_path)
            console.print(f"[green]✅ Removed sandbox for {skill_name}[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Error removing sandbox: {e}[/red]")
            return False
    
    def get_dependency_info(self, skill_name: str) -> Dict[str, str]:
        """
        Get installed packages and versions for a sandbox.
        
        Returns:
            Dict mapping package name to version string
        """
        sandbox = self.get_sandbox(skill_name)
        if not sandbox:
            return {}
        
        try:
            result = subprocess.run(
                [str(sandbox.pip_path), "list", "--format=freeze"],
                capture_output=True,
                text=True
            )
            
            deps = {}
            for line in result.stdout.strip().split("\n"):
                if "==" in line:
                    name, version = line.split("==", 1)
                    deps[name] = version
            
            return deps
            
        except Exception:
            return {}


# Global sandbox manager instance
_sandbox_manager: Optional[SandboxManager] = None


def get_sandbox_manager() -> SandboxManager:
    """Get or create the global SandboxManager instance."""
    global _sandbox_manager
    if _sandbox_manager is None:
        _sandbox_manager = SandboxManager()
    return _sandbox_manager