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

import difflib
from jcapy.utils.ai import call_ai_agent
from jcapy.ui.ux.safety import get_undo_stack, confirm

def rapid_fix(file_path, instruction, provider='gemini', diagnostics=None):
    """Entry point for jcapy fix <file> <instruction>"""
    if not file_path or not instruction:
        print(f"\033[1;31mError: Both file path and instruction are required.\033[0m")
        return

    if not os.path.exists(file_path):
        print(f"\033[1;31mError: File {file_path} not found.\033[0m")
        return

    print(f"{CYAN}🔧 Rapid Fix: {RESET}{BOLD}{instruction}{RESET} on {file_path}...")

    # 1. Read Current Content
    with open(file_path, 'r') as f:
        content = f.read()

    # 2. Prepare Prompt
    diag_context = f"\n### COMPILER ERROR CONTEXT:\n{diagnostics}\n" if diagnostics else ""

    prompt = f"""
You are the **jcapy Fix Bot**. Your goal is to apply a specific instruction to the provided code.
{diag_context}
### Instruction:
{instruction}

### Constraints:
1. Return ONLY the new, complete file content.
2. Do not include markdown code blocks (e.g., ```python) unless they are part of the file content itself.
3. No conversational filler.

--- TARGET FILE: {file_path} ---
{content}
"""

    # 3. Execution Loop (Level 2.0)
    print(f"{YELLOW}📡 Sending to {provider.upper()}...{RESET}")
    result, err = call_ai_agent(prompt, provider)

    if result:
        # Generate Diff
        diff = difflib.unified_diff(
            content.splitlines(),
            result.splitlines(),
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm=""
        )
        diff_output = "\n".join(diff)

        if not diff_output:
            print(f"{GREEN}✨ AI Result: No changes needed.{RESET}")
            return

        print(f"\n{BLUE}--- PROPOSED CHANGES ---{RESET}")
        for line in diff_output.splitlines():
            if line.startswith('+'): print(f"{GREEN}{line}{RESET}")
            elif line.startswith('-'): print(f"{RED}{line}{RESET}")
            else: print(line)
        print(f"{BLUE}------------------------{RESET}\n")

        # 4. Confirm and Apply
        if confirm(f"Apply fix to {file_path}?", destructive=True):
            stack = get_undo_stack()
            stack.push("fix", file_path, f"Rapid Fix: {instruction}")

            with open(file_path, 'w') as f:
                f.write(result)

            print(f"{GREEN}✔ Fix applied successfully.{RESET}")
        else:
            # Fallback to file dump if rejected
            out_file = file_path + ".fix.txt"
            with open(out_file, 'w') as f:
                f.write(result)
            print(f"{YELLOW}⚠ Fix rejected. Saved to {out_file} for manual review.{RESET}")
    else:
        print(f"{RED}AI Error: {err}{RESET}")
        print(f"{YELLOW}Falling back to Local Prompt Dump...{RESET}")

        # Fallback to local prompt generation
        out_file = file_path + ".fix.txt"
        with open(out_file, 'w') as f:
            f.write(prompt)
        print(f"\n{GREEN}📝 Local Fix Prompt generated:{RESET} {out_file}")

        if shutil.which('code'):
            subprocess.call(['code', out_file])
