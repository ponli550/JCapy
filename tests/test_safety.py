"""Tests for the safety module (undo stack, confirmations)."""
import pytest
import os
import tempfile
import shutil
from unittest.mock import patch
from jcapy.ui.ux.safety import UndoStack, confirm, require_dependency


class TestUndoStack:
    """Tests for the UndoStack class."""

    @pytest.fixture
    def temp_undo_dir(self, tmp_path):
        """Create a temporary undo directory."""
        undo_dir = tmp_path / "undo"
        undo_dir.mkdir()
        return str(undo_dir)

    @pytest.fixture
    def test_file(self, tmp_path):
        """Create a test file for backup."""
        test_file = tmp_path / "test_skill.md"
        test_file.write_text("# Test Skill\nContent here")
        return str(test_file)

    def test_push_creates_backup(self, temp_undo_dir, test_file):
        """Verify push creates a backup file."""
        with patch('jcapy.ui.ux.safety.UNDO_DIR', temp_undo_dir):
            with patch('jcapy.ui.ux.safety.UNDO_MANIFEST', os.path.join(temp_undo_dir, 'manifest.json')):
                stack = UndoStack()
                backup_path = stack.push("delete", test_file, "Test backup")

                assert os.path.exists(backup_path)
                assert len(stack.list_items()) == 1

    def test_pop_restores_file(self, temp_undo_dir, test_file):
        """Verify pop restores the original file."""
        with patch('jcapy.ui.ux.safety.UNDO_DIR', temp_undo_dir):
            with patch('jcapy.ui.ux.safety.UNDO_MANIFEST', os.path.join(temp_undo_dir, 'manifest.json')):
                stack = UndoStack()
                stack.push("delete", test_file, "Test backup")

                # Delete original
                os.remove(test_file)
                assert not os.path.exists(test_file)

                # Restore
                restored = stack.pop()
                assert restored is not None
                assert os.path.exists(test_file)

    def test_max_items_enforced(self, temp_undo_dir, tmp_path):
        """Verify only MAX_UNDO_ITEMS are kept."""
        with patch('jcapy.ui.ux.safety.UNDO_DIR', temp_undo_dir):
            with patch('jcapy.ui.ux.safety.UNDO_MANIFEST', os.path.join(temp_undo_dir, 'manifest.json')):
                with patch('jcapy.ui.ux.safety.MAX_UNDO_ITEMS', 2):
                    stack = UndoStack()

                    # Create 3 test files
                    for i in range(3):
                        f = tmp_path / f"skill{i}.md"
                        f.write_text(f"Content {i}")
                        stack.push("delete", str(f))

                    # Should only have 2 items
                    assert len(stack.list_items()) == 2


class TestConfirm:
    """Tests for the confirm function."""

    def test_confirm_destructive_default_no(self):
        """Verify destructive confirm defaults to No."""
        with patch('builtins.input', return_value=''):
            result = confirm("Delete?", destructive=True)
            assert result is False

    def test_confirm_non_destructive_default_yes(self):
        """Verify non-destructive confirm defaults to Yes."""
        with patch('builtins.input', return_value=''):
            result = confirm("Continue?", destructive=False)
            assert result is True

    def test_confirm_accepts_y(self):
        """Verify 'y' is accepted as confirmation."""
        with patch('builtins.input', return_value='y'):
            result = confirm("Delete?", destructive=True)
            assert result is True

    def test_confirm_auto_yes_bypasses(self):
        """Verify auto_yes=True bypasses prompt."""
        result = confirm("Delete?", destructive=True, auto_yes=True)
        assert result is True


class TestRequireDependency:
    """Tests for the require_dependency decorator."""

    def test_decorator_calls_function_when_available(self):
        """Verify function is called when dependency is available."""
        @require_dependency("os")  # os is always available
        def sample_func():
            return "success"

        assert sample_func() == "success"

    def test_decorator_uses_fallback_when_missing(self):
        """Verify fallback is used when dependency is missing."""
        def fallback():
            return "fallback"

        @require_dependency("nonexistent_module_xyz", fallback=fallback)
        def sample_func():
            return "original"

        assert sample_func() == "fallback"
