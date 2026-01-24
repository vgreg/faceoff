"""Game card widget for displaying a single game in the schedule."""

from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Label, Static


def get_local_time_with_tz(utc_time_str: str) -> str:
    """Convert UTC time string to local time with timezone abbreviation."""
    if not utc_time_str:
        return ""
    try:
        # Parse UTC time
        dt_utc = datetime.fromisoformat(utc_time_str.replace("Z", "+00:00"))
        # Convert to local time
        dt_local = dt_utc.astimezone()
        # Format time with timezone
        time_str = dt_local.strftime("%I:%M %p")
        # Get timezone abbreviation
        tz_abbrev = dt_local.strftime("%Z")
        # If no abbreviation available, show offset
        if not tz_abbrev or tz_abbrev == dt_local.strftime("%z"):
            offset = dt_local.strftime("%z")
            if offset and len(offset) >= 5:
                tz_abbrev = f"UTC{offset[:3]}:{offset[3:]}"
            elif offset:
                tz_abbrev = f"UTC{offset}"
            else:
                tz_abbrev = "UTC"
    except (ValueError, AttributeError, IndexError):
        return ""
    else:
        return f"{time_str} {tz_abbrev}"


class GameCard(Widget):
    """A card widget displaying a single game's status."""

    DEFAULT_CSS = """
    GameCard {
        width: 28;
        height: 5;
        border: solid $primary;
        padding: 0 1;
        margin: 0 1 0 0;
    }

    GameCard:hover {
        border: solid $secondary;
    }

    GameCard:focus {
        border: double $accent;
    }

    GameCard.-live {
        border: solid $success;
    }

    GameCard.-live:focus {
        border: double $accent;
    }

    GameCard.-final {
        border: solid $surface;
    }

    GameCard.-final:focus {
        border: double $accent;
    }

    GameCard .team-row {
        width: 100%;
        height: 1;
    }

    GameCard .team-name {
        width: 1fr;
    }

    GameCard .team-score {
        width: 3;
        text-align: right;
    }

    GameCard .game-status {
        width: 100%;
        height: 1;
        text-align: center;
        color: $text-muted;
    }

    GameCard.-live .game-status {
        color: $success;
    }
    """

    can_focus = True

    class Selected(Message):
        """Message sent when a game card is selected."""

        def __init__(self, game_id: int, game_data: dict) -> None:
            self.game_id = game_id
            self.game_data = game_data
            super().__init__()

    def __init__(self, game_data: dict, **kwargs) -> None:
        super().__init__(**kwargs)
        self.game_data = game_data
        self.game_id = game_data.get("id", 0)

    def compose(self) -> ComposeResult:
        away = self.game_data.get("awayTeam", {})
        home = self.game_data.get("homeTeam", {})
        game_state = self.game_data.get("gameState", "FUT")

        away_name = away.get("abbrev", "???")
        home_name = home.get("abbrev", "???")

        away_score = away.get("score", "-")
        home_score = home.get("score", "-")

        # Determine game status text
        status = self._get_status_text()

        with Vertical():
            with Horizontal(classes="team-row"):
                yield Label(f"{away_name}", classes="team-name")
                yield Label(f"{away_score}" if game_state not in ("FUT", "PRE") else "", classes="team-score")
            with Horizontal(classes="team-row"):
                yield Label(f"{home_name}", classes="team-name")
                yield Label(f"{home_score}" if game_state not in ("FUT", "PRE") else "", classes="team-score")
            yield Static(status, classes="game-status")

    def _get_status_text(self) -> str:  # noqa: C901
        """Get the status text for the game."""
        game_state = self.game_data.get("gameState", "FUT")
        game_schedule_state = self.game_data.get("gameScheduleState", "OK")

        if game_schedule_state == "PPD":
            return "Postponed"
        if game_schedule_state == "CNCL":
            return "Cancelled"

        if game_state == "FUT":
            start_time = self.game_data.get("startTimeUTC", "")
            local_time = get_local_time_with_tz(start_time)
            return local_time if local_time else "Scheduled"

        if game_state == "PRE":
            return "Pre-game"

        if game_state in ("LIVE", "CRIT"):
            period = self.game_data.get("periodDescriptor", {})
            period_num = period.get("number", 0)
            period_type = period.get("periodType", "REG")

            if period_type == "OT":
                period_str = "OT"
            elif period_type == "SO":
                period_str = "SO"
            else:
                ordinals = {1: "1st", 2: "2nd", 3: "3rd"}
                period_str = ordinals.get(period_num, f"{period_num}th")

            clock = self.game_data.get("clock", {})
            time_remaining = clock.get("timeRemaining", "")
            in_intermission = clock.get("inIntermission", False)

            if in_intermission:
                return f"{period_str} INT"
            return f"{period_str} {time_remaining}"

        if game_state in ("FINAL", "OFF"):
            period = self.game_data.get("periodDescriptor", {})
            period_type = period.get("periodType", "REG")
            if period_type == "OT":
                return "Final/OT"
            if period_type == "SO":
                return "Final/SO"
            return "Final"

        return game_state

    def on_mount(self) -> None:
        """Apply CSS classes based on game state."""
        game_state = self.game_data.get("gameState", "FUT")
        if game_state in ("LIVE", "CRIT"):
            self.add_class("-live")
        elif game_state in ("FINAL", "OFF"):
            self.add_class("-final")

    def on_click(self) -> None:
        """Handle click event."""
        self.post_message(self.Selected(self.game_id, self.game_data))

    def on_key(self, event) -> None:
        """Handle key events."""
        if event.key == "enter":
            self.post_message(self.Selected(self.game_id, self.game_data))
            event.stop()
