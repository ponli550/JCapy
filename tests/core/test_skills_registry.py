import os
import pytest
import shutil
import tempfile
from jcapy.core.skills import SkillRegistry, SkillManifest

@pytest.fixture
def temp_skills_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a mock skill
        skill_dir = os.path.join(tmpdir, "test-skill")
        os.makedirs(skill_dir)

        manifest = {
            "name": "test-skill",
            "version": "1.2.3",
            "description": "A test skill",
            "author": "Tester",
            "entry_point": "plugin.py",
            "commands": [{"name": "test", "description": "test cmd"}]
        }

        with open(os.path.join(skill_dir, "jcapy.yaml"), "w") as f:
            import yaml
            yaml.dump(manifest, f)

        yield tmpdir

def test_skill_discovery(temp_skills_dir):
    registry = SkillRegistry()
    registry._search_paths = [temp_skills_dir]
    registry.discover()

    skills = registry.list_skills()
    assert len(skills) == 1
    assert skills[0].manifest.name == "test-skill"
    assert skills[0].manifest.version == "1.2.3"

def test_get_skill(temp_skills_dir):
    registry = SkillRegistry()
    registry._search_paths = [temp_skills_dir]
    registry.discover()

    skill = registry.get_skill("test-skill")
    assert skill is not None
    assert skill.manifest.description == "A test skill"

    assert registry.get_skill("non-existent") is None

def test_invalid_manifest(temp_skills_dir):
    # Create another dir with invalid yaml
    bad_skill_dir = os.path.join(temp_skills_dir, "bad-skill")
    os.makedirs(bad_skill_dir)
    with open(os.path.join(bad_skill_dir, "jcapy.yaml"), "w") as f:
        f.write("invalid: yaml: :")

    registry = SkillRegistry()
    registry._search_paths = [temp_skills_dir]
    registry.discover()

    # Should still find the good skill but ignore the bad one
    assert len(registry.list_skills()) == 1
    assert registry.get_skill("test-skill") is not None
