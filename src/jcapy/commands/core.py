# SPDX-License-Identifier: Apache-2.0
from jcapy.core.base import CommandBase
from jcapy.memory import get_memory_bank
from jcapy.config import get_active_library_path, load_config, save_config, get_all_ux_preferences, set_api_key, set_ux_preference
from jcapy.ui.ux.feedback import show_success, show_error
from rich.console import Console
from rich.prompt import Prompt
import os

console = Console()

class MemorizeCommand(CommandBase):
    name = "memorize"
    description = "Ingest knowledge into Memory Bank"

    def setup_parser(self, parser):
        parser.add_argument("--force", action="store_true", help="Clear memory before ingesting")
        parser.add_argument("--path", help="Specific path to ingest (file or dir)", default=None)

    def execute(self, args):
        try:
            bank = get_memory_bank()

            # --- PIPING SUPPORT ---
            piped_data = getattr(args, 'piped_data', None)

            if piped_data and not args.path:
                console.print(f"[bold cyan]🧠 Memorizing Piped Data...[/bold cyan]")
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tf:
                    tf.write(piped_data)
                    tmp_path = tf.name

                try:
                    stats = bank.memorize([tmp_path], clear_first=args.force)
                    console.print(f"\n[bold green]✨ Piped Data Ingested:[/bold green]")
                    print(f"  • Added: {stats['added']}")
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                return

            paths = [args.path] if args.path else [get_active_library_path()]

            console.print(f"[bold cyan]🧠 Memorizing Knowledge...[/bold cyan]")
            if args.force:
                console.print(f"[yellow]  • Force Clean enabled.[/yellow]")

            stats = bank.memorize(paths, clear_first=args.force)
            console.print(f"\n[bold green]✨ Update Complete:[/bold green]")
            print(f"  • Added: {stats['added']}")
            print(f"  • Skipped: {stats['skipped']}")
            print(f"  • Errors: {stats['errors']}")
        except ImportError:
             console.print(f"[bold red]Error: 'chromadb' not installed.[/bold red]")
        except Exception as e:
            console.print(f"[bold red]Memorize Error: {e}[/bold red]")

class RecallCommand(CommandBase):
    name = "recall"
    description = "Semantic Search (Vector Memory)"

    def setup_parser(self, parser):
        parser.add_argument("query", nargs="+", help="Natural language query")

    def execute(self, args):
        try:
            bank = get_memory_bank()

            if not getattr(bank, 'client', None):
                console.print("[dim]Memory disabled (missing chromadb).[/dim]")
                return

            # Check if local bank needs init
            if hasattr(bank, 'collection') and bank.collection and bank.collection.count() == 0:
                console.print(f"[bold yellow]🧠 Initializing Memory Bank (First Run)...[/bold yellow]")
                bank.sync_library(get_active_library_path())

            query = " ".join(args.query)
            console.print(f"[bold cyan]🔍 Recalling knowledge related to: '{query}'...[/bold cyan]")
            results = bank.recall(query, n_results=5)

            if not results:
                console.print(f"[dim]No relevant memories found.[/dim]")
            else:
                for i, res in enumerate(results, 1):
                    meta = res['metadata']
                    similarity = (1 - res['distance']) * 100
                    console.print(f"\n{i}. [bold]{meta.get('name', 'Unknown')}[/bold] ( Relevance: {similarity:.1f}% )")
                    print(f"   Shape: {meta.get('source', 'Unknown')}")
        except ImportError:
             console.print(f"⚠️  Detailed error loading RemoteMemoryBank (check pinecone-client). Falling back to Local.")
        except Exception as e:
            console.print(f"[bold red]Memory Error: {e}[/bold red]")

class ConfigCommand(CommandBase):
    name = "config"
    description = "Manage UX preferences and keys"

    def setup_parser(self, parser):
        subparsers = parser.add_subparsers(dest="action")
        subparsers.add_parser("list", help="List all preferences")

        set_key_parser = subparsers.add_parser("set-key", help="Set AI Provider API Key")
        set_key_parser.add_argument("provider", choices=["gemini", "openai", "deepseek"], help="AI Provider name")

        config_get_parser = subparsers.add_parser("get", help="Get a preference")
        config_get_parser.add_argument("key_value", help="Key name")

        config_set_parser = subparsers.add_parser("set", help="Set a preference")
        config_set_parser.add_argument("key_value", help="key=value")

    def execute(self, args):
        action = getattr(args, 'action', 'list')
        if action == "list":
            prefs = get_all_ux_preferences()
            console.print(f"[bold cyan]UX Preferences:[/bold cyan]")
            for k, v in prefs.items():
                print(f"  {k}: {v}")
        elif action == "set-key":
            provider = args.provider
            key = Prompt.ask(f"Enter {provider.capitalize()} API Key", password=True)
            if key:
                success, msg = set_api_key(provider, key)
                if success:
                    show_success(msg)
                    console.print(f"[grey50]Tip: Run 'jcapy doctor' to verify.[/grey50]")
                else:
                    show_error(msg)
            else:
                console.print(f"[yellow]Key entry cancelled.[/yellow]")
        elif action == "set":
            key_value = getattr(args, 'key_value', None)
            if key_value and "=" in key_value:
                key, value = key_value.split("=", 1)
                if value.lower() in ("true", "1", "yes"): value = True
                elif value.lower() in ("false", "0", "no"): value = False
                set_ux_preference(key.strip(), value)
                show_success(f"Set {key.strip()} = {value}")
            else:
                console.print(f"[yellow]Usage: jcapy config set key=value[/yellow]")
        elif action == "get":
            key_value = getattr(args, 'key_value', None)
            if key_value:
                config = load_config()
                prefs = get_all_ux_preferences()
                val = config.get(key_value) or prefs.get(key_value, 'not set')
                print(f"{key_value}: {val}")
            else:
                 console.print(f"[yellow]Usage: jcapy config get key[/yellow]")
        else:
            console.print(f"[yellow]Usage: jcapy config set-key [provider] | set key=value | get key | list[/yellow]")
