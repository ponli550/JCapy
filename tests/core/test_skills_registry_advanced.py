import pytest
import os
import yaml
from jcapy.core.skills import SkillRegistry, SkillManifest, Skill
from jcapy.agents.security import ToolProxy
from jcapy.agents.base import BaseAgent, AgentIdentity

@pytest.fixture
def registry(tmp_path):
    reg = SkillRegistry()
    reg._search_paths = [str(tmp_path)]
    return reg

def test_central_indexing(tmp_path, registry):
    # Setup skills
    skill1_dir = tmp_path / "skill1"
    skill1_dir.mkdir()
    (skill1_dir / "jcapy.yaml").write_text(yaml.dump({
        "name": "skill1", "version": "1.0.0", "description": "S1", "category": "cat1"
    }))

    skill2_dir = tmp_path / "skill2"
    skill2_dir.mkdir()
    (skill2_dir / "jcapy.yaml").write_text(yaml.dump({
        "name": "skill2", "version": "1.0.0", "description": "S2", "category": "cat2"
    }))

    # Setup registry.yaml
    (tmp_path / "registry.yaml").write_text(yaml.dump({
        "skills": [
            {"name": "skill1", "path": "skill1"},
            {"name": "skill2", "path": "skill2"}
        ]
    }))

    registry.discover()
    assert "skill1" in registry._skills
    assert "skill2" in registry._skills
    assert registry.get_skill("skill1").manifest.category == "cat1"

def test_dependency_validation(tmp_path, registry):
    skill_dir = tmp_path / "dep_skill"
    skill_dir.mkdir()
    (skill_dir / "jcapy.yaml").write_text(yaml.dump({
        "name": "dep_skill", "version": "1.0.0", "description": "D",
        "dependencies": ["missing_skill"]
    }))

    registry.discover()
    missing = registry.validate_dependencies("dep_skill")
    assert "missing_skill" in missing

def test_tool_proxy_expansion():
    manifest = SkillManifest(
        name="test_skill", version="1.0.0", description="desc",
        permissions=["read_file", "write_file"]
    )
    skill = Skill(manifest=manifest, path="/tmp")

    from unittest.mock import MagicMock
    mock_agent = MagicMock()
    mock_agent.identity.name = "MockAgent"
    mock_agent.identity.id = "mock-agent"

    proxy = ToolProxy(mock_agent, allowed_tools=[])

    proxy.add_skill_permissions(skill)
    assert "read_file" in proxy.allowed_tools
    assert "write_file" in proxy.allowed_tools
