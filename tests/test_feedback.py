"""Tests for the feedback module (spinners, progress bars, banners)."""
import pytest
from unittest.mock import patch, MagicMock
from jcapy.ui.ux import feedback


class TestWithSpinner:
    """Tests for the with_spinner decorator."""

    def test_spinner_decorator_calls_function(self):
        """Verify decorated function is called and returns result."""
        @feedback.with_spinner("Testing...")
        def sample_func():
            return "success"

        result = sample_func()
        assert result == "success"

    def test_spinner_in_quiet_mode_skips_output(self):
        """Verify spinner is skipped in quiet mode."""
        feedback.set_quiet_mode(True)
        try:
            @feedback.with_spinner("Should not show")
            def sample_func():
                return "done"

            result = sample_func()
            assert result == "done"
        finally:
            feedback.set_quiet_mode(False)


class TestProgressBar:
    """Tests for the progress_bar context manager."""

    def test_progress_bar_update_callable(self):
        """Verify progress bar yields callable update function."""
        with feedback.progress_bar("Testing", total=3) as update:
            assert callable(update)
            update("Step 1")
            update("Step 2")
            update("Step 3")

    def test_progress_bar_quiet_mode(self):
        """Verify progress bar is skipped in quiet mode."""
        feedback.set_quiet_mode(True)
        try:
            with feedback.progress_bar("Testing", total=2) as update:
                update("Step 1")  # Should not raise
        finally:
            feedback.set_quiet_mode(False)


class TestBanners:
    """Tests for success/error/warning banners."""

    def test_show_success_no_hint(self, capsys):
        """Verify success message displays without hint."""
        feedback._quiet_mode = False
        # Use fallback mode (no Rich)
        with patch.object(feedback, 'HAS_RICH', False):
            feedback.show_success("Test passed")

        captured = capsys.readouterr()
        assert "Test passed" in captured.out

    def test_show_error_with_hint(self, capsys):
        """Verify error message displays with hint."""
        with patch.object(feedback, 'HAS_RICH', False):
            feedback.show_error("Test failed", hint="Check logs")

        captured = capsys.readouterr()
        assert "Test failed" in captured.out
        assert "Check logs" in captured.out

    def test_show_warning_quiet_mode_suppressed(self, capsys):
        """Verify warning is suppressed in quiet mode."""
        feedback.set_quiet_mode(True)
        try:
            feedback.show_warning("Should not show")
            captured = capsys.readouterr()
            assert "Should not show" not in captured.out
        finally:
            feedback.set_quiet_mode(False)
