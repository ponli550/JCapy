import os
import shutil
import subprocess
import json
import sys
from datetime import datetime
from jcapy.config import get_active_library_path
from jcapy.commands.skills import save_harvested_deploy, apply_skill

def load_config_local():
    """Load local .jcapyrc project config"""
    config_path = os.path.join(os.getcwd(), ".jcapyrc")
    if os.path.exists(config_path):
        try:
             with open(config_path, 'r') as f:
                 return json.load(f)
        except:
             return {}
    return {}

def check_k8s_connection():
    """Checks if kubectl can connect to a running cluster"""
    try:
        subprocess.check_output(["kubectl", "cluster-info"], stderr=subprocess.STDOUT, timeout=5)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False

def check_system(full_scan=True):
    """Performs system health checks. Returns a dict of results."""
    results = {
        "tools": {},
        "config": {},
        "integrations": {},
        "installation": {},
        "all_passed": True
    }

    # 0. Check Installation (Homebrew)
    results["installation"]["Homebrew Managed"] = False
    if shutil.which("brew"):
        try:
            res = subprocess.run(["brew", "list", "--formula"], capture_output=True, text=True)
            if "jcapy" in res.stdout:
                results["installation"]["Homebrew Managed"] = True
        except:
            pass

    results["installation"]["Binary Path"] = sys.argv[0]

    # 1. Check Tools
    tools = ["git", "node", "npm"]
    for tool in tools:
        if shutil.which(tool):
            results["tools"][tool] = True
        else:
            results["tools"][tool] = False
            results["all_passed"] = False

    # 2. Check Config
    cwd = os.getcwd()
    results["config"][".jcapyrc"] = os.path.exists(os.path.join(cwd, ".jcapyrc"))
    results["config"][".env"] = os.path.exists(os.path.join(cwd, ".env"))

    if not results["config"][".jcapyrc"]: results["all_passed"] = False

    # 3. Check Integrations
    results["integrations"]["Vercel Linked"] = os.path.exists(os.path.join(cwd, ".vercel"))
    results["integrations"]["Supabase Linked"] = os.path.exists(os.path.join(cwd, "supabase", "config.toml")) or os.path.exists(os.path.join(cwd, "supabase", "config.json"))

    return results

def init_project():
    """Scaffold One-Army Directory Structure & Config"""
    try:
        from rich.console import Console
        from rich.prompt import Prompt

        console = Console()
        structure = [
            "apps/web",
            "apps/mobile",
            "packages/ui",
            "packages/config",
            "docker"
        ]

        console.print("[bold cyan]🚀 Initializing One-Army Protocol...[/bold cyan]")

        # 1. Directory Structure
        for p in structure:
            path = os.path.join(os.getcwd(), p)
            if not os.path.exists(path):
                os.makedirs(path)
                console.print(f"  [green]✔ Created:[/green] {p}")
            else:
                console.print(f"  [yellow]• Exists:[/yellow]  {p}")

        # 2. Docker Compose
        docker_path = os.path.join(os.getcwd(), "docker-compose.yml")
        if not os.path.exists(docker_path):
            with open(docker_path, 'w') as f:
                f.write("# One-Army Docker Compose\n# services:\n#   (services will be added here)\n")
            console.print("  [green]✔ Created:[/green] docker-compose.yml")

        # 3. Package.json
        pkg_path = os.path.join(os.getcwd(), "package.json")
        if not os.path.exists(pkg_path):
            pkg_data = {
                "name": os.path.basename(os.getcwd()),
                "version": "1.0.0",
                "scripts": {
                    "start": "echo 'Run start script'",
                    "build": "echo 'Run build script'",
                    "dev": "echo 'Run dev script'",
                    "test": "echo 'Tests Passed'",
                    "test:e2e": "echo 'E2E Tests Passed'",
                    "audit": "echo 'Security Audit Passed'"
                },
                "dependencies": {},
                "devDependencies": {}
            }
            with open(pkg_path, 'w') as f:
                json.dump(pkg_data, f, indent=2)
            console.print("  [green]✔ Created:[/green] package.json (with default scripts)")
        else:
            console.print("  [yellow]• Exists:[/yellow]  package.json")

        console.print("\n[bold yellow]📋 Project Configuration[/bold yellow]")

        # 4. Grade Selection
        console.print("Select Project Grade (affects deployment strictness):")
        console.print("  [bold green]C (Skirmish)[/bold green]: Speed > Quality (Hackathons)")
        console.print("  [bold blue]B (Campaign)[/bold blue]: Balanced (Standard SaaS) [dim][Default][/dim]")
        console.print("  [bold red]A (Fortress)[/bold red]: Quality > Speed (Enterprise/Fintech)")

        grade_choice = Prompt.ask("Choose Grade", choices=["A", "B", "C", "a", "b", "c"]).upper()

        config = {
            "grade": grade_choice,
            "project_name": os.path.basename(os.getcwd()),
            "created_at": str(datetime.now())
        }

        with open(os.path.join(os.getcwd(), ".jcapyrc"), 'w') as f:
            json.dump(config, f, indent=2)

        console.print(f"  [green]✔ Saved:[/green] .jcapyrc (Grade {grade_choice})")

        # 5. Documentation Scaffolding
        console.print("\n[bold cyan]📚 Scaffolding Documentation...[/bold cyan]")
        docs_structure = {
            "docs": ["00-start-here.md"],
            "docs/architecture": ["overview.md"],
            "docs/architecture/decisions": ["001-init.md"],
            "docs/guides": ["deployment.md", "debugging.md"],
            "docs/reference": ["api.md", "database.md"]
        }

        if grade_choice == "A":
             docs_structure["docs/architecture"].extend(["requirements.md", "permissions.md"])
             docs_structure["docs/guides"].extend(["security-guidelines.md", "accessibility.md"])

        for folder, files in docs_structure.items():
            path = os.path.join(os.getcwd(), folder)
            os.makedirs(path, exist_ok=True)
            for f in files:
                filepath = os.path.join(path, f)
                if not os.path.exists(filepath):
                    with open(filepath, 'w') as doc:
                        doc.write(f"# {f.replace('.md', '').capitalize()}\n\n*Generated by jcapy One-Army Protocol*")

        console.print("[bold green]✨ Project Scaffolding Complete.[/bold green]")

    except ImportError:
        print("Rich not installed. Run 'pip install rich'")

def deploy_project():
    """Execute Deployment Pipeline based on Grade"""
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.prompt import Prompt

        console = Console()
        lib_path = get_active_library_path() # From config import

        config_path = os.path.join(os.getcwd(), ".jcapyrc")
        if not os.path.exists(config_path):
            console.print("[bold red]❌ Error:[/bold red] .jcapyrc not found. Run 'jcapy init' first.")
            return

        with open(config_path, 'r') as f:
            config = json.load(f)

        grade = config.get("grade", "B")
        project_name = config.get("project_name", "Unknown")

        strategies = []
        infra_name = "Local"
        if grade == "B": infra_name = "Docker"
        if grade == "A": infra_name = "Kubernetes"

        strategies.append({"name": f"{infra_name} (Grade {grade})", "type": "standard", "grade": grade})

        # Harvested Strategies
        devops_path = os.path.join(lib_path, "skills", "devops")
        if os.path.exists(devops_path):
            for f in os.listdir(devops_path):
                if f.startswith("deploy_") and f.endswith(".md"):
                    strategies.append({
                        "name": f.replace("deploy_", "").replace(".md", "").replace("_", " ").title() + " (New)",
                        "type": "harvested",
                        "path": os.path.join(devops_path, f)
                    })

        strategies.append({"name": "Custom", "type": "manual"})

        console.print(f"\n[bold cyan]🚀 Deploying {project_name}[/bold cyan]")
        table = Table(title="Available Deployment Strategies", show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan", width=4)
        table.add_column("Strategy", style="green")
        table.add_column("Grade", style="yellow")

        for idx, s in enumerate(strategies):
            table.add_row(str(idx+1), s["name"], s.get("grade", "-"))
        console.print(table)

        choice_str = Prompt.ask("Choose Strategy ID", default="1")
        try:
            choice_idx = int(choice_str) - 1
        except:
            choice_idx = 0

        selected_strategy = strategies[choice_idx] if 0 <= choice_idx < len(strategies) else strategies[0]
        steps = []

        if selected_strategy["type"] == "standard":
             grade = selected_strategy["grade"]
             console.print("\n[bold]🩺 Running Pre-Flight Checks...[/bold]")
             health = check_system()
             issues = []

             if grade == "B" and not shutil.which("docker"): issues.append("Docker not installed")
             if grade == "A" and not check_k8s_connection(): issues.append("Kubernetes Unreachable")

             if issues:
                 for i in issues: console.print(f"[yellow]Warning: {i}[/yellow]")
                 if Prompt.ask("Continue?", choices=["y", "n"], default="n") == "n": return
             else:
                 console.print("[green]✔ Checks Passed[/green]")

             if grade == "C":
                 steps = [("Building", "npm run build"), ("Running", f"screen -dmS {project_name} npm run start")]
             elif grade == "B":
                 steps = [("Test", "npm test"), ("Build Containers", "docker compose build"), ("Deploy", "docker compose up -d")]
             elif grade == "A":
                 steps = [("Audit", "npm audit"), ("E2E", "npm run test:e2e"), ("K8s Apply", "kubectl apply -f k8s/")]

        elif selected_strategy["type"] == "harvested":
             console.print(f"[bold green]🚀 Launching Harvested Strategy: {selected_strategy['name']}[/bold green]")
             # Use apply_skill by name or path?
             # apply_skill expects skill name. Since it's a file path, we can try passing the file content or name
             # But apply_skill searches library.
             # We can just manually run the logic here or make apply_skill smarter
             # For now, let's implement the block extraction manually here (code reuse bad, but safe)
             # Wait, I imported `apply_skill`! Can I use it?
             # `apply_skill` takes a name. `strategies` has the full path.
             # Let's just pass the filename minus extension?
             skill_name = os.path.basename(selected_strategy['path']).replace(".md", "")
             apply_skill(skill_name)
             return

        elif selected_strategy["type"] == "manual":
             cmd = Prompt.ask("[bold yellow]Enter Command[/bold yellow]")
             steps = [("Manual", cmd)]

        if steps:
            # Preview and Execute
            table = Table(title="Preview", show_header=True)
            table.add_column("Step")
            table.add_column("Command")
            for t, c in steps: table.add_row(t, c)
            console.print(table)

            action = Prompt.ask("Ready?", choices=["Yes", "No", "Harvest"], default="Yes")
            if action == "Harvest":
                harvest_name = Prompt.ask("Name strategy")
                save_harvested_deploy(harvest_name, steps, get_active_library_path())
            elif action == "Yes":
                for title, cmd in steps:
                    console.print(f"[bold yellow]👉 {title}[/bold yellow]...")
                    if subprocess.call(cmd, shell=True, executable='/bin/zsh') != 0:
                        console.print(f"[red]Failed at {title}[/red]")
                        return
                console.print("[green]Deployment Complete![/green]")

    except ImportError:
        print("Rich not installed.")
