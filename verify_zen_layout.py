import asyncio
import os
from textual.app import App
from textual.widgets import DirectoryTree, ListView, Button
from jcapy.ui.screens.dashboard import DashboardScreen
from jcapy.ui.widgets.dashboard_widgets import KanbanWidget, FileExplorerWidget, ConsoleDrawer

class MockApp(App):
    def on_mount(self):
        self.push_screen(DashboardScreen())

async def test_zen_layout():
    app = MockApp()
    async with app.run_test() as pilot:
        await pilot.pause()

        # Verify Sidebar elements
        sidebar = app.screen.query_one("#sidebar")
        assert sidebar is not None

        # Verify Main Area
        main_area = app.screen.query_one("#main-area")
        assert main_area is not None

        # Verify Core Widgets are still present
        # Note: Depending on DEFAULT_LAYOUT, they might be in different cols
        assert app.screen.query(KanbanWidget).first() is not None
        assert app.screen.query(FileExplorerWidget).first() is not None

        # Verify Console Drawer
        assert app.screen.query_one("#dashboard-console") is not None

        print("✅ Zen Layout Verification Passed!")

if __name__ == "__main__":
    asyncio.run(test_zen_layout())
