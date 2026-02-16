import os
import json
from dataclasses import dataclass
from typing import List

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
    """
    # In a real app, this would be a remote URL
    MOCK_REMOTE_URL = "https://raw.githubusercontent.com/jcapy/marketplace/main/items.json"

    @classmethod
    def get_available_items(cls) -> List[MarketplaceItemData]:
        # Mocking remote discovery
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
