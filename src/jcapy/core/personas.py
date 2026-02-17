# SPDX-License-Identifier: Apache-2.0
from typing import Dict, Any, Optional
from jcapy.core.base import CommandResult, ResultStatus

# ==========================================
# PERSONA DEFINITIONS
# ==========================================
PERSONAS = {
    "developer": {
        "description": "Full-stack development workflow (Default)",
        "commands_disabled": [],
        "dashboard_layout": {
            "left_col": ["FileExplorer", "MCP"],
            "center_col": ["Kanban"],
            "right_col": ["Marketplace"],
        },
        "theme": None,  # Keep current/default
    },
    "devops": {
        "description": "Infrastructure & deployment focus",
        "commands_disabled": ["brainstorm", "suggest", "fix", "explore"],
        "dashboard_layout": {
            "left_col": ["FileExplorer", "GitLog"],
            "center_col": ["Kanban"],
            "right_col": ["UsageTracker", "ProjectStatus"],
        },
        "theme": "midnight",
    },
    "writer": {
        "description": "Documentation & knowledge authoring",
        "commands_disabled": ["deploy", "init", "mcp", "install", "harvest"],
        "dashboard_layout": {
            "left_col": ["FileExplorer"],
            "center_col": ["Scratchpad"],
            "right_col": ["News"],
        },
        "theme": "dracula",
    },
    "minimal": {
        "description": "Lean mode — essential commands only",
        "commands_disabled": [
            "brainstorm", "suggest", "fix", "explore",
            "merge", "mcp", "news", "marketplace",
            "install", "harvest", "deploy"
        ],
        "dashboard_layout": {
            "left_col": ["FileExplorer"],
            "center_col": ["Kanban"],
            "right_col": [],
        },
        "theme": None,
    },
    "architect": {
        "description": "System architecture & technical oversight",
        "commands_disabled": ["writer", "blog", "draft"],
        "dashboard_layout": {
            "left_col": ["ProjectStatus", "MCP"],
            "center_col": ["Kanban"],
            "right_col": ["UsageTracker", "GitLog"],
        },
        "theme": "architect",
    },
}

def get_persona(name: str) -> Optional[Dict[str, Any]]:
    """Get persona definition by name (case-insensitive)."""
    return PERSONAS.get(name.lower())

def list_personas() -> Dict[str, str]:
    """Return dict of name -> description."""
    return {k: v["description"] for k, v in PERSONAS.items()}

def apply_persona(name: str, registry) -> CommandResult:
    """
    Apply a persona:
    1. Update `commands.disabled` in config (triggers plugin reload)
    2. Update `dashboard_layout` in config (triggers layout rebuild)
    3. Update `ux.theme` in config (triggers theme switch)
    4. Save `core.persona` as current
    """
    persona = get_persona(name)
    if not persona:
        return CommandResult(
            status=ResultStatus.FAILURE,
            message=f"Unknown persona: '{name}'. Available: {', '.join(PERSONAS.keys())}"
        )

    from jcapy.config import CONFIG_MANAGER

    # 1. Update Disabled Commands
    disabled_list = ",".join(persona["commands_disabled"])
    CONFIG_MANAGER.set("commands.disabled", disabled_list)

    # 2. Update Dashboard Layout
    if "dashboard_layout" in persona:
        CONFIG_MANAGER.set("dashboard_layout", persona["dashboard_layout"])

    # 3. Update Theme (if specified)
    if persona["theme"]:
        CONFIG_MANAGER.set("ux.theme", persona["theme"])

    # 4. Set Current Persona
    CONFIG_MANAGER.set("core.persona", name.lower())

    return CommandResult(
        status=ResultStatus.SUCCESS,
        message=f"Switched to '{name}' persona: {persona['description']}"
    )
