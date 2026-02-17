# SPDX-License-Identifier: Apache-2.0
import os
import sys
import glob
from rich.console import Console
from jcapy.config import load_config, save_config, get_active_library_path, get_current_persona_name, load_config_local
from jcapy.utils.ai import call_ai_agent

console = Console()

def link_brain(path):
    """Links a local directory as the JCapy Brain (Library Path)"""
    target_path = os.path.abspath(os.path.expanduser(path))

    if not os.path.exists(target_path):
        console.print(f"[bold red]❌ Error:[/bold red] Path does not exist: {target_path}")
        return

    config = load_config()
    current_persona = config.get("current_persona", "programmer")

    if "personas" not in config:
        config["personas"] = {}

    if current_persona not in config["personas"]:
        config["personas"][current_persona] = {}

    # Update path
    config["personas"][current_persona]["path"] = target_path
    save_config(config)

    console.print(f"[bold green]🚣 Rowboat Connected![/bold green]")
    console.print(f"    Brain Path: [cyan]{target_path}[/cyan]")
    console.print(f"    Persona: [yellow]{current_persona}[/yellow]")
    console.print("\n[dim]New harvests will be saved here. 'jcapy ask' will search here.[/dim]")

def ask_brain(question):
    """RAG-lite: Ask a question to the Knowledge Graph"""
    # 0. Handle Piping & MockArgs
    piped_data = getattr(question, 'piped_data', None) if hasattr(question, 'piped_data') else None
    q_str = question if isinstance(question, str) else " ".join(getattr(question, '_tokens', []))

    lib_path = get_active_library_path()

    if not os.path.exists(lib_path):
        console.print(f"[red]Brain not found at {lib_path}. Run 'jcapy brain link <path>' first.[/red]")
        return

    console.print(f"[bold magenta]🧠 Thinking...[/bold magenta] [dim](Scanning {lib_path})[/dim]")

    # 1. Scan for Knowledge
    md_files = glob.glob(os.path.join(lib_path, "**/*.md"), recursive=True)
    context_blob = ""
    file_count = 0
    max_files = 20 # Safety limit

    if piped_data:
        context_blob = f"--- PIPED CONTEXT ---\n{piped_data}\n\n"
        file_count += 1

    # Priority: Files with matching keywords in filename
    keywords = q_str.lower().split()
    scored_files = []

    for f in md_files:
        score = 0
        fname = os.path.basename(f).lower()
        for k in keywords:
            if k in fname: score += 10
        scored_files.append((score, f))

    scored_files.sort(key=lambda x: (x[0], os.path.getmtime(x[1])), reverse=True)

    used_files = []
    for score, fpath in scored_files[:max_files]:
        try:
            with open(fpath, 'r') as f:
                content = f.read()
                if len(context_blob) + len(content) > 50000: break
                context_blob += f"\n\n--- FILE: {os.path.basename(fpath)} ---\n{content}"
                used_files.append(os.path.basename(fpath))
                file_count += 1
        except:
            pass

    if not context_blob:
         console.print("[yellow]Brain is empty or unreadable.[/yellow]")
         return

    # 2. Construct Prompt
    prompt = f"""
You are JCapy, an intelligent coding assistant using a local knowledge graph (Rowboat).
Answer the user's question based STRICTLY on the provided Context.
If the answer is not in the context, say "I don't have that information in my brain yet."

QUESTION: {q_str}

--- KNOWLEDGE GRAPH CONTEXT ({file_count} files) ---
{context_blob}
"""

    # 3. Call AI
    # Determine provider from config
    config = load_config()
    # Default to available key
    provider = "gemini"
    if config.get("env", {}).get("OPENAI_API_KEY"): provider = "openai"
    if config.get("env", {}).get("GEMINI_API_KEY"): provider = "gemini"

    # Check if key exists
    from jcapy.config import get_api_key
    if not get_api_key(provider):
        console.print(f"[bold red]❌ No API Key found for {provider}.[/bold red]")
        console.print("Run 'jcapy config set-key <provider>' to enable RAG.")
        return

    console.print(f"[dim]Consulting {file_count} documents...[/dim]")

    try:
        response, err = call_ai_agent(prompt, provider=provider)
        if err:
             console.print(f"[red]AI Error: {err}[/red]")
        else:
             console.print("\n[bold cyan]🤖 JCapy:[/bold cyan]")
             console.print(response)
             console.print(f"\n[dim]Sources: {', '.join(used_files[:5])}...[/dim]")

    except Exception as e:
         console.print(f"[red]Error: {e}[/red]")

def run_brain(args):
    """Dispatcher for 'brain' command scope"""
    if hasattr(args, 'subcommand'):
        if args.subcommand == 'link':
            link_brain(args.path)
        elif args.subcommand == 'ask':
            # This path is usually handled by 'jcapy ask' top-level alias, but good to have here
            ask_brain(args)
    else:
        console.print("[yellow]Usage: jcapy brain [link|ask] ...[/yellow]")
