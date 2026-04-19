"""Main Textual application for faceoff."""

from textual.app import App

from faceoff.api import NHLClient
from faceoff.screens import ScheduleScreen


class FaceoffApp(App):
    """Terminal application for watching NHL hockey games."""

    TITLE = "Faceoff"
    SUB_TITLE = "NHL Game Tracker"

    CSS = """
    Screen {
        background: $surface;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.client = NHLClient()

    def on_mount(self) -> None:
        """Set up the application when mounted."""
        self.push_screen(ScheduleScreen(self.client))

    async def on_unmount(self) -> None:
        """Clean up when application exits."""
        await self.client.aclose()
