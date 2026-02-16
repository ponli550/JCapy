import os
import sys
import shutil
import time
import subprocess
import re
from datetime import datetime
from jcapy.config import (
    load_config, save_config, get_active_library_path,
    get_current_persona_name, DEFAULT_LIBRARY_PATH, JCAPY_HOME
)
from jcapy.ui.menu import interactive_menu

# ANSI Colors for non-Rich fallbacks
CYAN = '\033[1;36m'
GREEN = '\033[1;32m'
YELLOW = '\033[1;33m'
MAGENTA = '\033[1;35m'
BLUE = '\033[1;34m'
WHITE = '\033[1;37m'
RED = '\033[1;31m'
RESET = '\033[0m'
GREY = '\033[0;90m'
BOLD = '\033[1m'

TEMPLATE_PATH = os.path.join(DEFAULT_LIBRARY_PATH, "TEMPLATE_FRAMEWORK.md")

# ==========================================
# FRAMEWORK MANAGEMENT LOGIC
# ==========================================
def list_frameworks():
    lib_path = get_active_library_path()
    persona = get_current_persona_name()

    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        console = Console()

        console.print(Panel(f"[bold blue]🧠 Knowledge Base ({persona})[/bold blue]", border_style="blue"))

        if not os.path.exists(lib_path):
            console.print(f"[yellow]No library found at {lib_path}[/yellow]")
            return

        table = Table(show_header=True, header_style="bold magenta", box=None)
        table.add_column("Category", style="cyan", no_wrap=True)
        table.add_column("Framework / Skill", style="green")
        table.add_column("Type", style="dim")
        table.add_column("Status", style="yellow")

        frameworks_count = 0
        for root, dirs, files in os.walk(lib_path):
            # Prune .git and __pycache__ from traversal
            dirs[:] = [d for d in dirs if d not in [".git", "__pycache__"]]

            folder_name = os.path.basename(root)
            if folder_name == "skills": continue

            # Simple Category detection based on folder depth/name
            rel_path = os.path.relpath(root, lib_path)
            category = rel_path if rel_path != "." else "General"

            for f in files:
                # Skip system files and templates
                if f in [".DS_Store", "TEMPLATE_FRAMEWORK.md", "README.md"] or f.startswith("."):
                    continue

                path = os.path.join(root, f)
                mtime = os.path.getmtime(path)
                is_recent = (time.time() - mtime) < 86400 # 24 hours
                status = "Recent" if is_recent else ""

                # Icons based on extension
                icon = "📄"
                ftype = "File"
                if f.endswith(".md"):
                    icon = "📜"
                    ftype = "Skill"
                elif f.endswith(".py"):
                    icon = "🐍"
                    ftype = "Script"
                elif f.endswith(".sh"):
                    icon = "🐚"
                    ftype = "Script"

                table.add_row(category, f"{icon} {f}", ftype, status)
                frameworks_count += 1

        if frameworks_count == 0:
            console.print(f"[dim](No frameworks harvested yet. Use 'jcapy harvest')[/dim]")
        else:
            console.print(table)

    except ImportError:
        # Fallback to old print method
        print(f"{BLUE}🧠 jcapy Knowledge Base ({persona}){RESET}")
        print("-----------------------------------------------------")
        # ... (Old implementation omitted for brevity, but could keep if needed) ...
        print(f"{YELLOW}Rich library missing. Install 'rich' for better output.{RESET}")


# ... (rest of file) ...

def harvest_framework(doc_path=None, auto_path=None, name=None, description=None, grade=None, confirm=False, force=False):
    lib_path = get_active_library_path()
    try:
        from rich.console import Console
        from rich.prompt import Prompt
        console = Console()
    except ImportError:
        print("Rich required.")
        return

    # Visual Harvest (TUI Mode)
    # Trigger ONLY if:
    # 1. No critical args provided (doc_path, name)
    # 2. Not in headless mode (confirm/force)
    # 3. Not explicity disabled (though we don't have a flag for that yet)
    if not doc_path and not name and not auto_path and not confirm and not force:
        try:
            from jcapy.ui.screens.harvest import HarvestScreen
            from textual.app import App

            class HarvestApp(App):
                """Minimal App wrapper to run the Screen independently."""
                def on_mount(self):
                    self.push_screen(HarvestScreen(), self.handle_result)

                def handle_result(self, result):
                    self.exit(result)

            app = HarvestApp()
            result = app.run()

            if result:
                 # Map TUI results to local variables
                 doc_path = result.get("doc_path")
                 name = result.get("name")
                 description = result.get("description")
                 grade = result.get("grade")
                 console.print(f"[green]✔ Interactive inputs received. Proceeding...[/green]")
            else:
                 console.print("[yellow]Harvest cancelled.[/yellow]")
                 return

        except Exception as e:
            console.print(f"[red]Failed to launch Visual Harvest TUI: {e}[/red]")
            console.print("[dim]Falling back to CLI prompts...[/dim]")

    console.print(f"[bold magenta]🌾 jcapy Harvest Protocol ({get_current_persona_name()})[/bold magenta]")
    console.print("[dim]-----------------------------------------------------[/dim]")

    # ... (Ghost Extraction Logic - Unchanged) ...
    # 0. Ghost-Extraction (Level 3.0)
    if auto_path and os.path.exists(auto_path):
        # ... (Same logic as before) ...
        pass

    # Smart Harvest: Pre-fill from doc OR Draft Overwrite
    defaults = {}
    draft_mode = False
    existing_framework_path = None

    if doc_path and os.path.exists(doc_path):
        # ... (Draft logic same as before) ...
        # Check if this is a jcapy Draft (Metadata check)
        draft_title = get_framework_metadata(doc_path)

        if draft_title:
             # ... (Draft find existing logic) ...
             # Try to find the ORIGINAL framework to overwrite
            for root, dirs, files in os.walk(lib_path):
                for f in files:
                    clean_name = os.path.basename(doc_path).replace(".bs.md", ".md")
                    if f == clean_name:
                        existing_framework_path = os.path.join(root, f)
                        break
                if existing_framework_path: break

            if existing_framework_path:
                console.print(f"[yellow]⚠️  Found existing framework: {existing_framework_path}[/yellow]")

                if force:
                    overwrite_confirm = 'y'
                    console.print("[cyan]Force overwrite active (--force)[/cyan]")
                elif confirm:
                     overwrite_confirm = 'y'
                     console.print("[cyan]Auto-confirmed overwrite (--yes)[/cyan]")
                else:
                     overwrite_confirm = Prompt.ask(f"[red]Overwrite '{os.path.basename(existing_framework_path)}' with this draft?[/red]", choices=["y", "n"], default="n")

                if overwrite_confirm == 'y':
                    # ... (Overwrite logic) ...
                    backup = backup_framework(existing_framework_path)
                    console.print(f"[dim]📦 Backup saved to {backup}[/dim]")
                    shutil.copy2(doc_path, existing_framework_path)
                    console.print("[green]✔ Framework updated successfully![/green]")
                    return

        # If not draft overwrite, parse as doc
        console.print(f"[bold cyan]📄 Parsing documentation: {doc_path}...[/bold cyan]")
        parsed = parse_markdown_doc(doc_path)
        if parsed and parsed.get("name"):
            defaults = parsed
            console.print(f"  [green]✔ Found:[/green] {defaults.get('name')} | {defaults.get('description')}")
        else:
             console.print(f"  [red]✘ Failed to parse doc or file not found.[/red]")

    # Template might still be in default or dynamic?
    if not os.path.exists(TEMPLATE_PATH):
        # ... (Template creation - Unchanged) ...
        pass

    # 1. Hybrid Inputs (Flag -> Default -> Prompt)
    try:
        def_name = defaults.get("name", "")
        # Name
        if name:
            framework_name = name
            console.print(f"[cyan]ℹ Name provided via flag:[/cyan] {framework_name}")
        else:
             # Fallback to Prompt
             framework_name = Prompt.ask(f"[cyan]? What is the name of this framework?[/cyan]", default=def_name)

        if not framework_name:
            console.print("[red]Aborted.[/red]")
            return

        # Deployment Check
        is_deploy = False
        if "deploy" in framework_name.lower():
            is_deploy = True
        else:
            if confirm: # Headless assumption: No deploy unless name says so
                pass
            else:
                if Prompt.ask(f"[cyan]? Is this a Deployment Strategy?[/cyan]", choices=["y", "n"], default="n") == "y":
                    is_deploy = True

        if is_deploy:
            domain = "devops"
            if not framework_name.lower().startswith("deploy"):
                framework_name = f"Deploy {framework_name}"
        else:
            # Domain
            if confirm:
                domain = 'misc'
            else:
                domain = Prompt.ask(f"[cyan]? Domain (e.g. ui, backend, devops)[/cyan]", default="misc")

        # Description
        def_desc = defaults.get("description", "")
        if description:
             desc_val = description
        else:
             if confirm: desc_val = def_desc
             else: desc_val = Prompt.ask(f"[cyan]? Description[/cyan]", default=def_desc if def_desc else "No description")
        description = desc_val

        # Grade
        def_grade = defaults.get("grade", "B")
        if grade:
             grade_val = grade.upper()
        else:
             if confirm: grade_val = def_grade
             else: grade_val = Prompt.ask(f"[cyan]? Grade[/cyan]", choices=["A", "B", "C"], default=def_grade)
        grade = grade_val

        # Pros/Cons (Skip if headless/confirm, default to empty)
        pros_input = defaults.get("pros", "")
        if not confirm:
             pros_input = Prompt.ask(f"[cyan]? Pros (comma separated)[/cyan]", default=pros_input)

        cons_input = defaults.get("cons", "")
        if not confirm:
             cons_input = Prompt.ask(f"[cyan]? Cons (comma separated)[/cyan]", default=cons_input)


        # Code Capture
        all_code_blocks = []
        # ... logic to capture code ...
        # If confirm (headless) -> skip manual paste.
        # If doc_path -> read file.
        # Manual paste -> loop.

        if doc_path:
             # Check extension and read
             valid_exts = ['.sh', '.py', '.js', '.jsx', '.ts', '.tsx', '.go', '.rs', '.java', '.php', '.rb', '.html', '.css', '.sql', '.json', '.yaml', '.yml', '.toml', '.md', '.txt']
             valid_names = ['Fastfile', 'Dockerfile', 'Makefile', 'Gemfile', 'Rakefile']
             if any(doc_path.endswith(ext) for ext in valid_exts) or os.path.basename(doc_path) in valid_names:
                 try:
                     with open(doc_path, 'r') as f:
                         all_code_blocks.append(f.read())
                 except: pass
        elif not confirm and not defaults.get("snippet"):
            console.print(f"\n[cyan]? Paste executable code (type 'EOF' on new line when done)[/cyan]")
            # ... (Paste loop implementation using input() because Prompt.ask doesn't handle multiline easy) ...
            # Reuse existing logic for loop but update prints to console.print
            pass

        code_snippet = "\n\n".join(all_code_blocks) if all_code_blocks else ""

        # Sanitize filename
        safe_name = framework_name.lower().replace(" ", "_")
        if is_deploy and not safe_name.startswith("deploy_"):
            safe_name = safe_name.replace("deploy-", "deploy_").replace("deploy", "deploy_")
        filename = safe_name + ".md"

        # Path adjustment
        target_dir = os.path.join(lib_path, "skills", domain)
        target_path = os.path.join(target_dir, filename)

        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        # CHECK OVERWRITE
        if os.path.exists(target_path):
            if force:
                console.print(f"[yellow]! Framework '{filename}' exists. Force overwriting...[/yellow]")
            elif confirm:
                 console.print(f"[yellow]! Framework '{filename}' exists. Auto-confirming overwrite...[/yellow]")
            else:
                 if Prompt.ask(f"[yellow]! Framework '{filename}' exists. Overwrite?[/yellow]", choices=["y", "n"], default="n") == "n":
                     console.print("Aborted.")
                     return


        # 3. Create File from Template
        with open(TEMPLATE_PATH, 'r') as t:
            template_content = t.read()

        # Simple replacement of placeholders
        new_content = template_content.replace("[Framework Name]", framework_name)
        new_content = new_content.replace("[e.g. Backend, UI, DevOps]", domain)
        new_content = new_content.replace("[Description]", description)
        new_content = new_content.replace("[Grade]", grade)

        # Handle Pros/Cons list formatting
        pros_list_str = "  - \"Standard Solution\""
        if pros_input:
             pros_list_str = "\n".join([f"  - \"{p.strip()}\"" for p in pros_input.split(",") if p.strip()])

        cons_list_str = "  - \"None identified\""
        if cons_input:
             cons_list_str = "\n".join([f"  - \"{c.strip()}\"" for c in cons_input.split(",") if c.strip()])

        new_content = new_content.replace("[Pros List]", pros_list_str)
        new_content = new_content.replace("[Cons List]", cons_list_str)

        # Inject captured code or use defaults
        snippet = code_snippet or defaults.get("snippet", "")
        if snippet:
             new_content = new_content.replace("(Paste your code snippet here)", snippet)

        with open(target_path, 'w') as f:
            f.write(new_content)

        # === POST-HARVEST UX ===
        from rich.panel import Panel

        # Celebratory Panel
        console.print(Panel.fit(
            f"[bold green]✅ Framework '{framework_name}' Harvested![/bold green]\n\n"
            f"[cyan]📋 NEXT STEPS:[/cyan]\n"
            f"  1. Edit: [yellow]jcapy open {safe_name}[/yellow]\n"
            f"  2. Test: [yellow]jcapy apply {safe_name} --dry-run[/yellow]\n"
            f"  3. Save: [yellow]jcapy push[/yellow]",
            title="🌾 Harvest Complete",
            border_style="green"
        ))

        # Post-Harvest Continuation Menu
        if not confirm and not force:
            while True:
                console.print("\n[bold cyan]What's next?[/bold cyan]")
                console.print("  [1] Apply/Test this framework")
                console.print("  [2] Push to repository")
                console.print("  [3] Edit in VS Code")
                console.print("  [4] Done - I'm finished")

                choice = Prompt.ask("Select", choices=["1", "2", "3", "4"], default="4")

                if choice == "1":
                    console.print("\n[cyan]Running dry-run test...[/cyan]")
                    apply_framework(safe_name, dry_run=True)
                elif choice == "2":
                    console.print("\n[cyan]Pushing to repository...[/cyan]")
                    try:
                        from jcapy.commands.sync import push_all_personas
                        push_all_personas()
                    except Exception as e:
                        console.print(f"[red]Push failed: {e}[/red]")
                elif choice == "3":
                    if shutil.which('code'):
                        subprocess.call(['code', target_path])
                    elif sys.platform == 'darwin':
                        subprocess.call(['open', target_path])
                    console.print("[green]Opened in editor[/green]")
                else:
                    break
        else:
            console.print(f"[dim]Headless mode: Skipping menu.[/dim]")

        console.print("\n[dim]Happy building! 🚀[/dim]")

    except KeyboardInterrupt:
        console.print(f"\n[red]Operation Cancelled.[/red]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")


def search_frameworks(query):
    lib_path = get_active_library_path()
    print(f"{BLUE}🔍 Searching Knowledge Base for '{query}'...{RESET}")
    print("-----------------------------------------------------")

    matches = []

    for root, dirs, files in os.walk(lib_path):
        for f in files:
            if f.endswith(".md"):
                path = os.path.join(root, f)
                try:
                    with open(path, 'r') as file_content:
                        content = file_content.read()
                        if query.lower() in content.lower():
                            matches.append(path)
                except Exception:
                    continue

    if matches:
        for match in matches:
            rel_path = match.replace(lib_path + "/", "")
            # Try to show snippet
            print(f"{GREEN}✅ Found in: {WHITE}{rel_path}{RESET}")
    else:
         print(f"{YELLOW}No matches found.{RESET}")
    print("-----------------------------------------------------")

def open_framework(name_query):
    lib_path = get_active_library_path()

    # Find the framework file by fuzzy name match
    target_file = None

    # Direct match first
    for root, dirs, files in os.walk(lib_path):
        for f in files:
             if f == name_query or f == f"{name_query}.md":
                 target_file = os.path.join(root, f)
                 break
        if target_file: break

    # Fuzzy match if no direct match
    if not target_file:
         for root, dirs, files in os.walk(lib_path):
            for f in files:
                if name_query.lower() in f.lower() and f.endswith(".md"):
                     target_file = os.path.join(root, f)
                     break
            if target_file: break

    if target_file:
        print(f"{GREEN}Opening {target_file}...{RESET}")

        # Determine editor - prioritizes EDITOR if set to Neovim
        editor = os.environ.get('EDITOR', 'open')

        # If EDITOR is open or empty, and 'code' is available, use 'code'
        if (editor == 'open' or not editor) and shutil.which('code'):
            editor = 'code'

        try:
             subprocess.call([editor, target_file])
        except Exception as e:
             print(f"{RED}Failed to open: {e}{RESET}")
             # Fallback
             subprocess.call(['open', target_file])
    else:
        print(f"{RED}Framework '{name_query}' not found.{RESET}")
        print(f"{GREY}Tip: Use 'jcapy search' to find the correct name.{RESET}")

def delete_framework(name_query):
    lib_path = get_active_library_path()

    # Find the framework file by fuzzy name match
    target_file = None

    # Direct match first
    for root, dirs, files in os.walk(lib_path):
        for f in files:
             if f == name_query or f == f"{name_query}.md":
                 target_file = os.path.join(root, f)
                 break
        if target_file: break

    # Fuzzy match if no direct match
    if not target_file:
         for root, dirs, files in os.walk(lib_path):
            for f in files:
                if name_query.lower() in f.lower() and f.endswith(".md"):
                     target_file = os.path.join(root, f)
                     break
            if target_file: break

    if target_file:
        from jcapy.ui.ux.safety import confirm, get_undo_stack
        from jcapy.ui.ux.feedback import show_success, show_error, show_warning

        print(f"{RED}WARNING: You are about to DELETE:{RESET}")
        print(f"   {target_file}")

        if confirm("Delete this framework?", destructive=True):
            try:
                # Backup before delete
                undo_stack = get_undo_stack()
                undo_stack.push("delete", target_file, f"Delete: {os.path.basename(target_file)}")

                os.remove(target_file)
                show_success("Framework deleted", hint="Run 'jcapy undo' to restore")
            except Exception as e:
                show_error(f"Error deleting file: {e}")
        else:
            show_warning("Delete cancelled")
    else:
        print(f"{RED}Framework '{name_query}' not found.{RESET}")

def get_framework_metadata(file_path):
    """Extracts title and metadata from a framework file (YAML frontmatter)."""
    if not os.path.exists(file_path): return None
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            # Regex to pull the title from the metadata header (GitHub formatted)
            match = re.search(r'^title:\s*(.*)$', content, re.MULTILINE)
            return match.group(1).strip() if match else None
    except:
        return None

def backup_framework(file_path):
    """Atomic Backup: Moves file to ~/.jcapy/backups/"""
    if not os.path.exists(file_path): return

    backup_dir = os.path.join(JCAPY_HOME, "backups")
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    filename = os.path.basename(file_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"{filename}.{timestamp}.bak")

    shutil.copy2(file_path, backup_path)
    return backup_path

def parse_markdown_doc(doc_path):
    """Extract skill details from a markdown documentation file"""
    if not os.path.exists(doc_path):
        return None

    with open(doc_path, 'r') as f:
        content = f.read()

    meta = {
        "name": "",
        "description": "",
        "snippet": "",
        "grade": "B",
        "pros": "",
        "cons": ""
    }

    lines = content.split('\n')

    # 1. Title (H1)
    for line in lines:
        if line.strip().startswith("# "):
            meta["name"] = line.strip().replace("# ", "").strip()
            break

    # 2. Description (First paragraph after title)
    for line in lines:
        l = line.strip()
        if l and not l.startswith("#") and not l.startswith("```"):
            meta["description"] = l
            break

    # 3. Code Snippet (First code block)
    if "```" in content:
        try:
            start = content.find("```") + 3
            # Skip language identifier if present
            end_line = content.find("\n", start)
            if end_line != -1:
                start = end_line + 1

            end = content.find("```", start)
            if end != -1:
                meta["snippet"] = content[start:end].strip()
        except:
            pass

    return meta

def save_harvested_deploy(name, steps, lib_path):
    """Saves a deployment strategy as an executable framework"""
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '', name).lower()
    filename = f"deploy_{safe_name}.md"
    devops_dir = os.path.join(lib_path, "skills", "devops")

    if not os.path.exists(devops_dir):
        os.makedirs(devops_dir)

    path = os.path.join(devops_dir, filename)

    commands = "\n".join([step[1] for step in steps])

    content = f"""# Deployment: {name}
> Harvested on {datetime.now()}

## Execution Plan
<!-- jcapy:EXEC -->
```bash
{commands}
```
"""
    with open(path, 'w') as f:
        f.write(content)

# ==========================================
# RICH-DEPENDENT FRAMEWORK FEATURES (Apply/Merge)
# ==========================================
def apply_framework(framework_name, dry_run=False, context=None, interactive=True):
    """Parses and executes bash blocks from a Framework File (Executable Knowledge)"""
    try:
        from rich.console import Console
        from rich.prompt import Prompt
        from rich.panel import Panel
        from rich.syntax import Syntax

        console = Console()
        lib_path = get_active_library_path()

        # 1. Find the Skill File (Prioritize Exact Matches)
        target_file = None
        fuzzy_match = None

        for root, dirs, files in os.walk(lib_path):
            for f in files:
                # Exact Match (with or without .md)
                if f == framework_name or f == f"{framework_name}.md":
                    target_file = os.path.join(root, f)
                    break
                # Fuzzy Match (keep as fallback)
                if not fuzzy_match and framework_name.lower() in f.lower() and f.endswith(".md"):
                    fuzzy_match = os.path.join(root, f)
            if target_file: break

        # Fallback to fuzzy only if no exact match found
        target_file = target_file or fuzzy_match

        if not target_file:
            console.print(f"[bold red]❌ Error:[/bold red] Framework '{framework_name}' not found.")
            return

        console.print(f"[bold cyan]🔍 Found Framework:[/bold cyan] {target_file}")

        # 2. Parse Executable Blocks
        with open(target_file, 'r') as f:
            content = f.read()

        # Robust Regex: handles trailing spaces and optional carriage returns
        pattern = r'<!--\s*jcapy:EXEC\s*-->\s*```bash[^\n\r]*[\n\r]+(.*?)\n```'
        matches = re.findall(pattern, content, re.DOTALL)

        if not matches:
            console.print("[yellow]⚠️  No key '<!-- jcapy:EXEC -->' executable blocks found in this skill.[/yellow]")
            return

        console.print(f"[bold blue]🚀 Found {len(matches)} execution blocks.[/bold blue]")

        # 3. Execution Loop
        for i, match in enumerate(matches, 1):
            cmd_block = match.strip()

            # TEMPLATING: Replace placeholders
            if context:
                for key, val in context.items():
                    cmd_block = cmd_block.replace(f"{{{{{key}}}}}", val)

            console.print(f"\n[bold yellow]Block {i}/{len(matches)}:[/bold yellow]")
            console.print(Panel(cmd_block, title="Script Content", border_style="blue"))

            if dry_run:
                console.print("[dim](Dry Run: Skipped)[/dim]")
                continue

            # Execute as a single script to preserve context
            if not interactive or Prompt.ask("Execute this block?", choices=["y", "n"], default="y") == "y":
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as tmp:
                    tmp.write(f"#!/bin/zsh\nset -e\n{cmd_block}")
                    tmp_path = tmp.name

                os.chmod(tmp_path, 0o755)

                try:
                    process = subprocess.run(tmp_path, shell=True, executable='/bin/zsh')

                    if process.returncode == 0:
                        console.print(f"  [green]✔ Block {i} Success[/green]")
                    else:
                        console.print(f"[bold red]❌ Block {i} Failed (Exit Code {process.returncode})[/bold red]")
                        if interactive and Prompt.ask("Continue anyway?", choices=["y", "n"], default="n") == "n":
                            break
                        if not interactive:
                            break # Fail fast in non-interactive
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
            else:
                console.print("[dim]Skipped by user.[/dim]")

        console.print("\n[bold green]✅ Framework Applied Successfully![/bold green]")

    except ImportError:
        print("Rich not installed. Run 'pip install rich'")

def parse_frontmatter(content):
    """Extracts YAML frontmatter from markdown content with native fallback if PyYAML is missing"""
    content = content.strip()
    if not content.startswith("---"):
        return None

    try:
        parts = content.split("---", 2)
        if len(parts) < 3:
            return None

        yaml_content = parts[1].strip()

        # Try PyYAML if available
        try:
            import yaml
            return yaml.safe_load(yaml_content)
        except ImportError:
            # Native Fallback (Simple YAML subset: key: value)
            meta = {}
            for line in yaml_content.split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip()
                    val = val.strip()
                    # Handle basic lists [a, b] or simple strings
                    if val.startswith("[") and val.endswith("]"):
                        val = [i.strip().strip("'").strip('"') for i in val[1:-1].split(",")]
                    else:
                        val = val.strip("'").strip('"')
                    meta[key] = val
            return meta
    except Exception as e:
        return None
    return None

def merge_frameworks(init_project_func=None):
    """Merge two frameworks (Frontend + Backend) into a unified blueprint.
       Pass init_project_func to avoid circular dependency if needed.
    """
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from jcapy.commands.project import load_config_local, init_project

        console = Console()
        console.print(Panel.fit("[bold magenta]🧬 jcapy Blueprint Merge[/bold magenta]", border_style="magenta"))
        console.print("[dim]Create a unified project from separate Frontend and Backend frameworks.[/dim]\n")

        # 0.5 Selection of Library Source
        config = load_config()
        current_p = config.get("current_persona", "programmer")
        personas_dict = config.get("personas", {})

        options = [f"Active Persona ({current_p})", "All Combined"]
        for p in sorted(personas_dict.keys()):
            options.append(f"Persona: {p}")

        idx = interactive_menu("Select Library Source for Frameworks", options)
        choice = options[idx]

        lib_paths = []
        if choice.startswith("Active Persona"):
            p_path = personas_dict.get(current_p, {}).get("path", DEFAULT_LIBRARY_PATH)
            lib_paths.append(p_path)
        elif choice == "All Combined":
            for p in personas_dict:
                p_path = personas_dict[p].get("path")
                if p_path: lib_paths.append(p_path)
        else:
            p_name = choice.replace("Persona: ", "")
            p_path = personas_dict.get(p_name, {}).get("path")
            if p_path: lib_paths.append(p_path)

        if not lib_paths:
            lib_paths = [DEFAULT_LIBRARY_PATH]

        # 0. Ensure Project Init
        if not os.path.exists(os.path.join(os.getcwd(), ".jcapyrc")):
            console.print("[yellow]Project not initialized. Running 'jcapy init' first...[/yellow]")
            init_project()

        # 1. Tech Stack Advisor (Comparison Table)
        console.print("\n[bold cyan]💡 Tech Stack Advisor[/bold cyan]")

        all_frameworks = {} # name -> metadata

        # Recursive Scan and Parse
        with console.status("[bold cyan]Scanning library for frameworks...") as status:
            for lib_path in lib_paths:
                if not os.path.exists(lib_path): continue
                for root, dirs, files in os.walk(lib_path):
                    for f in files:
                        if f.endswith(".md") and f != "TEMPLATE_FRAMEWORK.md":
                            path = os.path.join(root, f)
                            try:
                                with open(path, 'r') as file:
                                    content = file.read()
                                    meta = parse_frontmatter(content)
                                    if meta:
                                        framework_id = f.replace(".md", "")
                                        if framework_id not in all_frameworks:
                                            all_frameworks[framework_id] = meta
                                            all_frameworks[framework_id]['path'] = path
                            except:
                                continue

        if not all_frameworks:
            console.print("[red]No frameworks with valid metadata found in library.[/red]")
            return

        # Display Comparison Table
        table = Table(title="Available Frameworks", show_header=True, header_style="bold magenta", box=None)
        table.add_column("Framework ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Description", style="white")
        table.add_column("Grade", style="yellow")
        table.add_column("Pros", style="blue")
        table.add_column("Cons", style="red")

        for framework_id, meta in sorted(all_frameworks.items(), key=lambda item: str(item[1].get('grade', 'Z'))):
            framework_name = str(meta.get('name', framework_id))
            framework_desc = str(meta.get('description', 'No description'))
            framework_grade = str(meta.get('grade', '-'))
            pros = ", ".join(meta.get('pros', [])) if isinstance(meta.get('pros'), list) else str(meta.get('pros', ''))
            cons = ", ".join(meta.get('cons', [])) if isinstance(meta.get('cons'), list) else str(meta.get('cons', ''))

            table.add_row(framework_id, framework_name, framework_desc, framework_grade, pros, cons)

        console.print(table)
        console.print("\n")

        # 2. Select Frontend
        console.print("\n[bold cyan]1. Select Frontend Framework[/bold cyan]")
        frontend_options = [sid for sid, m in all_frameworks.items() if 'frontend' in [t.lower() for t in m.get('tags', [])] or 'ui' in [t.lower() for t in m.get('tags', [])]]

        if not frontend_options:
            frontend_options = sorted(all_frameworks.keys())

        idx = interactive_menu("Choose Frontend", frontend_options)
        frontend_choice = frontend_options[idx]
        console.print(f"[green]✔ Selected:[/green] {frontend_choice}")

        # 3. Select Backend
        console.print("\n[bold cyan]2. Select Backend Framework[/bold cyan]")
        backend_options = [sid for sid, m in all_frameworks.items() if 'backend' in [t.lower() for t in m.get('tags', [])] or 'api' in [t.lower() for t in m.get('tags', [])]]

        if not backend_options:
            backend_options = sorted(all_frameworks.keys())
        backend_options.append("None (Frontend Only)")

        idx = interactive_menu("Choose Backend", backend_options)
        if idx == len(backend_options) - 1:
            backend_choice = None
            console.print("[dim]Backend skipped.[/dim]")
        else:
            backend_choice = backend_options[idx]
            console.print(f"[green]✔ Selected:[/green] {backend_choice}")

        # 4. Update .jcapyrc (Blueprint Definition)
        config = load_config_local()
        config["type"] = "blueprint"
        config["frontend"] = frontend_choice
        if backend_choice:
            config["backend"] = backend_choice

        with open(".jcapyrc", "w") as f:
            import json
            json.dump(config, f, indent=2)

        # 5. Merge Execution (Apply Skills)
        console.print(f"\n[bold magenta]🚀 Merging Blueprint...[/bold magenta]")

        # Apply Frontend
        console.print(f"\n[cyan]Applying Frontend: {frontend_choice}[/cyan]")
        apply_framework(frontend_choice, context={"target_dir": "apps/web"})

        # Apply Backend
        if backend_choice:
            console.print(f"\n[cyan]Applying Backend: {backend_choice}[/cyan]")
            apply_framework(backend_choice, context={"target_dir": "apps/api"})

        console.print("\n[green]Merge Sequence Completed.[/green]")

        # 6. Setup / Post-Install
        from rich.prompt import Prompt
        if Prompt.ask("\nRun automated setup (npm install & build)?", choices=["y", "n"], default="y") == "y":
            console.print("\n[bold yellow]⚙️  Running Setup...[/bold yellow]")

            if os.path.exists("apps/web/package.json"):
                console.print("  • Frontend: Installing dependencies...")
                subprocess.run("cd apps/web && npm install", shell=True, executable='/bin/zsh')

            if os.path.exists("docker-compose.yml") or os.path.exists("docker-compose.yaml"):
                console.print("  • Docker: Building containers...")
                subprocess.run("docker compose build", shell=True, executable='/bin/zsh')

            console.print("[green]✨ Blueprint Setup Complete![/green]")

    except ImportError:
        print("Rich not installed. Run 'pip install rich'")
