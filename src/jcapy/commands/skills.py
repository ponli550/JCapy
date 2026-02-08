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

TEMPLATE_PATH = os.path.join(DEFAULT_LIBRARY_PATH, "TEMPLATE_SKILL.md")

# ==========================================
# SKILL MANAGEMENT LOGIC
# ==========================================
def list_skills():
    lib_path = get_active_library_path()
    persona = get_current_persona_name()
    print(f"{BLUE}🧠 jcapy Knowledge Base ({persona}){RESET}")
    print("-----------------------------------------------------")

    if not os.path.exists(lib_path):
        print(f"{YELLOW}No library found at {lib_path}{RESET}")
        return

    skills_count = 0
    for root, dirs, files in os.walk(lib_path):
        # Prune .git and __pycache__ from traversal
        dirs[:] = [d for d in dirs if d not in [".git", "__pycache__"]]

        level = root.replace(lib_path, '').count(os.sep)
        indent = ' ' * 4 * (level)
        subindent = ' ' * 4 * (level + 1)

        # Print Directory Name
        folder_name = os.path.basename(root)
        if folder_name and folder_name != "skills":
            print(f"{GREY}{indent}📂 {folder_name}/{RESET}")

        for f in files:
            if f.endswith(".md") and f != "TEMPLATE_SKILL.md":
                path = os.path.join(root, f)
                mtime = os.path.getmtime(path)
                is_recent = (time.time() - mtime) < 86400 # 24 hours
                tag = f" {YELLOW}(RECENT){RESET}" if is_recent else ""

                print(f"{GREEN}{subindent}📜 {f}{tag}{RESET}")
                skills_count += 1

    if skills_count == 0:
        print(f"   {GREY}(No skills harvested yet. Use 'jcapy harvest'){RESET}")
    print("-----------------------------------------------------")

def search_skills(query):
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

def open_skill(name_query):
    lib_path = get_active_library_path()

    # Find the skill file by fuzzy name match
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

        # Determine editor
        editor = os.environ.get('EDITOR', 'open')
        # Check if 'code' is available
        if shutil.which('code'):
            editor = 'code'

        try:
             subprocess.call([editor, target_file])
        except Exception as e:
             print(f"{RED}Failed to open: {e}{RESET}")
             # Fallback
             subprocess.call(['open', target_file])
    else:
        print(f"{RED}Skill '{name_query}' not found.{RESET}")
        print(f"{GREY}Tip: Use 'jcapy search' to find the correct name.{RESET}")

def delete_skill(name_query):
    lib_path = get_active_library_path()

    # Find the skill file by fuzzy name match
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
        print(f"{RED}WARNING: You are about to DELETE:{RESET}")
        print(f"   {target_file}")
        confirm = input(f"{YELLOW}Are you sure? (type 'delete' to confirm): {RESET}")

        if confirm == 'delete':
            try:
                os.remove(target_file)
                print(f"{GREEN}File deleted.{RESET}")
            except Exception as e:
                print(f"{RED}Error deleting file: {e}{RESET}")
        else:
            print("Aborted.")
    else:
        print(f"{RED}Skill '{name_query}' not found.{RESET}")

def get_skill_metadata(file_path):
    """Extracts title and metadata from a skill file (YAML frontmatter)."""
    if not os.path.exists(file_path): return None
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            # Regex to pull the title from the metadata header (GitHub formatted)
            match = re.search(r'^title:\s*(.*)$', content, re.MULTILINE)
            return match.group(1).strip() if match else None
    except:
        return None

def backup_skill(file_path):
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

def harvest_skill(doc_path=None):
    lib_path = get_active_library_path()
    print(f"{MAGENTA}🌾 jcapy Harvest Protocol ({get_current_persona_name()}){RESET}")
    print("-----------------------------------------------------")

    # Smart Harvest: Pre-fill from doc OR Draft Overwrite
    defaults = {}
    draft_mode = False
    existing_skill_path = None

    if doc_path and os.path.exists(doc_path):
        # Check if this is a jcapy Draft (Metadata check)
        draft_title = get_skill_metadata(doc_path)

        if draft_title:
            print(f"{CYAN}📜 Detected Draft Skill: '{draft_title}'{RESET}")
            # Try to find the ORIGINAL skill to overwrite
            for root, dirs, files in os.walk(lib_path):
                for f in files:
                    clean_name = os.path.basename(doc_path).replace(".bs.md", ".md")
                    if f == clean_name:
                        existing_skill_path = os.path.join(root, f)
                        break
                if existing_skill_path: break

            if existing_skill_path:
                print(f"{YELLOW}⚠️  Found existing skill: {existing_skill_path}{RESET}")

                # Show Diff
                print(f"\n{BOLD}Diff Preview:{RESET}")
                try:
                    subprocess.run(["diff", "--color", "-u", existing_skill_path, doc_path])
                except Exception:
                    print(" (diff command failed, showing raw paths)")

                confirm = input(f"\n{RED}Overwrite '{os.path.basename(existing_skill_path)}' with this draft? (y/N): {RESET}").strip().lower()

                if confirm == 'y':
                    # Atomic Swap
                    backup = backup_skill(existing_skill_path)
                    print(f"{GREY}📦 Backup saved to {backup}{RESET}")

                    shutil.copy2(doc_path, existing_skill_path)
                    print(f"{GREEN}✔ Skill updated successfully!{RESET}")

                    # Optional: Delete draft?
                    rm_draft = input(f"{GREY}Delete draft file? (y/N): {RESET}").strip().lower()
                    if rm_draft == 'y':
                        os.remove(doc_path)
                        print(f"{GREY}Draft deleted.{RESET}")
                    return
                else:
                    print("Overwrite cancelled. Proceeding to normal harvest...")

        # If not draft overwrite, parse as doc
        print(f"[bold cyan]📄 Parsing documentation: {doc_path}...[/bold cyan]")
        parsed = parse_markdown_doc(doc_path)
        if parsed and parsed.get("name"):
            defaults = parsed
            print(f"  [green]✔ Found:[/green] {defaults.get('name')} | {defaults.get('description')}")
        else:
             print(f"  [red]✘ Failed to parse doc or file not found.[/red]")

    # Template might still be in default or dynamic?
    # For now assume template is in default
    if not os.path.exists(TEMPLATE_PATH):
        # Auto-create Default Template
        os.makedirs(os.path.dirname(TEMPLATE_PATH), exist_ok=True)
        with open(TEMPLATE_PATH, 'w') as f:
            f.write("""---
tags: [tag1, tag2]
grade: [Grade]
---

# [Skill Name]

> [Description]

## Pros
[Pros List]

## Cons
[Cons List]

## Implementation
<!-- jcapy:EXEC -->
```bash
(Paste your code snippet here)
```
        """)

    # 1. Interactive Inputs
    try:
        def_name = defaults.get("name", "")
        skill_name = input(f"{CYAN}? What is the name of this skill? (e.g., 'glass-card') [{def_name}]: {RESET}").strip() or def_name
        if not skill_name:
            print(f"{RED}Aborted.{RESET}")
            return

        # Auto-detect or ask for Deployment
        is_deploy = False
        if "deploy" in skill_name.lower():
            is_deploy = True
        else:
            is_deploy_in = input(f"{CYAN}? Is this a Deployment Strategy? (y/N): {RESET}").strip().lower()
            if is_deploy_in == 'y': is_deploy = True

        if is_deploy:
            domain = "devops"
            # Auto-prefix naming
            if not skill_name.lower().startswith("deploy"):
                skill_name = f"Deploy {skill_name}"
            print(f"{GREEN}   → Auto-categorized as '{domain}' and prefixed as '{skill_name}'{RESET}")
        else:
            domain = input(f"{CYAN}? Domain (e.g. ui, backend, devops): {RESET}").strip().lower()
            if not domain:
                domain = 'misc'

        def_desc = defaults.get("description", "")
        description = input(f"{CYAN}? Description (short summary) [{def_desc}]: {RESET}").strip() or def_desc
        def_grade = defaults.get("grade", "B")
        grade = input(f"{CYAN}? Grade (A/B/C) [{def_grade}]: {RESET}").strip().upper()
        if not grade: grade = def_grade

        def_pros = defaults.get("pros", "")
        pros_input = input(f"{CYAN}? Pros (comma separated) [{def_pros}]: {RESET}").strip() or def_pros

        def_cons = defaults.get("cons", "")
        cons_input = input(f"{CYAN}? Cons (comma separated) [{def_cons}]: {RESET}").strip() or def_cons

        # Sanitize filename
        safe_name = skill_name.lower().replace(" ", "_") # deploying_react -> deploy_react
        # Ensure deploy prefix uses underscore for filename convention
        if is_deploy and not safe_name.startswith("deploy_"):
            safe_name = safe_name.replace("deploy-", "deploy_").replace("deploy", "deploy_")

        filename = safe_name + ".md"
        # Path adjustment: Skills live in library/skills/[domain]
        target_dir = os.path.join(lib_path, "skills", domain)
        target_path = os.path.join(target_dir, filename)

        # 2. Prepare Directory
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        # 3. Create File from Template
        with open(TEMPLATE_PATH, 'r') as t:
            template_content = t.read()

        # Simple replacement of placeholders
        new_content = template_content.replace("[Skill Name]", skill_name)
        new_content = new_content.replace("[e.g. Backend, UI, DevOps]", domain)
        new_content = new_content.replace("[Description]", description)
        new_content = new_content.replace("[Grade]", grade)

        pros_list = "\n".join([f"  - \"{p.strip()}\"" for p in pros_input.split(",") if p.strip()]) if pros_input else "  - \"Standard Solution\""
        cons_list = "\n".join([f"  - \"{c.strip()}\"" for c in cons_input.split(",") if c.strip()]) if cons_input else "  - \"None identified\""

        new_content = new_content.replace("[Pros List]", pros_list)
        new_content = new_content.replace("[Cons List]", cons_list)

        snippet = defaults.get("snippet", "")
        if snippet:
             new_content = new_content.replace("(Paste your code snippet here)", snippet)

        if os.path.exists(target_path):
            overwrite = input(f"{YELLOW}! Skill '{filename}' exists. Overwrite? (y/N): {RESET}")
            if overwrite.lower() != 'y':
                print("Aborted.")
                return

        with open(target_path, 'w') as f:
            f.write(new_content)

        print(f"\n{GREEN}✅ Skill Harvested!{RESET}")
        print(f"   Location: {target_path}")
        print(f"   Action: Open this file and paste your code snippet.")

        # Auto-open
        print(f"\n{CYAN}? Open in editor now?{RESET}")
        print(f"  [1] VS Code (default)")
        print(f"  [2] Nano (terminal)")
        print(f"  [n] No")

        choice = input(f"{CYAN}Select [1]: {RESET}").strip().lower()

        if choice == '' or choice == '1':
             if shutil.which('code'):
                 subprocess.call(['code', target_path])
             elif sys.platform == 'darwin':
                 subprocess.call(['open', target_path])
             else:
                 print("VS Code not found in PATH. Trying nano...")
                 subprocess.call(['nano', target_path])
        elif choice == '2' or choice == 'nano':
             subprocess.call(['nano', target_path])

    except KeyboardInterrupt:
        print(f"\n{RED}Operation Cancelled.{RESET}")

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
    """Saves a deployment strategy as an executable skill"""
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
# RICH-DEPENDENT SKILL FEATURES (Apply/Merge)
# ==========================================
def apply_skill(skill_name, dry_run=False, context=None):
    """Parses and executes bash blocks from a Skill File (Executable Knowledge)"""
    try:
        from rich.console import Console
        from rich.prompt import Prompt
        from rich.panel import Panel
        from rich.syntax import Syntax

        console = Console()
        lib_path = get_active_library_path()

        # 1. Find the Skill File (Reuse logic from open_skill)
        target_file = None
        # Direct/Fuzzy Search
        for root, dirs, files in os.walk(lib_path):
            for f in files:
                if f == skill_name or f == f"{skill_name}.md":
                    target_file = os.path.join(root, f)
                    break
                if skill_name.lower() in f.lower() and f.endswith(".md"):
                     target_file = os.path.join(root, f)
                     break
            if target_file: break

        if not target_file:
            console.print(f"[bold red]❌ Error:[/bold red] Skill '{skill_name}' not found.")
            return

        console.print(f"[bold cyan]🔍 Found Skill:[/bold cyan] {target_file}")

        # 2. Parse Executable Blocks
        with open(target_file, 'r') as f:
            content = f.read()

        # Regex to find <!-- jcapy:EXEC --> followed by ```bash ... ```
        pattern = r'<!--\s*jcapy:EXEC\s*-->\s*```bash\n(.*?)\n```'
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
            if Prompt.ask("Execute this block?", choices=["y", "n"], default="y") == "y":
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
                        if Prompt.ask("Continue anyway?", choices=["y", "n"], default="n") == "n":
                            break
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
            else:
                console.print("[dim]Skipped by user.[/dim]")

        console.print("\n[bold green]✅ Skill Applied Successfully![/bold green]")

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

def merge_skills(init_project_func=None):
    """Merge two skills (Frontend + Backend) into a unified blueprint.
       Pass init_project_func to avoid circular dependency if needed.
    """
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from jcapy.commands.project import load_config_local, init_project

        console = Console()
        console.print(Panel.fit("[bold magenta]🧬 jcapy Blueprint Merge[/bold magenta]", border_style="magenta"))
        console.print("[dim]Create a unified project from separate Frontend and Backend skills.[/dim]\n")

        # 0.5 Selection of Library Source
        config = load_config()
        current_p = config.get("current_persona", "programmer")
        personas_dict = config.get("personas", {})

        options = [f"Active Persona ({current_p})", "All Combined"]
        for p in sorted(personas_dict.keys()):
            options.append(f"Persona: {p}")

        idx = interactive_menu("Select Library Source for Skills", options)
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

        all_skills = {} # name -> metadata

        # Recursive Scan and Parse
        with console.status("[bold cyan]Scanning library for skills...") as status:
            for lib_path in lib_paths:
                if not os.path.exists(lib_path): continue
                for root, dirs, files in os.walk(lib_path):
                    for f in files:
                        if f.endswith(".md") and f != "TEMPLATE_SKILL.md":
                            path = os.path.join(root, f)
                            try:
                                with open(path, 'r') as file:
                                    content = file.read()
                                    meta = parse_frontmatter(content)
                                    if meta:
                                        skill_id = f.replace(".md", "")
                                        if skill_id not in all_skills:
                                            all_skills[skill_id] = meta
                                            all_skills[skill_id]['path'] = path
                            except:
                                continue

        if not all_skills:
            console.print("[red]No skills with valid metadata found in library.[/red]")
            return

        # Display Comparison Table
        table = Table(title="Available Skills", show_header=True, header_style="bold magenta", box=None)
        table.add_column("Skill ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Description", style="white")
        table.add_column("Grade", style="yellow")
        table.add_column("Pros", style="blue")
        table.add_column("Cons", style="red")

        for skill_id, meta in sorted(all_skills.items(), key=lambda item: str(item[1].get('grade', 'Z'))):
            skill_name = str(meta.get('name', skill_id))
            skill_desc = str(meta.get('description', 'No description'))
            skill_grade = str(meta.get('grade', '-'))
            pros = ", ".join(meta.get('pros', [])) if isinstance(meta.get('pros'), list) else str(meta.get('pros', ''))
            cons = ", ".join(meta.get('cons', [])) if isinstance(meta.get('cons'), list) else str(meta.get('cons', ''))

            table.add_row(skill_id, skill_name, skill_desc, skill_grade, pros, cons)

        console.print(table)
        console.print("\n")

        # 2. Select Frontend
        console.print("\n[bold cyan]1. Select Frontend Skill[/bold cyan]")
        frontend_options = [sid for sid, m in all_skills.items() if 'frontend' in [t.lower() for t in m.get('tags', [])] or 'ui' in [t.lower() for t in m.get('tags', [])]]

        if not frontend_options:
            frontend_options = sorted(all_skills.keys())

        idx = interactive_menu("Choose Frontend", frontend_options)
        frontend_choice = frontend_options[idx]
        console.print(f"[green]✔ Selected:[/green] {frontend_choice}")

        # 3. Select Backend
        console.print("\n[bold cyan]2. Select Backend Skill[/bold cyan]")
        backend_options = [sid for sid, m in all_skills.items() if 'backend' in [t.lower() for t in m.get('tags', [])] or 'api' in [t.lower() for t in m.get('tags', [])]]

        if not backend_options:
            backend_options = sorted(all_skills.keys())
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
        apply_skill(frontend_choice, context={"target_dir": "apps/web"})

        # Apply Backend
        if backend_choice:
            console.print(f"\n[cyan]Applying Backend: {backend_choice}[/cyan]")
            apply_skill(backend_choice, context={"target_dir": "apps/api"})

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
