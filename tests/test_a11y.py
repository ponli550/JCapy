"""Tests for the a11y module (themes, screen reader, reduced motion)."""
import pytest
import os
from unittest.mock import patch
from jcapy.ui.ux.a11y import (
    THEMES, set_theme, get_theme, get_color,
    is_reduced_motion, format_for_screen_reader, get_spinner_style
)


class TestThemes:
    """Tests for theme management."""

    def test_default_theme_exists(self):
        """Verify default theme is defined."""
        assert "default" in THEMES
        assert "primary" in THEMES["default"]

    def test_high_contrast_theme_exists(self):
        """Verify high-contrast theme is defined."""
        assert "high-contrast" in THEMES
        assert "primary" in THEMES["high-contrast"]

    def test_monochrome_theme_exists(self):
        """Verify monochrome theme is defined."""
        assert "monochrome" in THEMES

    def test_set_theme_valid(self):
        """Verify setting a valid theme works."""
        original = get_theme()
        try:
            result = set_theme("high-contrast")
            assert result is True
            assert get_theme() == "high-contrast"
        finally:
            set_theme(original)

    def test_set_theme_invalid(self):
        """Verify setting invalid theme returns False."""
        result = set_theme("nonexistent")
        assert result is False


class TestGetColor:
    """Tests for theme-aware color retrieval."""

    def test_get_color_returns_ansi(self):
        """Verify get_color returns ANSI escape code."""
        color = get_color("primary")
        assert color.startswith("\033[")

    def test_get_color_fallback(self):
        """Verify unknown color falls back to text color."""
        color = get_color("unknown_color")
        assert color == get_color("text")


class TestReducedMotion:
    """Tests for reduced motion detection."""

    def test_reduced_motion_from_env(self):
        """Verify reduced motion detected from environment."""
        with patch.dict(os.environ, {"JCAPY_REDUCED_MOTION": "true"}):
            assert is_reduced_motion() is True

    def test_no_color_env_triggers_reduced_motion(self):
        """Verify NO_COLOR environment triggers reduced motion."""
        with patch.dict(os.environ, {"NO_COLOR": "1"}, clear=False):
            # Need to clear other env vars that might affect this
            with patch.dict(os.environ, {"JCAPY_REDUCED_MOTION": ""}, clear=False):
                result = is_reduced_motion()
                assert result is True

    def test_spinner_style_static_when_reduced(self):
        """Verify spinner style is static when reduced motion is on."""
        with patch('jcapy.ui.ux.a11y.is_reduced_motion', return_value=True):
            from jcapy.ui.ux import a11y
            # Need to reimport to get fresh function
            assert a11y.get_spinner_style() == "static"

    def test_spinner_style_dots_normally(self):
        """Verify spinner style is dots normally."""
        with patch('jcapy.ui.ux.a11y.is_reduced_motion', return_value=False):
            from jcapy.ui.ux import a11y
            assert a11y.get_spinner_style() == "dots"


class TestFormatForScreenReader:
    """Tests for screen reader text formatting."""

    def test_removes_emojis(self):
        """Verify emojis are removed for screen readers."""
        text = "🚀 Deploy complete! ✅"
        result = format_for_screen_reader(text)
        assert "🚀" not in result
        assert "✅" not in result
        assert "Deploy complete" in result

    def test_keeps_alphanumeric(self):
        """Verify alphanumeric characters are kept."""
        text = "Version 2.2.1 released"
        result = format_for_screen_reader(text)
        assert result == "Version 2.2.1 released"

    def test_handles_mixed_content(self):
        """Verify mixed content is cleaned properly."""
        text = "⚠️ Warning: 3 issues found!"
        result = format_for_screen_reader(text)
        assert "Warning" in result
        assert "3 issues found" in result
