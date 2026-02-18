#!/usr/bin/env python3
import os
import sys
import argparse
import re
from pathlib import Path

try:
    import tomllib
except ImportError:
    # Fallback for Python < 3.11, though jcapy requires >=3.11
    # We can try to use pip to install it or just fail if not present.
    # Given the environment, we'll assume 3.11+ or 'toml' package installed.
    try:
        import toml as tomllib
    except ImportError:
        print("Error: This script requires Python 3.11+ (tomllib) or 'toml' package.")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Update Homebrew Formula Dependencies")
    parser.add_argument("formula_path", type=Path, help="Path to jcapy.rb")
    parser.add_argument("--pyproject", type=Path, default=Path("pyproject.toml"), help="Path to pyproject.toml")
    parser.add_argument("--url", required=True, help="New URL for the formula")
    parser.add_argument("--sha256", required=True, help="New SHA256 for the formula")
    args = parser.parse_args()

    if not args.pyproject.exists():
        print(f"Error: {args.pyproject} not found.")
        sys.exit(1)

    if not args.formula_path.exists():
        print(f"Error: {args.formula_path} not found.")
        sys.exit(1)

    # 1. Parse pyproject.toml
    with open(args.pyproject, "rb") as f:
        data = tomllib.load(f)

    dependencies = data.get("project", {}).get("dependencies", [])

    # 2. Format dependencies for Ruby
    # We need to turn "package>=1.2.3" into 'venv.pip_install "package>=1.2.3"'
    # We should also handle specific edge cases if needed, but direct mapping is usually fine for pip.

    pip_install_lines = []
    for dep in dependencies:
        pip_install_lines.append(f'    venv.pip_install "{dep}"')

    pip_install_block = "\n".join(pip_install_lines)

    # 3. Read existing Formula
    with open(args.formula_path, "r") as f:
        content = f.read()

    # 4. Update Formula Content

    # Update URL
    content = re.sub(r'url ".*?"', f'url "{args.url}"', content, count=1)

    # Update SHA256
    content = re.sub(r'sha256 ".*?"', f'sha256 "{args.sha256}"', content, count=1)

    # Update Dependencies
    # We look for the `def install` block and replace the pip_install commands
    # This is a bit fragile with Regex, but standard for this file structure.
    # We'll look for the marker `# Install dependencies via pip` and replace until `# Install jcapy package`

    # Heuristic: Find the block between 'venv = virtualenv_create...' and 'bin.install_symlink'
    # and re-generate the install body.

    # New install method body
    new_install_body = f"""  def install
    # Install into virtualenv
    venv = virtualenv_create(libexec, "python3.11")

    # Install dependencies via pip (synced from pyproject.toml)
{pip_install_block}

    # Install jcapy package
    venv.pip_install buildpath

    # Create bin symlink
    bin.install_symlink libexec/"bin/jcapy"
  end"""

    # Regex to replace the function body
    # We match `def install` ... `end` (non-greedy)
    # We use `^\s+end` to match the end of the block, assuming standard indentation.
    pattern = r"def install.*?^\s+end"

    if re.search(pattern, content, re.DOTALL | re.MULTILINE):
        content = re.sub(pattern, new_install_body, content, flags=re.DOTALL | re.MULTILINE)
    else:
        print("Error: Could not find 'def install' block in formula.")
        sys.exit(1)

    # 5. Write back
    with open(args.formula_path, "w") as f:
        f.write(content)

    print(f"✅ Updated {args.formula_path} with {len(dependencies)} dependencies.")

if __name__ == "__main__":
    main()
