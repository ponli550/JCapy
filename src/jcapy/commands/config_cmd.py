# SPDX-License-Identifier: Apache-2.0
from rich.console import Console
from rich.prompt import Prompt
from jcapy.config import load_config, save_config, get_all_ux_preferences, set_api_key, set_ux_preference
from jcapy.ui.ux.feedback import show_success, show_error

console = Console()

def setup_config(parser):
    subparsers = parser.add_subparsers(dest="action")
    subparsers.add_parser("list", help="List all preferences")

    set_key_parser = subparsers.add_parser("set-key", help="Set AI Provider API Key")
    set_key_parser.add_argument("provider", choices=["gemini", "openai", "deepseek"], help="AI Provider name")

    config_get_parser = subparsers.add_parser("get", help="Get a preference")
    config_get_parser.add_argument("key_value", help="Key name")

    config_set_parser = subparsers.add_parser("set", help="Set a preference")
    config_set_parser.add_argument("key_value", help="key=value")

def run_config(args):
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
