import os
import yaml
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from jcapy.config import JCAPY_HOME, BASE_DIR

@dataclass
class SkillManifest:
    name: str
    version: str
    description: str
    author: Optional[str] = None
    category: str = "general"
    entry_point: Optional[str] = None
    commands: List[Dict[str, str]] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)

@dataclass
class Skill:
    manifest: SkillManifest
    path: str
    is_bundled: bool = False

class SkillRegistry:
    """
    Central registry for JCapy Skills (ASI05, 2.1).
    Handles discovery, versioning, metadata validation, and dependency resolution.
    """
    def __init__(self):
        self._skills: Dict[str, Skill] = {}
        self._search_paths: List[str] = [
            os.path.join(os.getcwd(), "jcapy-skills"),
            os.path.join(JCAPY_HOME, "skills"),
            os.path.join(BASE_DIR, "skills")
        ]

    def add_search_path(self, path: str):
        if os.path.exists(path) and path not in self._search_paths:
            self._search_paths.append(path)

    def discover(self):
        """Discovers skills across all search paths."""
        for path in self._search_paths:
            if not os.path.exists(path):
                continue

            # Check for central registry.yaml in the search path (ASI05, 2.1)
            registry_index_path = os.path.join(path, "registry.yaml")
            if os.path.exists(registry_index_path):
                try:
                    self._load_from_index(path, registry_index_path)
                except Exception as e:
                    print(f"Warning: Failed to load index at {registry_index_path}: {e}")

            for item in os.listdir(path):
                if item == "registry.yaml": continue
                skill_dir = os.path.join(path, item)
                manifest_path = os.path.join(skill_dir, "jcapy.yaml")

                if os.path.isdir(skill_dir) and os.path.exists(manifest_path):
                    try:
                        skill = self._load_skill(skill_dir, manifest_path)
                        # Don't overwrite if already loaded via index
                        if skill.manifest.name not in self._skills:
                            self._skills[skill.manifest.name] = skill
                    except Exception as e:
                        print(f"Warning: Failed to load skill at {skill_dir}: {e}")

    def _load_from_index(self, base_path: str, index_path: str):
        with open(index_path, 'r') as f:
            index_data = yaml.safe_load(f) or {}
            skills_list = index_data.get("skills", [])
            for item in skills_list:
                name = item.get("name")
                rel_path = item.get("path", name)
                skill_dir = os.path.join(base_path, rel_path)
                manifest_path = os.path.join(skill_dir, "jcapy.yaml")
                if os.path.exists(manifest_path):
                    skill = self._load_skill(skill_dir, manifest_path)
                    self._skills[skill.manifest.name] = skill

    def _load_skill(self, skill_dir: str, manifest_path: str) -> Skill:
        with open(manifest_path, 'r') as f:
            data = yaml.safe_load(f)

        manifest = SkillManifest(
            name=data.get("name"),
            version=data.get("version"),
            description=data.get("description"),
            author=data.get("author"),
            category=data.get("category", "general"),
            entry_point=data.get("entry_point"),
            commands=data.get("commands", []),
            permissions=data.get("permissions", []),
            dependencies=data.get("dependencies", [])
        )

        return Skill(manifest=manifest, path=skill_dir)

    def validate_dependencies(self, skill_name: str) -> List[str]:
        """Returns a list of missing dependencies for a given skill."""
        skill = self.get_skill(skill_name)
        if not skill: return []

        missing = []
        for dep in skill.manifest.dependencies:
            if dep not in self._skills:
                missing.append(dep)
        return missing

    def get_skill(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def list_skills(self) -> List[Skill]:
        return list(self._skills.values())

    def __repr__(self):
        return f"<SkillRegistry(skills={list(self._skills.keys())})>"

# Global registry instance
_skill_registry = SkillRegistry()

def get_skill_registry() -> SkillRegistry:
    return _skill_registry
