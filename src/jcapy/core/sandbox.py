import os
import subprocess
import shutil
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class BaseSandbox(ABC):
    """
    Abstract interface for JCapy execution sandboxes (ASI02, 2.3).
    """
    @abstractmethod
    def run_command(self, command: str, workdir: Optional[str] = None) -> str:
        """Executes a command inside the sandbox."""
        pass

    @abstractmethod
    def upload_file(self, local_path: str, remote_path: str):
        """Copies a file into the sandbox."""
        pass

    @abstractmethod
    def download_file(self, remote_path: str, local_path: str):
        """Retrieves a file from the sandbox."""
        pass

class LocalSandbox(BaseSandbox):
    """
    Fallback sandbox that runs commands on the host machine.
    """
    def run_command(self, command: str, workdir: Optional[str] = None) -> str:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=workdir,
                executable="/bin/zsh"
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                raise RuntimeError(f"Command failed (Exit {result.returncode}): {result.stderr.strip()}")
        except Exception as e:
            raise RuntimeError(f"Local Execution Error: {str(e)}")

    def upload_file(self, local_path: str, remote_path: str):
        # On local, this is just a copy or no-op if paths are same
        if os.path.abspath(local_path) == os.path.abspath(remote_path):
            return
        shutil.copy2(local_path, remote_path)

    def download_file(self, remote_path: str, local_path: str):
        if os.path.abspath(local_path) == os.path.abspath(remote_path):
            return
        shutil.copy2(remote_path, local_path)

class DockerSandbox(BaseSandbox):
    """
    Isolated sandbox using Docker (Gap Analysis 2.3).
    """
    def __init__(self, image: str = "python:3.11-slim", container_name: str = "jcapy-sandbox"):
        self.image = image
        self.container_name = container_name
        self._ensure_image()

    def _ensure_image(self):
        # Check if docker is available and image exists
        try:
            subprocess.run(["docker", "--version"], capture_output=True, check=True)
        except:
            raise RuntimeError("Docker is not installed or available in PATH.")

    def run_command(self, command: str, workdir: Optional[str] = None) -> str:
        # Spin up a container, run the command, and remove it
        # In a real impl, we might keep a persistent container for the session
        docker_cmd = [
            "docker", "run", "--rm",
            "-v", f"{os.getcwd()}:/workspace",
            "-w", "/workspace",
            self.image,
            "sh", "-c", command
        ]

        try:
            result = subprocess.run(docker_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                raise RuntimeError(f"Docker Command failed (Exit {result.returncode}): {result.stderr.strip()}")
        except Exception as e:
            raise RuntimeError(f"Docker Sandbox Error: {str(e)}")

    def upload_file(self, local_path: str, remote_path: str):
        # Note: Docker run mounts the workspace, so this might be handled via volumes
        pass

    def download_file(self, remote_path: str, local_path: str):
        pass

def get_sandbox(sandbox_type: str = "local", **kwargs) -> BaseSandbox:
    if sandbox_type == "docker":
        return DockerSandbox(**kwargs)
    return LocalSandbox()
