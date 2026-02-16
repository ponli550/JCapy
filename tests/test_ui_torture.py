import pytest
from textual.pilot import Pilot
from jcapy.ui.app import JCapyApp
from jcapy.ui.widgets.output import CommandBlock

@pytest.mark.asyncio
async def test_torture_command():
    app = JCapyApp()
    async with app.run_test() as pilot:
        # 1. Run command directly (bypassing palette lookup since 'torture' isn't registered)
        # Note: run_command is sync and might block the main thread.
        # We call it directly. Textual's loop might be blocked during this call if logic is sync.
        app.run_command("torture")

        # 2. Yield to let UI process the mount event
        await pilot.pause(0.5)

        # 3. Check for CommandBlock in terminal scroll
        terminal = app.query_one("#terminal-scroll")
        assert terminal is not None

        # Get the generic CommandBlock
        blocks = terminal.query(CommandBlock)
        assert len(blocks) > 0, "No CommandBlock found after running torture command"

        last_block = blocks.last()
        content = last_block.output

        # 4. Assertions
        assert "🧪 Starting TUI Torture Test..." in content
        assert "Log line 49" in content # Burst check
        assert "Green ANSI" in content # ANSI check existence
        assert "This is a standard error message" in content # Stderr check
