import os
import sys
from mcp.server.fastmcp import FastMCP
from jcapy.config import get_active_library_path
from jcapy.commands.frameworks import apply_framework

# Initialize FastMCP Server
mcp = FastMCP("JCapy")

@mcp.tool()
def list_skills() -> str:
    """List all available skills (frameworks) in the active JCapy library."""
    lib_path = get_active_library_path()
    if not os.path.exists(lib_path):
        return "No library found."

    skills = []
    for root, dirs, files in os.walk(lib_path):
        for f in files:
            if f.endswith(".md") and not f.startswith("."):
                skills.append(f.replace(".md", ""))

    return "\n".join(skills) if skills else "No skills found."

@mcp.tool()
def read_skill(name: str) -> str:
    """Read the full content of a specific skill by name."""
    lib_path = get_active_library_path()
    for root, dirs, files in os.walk(lib_path):
        for f in files:
            if f == name or f == f"{name}.md":
                with open(os.path.join(root, f), 'r') as file:
                    return file.read()
    return f"Skill '{name}' not found."

@mcp.tool()
def apply_skill(name: str, dry_run: bool = True) -> str:
    """Apply a skill (execute its bash blocks)."""
    # Redirect stdout to capture output if possible,
    # but apply_framework uses its own console.
    # For MVP, we'll run it and return success/fail message.
    try:
        # Note: apply_framework might be interactive.
        # In MCP mode, we should ideally have a non-interactive version.
        # However, for now, we'll wrap it.
        apply_framework(name, dry_run=dry_run)
        return f"Successfully processed skill '{name}' (DryRun: {dry_run})"
    except Exception as e:
        return f"Error applying skill: {e}"

@mcp.tool()
def brainstorm(file_content: str, instruction: str) -> str:
    """Refactor code into a JCapy skill draft based on instructions."""
    from jcapy.commands.brain import get_brainstorm_prompt
    # This is a simplified version of the logic in brain.py
    # Ideally, we call the AI here.
    prompt = get_brainstorm_prompt()
    # In a real implementation, we would call an LLM here.
    # For now, we'll return a formatted response.
    return f"REFRACTORING LOGIC PENDING\nInstruction: {instruction}\nContent Length: {len(file_content)}"

def run_mcp_server():
    """Entry point to run the JCapy MCP server."""
    mcp.run(transport="stdio")
