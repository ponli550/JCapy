import os
from typing import List, Optional, Dict, Any
from jcapy.models.frameworks import FrameworkResult, ResultStatus
from jcapy.services.frameworks.parsers.markdown import MarkdownParser

class FrameworkEngine:
    """Core orchestrator for JCapy Frameworks/Skills."""

    def __init__(self):
        # In a real DI setup, these would be injected
        self.parsers = [
            MarkdownParser()
        ]

    def harvest(self, doc_path: str, tui_data: Optional[Dict[str, Any]] = None) -> FrameworkResult:
        """
        Orchestrates the harvesting of a skill from a document.
        Returns a FrameworkResult.
        """
        if not os.path.exists(doc_path) or os.path.isdir(doc_path):
            return FrameworkResult(status=ResultStatus.FAILURE, message=f"Path not found: {doc_path}")

        try:
            with open(doc_path, 'r') as f:
                content = f.read()
        except Exception as e:
             return FrameworkResult(status=ResultStatus.FAILURE, message=str(e))

        # 1. Extraction Logic
        metadata = {}
        found_parser = False

        for parser in self.parsers:
            if parser.can_handle(doc_path, content):
                metadata = parser.parse(content)
                found_parser = True
                break

        # 2. Layering (TUI data overrides extracted metadata)
        if tui_data:
            metadata.update({k: v for k, v in tui_data.items() if v})

        if not found_parser and not tui_data:
            return FrameworkResult(status=ResultStatus.FAILURE, message="No parser found for this file type.")

        return FrameworkResult(
            status=ResultStatus.SUCCESS,
            message="Metadata extracted successfully",
            path=doc_path,
            payload=metadata
        )
    def save_skill(self, metadata: Dict[str, Any], force: bool = False) -> FrameworkResult:
        """
        Finalizes and saves the skill to the library.
        """
        from jcapy.config import get_active_library_path, DEFAULT_LIBRARY_PATH

        name = metadata.get("name")
        domain = metadata.get("domain", "misc")

        if not name:
            return FrameworkResult(status=ResultStatus.FAILURE, message="Skill name is required for saving.")

        # 1. Path Preparation
        lib_path = get_active_library_path()
        safe_name = name.lower().replace(" ", "_")
        if domain == "devops" and not safe_name.startswith("deploy_"):
            safe_name = f"deploy_{safe_name}"

        filename = f"{safe_name}.md"
        target_dir = os.path.join(lib_path, "skills", domain)
        target_path = os.path.join(target_dir, filename)

        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)

        if os.path.exists(target_path) and not force:
            return FrameworkResult(status=ResultStatus.FAILURE, message=f"Framework '{filename}' already exists.", path=target_path)

        # 2. Templating
        template_path = os.path.join(DEFAULT_LIBRARY_PATH, "TEMPLATE_FRAMEWORK.md")
        if not os.path.exists(template_path):
             return FrameworkResult(status=ResultStatus.FAILURE, message="Base template not found.")

        try:
            with open(template_path, 'r') as t:
                content = t.read()

            # Simple manual interpolation (can be upgraded to Jinja if needed)
            content = content.replace("[Framework Name]", name)
            content = content.replace("[e.g. Backend, UI, DevOps]", domain)
            content = content.replace("[Description]", metadata.get("description", "No description"))
            content = content.replace("[Grade]", metadata.get("grade", "B"))

            # Pros/Cons
            pros = metadata.get("pros", "")
            cons = metadata.get("cons", "")
            pros_str = "\n".join([f"  - \"{p.strip()}\"" for p in pros.split(",") if p.strip()]) if pros else "  - \"Standard Solution\""
            cons_str = "\n".join([f"  - \"{c.strip()}\"" for c in cons.split(",") if c.strip()]) if cons else "  - \"None identified\""

            content = content.replace("[Pros List]", pros_str)
            content = content.replace("[Cons List]", cons_str)

            # Snippet
            snippet = metadata.get("snippet", "")
            if snippet:
                content = content.replace("(Paste your code snippet here)", snippet)

            # 3. Write
            with open(target_path, 'w') as f:
                f.write(content)

            return FrameworkResult(
                status=ResultStatus.SUCCESS,
                message=f"Skill '{name}' saved to {domain}",
                path=target_path,
                payload={"safe_name": safe_name}
            )
        except Exception as e:
            return FrameworkResult(status=ResultStatus.FAILURE, message=f"Failed to save skill: {str(e)}")
