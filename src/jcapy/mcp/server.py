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
    # Search in 'skills/' subdirectory as per JCapy standard
    skills_root = os.path.join(lib_path, "skills")
    search_path = skills_root if os.path.exists(skills_root) else lib_path

    for root, dirs, files in os.walk(search_path):
        for f in files:
            if f.endswith(".md") and not f.startswith("."):
                # Return relative path from search_path for better discovery
                rel_path = os.path.relpath(os.path.join(root, f), search_path)
                skills.append(rel_path.replace(".md", ""))

    return "\n".join(skills) if skills else "No skills found."

@mcp.tool()
def read_skill(name: str) -> str:
    """Read the full content of a specific skill by name or path."""
    lib_path = get_active_library_path()
    skills_root = os.path.join(lib_path, "skills")
    search_path = skills_root if os.path.exists(skills_root) else lib_path

    # Try exact path first
    exact_path = os.path.join(search_path, f"{name}.md")
    if os.path.exists(exact_path):
        with open(exact_path, 'r') as file:
            return file.read()

    # Search recursively
    for root, dirs, files in os.walk(search_path):
        for f in files:
            if f == name or f == f"{name}.md":
                with open(os.path.join(root, f), 'r') as file:
                    return file.read()
    return f"Skill '{name}' not found."

@mcp.tool()
def apply_skill(name: str, dry_run: bool = True) -> str:
    """Apply a skill (execute its bash blocks) non-interactively."""
    try:
        # Pass interactive=False to avoid hanging on stdin prompts
        apply_framework(name, dry_run=dry_run, interactive=False)
        return f"Successfully processed skill '{name}' (DryRun: {dry_run})"
    except Exception as e:
        return f"Error applying skill: {e}"

@mcp.tool()
def brainstorm(file_content: str, instruction: str) -> str:
    """Refactor code into a JCapy skill draft based on instructions using AI."""
    from jcapy.commands.brain import get_brainstorm_prompt
    from jcapy.utils.ai import call_ai_agent

    system_prompt = get_brainstorm_prompt()
    full_prompt = f"{system_prompt}\n\nUser Instruction: {instruction}\n\n--- TARGET CODE ---\n{file_content}"

    # Try all configured providers
    for provider in ['gemini', 'openai', 'deepseek']:
        result, err = call_ai_agent(full_prompt, provider=provider)
        if result:
            return result

    return f"Brainstorming failed. Error: {err or 'No AI keys configured.'}"

def run_mcp_server():
    """Entry point to run the JCapy MCP server."""
    mcp.run(transport="stdio")
