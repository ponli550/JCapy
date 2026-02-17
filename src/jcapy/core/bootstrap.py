# SPDX-License-Identifier: Apache-2.0
from jcapy.core.plugins import CommandRegistry
import sys
import os

# Import commands
from jcapy.commands.frameworks import list_frameworks, harvest_framework, search_frameworks, delete_framework, merge_frameworks, apply_framework
from jcapy.commands.brain import select_persona, open_brain_vscode, run_brainstorm_wizard
from jcapy.commands.sync import sync_all_personas, push_all_personas
from jcapy.commands.project import init_project, deploy_project, map_project_patterns
from jcapy.commands.install import InstallCommand
from jcapy.commands.manage import ManageCommand
from jcapy.commands.core import MemorizeCommand, RecallCommand, ConfigCommand
from jcapy.commands.doctor import DoctorCommand
from jcapy.commands.core_cmd import run_undo, setup_undo, run_suggest, run_tutorial, setup_tutorial, run_tui
from jcapy.commands.theme import ThemeCommand
from jcapy.commands.grep import GrepCommand
from jcapy.commands.edit import EditCommand
from jcapy.ui.ux.safety import get_undo_stack
from jcapy.ui.ux.feedback import show_success, show_error
from jcapy.config import get_active_library_path, load_config


def register_core_commands(registry):
    """
    Register all built-in commands.
    This acts as the 'Standard Library' of JCapy.

    Commands are organized into categories:
    ─────────────────────────────────────────────
    🏗️  PROJECT LIFECYCLE    init, deploy, map
    📦  SKILL LIBRARY        list, harvest, search, delete, merge, apply, install
    🧠  KNOWLEDGE & MEMORY   memorize, recall, persona, brain, ask
    🩺  DIAGNOSTICS & CONFIG  doctor, config, theme, manage, undo
    🤖  AI-POWERED           brainstorm, suggest, fix, explore
    🔌  INFRASTRUCTURE       tui, mcp, sync, push, code, tutorial
    ─────────────────────────────────────────────

    Interactive commands (suspend TUI for raw terminal I/O):
      init, deploy, harvest, persona, tutorial, brainstorm, tui, install, apply
    """

    # ══════════════════════════════════════════
    # 🏗️  PROJECT LIFECYCLE
    # ══════════════════════════════════════════

    def setup_init(parser):
        parser.add_argument("--grade", choices=["A", "B", "C"], help="Project Grade (Headless)")

    registry.register("init", lambda args: init_project(grade=getattr(args, 'grade', None)),
                      "Scaffold One-Army Project", setup_parser=setup_init, interactive=True)

    registry.register("deploy", lambda args: deploy_project(),
                      "Deploy Project", interactive=True)

    def setup_map(parser):
        parser.add_argument("path", nargs="?", default=".", help="Project path to map")

    registry.register("map", lambda args: map_project_patterns(args.path),
                      "Analyze project for harvesting candidates", setup_parser=setup_map)

    # ══════════════════════════════════════════
    # 📦  SKILL LIBRARY
    # ══════════════════════════════════════════

    registry.register(
        name="list",
        handler=lambda args: list_frameworks(),
        description="List all harvested frameworks",
        aliases=["ls"]
    )

    def setup_harvest(parser):
        parser.add_argument("--doc", help="Document path to harvest")
        parser.add_argument("--auto", help="Auto-harvest from code file")
        parser.add_argument("--name", help="Framework Name")
        parser.add_argument("--desc", help="Framework Description")
        parser.add_argument("--grade", choices=["A", "B", "C"], help="Framework Grade")
        parser.add_argument("--yes", action="store_true", help="Skip confirmation prompts (Headless Mode)")
        parser.add_argument("--force", action="store_true", help="Force overwrite existing framework")

    registry.register("harvest", lambda args: harvest_framework(
        doc_path=getattr(args, 'doc', None),
        auto_path=getattr(args, 'auto', None),
        name=getattr(args, 'name', None),
        description=getattr(args, 'desc', None),
        grade=getattr(args, 'grade', None),
        confirm=getattr(args, 'yes', False),
        force=getattr(args, 'force', False)
    ), "Create a new Skill (Interactive/Headless)", aliases=["new"], setup_parser=setup_harvest, interactive=True)

    def setup_search(parser):
        parser.add_argument("query", help="Keyword to search for")

    registry.register("search", lambda args: search_frameworks(args.query),
                      "Search frameworks by content", setup_parser=setup_search)

    def setup_delete(parser):
        parser.add_argument("name", help="Name of the framework to delete")

    registry.register("delete", lambda args: delete_framework(args.name),
                      "Delete a framework", aliases=["rm"], setup_parser=setup_delete)

    registry.register("merge", lambda args: merge_frameworks(),
                      "Merge Skills into Blueprint")

    def setup_apply(parser):
        parser.add_argument("name", help="Name of the framework to apply")
        parser.add_argument("--dry-run", action="store_true", help="Preview commands without running")

    registry.register("apply", lambda args: apply_framework(args.name, args.dry_run),
                      "Apply Skill (Executable Knowledge)", setup_parser=setup_apply, interactive=True)

    registry.register(InstallCommand(), interactive=True)

    # ══════════════════════════════════════════
    # 🧠  KNOWLEDGE & MEMORY
    # ══════════════════════════════════════════

    registry.register(MemorizeCommand())
    registry.register(RecallCommand())

    def setup_persona(parser):
        parser.add_argument("name", nargs="?", help="Name of the persona to switch to")

    registry.register("persona", lambda args: select_persona(getattr(args, 'name', None)),
                      "Switch Persona", aliases=["p"], setup_parser=setup_persona, interactive=True)

    from jcapy.commands import brain_cmd

    def setup_brain(parser):
        subs = parser.add_subparsers(dest="subcommand", help="Brain actions")
        link = subs.add_parser("link", help="Link a local directory as Brain")
        link.add_argument("path", help="Path to Rowboat/Obsidian vault")
        ask = subs.add_parser("ask", help="Ask the Brain a question")
        ask.add_argument("question", nargs="+", help="Question to ask")

    registry.register("brain", brain_cmd.run_brain,
                      "Manage Knowledge Graph (Rowboat)", setup_parser=setup_brain)

    def setup_ask(parser):
        parser.add_argument("question", nargs="+", help="Question")

    registry.register("ask", lambda args: brain_cmd.ask_brain(args),
                      "Ask the Brain (Shortcut)", setup_parser=setup_ask)

    # ══════════════════════════════════════════
    # 🩺  DIAGNOSTICS & CONFIG
    # ══════════════════════════════════════════

    registry.register(DoctorCommand())
    registry.register(ConfigCommand())
    registry.register(ThemeCommand())
    registry.register(ManageCommand())
    registry.register("undo", run_undo, "Undo last destructive action", setup_parser=setup_undo)

    # ══════════════════════════════════════════
    # 🤖  AI-POWERED
    # ══════════════════════════════════════════

    registry.register("brainstorm", lambda args: run_brainstorm_wizard(),
                      "AI Refactor & Optimization", aliases=["bs"], interactive=True)

    registry.register("suggest", run_suggest, "Recommend next best actions")

    def setup_fix(parser):
        parser.add_argument("file", help="Path to file to fix")
        parser.add_argument("instruction", help="Instruction for the fix")
        parser.add_argument("--diag", help="LSP diagnostic context (error messages)")

    registry.register("fix", lambda args: rapid_fix(args.file, args.instruction, diagnostics=args.diag),
                      "Rapid tactical code fix", setup_parser=setup_fix)

    def setup_explore(parser):
        parser.add_argument("topic", help="Topic to research")

    registry.register("explore", lambda args: autonomous_explore(args.topic),
                      "Autonomous research & draft skill", setup_parser=setup_explore)

    # ══════════════════════════════════════════
    # 🔌  INFRASTRUCTURE
    # ══════════════════════════════════════════

    registry.register("tui", run_tui, "Launch Interactive TUI Dashboard", interactive=True)

    def run_mcp(args):
        from jcapy.mcp.server import run_mcp_server
        run_mcp_server()

    registry.register("mcp", run_mcp, "Start JCapy MCP Server (Stdio)")

    registry.register(sync_all_personas)
    registry.register(push_all_personas)

    registry.register("code", lambda args: open_brain_vscode(),
                      "Open jcapy Brain in VS Code")

    registry.register("tutorial", run_tutorial,
                      "Interactive onboarding", setup_parser=setup_tutorial, interactive=True)

    registry.register(GrepCommand())
    registry.register(EditCommand())


    # ══════════════════════════════════════════
    # 🔧  CONFIG OVERRIDES
    # ══════════════════════════════════════════
    # 1. Interactive Commands (TUI vs Raw)
    registry.apply_config_overrides()

    # 2. Disabled Commands (Plugin Filter)
    registry.apply_disabled_from_config()

def _switch_persona(args):
    """Handler for 'persona' command."""
    from jcapy.core.personas import apply_persona, list_personas, PERSONAS
    from jcapy.core.plugins import get_registry

    if not args._tokens:
        # List available
        print("\n👥  Available Personas:\n")
        current = _get_current_persona()
        for name, data in PERSONAS.items():
            marker = "●" if name == current else "○"
            print(f"  {marker} [bold cyan]{name:<12}[/] {data['description']}")
        print("\nusage: persona <name>\n")
        return

    name = args._tokens[0].lower()
    result = apply_persona(name, get_registry())
    print(f"\n{result.message}\n")

def _get_current_persona():
    from jcapy.config import CONFIG_MANAGER
    return CONFIG_MANAGER.get("core.persona", "developer")
