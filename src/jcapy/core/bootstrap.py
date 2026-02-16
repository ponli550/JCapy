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
from jcapy.commands.core import MemorizeCommand, RecallCommand, ConfigCommand
from jcapy.commands.doctor import DoctorCommand
from jcapy.commands.core_cmd import run_undo, setup_undo, run_suggest, run_tutorial, setup_tutorial, run_tui
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
    # 1. Install (The Marketplace)
    registry.register(InstallCommand(), interactive=True)

    # 2. Management
    registry.register(
        name="list",
        handler=lambda args: list_frameworks(),
        description="List all harvested frameworks",
        aliases=["ls"]
    )

    # HARVEST
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

    # SEARCH
    def setup_search(parser):
        parser.add_argument("query", help="Keyword to search for")

    registry.register("search", lambda args: search_frameworks(args.query), "Search frameworks by content", setup_parser=setup_search)

    # OPEN (Code)
    registry.register("code", lambda args: open_brain_vscode(), "Open jcapy Brain in VS Code")

    # DELETE
    def setup_delete(parser):
        parser.add_argument("name", help="Name of the framework to delete")

    registry.register("delete", lambda args: delete_framework(args.name), "Delete a framework", aliases=["rm"], setup_parser=setup_delete, interactive=True)

    # MANAGE
    registry.register("manage", lambda args: run_tui(args), "Interactive TUI Manager", aliases=["tui"], interactive=True)

    # PERSONA
    def setup_persona(parser):
        parser.add_argument("name", nargs="?", help="Name of the persona to switch to")

    registry.register("persona", lambda args: select_persona(getattr(args, 'name', None)), "Switch Persona", aliases=["p"], setup_parser=setup_persona, interactive=True)

    # INIT
    def setup_init(parser):
        parser.add_argument("--grade", choices=["A", "B", "C"], help="Project Grade (Headless)")

    registry.register("init", lambda args: init_project(grade=getattr(args, 'grade', None)), "Scaffold One-Army Project", setup_parser=setup_init, interactive=True)

    # MERGE
    registry.register("merge", lambda args: merge_frameworks(), "Merge Skills into Blueprint")

    # DEPLOY
    registry.register("deploy", lambda args: deploy_project(), "Deploy Project", interactive=True)

    # APPLY
    def setup_apply(parser):
        parser.add_argument("name", help="Name of the framework to apply")
        parser.add_argument("--dry-run", action="store_true", help="Preview commands without running")

    registry.register("apply", lambda args: apply_framework(args.name, args.dry_run), "Apply Skill (Executable Knowledge)", setup_parser=setup_apply, interactive=True)

    # DOCTOR
    # DOCTOR
    registry.register(DoctorCommand())

    # SYNC
    registry.register("sync", lambda args: sync_all_personas(), "Sync frameworks with remote library", interactive=True)

    # PUSH
    registry.register("push", lambda args: push_all_personas(), "Push frameworks to remote library")

    # BRAINSTORM
    registry.register("brainstorm", lambda args: run_brainstorm_wizard(), "AI Refactor & Optimization", aliases=["bs"], interactive=True)

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
    # RECALL
    registry.register(RecallCommand())

    # MEMORIZE
    registry.register(MemorizeCommand())

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
    registry.register("tutorial", run_tutorial, "Interactive onboarding", setup_parser=setup_tutorial, interactive=True)

    # CONFIG
    registry.register(ConfigCommand())

    # BRAIN (Rowboat Integration)
    from jcapy.commands import brain_cmd

    def setup_brain(parser):
        subs = parser.add_subparsers(dest="subcommand", help="Brain actions")
        link = subs.add_parser("link", help="Link a local directory as Brain")
        link.add_argument("path", help="Path to Rowboat/Obsidian vault")

        ask = subs.add_parser("ask", help="Ask the Brain a question")
        ask.add_argument("question", nargs="+", help="Question to ask")

    registry.register("brain", brain_cmd.run_brain, "Manage Knowledge Graph (Rowboat)", setup_parser=setup_brain)

    # ASK SHORTCUT
    def setup_ask(parser):
        parser.add_argument("question", nargs="+", help="Question")

    registry.register("ask", lambda args: brain_cmd.ask_brain(" ".join(args.question)), "Ask the Brain (Shortcut)", setup_parser=setup_ask)




