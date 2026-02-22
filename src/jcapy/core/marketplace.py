# SPDX-License-Identifier: Apache-2.0
import os
import json
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import List, Optional
from rich.console import Console

console = Console()

@dataclass
class MarketplaceItemData:
    name: str
    description: str
    git_url: str
    type: str  # 'skill', 'widget', 'both'
    installed: bool = False

class MarketplaceService:
    """
    Service for discovering and managing JCapy extensions.
    Fetches from remote registry with local fallback.
    """
    # Remote registry URL (GitHub raw)
    REMOTE_REGISTRY_URL = "https://raw.githubusercontent.com/ponli550/jcapy-skills/main/registry.json"
    
    # Local fallback path
    LOCAL_REGISTRY_PATH = os.path.expanduser("~/.jcapy/registry.json")
    
    # GitHub repo base URL for skills
    GITHUB_BASE = "https://github.com/ponli550/jcapy-skills"

    @classmethod
    def fetch_remote_registry(cls) -> Optional[dict]:
        """Fetch registry from remote URL with timeout."""
        try:
            req = urllib.request.Request(
                cls.REMOTE_REGISTRY_URL,
                headers={'User-Agent': 'JCapy/4.1'}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                return json.loads(response.read().decode())
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
            console.print(f"[dim]Could not fetch remote registry: {e}[/dim]")
            return None

    @classmethod
    def load_local_registry(cls) -> Optional[dict]:
        """Load cached registry from local filesystem."""
        try:
            if os.path.exists(cls.LOCAL_REGISTRY_PATH):
                with open(cls.LOCAL_REGISTRY_PATH, 'r') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
        return None

    @classmethod
    def save_local_registry(cls, data: dict) -> None:
        """Cache registry locally for offline use."""
        try:
            os.makedirs(os.path.dirname(cls.LOCAL_REGISTRY_PATH), exist_ok=True)
            with open(cls.LOCAL_REGISTRY_PATH, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            console.print(f"[dim]Could not cache registry: {e}[/dim]")

    @classmethod
    def get_available_items(cls) -> List[MarketplaceItemData]:
        """Get available skills from registry (remote first, local fallback, then mock)."""
        # Try remote first
        registry_data = cls.fetch_remote_registry()
        
        if registry_data:
            # Cache it for offline use
            cls.save_local_registry(registry_data)
        else:
            # Try local cache
            registry_data = cls.load_local_registry()
        
        if registry_data and 'skills' in registry_data:
            return cls._parse_registry(registry_data)
        
        # Fallback to mock data if no registry available
        return cls._get_mock_items()

    @classmethod
    def _parse_registry(cls, data: dict) -> List[MarketplaceItemData]:
        """Parse registry JSON into MarketplaceItemData objects."""
        items = []
        install_base = os.path.expanduser("~/.jcapy/skills")
        
        for skill in data.get('skills', []):
            name = skill.get('name', 'Unknown')
            skill_path = skill.get('path', f'skills/{name}')
            
            # Construct git URL
            git_url = f"{cls.GITHUB_BASE}/tree/main/{skill_path}"
            
            item = MarketplaceItemData(
                name=name,
                description=skill.get('description', 'No description'),
                git_url=git_url,
                type=skill.get('type', 'skill'),
                installed=False
            )
            
            # Check if installed
            skill_install_dir = os.path.join(install_base, name)
            if os.path.exists(skill_install_dir):
                item.installed = True
            
            items.append(item)
        
        return items

    @classmethod
    def _get_mock_items(cls) -> List[MarketplaceItemData]:
        """Fallback mock items when registry unavailable."""
        items = [
            MarketplaceItemData(
                name="Git Deep Dive",
                description="Advanced git history visualization and diffing.",
                git_url="https://github.com/jcapy/skill-git-deep-dive",
                type="both"
            ),
            MarketplaceItemData(
                name="Spotify Controller",
                description="Control your music directly from the dashboard.",
                git_url="https://github.com/jcapy/skill-spotify",
                type="widget"
            ),
            MarketplaceItemData(
                name="Network Monitor",
                description="Live traffic and latency visualization.",
                git_url="https://github.com/jcapy/skill-netmon",
                type="widget"
            ),
            MarketplaceItemData(
                name="Supabase Explorer",
                description="Query your vector DB directly from the TUI.",
                git_url="https://github.com/jcapy/skill-supabase-explorer",
                type="both"
            )
        ]

        # Check local installation status
        install_base = os.path.expanduser("~/.jcapy/skills")
        for item in items:
            skill_name = item.git_url.rstrip("/").split("/")[-1]
            if skill_name.endswith(".git"):
                skill_name = skill_name[:-4]

            if os.path.exists(os.path.join(install_base, skill_name)):
                item.installed = True

        return items

    @classmethod
    def search(cls, query: str) -> List[MarketplaceItemData]:
        """Search available skills by name or description."""
        items = cls.get_available_items()
        query_lower = query.lower()
        
        return [
            item for item in items
            if query_lower in item.name.lower() or query_lower in item.description.lower()
        ]

    @classmethod
    def get_installed_skills(cls) -> List[str]:
        """List all installed skill names."""
        install_base = os.path.expanduser("~/.jcapy/skills")
        if not os.path.exists(install_base):
            return []
        
        installed = []
        for name in os.listdir(install_base):
            skill_dir = os.path.join(install_base, name)
            manifest = os.path.join(skill_dir, "jcapy.yaml")
            if os.path.isdir(skill_dir) and os.path.exists(manifest):
                installed.append(name)
        
        return installed