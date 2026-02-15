# SPDX-License-Identifier: Apache-2.0
from jcapy.core.plugins import CommandRegistry
import sys
import os

# Import commands
from jcapy.commands.frameworks import list_frameworks, harvest_framework, search_frameworks, delete_framework, merge_frameworks, apply_framework
from jcapy.commands.brain import select_persona, open_brain_vscode, run_brainstorm_wizard
from jcapy.commands.sync import sync_all_personas, push_all_personas
from jcapy.commands.project import init_project, deploy_project, map_project_patterns
from jcapy.commands.doctor import run_doctor
from jcapy.commands.edit import rapid_fix
from jcapy.commands.research import autonomous_explore
from jcapy.commands.install import run_install, setup_parser as setup_install_parser
from jcapy.commands.memory_cmd import run_recall, run_memorize, setup_recall, setup_memorize
from jcapy.commands.config_cmd import run_config, setup_config
from jcapy.commands.core_cmd import run_undo, setup_undo, run_suggest, run_tutorial, setup_tutorial, run_tui

from jcapy.ui.ux.safety import get_undo_stack
from jcapy.ui.ux.feedback import show_success, show_error
from jcapy.config import get_active_library_path, load_config

def register_core_commands(registry):
    """
    Register all built-in commands.
    This acts as the 'Standard Library' of JCapy.
    """
    # 1. Install (The Marketplace)
    registry.register(
        name="install",
        handler=run_install,
        description="Install a skill from a GitHub URL",
        setup_parser=setup_install_parser
    )

    # 2. Management
    registry.register(
        name="list",
        handler=lambda args: run_tui(args),
        description="List all harvested frameworks",
        aliases=["ls"]
    )

    # HARVEST
    def setup_harvest(parser):
        parser.add_argument("--doc", help="Path to existing documentation to parse")
        parser.add_argument("--auto", help="Path to file to automatically extract a skill from")
        parser.add_argument("doc_flag", nargs='?', help="Positional path to doc (optional)")

    def run_harvest(args):
        doc_arg = args.doc if args.doc else getattr(args, 'doc_flag', None)
        harvest_framework(doc_arg, auto_path=args.auto)

    registry.register("harvest", run_harvest, "Extract current code into a reusable skill", aliases=["new"], setup_parser=setup_harvest)

    # SEARCH
    def setup_search(parser):
        parser.add_argument("query", help="Keyword to search for")

    registry.register("search", lambda args: search_frameworks(args.query), "Search frameworks by content", setup_parser=setup_search)

    # OPEN (Code)
    registry.register("code", lambda args: open_brain_vscode(), "Open jcapy Brain in VS Code")

    # DELETE
    def setup_delete(parser):
        parser.add_argument("name", help="Name of the framework to delete")

    registry.register("delete", lambda args: delete_framework(args.name), "Delete a framework", aliases=["rm"], setup_parser=setup_delete)

    # MANAGE
    registry.register("manage", lambda args: run_tui(args), "Interactive TUI Manager", aliases=["tui"])

    # PERSONA
    def setup_persona(parser):
        parser.add_argument("name", nargs="?", help="Name of the persona to switch to")

    registry.register("persona", lambda args: select_persona(getattr(args, 'name', None)), "Switch Persona", aliases=["p"], setup_parser=setup_persona)

    # INIT
    registry.register("init", lambda args: init_project(), "Scaffold One-Army Project")

    # MERGE
    registry.register("merge", lambda args: merge_frameworks(), "Merge Skills into Blueprint")

    # DEPLOY
    registry.register("deploy", lambda args: deploy_project(), "Deploy Project")

    # APPLY
    def setup_apply(parser):
        parser.add_argument("name", help="Name of the framework to apply")
        parser.add_argument("--dry-run", action="store_true", help="Preview commands without running")

    registry.register("apply", lambda args: apply_framework(args.name, args.dry_run), "Apply Skill (Executable Knowledge)", setup_parser=setup_apply)

    # DOCTOR
    registry.register("doctor", lambda args: run_doctor(), "Check system health", aliases=["chk", "check"])

    # SYNC
    registry.register("sync", lambda args: sync_all_personas(), "Sync frameworks with remote library")

    # PUSH
    registry.register("push", lambda args: push_all_personas(), "Push frameworks to remote library")

    # BRAINSTORM
    registry.register("brainstorm", lambda args: run_brainstorm_wizard(), "AI Refactor & Optimization", aliases=["bs"])

    # SUGGEST
    registry.register("suggest", run_suggest, "Recommend next best actions")

    # MCP
    def run_mcp(args):
        from jcapy.mcp.server import run_mcp_server
        run_mcp_server()
    registry.register("mcp", run_mcp, "Start JCapy MCP Server (Stdio)")

    # UNDO
    registry.register("undo", run_undo, "Undo last destructive action", setup_parser=setup_undo)

    # RECALL
    registry.register("recall", run_recall, "Semantic Search (Vector Memory)", setup_parser=setup_recall)

    # MEMORIZE
    registry.register("memorize", run_memorize, "Ingest knowledge into Memory Bank", setup_parser=setup_memorize)

    # FIX
    def setup_fix(parser):
        parser.add_argument("file", help="Path to file to fix")
        parser.add_argument("instruction", help="Instruction for the fix")
        parser.add_argument("--diag", help="LSP diagnostic context (error messages)")

    registry.register("fix", lambda args: rapid_fix(args.file, args.instruction, diagnostics=args.diag), "Rapid tactical code fix", setup_parser=setup_fix)

    # EXPLORE
    def setup_explore(parser):
        parser.add_argument("topic", help="Topic to research")

    registry.register("explore", lambda args: autonomous_explore(args.topic), "Autonomous research & draft skill", setup_parser=setup_explore)

    # MAP
    def setup_map(parser):
        parser.add_argument("path", nargs="?", default=".", help="Project path to map")

    registry.register("map", lambda args: map_project_patterns(args.path), "Analyze project for harvesting candidates", setup_parser=setup_map)

    # TUTORIAL
    registry.register("tutorial", run_tutorial, "Interactive onboarding", setup_parser=setup_tutorial)

    # CONFIG
    registry.register("config", run_config, "Manage UX preferences and keys", setup_parser=setup_config)




