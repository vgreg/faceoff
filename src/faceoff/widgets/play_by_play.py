"""Play-by-play widget for displaying game events."""

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.widgets import Label, Static


class PlayByPlay(Widget):
    """Widget displaying play-by-play events for a game."""

    DEFAULT_CSS = """
    PlayByPlay {
        width: 100%;
        height: 1fr;
        border: solid $primary;
    }

    PlayByPlay .header {
        width: 100%;
        height: 1;
        background: $primary;
        color: $text;
        text-align: center;
        text-style: bold;
        padding: 0 1;
    }

    PlayByPlay .plays-container {
        width: 100%;
        height: 1fr;
        padding: 0 1;
    }

    PlayByPlay .play-item {
        width: 100%;
        height: auto;
        margin: 0 0 1 0;
    }

    PlayByPlay .play-time {
        color: $text-muted;
        width: 8;
    }

    PlayByPlay .play-description {
        width: 1fr;
    }

    PlayByPlay .play-goal {
        color: $success;
        text-style: bold;
    }

    PlayByPlay .play-penalty {
        color: $warning;
    }

    PlayByPlay .play-period {
        width: 100%;
        height: 1;
        background: $surface;
        text-align: center;
        text-style: bold;
        margin: 1 0;
    }

    PlayByPlay .no-plays {
        width: 100%;
        height: 100%;
        align: center middle;
        color: $text-muted;
    }
    """

    def __init__(self, plays: list | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.plays = plays or []

    def compose(self) -> ComposeResult:
        yield Static("Play-by-Play", classes="header")

        with VerticalScroll(classes="plays-container"):
            if not self.plays:
                yield Label("No plays yet", classes="no-plays")
            else:
                current_period = None
                # Show plays in reverse order (newest first)
                for play in reversed(self.plays):
                    period_desc = play.get("periodDescriptor", {})
                    period_num = period_desc.get("number", 0)
                    period_type = period_desc.get("periodType", "REG")

                    # Period header
                    if period_type == "OT":
                        period_label = "Overtime"
                    elif period_type == "SO":
                        period_label = "Shootout"
                    else:
                        ordinals = {1: "1st", 2: "2nd", 3: "3rd"}
                        period_label = f"{ordinals.get(period_num, str(period_num))} Period"

                    if period_label != current_period:
                        current_period = period_label
                        yield Static(period_label, classes="play-period")

                    yield self._render_play(play)

    def _render_play(self, play: dict) -> Widget:  # noqa: C901
        """Render a single play event."""
        event_type = play.get("typeDescKey", "")
        time_in_period = play.get("timeInPeriod", "")
        desc = play.get("typeDescKey", "").replace("-", " ").title()

        # Get more detailed description based on event type
        details = play.get("details", {})

        # Determine CSS class based on event type
        css_class = "play-description"
        if event_type == "goal":
            css_class = "play-description play-goal"
            scorer = details.get("scoringPlayerTotal", details.get("scoredBy", ""))
            if isinstance(scorer, dict):
                scorer = scorer.get("name", {}).get("default", "")
            desc = f"GOAL - {scorer}" if scorer else "GOAL"

            # Add assists
            assists = []
            for key in ["assist1PlayerTotal", "assist2PlayerTotal"]:
                if key in details:
                    assist_data = details[key]
                    if isinstance(assist_data, dict):
                        assist_name = assist_data.get("name", {}).get("default", "")
                        if assist_name:
                            assists.append(assist_name)

            if assists:
                desc += f" (Assists: {', '.join(assists)})"

        elif event_type == "penalty":
            css_class = "play-description play-penalty"
            committed_by = details.get("committedByPlayer", "")
            if isinstance(committed_by, dict):
                committed_by = committed_by.get("name", {}).get("default", "")
            penalty_type = details.get("descKey", "penalty")
            minutes = details.get("duration", 2)
            desc = (
                f"PENALTY - {committed_by}: {penalty_type} ({minutes} min)"
                if committed_by
                else f"PENALTY ({minutes} min)"
            )

        elif event_type == "shot-on-goal":
            shooter = details.get("shootingPlayer", "")
            if isinstance(shooter, dict):
                shooter = shooter.get("name", {}).get("default", "")
            shot_type = details.get("shotType", "")
            desc = f"Shot on goal - {shooter}" if shooter else "Shot on goal"
            if shot_type:
                desc += f" ({shot_type})"

        elif event_type == "stoppage":
            reason = details.get("reason", "")
            desc = f"Stoppage - {reason}" if reason else "Stoppage"

        elif event_type == "faceoff":
            winner = details.get("winningPlayer", "")
            if isinstance(winner, dict):
                winner = winner.get("name", {}).get("default", "")
            desc = f"Faceoff won by {winner}" if winner else "Faceoff"

        text = f"{time_in_period:>6}  {desc}"
        return Label(text, classes=css_class)

    def update_plays(self, plays: list) -> None:
        """Update the plays list and refresh the display."""
        self.plays = plays
        self.refresh(recompose=True)
