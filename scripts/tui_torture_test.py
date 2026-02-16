import time
import sys
from rich.console import Console

console = Console()

def run():
    console.print("[bold cyan]🧪 Starting TUI Torture Test...[/bold cyan]")

    # 1. Burst Test
    console.print("\n[yellow]⚡ Burst Mode (50 lines)[/yellow]")
    for i in range(50):
        print(f"Log line {i}: The quick brown fox jumps over the lazy dog.")

    # 2. Streaming Test
    console.print("\n[yellow]⏳ Slow Stream (3s)[/yellow]")
    for i in range(3):
        console.print(f"Working step {i+1}...")
        time.sleep(1)

    # 3. ANSI Colors
    console.print("\n[yellow]🎨 Color Test[/yellow]")
    print("\033[92mGreen ANSI\033[0m")
    print("\033[91mRed ANSI\033[0m")

    # 4. Stderr
    console.print("\n[yellow]⚠️  Stderr Test[/yellow]")
    print("This is a standard error message.", file=sys.stderr)

    console.print("\n[bold green]✅ Test Complete[/bold green]")

if __name__ == "__main__":
    run()
