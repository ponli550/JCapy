import os
import shutil
import subprocess
import sys
from jcapy.config import load_config, get_api_key

# ANSI Colors
CYAN = '\033[1;36m'
GREEN = '\033[1;32m'
YELLOW = '\033[1;33m'
MAGENTA = '\033[1;35m'
BLUE = '\033[1;34m'
WHITE = '\033[1;37m'
RED = '\033[1;31m'
BOLD = '\033[1m'
RESET = '\033[0m'
GREY = '\033[0;90m'

def rapid_fix(file_path, instruction, provider='local'):
    """Entry point for jcapy fix <file> <instruction>"""
    if not os.path.exists(file_path):
        print(f"{RED}Error: File {file_path} not found.{RESET}")
        return

    print(f"{CYAN}🔧 Rapid Fix: {RESET}{BOLD}{instruction}{RESET} on {file_path}...")

    # 1. Read Current Content
    with open(file_path, 'r') as f:
        content = f.read()

    # 2. Prepare Prompt
    prompt = f"""
You are the **jcapy Fix Bot**. Your goal is to apply a specific instruction to the provided code.

### Instruction:
{instruction}

### Constraints:
1. Return ONLY the new, complete file content.
2. Do not include markdown code blocks (e.g., ```python) unless they are part of the file content itself.
3. No conversational filler.

--- TARGET FILE: {file_path} ---
{content}
"""

    # 3. Handle Provider logic
    if provider == 'local':
        out_file = file_path + ".fix.txt"
        with open(out_file, 'w') as f:
            f.write(prompt)
        print(f"\n{GREEN}📝 Fix Context generated:{RESET} {out_file}")
        print(f"{GREY}Apply the result from your AI to this file.{RESET}")

        # Auto-open
        if shutil.which('code'):
            subprocess.call(['code', out_file])
        elif sys.platform == 'darwin':
            subprocess.call(['open', out_file])
    else:
        # Placeholder for AI integration (simulated for now as per plan)
        print(f"{YELLOW}📡 Connecting to {provider.upper()} (Simulation)...{RESET}")
        print(f"{RED}Direct AI application not yet hydrated. Using Local Dump.{RESET}")
        rapid_fix(file_path, instruction, 'local')
