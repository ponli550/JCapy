import os
import re
from typing import Dict, Any, Optional
from datetime import datetime
from jcapy.services.frameworks.parsers.base import BaseParser

class MarkdownParser(BaseParser):
    """Parses JCapy Skills from Markdown files with YAML frontmatter or structural H1/Para."""

    def can_handle(self, doc_path: str, content: str) -> bool:
        return doc_path.lower().endswith(".md") or content.strip().startswith("# ") or content.strip().startswith("---")

    def parse(self, content: str) -> Dict[str, Any]:
        """Extract skill details from a markdown documentation string."""
        meta = {
            "name": "",
            "description": "",
            "snippet": "",
            "grade": "B",
            "pros": "",
            "cons": ""
        }

        # 1. Try Frontmatter first
        frontmatter = self._parse_frontmatter(content)
        if frontmatter:
            for key in meta:
                if key in frontmatter:
                    meta[key] = str(frontmatter[key])
            # If frontmatter has snippet, we are done
            if meta["snippet"]:
                return meta

        # 2. Fallback to structural parsing
        lines = content.split('\n')

        # Title (H1)
        if not meta["name"]:
            for line in lines:
                if line.strip().startswith("# "):
                    meta["name"] = line.strip().replace("# ", "").strip()
                    break

        # Description (First paragraph after title)
        if not meta["description"]:
            for line in lines:
                l = line.strip()
                if l and not l.startswith("#") and not l.startswith("```"):
                    meta["description"] = l
                    break

        # Code Snippet (First code block)
        if not meta["snippet"] and "```" in content:
            try:
                start = content.find("```") + 3
                # Skip language identifier if present
                end_next = content.find("\n", start)
                if end_next != -1:
                    start = end_next + 1

                end = content.find("```", start)
                if end != -1:
                    meta["snippet"] = content[start:end].strip()
            except:
                pass

        return meta

    def _parse_frontmatter(self, content: str) -> Optional[Dict[str, Any]]:
        """Internal YAML frontmatter parser (subset of YAML)."""
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
                # Native Fallback (Simple subset)
                meta = {}
                for line in yaml_content.split("\n"):
                    if ":" in line:
                        key, val = line.split(":", 1)
                        key = key.strip()
                        val = val.strip()
                        if val.startswith("[") and val.endswith("]"):
                            val = [i.strip().strip("'").strip('"') for i in val[1:-1].split(",")]
                        else:
                            val = val.strip("'").strip('"')
                        meta[key] = val
                return meta
        except:
            return None
        return None
