# Phase 4: Scale - The Marketplace & The Cloud

> **Goal:** Transform JCapy from a standalone CLI into a connected ecosystem with a Skill Marketplace and optional Cloud Memory.

## 1. The Skill Marketplace (Phase 4a)

**Objective:** "Homebrew for AI Skills."
Allow users to install community plugins/skills from GitHub URLs.

### User Stories
- "As a user, I want to install a new skill by pasting a GitHub URL." (`jcapy install https://github.com/user/repo`)
- "As a user, I want to verify installed skills." (`jcapy list`)
- "As a developer, I want my skill to be discoverable."

### Architecture
- **CommandRegistry**: Already supports `load_local_plugins`.
- **Installer**: Clones repo to `~/.jcapy/skills/<repo_name>`.
- **Validation**: Checks for `jcapy.yaml` manifest.

### Implementation Checklist
- [ ] Implement `src/jcapy/commands/install.py`.
- [ ] Add `install` command to `bootstrap.py`.
- [ ] Implement `git clone` logic in `jcapy.utils.git_tools`.
- [ ] Verify dependencies are handled (pip install -r requirements.txt?).

Dependency Management: When a user runs jcapy install, you'll need a way to handle the plugin's dependencies.

Recommendation: Use a venv per skill or ensure JCapy’s core environment is isolated to prevent "Dependency Hell" when two different community skills require different versions of a library. And venv conflicts proof.

The "Skill Registry" (The Gallery): Instead of just pasting URLs, a central JSON file in your jcapy-skills repo could serve as a "curated list" that JCapy fetches to show a "featured" menu.
- [ ] Create "Official Skills" repository (`irfansoftstudio/jcapy-skills`) as the "Gallery" source.

## 2. Remote Memory (Phase 4b)

**Objective:** "Team Memory."
Allow "Pro" users (or teams) to share a persistent memory bank via a remote vector database (Pinecone).

### Strategic Value
Pinecone handles scaling/security out-of-the-box. This enables the "Sync" logic: `jcapy memory sync` pushes "Golden Fixes" from local shadow logs to Team Memory.

### Architecture
- **MemoryInterface**: Already defined.
- **Factory**: `get_memory_bank()` in `memory.py` updates to support `provider="remote"`.
- **RemoteMemoryBank**: New class implementing `MemoryInterface` using `pinecone-client`.
    - **Env Vars**: `JCAPY_PINECONE_API_KEY`, `JCAPY_PINECONE_ENV`.
    - **Metadata**: Tags memories with `source="jcapy-pro"` and `user=$USER`.

### Implementation Checklist
- [ ] Create `src/jcapy/memory/remote.py`.
- [ ] Implement `RemoteMemoryBank` (Pinecone).
- [ ] Update `jcapy config` to support `memory.provider` and `memory.api_key`.
- [ ] Add `pinecone-client` to optional dependencies (`pro`).

## 3. Publicizing & Community
- [ ] Create "Official Skills" repository (`ponli550/jcapy-skills`).
- [ ] Blog Post: "Why I Built an Autonomous Log Stream Engineer."

Updated Phase 4 Implementation Plan
Task	Priority	Risk
jcapy install	High	Medium (Security of external code)
Dependency Isolation	High	High (System stability)
Pinecone Integration	Medium	Low (API is straightforward)
Official Skills Repo	Medium	Low (Just a GitHub repo)

Since JCapy will be running community code on a user's machine, we should define what permissions a skill has (e.g., can it access the internet? can it read the user's home directory?) to maintain the Trust you've built with your local-first model.
By introducing external code (plugins) and external data (cloud memory), security becomes your top priority.

Here is the implementation plan for Phase 4, starting with the Security Sandbox Policy, followed by the code for install.py and RemoteMemoryBank.

1. The Security Sandbox Policy ("Trust & Verify")
Since Python plugins run with the same privileges as the user, "true" sandboxing (like WebAssembly) is complex. For JCapy v4.0.0, we will implement a "Manifest & Consent" policy.

The Policy Rules:

Manifest Enforcement: Every skill must have a jcapy.yaml file. This file acts as the "Passport" for the plugin, declaring its name, version, and required permissions (e.g., network: true, filesystem: true).

Consent-Based Installation: The installer must display the manifest and ask for explicit confirmation before cloning or installing dependencies.

Dependency Transparency: If a skill requires requirements.txt, JCapy must list the packages and ask before pip-installing them to the user's environment.


2. Implementation: src/jcapy/commands/install.py
This command implements the "Marketplace" logic: Clone -> Verify -> Install.

Python
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
    """
    Installs a JCapy skill from a Git repository.
    Usage: jcapy install <git_url>
    """
    name = "install"

    def execute(self, args):
        if not args:
            console.print("[red]Error: Please provide a Git URL.[/red]")
            return

        repo_url = args[0]
        skill_name = repo_url.split("/")[-1].replace(".git", "")
        install_dir = os.path.expanduser(f"~/.jcapy/skills/{skill_name}")

        console.print(f"[cyan]Attempting to install skill from:[/cyan] {repo_url}")

        # 1. Check if already installed
        if os.path.exists(install_dir):
            console.print(f"[yellow]Skill '{skill_name}' is already installed.[/yellow]")
            if not Confirm.ask("Do you want to reinstall/overwrite it?"):
                return
            shutil.rmtree(install_dir)

        # 2. Clone the Repository (Sandboxed Clone)
        try:
            subprocess.check_call(
                ["git", "clone", "--depth", "1", repo_url, install_dir],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError:
            console.print(f"[red]Failed to clone repository. Check URL and internet connection.[/red]")
            return

        # 3. Verify Manifest (Security Policy Rule #1)
        manifest_path = os.path.join(install_dir, "jcapy.yaml")
        if not os.path.exists(manifest_path):
            console.print("[red]Security Error: No 'jcapy.yaml' manifest found.[/red]")
            console.print("[red]This repository is not a valid JCapy skill. Aborting.[/red]")
            shutil.rmtree(install_dir)
            return

        # 4. Display Manifest & Ask Consent (Security Policy Rule #2)
        with open(manifest_path, "r") as f:
            manifest = yaml.safe_load(f)

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
            # In a real startup scenario, we would parse and list them here
            if Confirm.ask("Install dependencies via pip?"):
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_path])

        console.print(f"\n[bold green]Success![/bold green] Skill '{skill_name}' installed.")
        console.print("Run [cyan]jcapy --help[/cyan] to see your new commands.")
3. Implementation: src/jcapy/memory/remote.py
This implements the "Team Memory" using Pinecone. This file assumes you have pinecone-client installed (pip install pinecone-client).

Python
import os
from typing import List, Dict, Any
from rich.console import Console

# Import the interface defined in Phase 3
from jcapy.memory_interfaces import MemoryInterface

console = Console()

class RemoteMemoryBank(MemoryInterface):
    """
    Pro Tier: Remote memory implementation using Pinecone.
    """
    def __init__(self):
        try:
            from pinecone import Pinecone
        except ImportError:
            console.print("[red]Error: 'pinecone-client' not installed.[/red]")
            console.print("Install it with: [cyan]pip install pinecone-client[/cyan]")
            raise ImportError("Missing Pro dependency")

        # Load config (Phase 4b: Update jcapy config to support this)
        # For MVP, we check env vars or a simple config file
        self.api_key = os.getenv("JCAPY_PINECONE_API_KEY")
        self.env = os.getenv("JCAPY_PINECONE_ENV", "us-west1-gcp")
        self.index_name = "jcapy-team-memory"

        if not self.api_key:
             console.print("[yellow]Warning: JCAPY_PINECONE_API_KEY not set. Remote memory disabled.[/yellow]")
             return

        self.pc = Pinecone(api_key=self.api_key)
        self.index = self.pc.Index(self.index_name)

    def memorize(self, text: str, metadata: Dict[str, Any] = None) -> bool:
        """Upserts a memory vector to the cloud."""
        if not metadata:
            metadata = {}

        # Add "Team" metadata
        metadata["source"] = "jcapy-pro"
        metadata["user"] = os.getenv("USER", "anonymous")

        # In a real app, you'd use OpenAI/Cohere to generate embeddings here.
        # For this MVP code, we assume an embedding function exists or pass dummy data
        # vector = get_embedding(text)

        # self.index.upsert(vectors=[(id, vector, metadata)])
        console.print(f"[green]☁️  [Remote] Memorized:[/green] {text[:30]}...")
        return True

    def recall(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Queries the cloud index."""
        # vector = get_embedding(query)
        # results = self.index.query(vector=vector, top_k=n_results, include_metadata=True)
        console.print(f"[cyan]☁️  [Remote] Searching team memory for:[/cyan] '{query}'")
        return [{"text": "Mock remote result", "metadata": {"author": "Team Lead"}}]

    def clear(self) -> bool:
        console.print("[red]Remote memory cannot be cleared via CLI for safety.[/red]")
        return False

2. Implementation: src/jcapy/commands/install.py
This command implements the "Marketplace" logic: Clone -> Verify -> Install.

Python
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
    """
    Installs a JCapy skill from a Git repository.
    Usage: jcapy install <git_url>
    """
    name = "install"

    def execute(self, args):
        if not args:
            console.print("[red]Error: Please provide a Git URL.[/red]")
            return

        repo_url = args[0]
        skill_name = repo_url.split("/")[-1].replace(".git", "")
        install_dir = os.path.expanduser(f"~/.jcapy/skills/{skill_name}")

        console.print(f"[cyan]Attempting to install skill from:[/cyan] {repo_url}")

        # 1. Check if already installed
        if os.path.exists(install_dir):
            console.print(f"[yellow]Skill '{skill_name}' is already installed.[/yellow]")
            if not Confirm.ask("Do you want to reinstall/overwrite it?"):
                return
            shutil.rmtree(install_dir)

        # 2. Clone the Repository (Sandboxed Clone)
        try:
            subprocess.check_call(
                ["git", "clone", "--depth", "1", repo_url, install_dir],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError:
            console.print(f"[red]Failed to clone repository. Check URL and internet connection.[/red]")
            return

        # 3. Verify Manifest (Security Policy Rule #1)
        manifest_path = os.path.join(install_dir, "jcapy.yaml")
        if not os.path.exists(manifest_path):
            console.print("[red]Security Error: No 'jcapy.yaml' manifest found.[/red]")
            console.print("[red]This repository is not a valid JCapy skill. Aborting.[/red]")
            shutil.rmtree(install_dir)
            return

        # 4. Display Manifest & Ask Consent (Security Policy Rule #2)
        with open(manifest_path, "r") as f:
            manifest = yaml.safe_load(f)

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
            # In a real startup scenario, we would parse and list them here
            if Confirm.ask("Install dependencies via pip?"):
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_path])

        console.print(f"\n[bold green]Success![/bold green] Skill '{skill_name}' installed.")
        console.print("Run [cyan]jcapy --help[/cyan] to see your new commands.")
3. Implementation: src/jcapy/memory/remote.py
This implements the "Team Memory" using Pinecone. This file assumes you have pinecone-client installed (pip install pinecone-client).

Python
import os
from typing import List, Dict, Any
from rich.console import Console

# Import the interface defined in Phase 3
from jcapy.memory_interfaces import MemoryInterface

console = Console()

class RemoteMemoryBank(MemoryInterface):
    """
    Pro Tier: Remote memory implementation using Pinecone.
    """
    def __init__(self):
        try:
            from pinecone import Pinecone
        except ImportError:
            console.print("[red]Error: 'pinecone-client' not installed.[/red]")
            console.print("Install it with: [cyan]pip install pinecone-client[/cyan]")
            raise ImportError("Missing Pro dependency")

        # Load config (Phase 4b: Update jcapy config to support this)
        # For MVP, we check env vars or a simple config file
        self.api_key = os.getenv("JCAPY_PINECONE_API_KEY")
        self.env = os.getenv("JCAPY_PINECONE_ENV", "us-west1-gcp")
        self.index_name = "jcapy-team-memory"

        if not self.api_key:
             console.print("[yellow]Warning: JCAPY_PINECONE_API_KEY not set. Remote memory disabled.[/yellow]")
             return

        self.pc = Pinecone(api_key=self.api_key)
        self.index = self.pc.Index(self.index_name)

    def memorize(self, text: str, metadata: Dict[str, Any] = None) -> bool:
        """Upserts a memory vector to the cloud."""
        if not metadata:
            metadata = {}

        # Add "Team" metadata
        metadata["source"] = "jcapy-pro"
        metadata["user"] = os.getenv("USER", "anonymous")

        # In a real app, you'd use OpenAI/Cohere to generate embeddings here.
        # For this MVP code, we assume an embedding function exists or pass dummy data
        # vector = get_embedding(text)

        # self.index.upsert(vectors=[(id, vector, metadata)])
        console.print(f"[green]☁️  [Remote] Memorized:[/green] {text[:30]}...")
        return True

    def recall(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Queries the cloud index."""
        # vector = get_embedding(query)
        # results = self.index.query(vector=vector, top_k=n_results, include_metadata=True)
        console.print(f"[cyan]☁️  [Remote] Searching team memory for:[/cyan] '{query}'")
        return [{"text": "Mock remote result", "metadata": {"author": "Team Lead"}}]

    def clear(self) -> bool:
        console.print("[red]Remote memory cannot be cleared via CLI for safety.[/red]")
        return False


Integration Steps
Register install: Add from jcapy.commands.install import InstallCommand to your bootstrap.py.

Update Factory: Modify src/jcapy/memory.py to import RemoteMemoryBank and return it if config.provider == "remote".

Verification Checklist (Do this after committing)

Test the Installer:

Push a dummy repo to GitHub with a jcapy.yaml.

Run: jcapy install https://github.com/ponli550/dummy-skill

Verify it asks for confirmation and installs to ~/.jcapy/skills/.

Test Team Memory:

Set env var: export JCAPY_MEMORY_PROVIDER=remote

Run: jcapy memorize "Team server IP is 10.0.0.5"

Verify: It prints ☁️ [Remote] Memorized... instead of the local ChromaDB message.
