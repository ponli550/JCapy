import os
import shutil
import subprocess
import sys
import time
from jcapy.config import JCAPY_HOME, load_config

# ANSI Colors
CYAN = '\033[1;36m'
GREEN = '\033[1;32m'
YELLOW = '\033[1;33m'
MAGENTA = '\033[1;35m'
RESET = '\033[0m'
GREY = '\033[0;90m'

def autonomous_explore(topic, provider='local'):
    """Entry point for jcapy explore <topic>"""
    print(f"{MAGENTA}🔍 Autonomous Research: {RESET}{topic}...")

    # 1. Prepare Research Prompt
    prompt = f"""
You are the **jcapy Research Agent**. Generate a 2026 "Fortress" Standard Skill for: {topic}.

### Goal:
Research best practices, CLI commands, and directory structures for {topic}.
Create a comprehensive JCapy Skill (Markdown) that adheres to:
1. Idempotency.
2. Pre-flight checks.
3. Observability (echoes/emojis).
4. Markdown <!-- jcapy:EXEC --> structure.

### Output:
Return ONLY the Markdown content for the skill.
"""

    # 2. Draft Storage
    drafts_dir = os.path.join(JCAPY_HOME, "library_drafts")
    if not os.path.exists(drafts_dir):
        os.makedirs(drafts_dir, exist_ok=True)

    # 3. Handle Provider logic
    if provider == 'local':
        out_file = os.path.join(drafts_dir, f"{topic.replace(' ', '_')}.explore_v1.txt")
        with open(out_file, 'w') as f:
            f.write(prompt)

        print(f"\n{GREEN}📝 Research Prompt generated:{RESET} {out_file}")
        print(f"{GREY}Use this prompt to generate your new skill, then save it to your library.{RESET}")

        # Auto-open
        if shutil.which('code'):
            subprocess.call(['code', out_file])
    else:
        print(f"{YELLOW}📡 Researching {topic} via {provider}... (Simulation){RESET}")
        autonomous_explore(topic, 'local')
