from textual.widget import Widget
from textual.events import MouseDown, MouseUp, MouseMove
from textual.reactive import reactive
from textual.message import Message
from rich.text import Text

class SplitterUpdated(Message):
    """Message sent when a splitter has updated a target's dimension."""
    def __init__(self, target_id: str, dimension: str, value: int):
        super().__init__()
        self.target_id = target_id
        self.dimension = dimension  # "width" or "height"
        self.value = value

class VerticalSplitter(Widget):
    """A vertical splitter widget for manual resizing of adjacent widgets."""

    DEFAULT_CSS = """
    VerticalSplitter {
        width: 1;
        height: 100%;
        background: $accent 10%;
        border: none;
        content-align: center middle;
        color: $accent 40%;
    }
    VerticalSplitter:hover {
        background: $accent 40%;
        color: $accent;
    }
    VerticalSplitter.dragging {
        background: $accent 60%;
        color: $accent;
    }
    """

    dragging = reactive(False)

    def __init__(self, target_id: str, is_left: bool = True, min_width: int = 10, max_width: int = 100, **kwargs):
        super().__init__(**kwargs)
        self.target_id = target_id
        self.is_left = is_left
        self.min_width = min_width
        self.max_width = max_width
        self._initial_mouse_x = 0
        self._initial_target_width = 0

    def render(self) -> Text:
        # Sleek vertical handle indicator
        return Text("┇", style="bold")

    def on_mouse_down(self, event: MouseDown) -> None:
        self.dragging = True
        self.add_class("dragging")
        self.capture_mouse()
        self._initial_mouse_x = event.screen_x

        try:
            target = self.screen.query_one(f"#{self.target_id}")
            self._initial_target_width = target.size.width
        except:
            self.dragging = False

    def on_mouse_up(self, event: MouseUp) -> None:
        if self.dragging:
            self.dragging = False
            self.remove_class("dragging")
            self.release_mouse()

            # Emit update for persistence
            try:
                target = self.screen.query_one(f"#{self.target_id}")
                self.post_message(SplitterUpdated(self.target_id, "width", target.styles.width.value))
            except:
                pass

    def on_mouse_move(self, event: MouseMove) -> None:
        if self.dragging:
            delta_x = event.screen_x - self._initial_mouse_x
            if not self.is_left:
                delta_x = -delta_x

            new_width = max(self.min_width, min(self.max_width, self._initial_target_width + delta_x))

            try:
                target = self.screen.query_one(f"#{self.target_id}")
                target.styles.width = new_width
            except:
                pass


class HorizontalSplitter(Widget):
    """A horizontal splitter widget for manual resizing of adjacent widgets."""

    DEFAULT_CSS = """
    HorizontalSplitter {
        width: 100%;
        height: 1;
        background: $accent 10%;
        border: none;
        content-align: center middle;
        color: $accent 40%;
    }
    HorizontalSplitter:hover {
        background: $accent 40%;
        color: $accent;
    }
    HorizontalSplitter.dragging {
        background: $accent 60%;
        color: $accent;
    }
    """

    dragging = reactive(False)

    def __init__(self, target_id: str, is_top: bool = True, min_height: int = 5, max_height: int = 50, **kwargs):
        super().__init__(**kwargs)
        self.target_id = target_id
        self.is_top = is_top
        self.min_height = min_height
        self.max_height = max_height
        self._initial_mouse_y = 0
        self._initial_target_height = 0

    def render(self) -> Text:
        # Sleek horizontal handle indicator
        return Text("⋯", style="bold")

    def on_mouse_down(self, event: MouseDown) -> None:
        self.dragging = True
        self.add_class("dragging")
        self.capture_mouse()
        self._initial_mouse_y = event.screen_y

        try:
            target = self.screen.query_one(f"#{self.target_id}")
            self._initial_target_height = target.size.height
        except:
            self.dragging = False

    def on_mouse_up(self, event: MouseUp) -> None:
        if self.dragging:
            self.dragging = False
            self.remove_class("dragging")
            self.release_mouse()

            # Emit update for persistence
            try:
                target = self.screen.query_one(f"#{self.target_id}")
                self.post_message(SplitterUpdated(self.target_id, "height", target.styles.height.value))
            except:
                pass

    def on_mouse_move(self, event: MouseMove) -> None:
        if self.dragging:
            delta_y = event.screen_y - self._initial_mouse_y
            if not self.is_top:
                delta_y = -delta_y

            new_height = max(self.min_height, min(self.max_height, self._initial_target_height + delta_y))

            try:
                target = self.screen.query_one(f"#{self.target_id}")
                target.styles.height = new_height
            except:
                pass
