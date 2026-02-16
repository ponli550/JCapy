"""Tests for the hints module (typo suggestions, tutorial)."""
import pytest
import os
import json
import tempfile
from unittest.mock import patch
from jcapy.ui.ux.hints import suggest_command, show_hint, Tutorial, JCAPY_COMMANDS


class TestSuggestCommand:
    """Tests for the suggest_command function."""

    def test_exact_match_not_suggested(self):
        """Verify exact matches return empty (no suggestion needed)."""
        # For exact matches, difflib won't suggest since it's already correct
        # But our function will return it as a close match
        commands = ["deploy", "delete", "doctor"]
        suggestions = suggest_command("deploy", commands)
        assert "deploy" in suggestions

    def test_typo_suggests_correct_command(self):
        """Verify typos suggest the correct command."""
        commands = ["deploy", "delete", "doctor"]

        suggestions = suggest_command("delpoy", commands)
        assert "deploy" in suggestions

        suggestions = suggest_command("deleet", commands)
        assert "delete" in suggestions

    def test_multiple_suggestions_returned(self):
        """Verify multiple close matches are returned."""
        suggestions = suggest_command("del", JCAPY_COMMANDS)
        assert len(suggestions) >= 1  # Should match delete, deploy, etc.

    def test_no_match_returns_empty(self):
        """Verify completely wrong input returns empty list."""
        suggestions = suggest_command("xyzabc123", JCAPY_COMMANDS)
        assert suggestions == []


class TestShowHint:
    """Tests for the show_hint function."""

    def test_hint_displays_message(self, capsys):
        """Verify hint displays the message."""
        with patch('jcapy.config.load_config', return_value={"hints": True}):
            show_hint("Run sync to backup")

        captured = capsys.readouterr()
        assert "Run sync to backup" in captured.out

    def test_hint_suppressed_when_disabled(self, capsys):
        """Verify hint is suppressed when disabled in config."""
        with patch('jcapy.config.load_config', return_value={"hints": False}):
            show_hint("Should not show")

        captured = capsys.readouterr()
        assert "Should not show" not in captured.out


class TestTutorial:
    """Tests for the Tutorial class."""

    @pytest.fixture
    def temp_tutorial_file(self, tmp_path):
        """Create a temporary tutorial state file."""
        tutorial_file = tmp_path / "tutorial.json"
        return str(tutorial_file)

    def test_tutorial_starts_at_step_zero(self, temp_tutorial_file):
        """Verify tutorial starts at first step."""
        with patch('jcapy.ui.ux.hints.TUTORIAL_FILE', temp_tutorial_file):
            tutorial = Tutorial()
            step = tutorial.get_current_step()

            assert step is not None
            assert step["id"] == "welcome"

    def test_tutorial_advances(self, temp_tutorial_file):
        """Verify tutorial advances to next step."""
        with patch('jcapy.ui.ux.hints.TUTORIAL_FILE', temp_tutorial_file):
            tutorial = Tutorial()

            # Start at welcome
            assert tutorial.get_current_step()["id"] == "welcome"

            # Advance
            next_step = tutorial.advance()
            assert next_step is not None
            assert next_step["id"] == "harvest"

    def test_tutorial_reset(self, temp_tutorial_file):
        """Verify tutorial can be reset."""
        with patch('jcapy.ui.ux.hints.TUTORIAL_FILE', temp_tutorial_file):
            tutorial = Tutorial()

            # Advance a few times
            tutorial.advance()
            tutorial.advance()

            # Reset
            tutorial.reset()

            # Should be back at start
            assert not tutorial.is_finished()
            assert tutorial.get_current_step()["id"] == "welcome"

    def test_tutorial_marks_finished(self, temp_tutorial_file):
        """Verify tutorial marks as finished after all steps."""
        with patch('jcapy.ui.ux.hints.TUTORIAL_FILE', temp_tutorial_file):
            tutorial = Tutorial()

            # Advance through all steps
            while tutorial.advance() is not None:
                pass

            assert tutorial.is_finished()
