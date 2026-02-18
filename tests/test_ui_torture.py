import pytest
from textual.pilot import Pilot
from jcapy.ui.app import JCapyApp
from textual.widgets import RichLog

@pytest.mark.asyncio
async def test_torture_command():
    """Test that the app initializes correctly with the dual terminal layout."""
    app = JCapyApp()
    async with app.run_test() as pilot:
        # 1. Verify the dual terminal layout exists
        terminal_log = app.query_one("#terminal-log", RichLog)
        assert terminal_log is not None, "Terminal log should exist"

        history_log = app.query_one("#history-log", RichLog)
        assert history_log is not None, "History log should exist"

        # 2. Verify the app starts with a valid mode (INSERT because input is auto-focused)
        from jcapy.ui.modes import InputMode
        assert app.current_mode in (InputMode.NORMAL, InputMode.INSERT), "App should start in NORMAL or INSERT mode"

        # 3. Test mode switching - switch to NORMAL first
        app.action_switch_mode("normal")
        assert app.current_mode == InputMode.NORMAL, "Mode should switch to NORMAL"

        # 4. Test switching to INSERT
        app.action_switch_mode("insert")
        assert app.current_mode == InputMode.INSERT, "Mode should switch to INSERT"

        # 5. Test grammar processor exists
        assert app.grammar is not None, "Grammar processor should be initialized"
