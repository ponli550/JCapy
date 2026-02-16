import os
import subprocess
import time
from rich.console import Console
from rich.table import Table

console = Console()

def measure_performance():
    base_dir = "showcase"
    results = []

    console.print("[bold cyan]🚀 Starting JCapy Performance Analysis...[/bold cyan]")

    # Discovery
    use_cases = sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and not d.startswith(".")])

    for case in use_cases:
        case_dir = os.path.join(base_dir, case)
        script_path = os.path.join(case_dir, "usecase.sh")

        if not os.path.exists(script_path):
            console.print(f"[yellow]⚠️  Skipping {case}: No usecase.sh found[/yellow]")
            continue

        console.print(f"\n[bold]🏃 Running {case}...[/bold]")
        start_time = time.time()

        try:
            # Run assuming the script is executable and handles its own cleanup/setup if needed
            # We use check=True to catch failures, but might want to allow failures to measure time anyway?
            # Let's cap execution output to avoid flooding
            process = subprocess.run(
                [script_path],
                cwd=os.getcwd(), # Run from root so relative paths in script might need adjustment?
                                 # Usually scripts assume they are run from project root or their own dir.
                                 # Let's try running from project root.
                capture_output=True,
                text=True
            )

            duration = time.time() - start_time
            status = "✅ PASS" if process.returncode == 0 else "❌ FAIL"

            results.append({
                "name": case,
                "duration": duration,
                "status": status,
                "error": process.stderr if process.returncode != 0 else ""
            })

            color = "green" if process.returncode == 0 else "red"
            console.print(f"  [{color}]{status}[/{color}] in {duration:.2f}s")

        except Exception as e:
            console.print(f"[red]Error running {case}: {e}[/red]")
            results.append({"name": case, "duration": 0, "status": "💥 ERROR", "error": str(e)})

    # Reporting
    console.print("\n[bold magenta]📊 Performance Report[/bold magenta]")
    table = Table(show_header=True, header_style="bold white")
    table.add_column("Use Case", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Duration (s)", justify="right")

    total_time = 0
    for r in results:
        table.add_row(r["name"], r["status"], f"{r['duration']:.2f}")
        total_time += r["duration"]

    console.print(table)
    console.print(f"\n[bold]Total Execution Time:[/bold] {total_time:.2f}s")

if __name__ == "__main__":
    measure_performance()
