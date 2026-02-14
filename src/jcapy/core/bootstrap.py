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
from jcapy.ui.ux.safety import get_undo_stack
from jcapy.ui.ux.feedback import show_success, show_error
from jcapy.ui.ux.hints import get_tutorial
from jcapy.config import get_active_library_path, load_config, set_ux_preference, get_all_ux_preferences, set_api_key

def register_core_commands(registry: CommandRegistry):
    """Registers all built-in JCapy commands."""

    # LIST
    registry.register("list",
                      lambda args: _run_tui(),
                      "List all harvested frameworks",
                      aliases=["ls"])

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
    registry.register("manage", lambda args: _run_tui(), "Interactive TUI Manager", aliases=["tui"])

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
    registry.register("suggest", _run_suggest, "Recommend next best actions")

    # MCP
    def run_mcp(args):
        from jcapy.mcp.server import run_mcp_server
        run_mcp_server()
    registry.register("mcp", run_mcp, "Start JCapy MCP Server (Stdio)")

    # UNDO
    def setup_undo(parser):
        parser.add_argument("--list", action="store_true", dest="list_undo", help="List undo history")

    registry.register("undo", _run_undo, "Undo last destructive action", setup_parser=setup_undo)

    # RECALL
    def setup_recall(parser):
        parser.add_argument("query", nargs="+", help="Natural language query")

    registry.register("recall", _run_recall, "Semantic Search (Vector Memory)", setup_parser=setup_recall)

    # MEMORIZE
    def setup_memorize(parser):
        parser.add_argument("--force", action="store_true", help="Clear memory before ingesting")
        parser.add_argument("--path", help="Specific path to ingest (file or dir)", default=None)

    registry.register("memorize", _run_memorize, "Ingest knowledge into Memory Bank", setup_parser=setup_memorize)

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
    def setup_tutorial(parser):
        parser.add_argument("--reset", action="store_true", help="Reset tutorial progress")

    registry.register("tutorial", _run_tutorial, "Interactive onboarding", setup_parser=setup_tutorial)

    # CONFIG
    def setup_config(parser):
        subparsers = parser.add_subparsers(dest="action")
        subparsers.add_parser("list", help="List all preferences")

        set_key_parser = subparsers.add_parser("set-key", help="Set AI Provider API Key")
        set_key_parser.add_argument("provider", choices=["gemini", "openai", "deepseek"], help="AI Provider name")

        config_get_parser = subparsers.add_parser("get", help="Get a preference")
        config_get_parser.add_argument("key_value", help="Key name")

        config_set_parser = subparsers.add_parser("set", help="Set a preference")
        config_set_parser.add_argument("key_value", help="key=value")

    registry.register("config", _run_config, "Manage UX preferences and keys", setup_parser=setup_config)


# --- Helper Functions (moved from main logic) ---

def _run_tui():
    from jcapy.ui.tui import run as run_tui
    run_tui(get_active_library_path())

def _run_suggest(args):
    print(f"\033[1;36m🤖 jcapy Recommendations:\033[0m")
    lib_path = get_active_library_path()
    has_files = False
    for r, d, f in os.walk(lib_path):
        if any(k.endswith('.md') for k in f):
            has_files = True
            break

    if not has_files:
        print(f"  • \033[1;32mjcapy harvest\033[0m: Start building your knowledge base.")
        print(f"  • \033[1;32mjcapy init\033[0m: Create a new project structure.")
    else:
        try:
            from jcapy.utils.git_lib import get_git_status
            _, pending = get_git_status(lib_path)
            if pending > 0:
                print(f"  • \033[1;32mjcapy push\033[0m: You have {pending} uncommitted changes.")
        except: pass
        print(f"  • \033[1;32mjcapy list\033[0m: Browse your library.")
        print(f"  • \033[1;32mjcapy manage\033[0m: Open the Dashboard.")
    print(f"  • \033[1;32mjcapy doctor\033[0m: Verify system health.")

def _run_undo(args):
    undo_stack = get_undo_stack()
    if getattr(args, 'list_undo', False):
        items = undo_stack.list_items()
        if not items:
            print(f"\033[0;90mNo undo history.\033[0m")
        else:
            print(f"\033[1;36mUndo History:\033[0m")
            for i, item in enumerate(items, 1):
                print(f"  {i}. {item.get('description', 'Unknown')} ({item.get('timestamp', '')[:16]})")
    else:
        restored = undo_stack.pop()
        if restored:
            show_success(f"Restored: {restored.get('description', 'item')}")
        else:
            show_error("Nothing to undo", hint="Run 'jcapy undo --list' to see history")

def _run_recall(args):
    try:
        from jcapy.memory import MemoryBank
        bank = MemoryBank()
        if bank.collection.count() == 0:
            print(f"\033[1;33m🧠 Initializing Memory Bank (First Run)...\033[0m")
            bank.sync_library(get_active_library_path())

        query = " ".join(args.query)
        print(f"\033[1;36m🔍 Recalling knowledge related to: '{query}'...\033[0m")
        results = bank.recall(query, n_results=5)

        if not results:
            print(f"\033[0;90mNo relevant memories found.\033[0m")
        else:
            for i, res in enumerate(results, 1):
                meta = res['metadata']
                similarity = (1 - res['distance']) * 100
                print(f"\n{i}. \033[1m{meta['name']}\033[0m ( Relevance: {similarity:.1f}% )")
                print(f"   Shape: {meta['source']}")
    except ImportError:
        print(f"\033[1;31mError: 'chromadb' not installed.\033[0m")
    except Exception as e:
        print(f"\033[1;31mMemory Error: {e}\033[0m")

def _run_memorize(args):
    try:
        from jcapy.memory import MemoryBank
        bank = MemoryBank()
        paths = [args.path] if args.path else [get_active_library_path()]

        print(f"\033[1;36m🧠 Memorizing Knowledge...\033[0m")
        if args.force:
            print(f"\033[1;33m  • Force Clean enabled.\033[0m")

        stats = bank.memorize(paths, clear_first=args.force)
        print(f"\n\033[1;32m✨ Update Complete:\033[0m")
        print(f"  • Added: {stats['added']}")
        print(f"  • Skipped: {stats['skipped']}")
        print(f"  • Errors: {stats['errors']}")
    except ImportError:
        print(f"\033[1;31mError: 'chromadb' not installed.\033[0m")
    except Exception as e:
        print(f"\033[1;31mMemorize Error: {e}\033[0m")

def _run_tutorial(args):
    tutorial = get_tutorial()
    if getattr(args, 'reset', False):
        tutorial.reset()
        show_success("Tutorial progress reset")
    else:
        try:
            from jcapy.ui.animations import cinematic_intro, should_animate
            if should_animate():
                cinematic_intro()
        except ImportError: pass
        tutorial.run_interactive()

def _run_config(args):
    action = getattr(args, 'action', 'list')
    if action == "list":
        prefs = get_all_ux_preferences()
        print(f"\033[1;36mUX Preferences:\033[0m")
        for k, v in prefs.items():
            print(f"  {k}: {v}")
    elif action == "set-key":
        from rich.prompt import Prompt
        provider = args.provider
        key = Prompt.ask(f"Enter {provider.capitalize()} API Key", password=True)
        if key:
            success, msg = set_api_key(provider, key)
            if success:
                show_success(msg)
                print(f"\033[0;90mTip: Run 'jcapy doctor' to verify.\033[0m")
            else:
                show_error(msg)
        else:
            print(f"\033[1;33mKey entry cancelled.\033[0m")
    elif action == "set":
        key_value = getattr(args, 'key_value', None)
        if key_value and "=" in key_value:
            key, value = key_value.split("=", 1)
            if value.lower() in ("true", "1", "yes"): value = True
            elif value.lower() in ("false", "0", "no"): value = False
            set_ux_preference(key.strip(), value)
            show_success(f"Set {key.strip()} = {value}")
        else:
            print(f"\033[1;33mUsage: jcapy config set key=value\033[0m")
    elif action == "get":
        key_value = getattr(args, 'key_value', None)
        if key_value:
            config = load_config()
            prefs = get_all_ux_preferences()
            val = config.get(key_value) or prefs.get(key_value, 'not set')
            print(f"{key_value}: {val}")
        else:
            print(f"\033[1;33mUsage: jcapy config get key\033[0m")
    else:
        print(f"\033[1;33mUsage: jcapy config set-key [provider] | set key=value | get key | list\033[0m")

