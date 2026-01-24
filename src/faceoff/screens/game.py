"""Game screen for viewing a single game's details."""

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import Footer, Header, Label, Static

from faceoff.api import NHLClient

# Minimum width for side-by-side layout
WIDE_LAYOUT_MIN_WIDTH = 100


class GameScreen(Screen):
    """Screen for viewing a single game's details."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape,b", "back", "Back"),
        Binding("r", "refresh", "Refresh"),
        Binding("q", "quit", "Quit"),
    ]

    DEFAULT_CSS = """
    GameScreen {
        background: $surface;
    }

    GameScreen .game-content {
        width: 100%;
        height: 1fr;
    }

    GameScreen .main-content {
        width: 100%;
        height: auto;
        padding: 0 1;
    }

    GameScreen .left-panel {
        width: 1fr;
        height: auto;
    }

    GameScreen .right-panel {
        width: 1fr;
        height: auto;
        margin-left: 1;
    }

    GameScreen .score-box {
        width: 100%;
        height: auto;
        border: solid $primary;
        margin-bottom: 1;
        padding: 0 1;
    }

    GameScreen .score-line {
        width: 100%;
        height: 1;
    }

    GameScreen .score-away {
        width: 5;
        text-style: bold;
    }

    GameScreen .score-vs {
        width: 3;
        text-align: center;
    }

    GameScreen .score-home {
        width: 5;
        text-style: bold;
    }

    GameScreen .score-away-val {
        width: 3;
        text-align: right;
    }

    GameScreen .score-separator {
        width: 3;
        text-align: center;
    }

    GameScreen .score-home-val {
        width: 3;
        text-align: left;
    }

    GameScreen .score-home-val.-winning {
        color: $success;
    }

    GameScreen .score-away-val.-winning {
        color: $success;
    }

    GameScreen .score-status {
        width: 1fr;
        text-align: right;
        color: $success;
    }

    GameScreen .section-title {
        text-style: bold;
        background: $primary;
        padding: 0 1;
        width: 100%;
    }

    GameScreen .goals-section {
        width: 100%;
        height: auto;
        border: solid $primary;
        margin-bottom: 1;
    }

    GameScreen .goal-row {
        width: 100%;
        height: 1;
        padding: 0 1;
    }

    GameScreen .goal-time {
        width: 10;
        color: $text-muted;
    }

    GameScreen .goal-team {
        width: 5;
        text-style: bold;
        margin-left: 1;
    }

    GameScreen .goal-scorer {
        width: 1fr;
        color: $success;
    }

    GameScreen .goal-assists {
        width: 1fr;
        color: $text-muted;
    }

    GameScreen .stats-section {
        width: 100%;
        height: auto;
        border: solid $primary;
        margin-bottom: 1;
    }

    GameScreen .stats-header {
        width: 100%;
        height: 1;
        padding: 0 1;
    }

    GameScreen .stats-away {
        width: 6;
        text-align: right;
        text-style: bold;
    }

    GameScreen .stats-label {
        width: 1fr;
        text-align: center;
    }

    GameScreen .stats-home {
        width: 6;
        text-align: left;
        text-style: bold;
    }

    GameScreen .stats-row {
        width: 100%;
        height: 1;
        padding: 0 1;
    }

    GameScreen .pbp-section {
        width: 100%;
        height: auto;
        border: solid $primary;
    }

    GameScreen .pbp-section.-scrollable {
        height: 20;
        max-height: 20;
    }

    GameScreen .pbp-scroll {
        width: 100%;
        height: 100%;
    }

    GameScreen .pbp-item {
        width: 100%;
        height: auto;
        padding: 0 1;
    }

    GameScreen .pbp-team {
        width: 5;
        text-style: bold;
        margin-right: 1;
    }

    GameScreen .pbp-time {
        width: 8;
        color: $text-muted;
    }

    GameScreen .pbp-event {
        width: 1fr;
    }

    GameScreen .pbp-goal {
        color: $success;
        text-style: bold;
    }

    GameScreen .pbp-penalty {
        color: $warning;
    }

    GameScreen .pbp-period {
        width: 100%;
        background: $surface-lighten-1;
        text-style: bold;
        text-align: center;
        padding: 0 1;
        margin: 1 0;
    }

    GameScreen .no-data {
        color: $text-muted;
        padding: 1;
    }
    """

    REFRESH_INTERVAL: ClassVar[int] = 30  # Seconds between auto-refreshes

    def __init__(self, client: NHLClient, game_id: int, game_data: dict, **kwargs) -> None:
        super().__init__(**kwargs)
        self.client = client
        self.game_id = game_id
        self.game_data = game_data
        self.boxscore: dict = {}
        self.play_by_play: list = []
        self.scoring_summary: list = []  # From landing page
        self._refresh_timer: Timer | None = None
        self._countdown_timer: Timer | None = None
        self._countdown: int = self.REFRESH_INTERVAL
        self._last_width: int = 0

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(classes="game-content", id="game-content"):
            yield Horizontal(classes="main-content", id="main-content")
        yield Footer()

    def on_mount(self) -> None:
        """Load game data when screen is mounted."""
        self.load_game_data()

        # Set up auto-refresh for pre-game and live games
        game_state = self.game_data.get("gameState", "FUT")
        if game_state in ("PRE", "LIVE", "CRIT"):
            self._countdown = self.REFRESH_INTERVAL
            self._refresh_timer = self.set_interval(30, callback=self._auto_refresh)  # type: ignore[arg-type]
            self._countdown_timer = self.set_interval(1, callback=self._update_countdown)
            self._update_subtitle()

    def on_unmount(self) -> None:
        """Clean up when screen is unmounted."""
        if self._refresh_timer:
            self._refresh_timer.stop()
        if self._countdown_timer:
            self._countdown_timer.stop()

    def on_resize(self, event) -> None:
        """Handle resize to adjust layout."""
        try:
            content = self.query_one("#game-content", VerticalScroll)
            new_width = content.size.width
        except Exception:
            return

        # Only re-layout if width changed significantly
        if abs(new_width - self._last_width) >= 20:
            self._last_width = new_width
            self._update_main_content()

    def load_game_data(self) -> None:
        """Load detailed game data."""
        self.run_worker(self._fetch_game_data())

    async def _fetch_game_data(self) -> None:
        """Fetch game data from the API."""
        try:
            # Fetch boxscore, play-by-play, and landing page
            self.boxscore = self.client.get_game_boxscore(self.game_id)
            pbp_data = self.client.get_game_play_by_play(self.game_id)
            landing = self.client.get_game_landing(self.game_id)

            # Update game data from boxscore
            if self.boxscore:
                self._update_game_from_boxscore()

            # Extract plays
            self.play_by_play = pbp_data.get("plays", [])

            # Extract scoring summary from landing page (has player names)
            summary = landing.get("summary", {})
            self.scoring_summary = []
            for period in summary.get("scoring", []):
                period_desc = period.get("periodDescriptor", {})
                for goal in period.get("goals", []):
                    # Add period info to each goal
                    goal["periodDescriptor"] = period_desc
                    self.scoring_summary.append(goal)

            self._update_display()
        except Exception as e:
            self.notify(f"Error loading game data: {e}", severity="error")

    def _update_game_from_boxscore(self) -> None:
        """Update game data from boxscore response."""
        if "awayTeam" in self.boxscore:
            self.game_data["awayTeam"] = self.boxscore["awayTeam"]
        if "homeTeam" in self.boxscore:
            self.game_data["homeTeam"] = self.boxscore["homeTeam"]
        if "gameState" in self.boxscore:
            self.game_data["gameState"] = self.boxscore["gameState"]
        if "clock" in self.boxscore:
            self.game_data["clock"] = self.boxscore["clock"]
        if "periodDescriptor" in self.boxscore:
            self.game_data["periodDescriptor"] = self.boxscore["periodDescriptor"]

    def _update_display(self) -> None:
        """Update all display components."""
        self._update_main_content()

    def _is_wide_layout(self) -> bool:
        """Check if we should use wide (side-by-side) layout."""
        try:
            content = self.query_one("#game-content", VerticalScroll)
        except Exception:
            return False
        else:
            return content.size.width >= WIDE_LAYOUT_MIN_WIDTH

    def _update_main_content(self) -> None:
        """Update the main content area with goals, stats, and play-by-play."""
        container = self.query_one("#main-content", Horizontal)
        container.remove_children()

        if not self.boxscore:
            container.mount(Label("Loading game data...", classes="no-data"))
            return

        wide = self._is_wide_layout()

        if wide:
            # Side-by-side layout: left panel (score + goals + stats), right panel (play-by-play)
            left_panel = Vertical(classes="left-panel")
            left_panel.compose_add_child(self._build_score_box())
            left_panel.compose_add_child(self._build_goals_section())
            left_panel.compose_add_child(self._build_stats_section())

            right_panel = Vertical(classes="right-panel")
            right_panel.compose_add_child(self._build_pbp_section(scrollable=True))

            container.mount(left_panel)
            container.mount(right_panel)
        else:
            # Stacked layout: score, goals, stats, then play-by-play
            single_panel = Vertical(classes="left-panel")
            single_panel.compose_add_child(self._build_score_box())
            single_panel.compose_add_child(self._build_goals_section())
            single_panel.compose_add_child(self._build_stats_section())
            single_panel.compose_add_child(self._build_pbp_section(scrollable=False))
            container.mount(single_panel)

    def _build_score_box(self) -> Vertical:
        """Build a compact score display box."""
        section = Vertical(classes="score-box")

        away_team = self.boxscore.get("awayTeam", {})
        home_team = self.boxscore.get("homeTeam", {})
        away_abbrev = away_team.get("abbrev", "AWY")
        home_abbrev = home_team.get("abbrev", "HOM")
        away_score = away_team.get("score", 0)
        home_score = home_team.get("score", 0)
        game_state = self.game_data.get("gameState", "FUT")

        # Score line: BOS @ DAL  1 - 6  3rd 06:01
        score_line = Horizontal(classes="score-line")
        score_line.compose_add_child(Label(away_abbrev, classes="score-away"))
        score_line.compose_add_child(Label("@", classes="score-vs"))
        score_line.compose_add_child(Label(home_abbrev, classes="score-home"))

        away_class = "score-away-val -winning" if away_score > home_score else "score-away-val"
        home_class = "score-home-val -winning" if home_score > away_score else "score-home-val"

        if game_state not in ("FUT", "PRE"):
            score_line.compose_add_child(Label(str(away_score), classes=away_class))
            score_line.compose_add_child(Label("-", classes="score-separator"))
            score_line.compose_add_child(Label(str(home_score), classes=home_class))
        else:
            score_line.compose_add_child(Label("-", classes="score-away-val"))
            score_line.compose_add_child(Label("-", classes="score-separator"))
            score_line.compose_add_child(Label("-", classes="score-home-val"))

        # Status text
        status = self._get_status_text()
        score_line.compose_add_child(Label(status, classes="score-status"))

        section.compose_add_child(score_line)
        return section

    def _get_status_text(self) -> str:
        """Get game status text."""
        game_state = self.game_data.get("gameState", "FUT")

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

        if game_state == "PRE":
            return "Pre-game"

        return game_state

    def _build_goals_section(self) -> Vertical:
        """Build the goals/scoring summary section."""
        section = Vertical(classes="goals-section")
        section.compose_add_child(Static("Scoring Summary", classes="section-title"))

        if not self.scoring_summary:
            section.compose_add_child(Label("No goals scored yet", classes="no-data"))
            return section

        for goal in self.scoring_summary:
            row = self._build_goal_row(goal)
            section.compose_add_child(row)

        return section

    def _build_goal_row(self, goal: dict) -> Horizontal:
        """Build a single goal row widget."""
        # Get period info
        period_desc = goal.get("periodDescriptor", {}) if "periodDescriptor" in goal else {}
        period_num = period_desc.get("number", 0)
        period_type = period_desc.get("periodType", "REG")

        if period_type == "OT":
            period_label = "OT"
        elif period_type == "SO":
            period_label = "SO"
        else:
            period_label = f"P{period_num}"

        time_in_period = goal.get("timeInPeriod", "")
        team = goal.get("teamAbbrev", {}).get("default", "???")

        # Get scorer name from landing page data
        scorer_name = goal.get("name", {}).get("default", "")
        if not scorer_name:
            first = goal.get("firstName", {}).get("default", "")
            last = goal.get("lastName", {}).get("default", "")
            scorer_name = f"{first} {last}".strip()

        # Get assists from landing page data
        assists = []
        for assist in goal.get("assists", []):
            assist_name = assist.get("name", {}).get("default", "")
            if not assist_name:
                first = assist.get("firstName", {}).get("default", "")
                last = assist.get("lastName", {}).get("default", "")
                assist_name = f"{first} {last}".strip()
            if assist_name:
                assists.append(assist_name)

        row = Horizontal(classes="goal-row")
        row.compose_add_child(Label(f"{period_label} {time_in_period}", classes="goal-time"))
        row.compose_add_child(Label(team, classes="goal-team"))
        row.compose_add_child(Label(scorer_name or "Goal", classes="goal-scorer"))
        if assists:
            row.compose_add_child(Label(f"({', '.join(assists)})", classes="goal-assists"))
        return row

    def _build_stats_section(self) -> Vertical:
        """Build the game stats comparison section."""
        section = Vertical(classes="stats-section")

        away_team = self.boxscore.get("awayTeam", {})
        home_team = self.boxscore.get("homeTeam", {})
        away_abbrev = away_team.get("abbrev", "AWY")
        home_abbrev = home_team.get("abbrev", "HOM")

        # Header with team names
        header = Horizontal(classes="stats-header")
        header.compose_add_child(Label(away_abbrev, classes="stats-away"))
        header.compose_add_child(Label("Game Stats", classes="stats-label"))
        header.compose_add_child(Label(home_abbrev, classes="stats-home"))
        section.compose_add_child(header)

        # Get team stats - sog is directly on team, others need aggregation
        away_sog = away_team.get("sog", 0)
        home_sog = home_team.get("sog", 0)

        # Aggregate stats from player data
        away_stats = self._aggregate_team_stats("awayTeam")
        home_stats = self._aggregate_team_stats("homeTeam")

        # Stats to display
        stats_rows = [
            (str(away_sog), "Shots", str(home_sog)),
            (f"{away_stats['faceoffPct']:.0%}", "Faceoff %", f"{home_stats['faceoffPct']:.0%}"),
            (f"{away_stats['ppg']}/{away_stats['ppo']}", "Power Play", f"{home_stats['ppg']}/{home_stats['ppo']}"),
            (str(away_stats["pim"]), "PIM", str(home_stats["pim"])),
            (str(away_stats["hits"]), "Hits", str(home_stats["hits"])),
            (str(away_stats["blocks"]), "Blocked Shots", str(home_stats["blocks"])),
            (str(away_stats["giveaways"]), "Giveaways", str(home_stats["giveaways"])),
            (str(away_stats["takeaways"]), "Takeaways", str(home_stats["takeaways"])),
        ]

        for away_val, label, home_val in stats_rows:
            row = Horizontal(classes="stats-row")
            row.compose_add_child(Label(away_val, classes="stats-away"))
            row.compose_add_child(Label(label, classes="stats-label"))
            row.compose_add_child(Label(home_val, classes="stats-home"))
            section.compose_add_child(row)

        return section

    def _aggregate_team_stats(self, team_key: str) -> dict:
        """Aggregate team stats from individual player stats."""
        player_stats = self.boxscore.get("playerByGameStats", {}).get(team_key, {})

        totals = {
            "hits": 0,
            "pim": 0,
            "blocks": 0,
            "giveaways": 0,
            "takeaways": 0,
            "ppg": 0,
            "ppo": 0,
            "faceoffWins": 0,
            "faceoffTotal": 0,
        }

        # Aggregate from forwards and defense
        for position in ["forwards", "defense"]:
            for player in player_stats.get(position, []):
                totals["hits"] += player.get("hits", 0)
                totals["pim"] += player.get("pim", 0)
                totals["blocks"] += player.get("blockedShots", 0)
                totals["giveaways"] += player.get("giveaways", 0)
                totals["takeaways"] += player.get("takeaways", 0)
                totals["ppg"] += player.get("powerPlayGoals", 0)

                # Faceoff percentage - need to calculate weighted average
                fo_pct = player.get("faceoffWinningPctg", 0)
                if fo_pct > 0:
                    # Estimate faceoffs taken (not exact but reasonable)
                    totals["faceoffTotal"] += 1
                    totals["faceoffWins"] += fo_pct

        # Calculate faceoff percentage
        if totals["faceoffTotal"] > 0:
            totals["faceoffPct"] = totals["faceoffWins"] / totals["faceoffTotal"]
        else:
            totals["faceoffPct"] = 0

        return totals

    def _build_pbp_section(self, scrollable: bool = False) -> Vertical:
        """Build the play-by-play section."""
        classes = "pbp-section -scrollable" if scrollable else "pbp-section"
        section = Vertical(classes=classes)
        section.compose_add_child(Static("Play-by-Play", classes="section-title"))

        if not self.play_by_play:
            section.compose_add_child(Label("No plays yet", classes="no-data"))
            return section

        # Get team info for play descriptions
        away_id = self.boxscore.get("awayTeam", {}).get("id")
        home_id = self.boxscore.get("homeTeam", {}).get("id")
        away_abbrev = self.boxscore.get("awayTeam", {}).get("abbrev", "AWY")
        home_abbrev = self.boxscore.get("homeTeam", {}).get("abbrev", "HOM")
        team_map = {away_id: away_abbrev, home_id: home_abbrev}

        # Use VerticalScroll if scrollable
        if scrollable:
            scroll = VerticalScroll(classes="pbp-scroll")
            container = scroll
        else:
            container = section

        current_period = None

        # Show plays in reverse order (most recent first)
        for play in reversed(self.play_by_play):
            period_desc = play.get("periodDescriptor", {})
            period_num = period_desc.get("number", 0)
            period_type = period_desc.get("periodType", "REG")

            if period_type == "OT":
                period_label = "Overtime"
            elif period_type == "SO":
                period_label = "Shootout"
            else:
                ordinals = {1: "1st Period", 2: "2nd Period", 3: "3rd Period"}
                period_label = ordinals.get(period_num, f"{period_num}th Period")

            # Add period header if changed
            if period_label != current_period:
                current_period = period_label
                container.compose_add_child(Static(period_label, classes="pbp-period"))

            # Render play with team info
            play_widget = self._render_play(play, team_map)
            if play_widget:
                container.compose_add_child(play_widget)

        if scrollable:
            section.compose_add_child(scroll)

        return section

    def _render_play(self, play: dict, team_map: dict | None = None) -> Horizontal | None:
        """Render a single play event."""
        event_type = play.get("typeDescKey", "")
        time_in_period = play.get("timeInPeriod", "")
        details = play.get("details", {})

        # Skip certain event types to reduce noise
        if event_type in ("game-end", "period-start", "period-end"):
            return None

        # Get team abbreviation for this event
        team_abbrev = ""
        if team_map:
            event_team_id = details.get("eventOwnerTeamId")
            team_abbrev = team_map.get(event_team_id, "")

        # Get description and CSS class for this event type
        result = self._get_play_description(event_type, details, team_abbrev)
        if result is None:
            return None

        desc, css_class = result
        if not desc:
            return None

        row = Horizontal(classes="pbp-item")
        row.compose_add_child(Label(f"{time_in_period:>6}", classes="pbp-time"))
        if team_abbrev:
            row.compose_add_child(Label(team_abbrev, classes="pbp-team"))
        row.compose_add_child(Label(desc, classes=css_class))
        return row

    def _get_play_description(self, event_type: str, details: dict, team_abbrev: str = "") -> tuple[str, str] | None:
        """Get description and CSS class for a play event type."""
        handlers = {
            "goal": self._describe_goal,
            "penalty": self._describe_penalty,
            "shot-on-goal": self._describe_shot,
            "blocked-shot": self._describe_blocked_shot,
            "missed-shot": self._describe_missed_shot,
            "hit": self._describe_hit,
            "giveaway": self._describe_giveaway,
            "takeaway": self._describe_takeaway,
            "faceoff": self._describe_faceoff,
            "stoppage": self._describe_stoppage,
        }
        handler = handlers.get(event_type)
        return handler(details) if handler else None

    def _describe_goal(self, details: dict) -> tuple[str, str]:
        """Get description for a goal event."""
        scorer = self._get_player_name(details, "scoringPlayerTotal", "scoredBy")
        desc = f"GOAL - {scorer}" if scorer else "GOAL"
        assists = self._get_assists(details)
        if assists:
            desc += f" ({', '.join(assists)})"
        return (desc, "pbp-event pbp-goal")

    def _describe_penalty(self, details: dict) -> tuple[str, str]:
        """Get description for a penalty event."""
        player = self._get_player_name(details, "committedByPlayer")
        penalty_type = details.get("descKey", "penalty")
        minutes = details.get("duration", 2)
        desc = f"PENALTY - {player}: {penalty_type} ({minutes} min)" if player else f"PENALTY ({minutes} min)"
        return (desc, "pbp-event pbp-penalty")

    def _describe_hit(self, details: dict) -> tuple[str, str]:
        """Get description for a hit event."""
        hitter = self._get_player_name(details, "hittingPlayer")
        hittee = self._get_player_name(details, "hitteePlayer")
        if hitter and hittee:
            desc = f"Hit - {hitter} on {hittee}"
        elif hitter:
            desc = f"Hit - {hitter}"
        else:
            desc = "Hit"
        return (desc, "pbp-event")

    def _describe_shot(self, details: dict) -> tuple[str, str]:
        """Get description for a shot on goal event."""
        shooter = self._get_player_name(details, "shootingPlayer")
        return (f"Shot - {shooter}" if shooter else "Shot on goal", "pbp-event")

    def _describe_blocked_shot(self, details: dict) -> tuple[str, str]:
        """Get description for a blocked shot event."""
        blocker = self._get_player_name(details, "blockingPlayer")
        return (f"Blocked shot - {blocker}" if blocker else "Blocked shot", "pbp-event")

    def _describe_missed_shot(self, details: dict) -> tuple[str, str]:
        """Get description for a missed shot event."""
        shooter = self._get_player_name(details, "shootingPlayer")
        return (f"Missed shot - {shooter}" if shooter else "Missed shot", "pbp-event")

    def _describe_giveaway(self, details: dict) -> tuple[str, str]:
        """Get description for a giveaway event."""
        player = self._get_player_name(details, "playerId")
        return (f"Giveaway - {player}" if player else "Giveaway", "pbp-event")

    def _describe_takeaway(self, details: dict) -> tuple[str, str]:
        """Get description for a takeaway event."""
        player = self._get_player_name(details, "playerId")
        return (f"Takeaway - {player}" if player else "Takeaway", "pbp-event")

    def _describe_faceoff(self, details: dict) -> tuple[str, str]:
        """Get description for a faceoff event."""
        winner = self._get_player_name(details, "winningPlayer")
        return (f"Faceoff won - {winner}" if winner else "Faceoff", "pbp-event")

    def _describe_stoppage(self, details: dict) -> tuple[str, str]:
        """Get description for a stoppage event."""
        reason = details.get("reason", "")
        return (f"Stoppage - {reason}" if reason else "Stoppage", "pbp-event")

    def _get_player_name(self, details: dict, *keys: str) -> str:
        """Get player name from details using multiple possible keys."""
        for key in keys:
            if key in details:
                data = details[key]
                if isinstance(data, dict):
                    return data.get("name", {}).get("default", "")
                elif isinstance(data, str):
                    return data
        return ""

    def _get_assists(self, details: dict) -> list[str]:
        """Get assist player names from goal details."""
        assists = []
        for key in ["assist1PlayerTotal", "assist2PlayerTotal"]:
            if key in details:
                data = details[key]
                if isinstance(data, dict):
                    name = data.get("name", {}).get("default", "")
                    if name:
                        assists.append(name)
        return assists

    def _update_countdown(self) -> None:
        """Update the countdown timer every second."""
        self._countdown -= 1
        if self._countdown < 0:
            self._countdown = self.REFRESH_INTERVAL
        self._update_subtitle()

    def _update_subtitle(self) -> None:
        """Update the screen subtitle with countdown."""
        self.sub_title = f"Refreshing in {self._countdown}s"

    def _auto_refresh(self) -> None:
        """Auto-refresh game data."""
        self._countdown = self.REFRESH_INTERVAL
        self._update_subtitle()
        self.client.clear_cache()
        self.load_game_data()

    def action_back(self) -> None:
        """Go back to schedule."""
        self.app.pop_screen()

    def action_refresh(self) -> None:
        """Manually refresh game data."""
        self._countdown = self.REFRESH_INTERVAL
        self._update_subtitle()
        self.client.clear_cache()
        self.load_game_data()
        self.notify("Refreshed")

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
