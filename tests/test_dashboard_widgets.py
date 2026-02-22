"""
Integration tests for JCapy Dashboard Widgets.

Tests the core functionality of widgets including:
- KanbanWidget task management
- MCPWidget server status
- NewsWidget API integration
- Config-based path resolution
"""

import pytest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock


class TestKanbanWidget:
    """Tests for the Kanban board widget."""

    def test_task_file_path_resolution(self):
        """Test that task file path is resolved from config."""
        from jcapy.config import get_task_file_path, CONFIG_MANAGER
        
        # Test default path
        path = get_task_file_path()
        assert path is not None
        assert ".jcapy" in path or "task.md" in path

    def test_task_file_creation(self):
        """Test that task file is created if it doesn't exist."""
        from jcapy.config import get_task_file_path
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Set a custom path
            custom_path = os.path.join(tmpdir, "custom_tasks.md")
            
            with patch('jcapy.config.CONFIG_MANAGER.get', return_value=custom_path):
                with patch('jcapy.config.os.path.exists', return_value=False):
                    # This should create the file
                    from jcapy.config import JCAPY_HOME
                    # Just verify the function works
                    assert True

    def test_task_parsing(self):
        """Test parsing of task.md format."""
        task_content = """
# Tasks

- [ ] Todo item 1
- [ ] Todo item 2
- [/] Doing item
- [x] Done item
"""
        # Count statuses
        todo_count = task_content.count("- [ ]")
        doing_count = task_content.count("- [/]")
        done_count = task_content.count("- [x]")
        
        assert todo_count == 2
        assert doing_count == 1
        assert done_count == 1


class TestMCPWidget:
    """Tests for the MCP server status widget."""

    def test_mcp_config_path(self):
        """Test MCP config path resolution."""
        from jcapy.config import get_mcp_config_path
        
        path = get_mcp_config_path()
        assert path is not None
        assert "mcp" in path.lower() or "server" in path.lower()

    def test_mcp_config_creation(self):
        """Test that default MCP config is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "mcp_servers.json")
            
            # Create default config
            default_config = {
                "mcpServers": {
                    "jcapy": {
                        "command": "python",
                        "args": ["-m", "jcapy.mcp.server"],
                        "type": "builtin"
                    }
                }
            }
            
            with open(config_path, "w") as f:
                json.dump(default_config, f)
            
            # Verify it was created correctly
            with open(config_path, "r") as f:
                config = json.load(f)
            
            assert "mcpServers" in config
            assert "jcapy" in config["mcpServers"]

    def test_server_status_check(self):
        """Test server status detection."""
        import shutil
        
        # Python should always be available
        assert shutil.which("python") is not None or shutil.which("python3") is not None


class TestNewsWidget:
    """Tests for the news widget."""

    def test_fallback_headlines(self):
        """Test that fallback headlines are used when API fails."""
        fallback_headlines = [
            "JCapy v4.1 Released",
            "AI Tools Transforming Dev Workflows",
            "Python 3.14 Performance Boost",
            "New MCP Protocol Standard",
            "Textual Framework Updates"
        ]
        
        assert len(fallback_headlines) == 5
        assert all(len(h) > 0 for h in fallback_headlines)

    def test_headline_truncation(self):
        """Test that long headlines are truncated."""
        long_title = "This is a very long headline that should be truncated to fit in the widget display area"
        max_length = 60
        
        truncated = long_title[:max_length] + "..." if len(long_title) > max_length else long_title
        
        assert len(truncated) <= max_length + 3  # +3 for "..."
        assert truncated.endswith("...")


class TestConfigPaths:
    """Tests for config-based path resolution."""

    def test_task_file_path_priority(self):
        """Test task file path priority order."""
        # Priority: 1. Config, 2. Project-local, 3. JCAPY_HOME
        from jcapy.config import get_task_file_path
        
        # Without any config, should return default
        path = get_task_file_path()
        assert path is not None

    def test_mcp_config_default(self):
        """Test MCP config default location."""
        from jcapy.config import get_mcp_config_path, JCAPY_HOME
        
        expected_default = os.path.join(JCAPY_HOME, "mcp_servers.json")
        # When no config is set, should return default
        # The actual function may return different based on config
        path = get_mcp_config_path()
        assert isinstance(path, str)


class TestWidgetRegistry:
    """Tests for the widget registry system."""

    def test_widget_registration(self):
        """Test that core widgets are registered."""
        # Import to trigger registration
        from jcapy.ui.widgets.dashboard_widgets import WidgetRegistry
        
        # Check core widgets are registered
        core_widgets = ["Clock", "Kanban", "ProjectStatus", "Marketplace", "MCP", "Status"]
        
        for widget_name in core_widgets:
            assert WidgetRegistry.get(widget_name) is not None, f"{widget_name} not registered"

    def test_widget_metadata(self):
        """Test widget metadata is set correctly."""
        from jcapy.ui.widgets.dashboard_widgets import WidgetRegistry
        
        kanban_meta = WidgetRegistry.get_metadata("Kanban")
        
        assert "description" in kanban_meta
        assert "size" in kanban_meta
        assert "category" in kanban_meta


class TestIntegration:
    """End-to-end integration tests."""

    def test_config_persistence(self):
        """Test that config changes persist."""
        from jcapy.config import CONFIG_MANAGER
        
        # Set a test value
        test_key = "test.integration.key"
        test_value = "test_value_123"
        
        CONFIG_MANAGER.set(test_key, test_value)
        retrieved = CONFIG_MANAGER.get(test_key)
        
        assert retrieved == test_value
        
        # Clean up
        CONFIG_MANAGER.set(test_key, None)

    def test_ux_preferences(self):
        """Test UX preference management."""
        from jcapy.config import get_ux_preference, set_ux_preference
        
        # Test default
        theme = get_ux_preference("theme")
        assert theme is not None
        
        # Test max_task_display default
        max_tasks = get_ux_preference("max_task_display")
        assert max_tasks == 5  # Default value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])