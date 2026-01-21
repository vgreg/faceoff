"""Scoreboard widget for displaying game score and status."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Label, Static

from faceoff.widgets.game_card import get_local_time_with_tz


class Scoreboard(Widget):
    """Widget displaying the current game score and status."""

    DEFAULT_CSS = """
    Scoreboard {
        width: 100%;
        height: auto;
        border: solid $primary;
        padding: 0 1;
    }

    Scoreboard .header {
        width: 100%;
        height: 1;
        text-align: center;
        text-style: bold;
    }

    Scoreboard .teams-container {
        width: 100%;
        height: auto;
        align: center middle;
    }

    Scoreboard .team-block {
        width: auto;
        min-width: 16;
        height: auto;
        align: center middle;
        padding: 0 1;
    }

    Scoreboard .team-name {
        text-align: center;
        text-style: bold;
        width: 100%;
    }

    Scoreboard .team-score {
        text-align: center;
        width: 100%;
        text-style: bold;
    }

    Scoreboard .team-score.-winning {
        color: $success;
    }

    Scoreboard .vs-label {
        width: auto;
        padding: 0 1;
    }

    Scoreboard .status-line {
        width: 100%;
        height: 1;
        text-align: center;
    }

    Scoreboard.-live .status-line {
        color: $success;
    }

    Scoreboard .period-scores {
        width: 100%;
        height: auto;
        align: center middle;
    }

    Scoreboard .period-header {
        width: 6;
        text-align: center;
        text-style: bold;
    }

    Scoreboard .period-score {
        width: 6;
        text-align: center;
    }
    """

    def __init__(self, game_data: dict, **kwargs) -> None:
        super().__init__(**kwargs)
        self.game_data = game_data

    def compose(self) -> ComposeResult:
        away = self.game_data.get("awayTeam", {})
        home = self.game_data.get("homeTeam", {})
        game_state = self.game_data.get("gameState", "FUT")

        away_name = away.get("name", {}).get("default", away.get("abbrev", "Away"))
        home_name = home.get("name", {}).get("default", home.get("abbrev", "Home"))
        away_abbrev = away.get("abbrev", "AWY")
        home_abbrev = home.get("abbrev", "HOM")

        away_score = away.get("score", 0)
        home_score = home.get("score", 0)

        # Venue info
        venue = self.game_data.get("venue", {}).get("default", "")

        with Vertical():
            yield Static(venue, classes="header")

            with Horizontal(classes="teams-container"):
                with Vertical(classes="team-block"):
                    yield Label(away_name, classes="team-name")
                    away_class = "team-score -winning" if away_score > home_score else "team-score"
                    yield Label(str(away_score) if game_state not in ("FUT", "PRE") else "-", classes=away_class)

                yield Label("@", classes="vs-label")

                with Vertical(classes="team-block"):
                    yield Label(home_name, classes="team-name")
                    home_class = "team-score -winning" if home_score > away_score else "team-score"
                    yield Label(str(home_score) if game_state not in ("FUT", "PRE") else "-", classes=home_class)

            yield Static(self._get_status_text(), classes="status-line")

            # Period-by-period scoring
            if game_state not in ("FUT", "PRE") and "periodDescriptor" in self.game_data:
                yield self._compose_period_scores(away_abbrev, home_abbrev)

    def _compose_period_scores(self, away_abbrev: str, home_abbrev: str) -> Widget:
        """Compose the period-by-period scoring table (placeholder)."""
        # Note: Period-by-period data is not currently available in game_data
        # This could be extended to show linescore if passed from GameScreen
        return Static("")

    def _get_status_text(self) -> str:
        """Get the status text for the game."""
        game_state = self.game_data.get("gameState", "FUT")

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
            time_remaining = clock.get("timeRemaining", "20:00")
            in_intermission = clock.get("inIntermission", False)

            if in_intermission:
                return f"{period_str} Intermission"
            return f"{period_str} Period - {time_remaining}"

        if game_state in ("FINAL", "OFF"):
            period = self.game_data.get("periodDescriptor", {})
            period_type = period.get("periodType", "REG")
            if period_type == "OT":
                return "Final (OT)"
            if period_type == "SO":
                return "Final (SO)"
            return "Final"

        return game_state

    def on_mount(self) -> None:
        """Apply CSS classes based on game state."""
        game_state = self.game_data.get("gameState", "FUT")
        if game_state in ("LIVE", "CRIT"):
            self.add_class("-live")

    def update_game(self, game_data: dict) -> None:
        """Update the game data and refresh the display."""
        self.game_data = game_data
        self.refresh(recompose=True)
