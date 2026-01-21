"""Player screen for viewing player details and stats."""

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, Static

from faceoff.api import NHLClient


class PlayerScreen(Screen):
    """Screen for viewing player details."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape,b", "back", "Back"),
        Binding("r", "refresh", "Refresh"),
        Binding("q", "quit", "Quit"),
    ]

    DEFAULT_CSS = """
    PlayerScreen {
        background: $surface;
    }

    PlayerScreen .player-header {
        width: 100%;
        height: 3;
        align: center middle;
        text-style: bold;
        border-bottom: solid $primary;
    }

    PlayerScreen .player-container {
        width: 100%;
        height: 1fr;
        padding: 1;
    }

    PlayerScreen .info-section {
        width: 100%;
        height: auto;
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
    }

    PlayerScreen .info-row {
        width: 100%;
        height: 1;
    }

    PlayerScreen .info-label {
        width: 16;
        text-style: bold;
    }

    PlayerScreen .info-value {
        width: 1fr;
    }

    PlayerScreen .stats-section {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }

    PlayerScreen .section-header {
        width: 100%;
        height: 1;
        text-style: bold;
        background: $primary;
        padding: 0 1;
        margin-bottom: 1;
    }

    PlayerScreen .stats-header {
        width: 100%;
        height: 1;
        padding: 0 1;
        text-style: bold;
        color: $text-muted;
    }

    PlayerScreen .stats-row {
        width: 100%;
        height: 1;
        padding: 0 1;
    }

    PlayerScreen .stat-cell {
        width: 8;
        text-align: center;
    }

    PlayerScreen .stat-cell-wide {
        width: 12;
        text-align: center;
    }

    PlayerScreen .loading {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    PlayerScreen .game-log-row {
        width: 100%;
        height: 1;
        padding: 0 1;
    }

    PlayerScreen .game-log-row:hover {
        background: $surface-lighten-2;
    }
    """

    def __init__(self, client: NHLClient, player_id: int, player_name: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.client = client
        self.player_id = player_id
        self.player_name = player_name
        self.player_data: dict = {}
        self.game_log: dict = {}

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(self.player_name, classes="player-header", id="player-header")
        with VerticalScroll(id="player-container", classes="player-container"):
            yield Label("Loading...", classes="loading")
        yield Footer()

    def on_mount(self) -> None:
        """Load player data when screen is mounted."""
        self.load_player_data()

    def load_player_data(self) -> None:
        """Load player data from API."""
        self.run_worker(self._fetch_player_data())

    async def _fetch_player_data(self) -> None:
        """Fetch player data from the API."""
        try:
            self.player_data = self.client.get_player_landing(self.player_id)
            self.game_log = self.client.get_player_game_log(self.player_id)

            # Update header with full name
            first = self.player_data.get("firstName", {}).get("default", "")
            last = self.player_data.get("lastName", {}).get("default", "")
            if first and last:
                header = self.query_one("#player-header", Static)
                header.update(f"{first} {last}")

            self._update_player_view()
        except Exception as e:
            self.notify(f"Error loading player data: {e}", severity="error")

    def _update_player_view(self) -> None:
        """Update the combined player view with info, stats, and game log."""
        container = self.query_one("#player-container", VerticalScroll)
        container.remove_children()

        if not self.player_data:
            container.mount(Label("No player data available"))
            return

        position = self.player_data.get("position", "")
        is_goalie = position == "G"

        # Mount all sections
        container.mount(self._build_info_section())

        stats_section = self._build_stats_section(is_goalie)
        if stats_section:
            container.mount(stats_section)

        gamelog_section = self._build_gamelog_section(is_goalie)
        if gamelog_section:
            container.mount(gamelog_section)

    def _build_info_section(self) -> Vertical:
        """Build the player info section."""
        info_section = Vertical(classes="info-section")

        info_items = [
            ("Team", self.player_data.get("fullTeamName", {}).get("default", "N/A")),
            ("Position", self.player_data.get("position", "N/A")),
            ("Number", f"#{self.player_data.get('sweaterNumber', 'N/A')}"),
            ("Height", self.player_data.get("heightInCentimeters", "N/A")),
            ("Weight", f"{self.player_data.get('weightInPounds', 'N/A')} lbs"),
            ("Birth Date", self.player_data.get("birthDate", "N/A")),
            ("Birth City", self.player_data.get("birthCity", {}).get("default", "N/A")),
            ("Birth Country", self.player_data.get("birthCountry", "N/A")),
            ("Shoots/Catches", self.player_data.get("shootsCatches", "N/A")),
        ]

        for label, value in info_items:
            row = Horizontal(classes="info-row")
            row.compose_add_child(Label(label, classes="info-label"))
            row.compose_add_child(Label(str(value), classes="info-value"))
            info_section.compose_add_child(row)

        return info_section

    def _build_stats_section(self, is_goalie: bool) -> Vertical | None:
        """Build the stats section."""
        featured_stats = self.player_data.get("featuredStats", {})
        season_stats = featured_stats.get("regularSeason", {}).get("subSeason", {})
        career_stats = featured_stats.get("regularSeason", {}).get("career", {})

        if not season_stats and not career_stats:
            return None

        stats_section = Vertical(classes="stats-section")
        stats_section.compose_add_child(Static("Season & Career Stats", classes="section-header"))

        if is_goalie:
            self._add_goalie_stats(stats_section, season_stats, career_stats)
        else:
            self._add_skater_stats(stats_section, season_stats, career_stats)

        return stats_section

    def _add_goalie_stats(self, section: Vertical, season: dict, career: dict) -> None:
        """Add goalie stats to a section."""
        header = Horizontal(classes="stats-header")
        for col in ["", "GP", "W", "L", "OTL", "GAA", "SV%", "SO"]:
            header.compose_add_child(Label(col, classes="stat-cell-wide" if not col else "stat-cell"))
        section.compose_add_child(header)

        for label, stats in [("This Season", season), ("Career", career)]:
            if stats:
                gaa = stats.get("goalsAgainstAvg", 0)
                sv_pct = stats.get("savePctg", 0)
                row = Horizontal(classes="stats-row")
                row.compose_add_child(Label(label, classes="stat-cell-wide"))
                row.compose_add_child(Label(str(stats.get("gamesPlayed", 0)), classes="stat-cell"))
                row.compose_add_child(Label(str(stats.get("wins", 0)), classes="stat-cell"))
                row.compose_add_child(Label(str(stats.get("losses", 0)), classes="stat-cell"))
                row.compose_add_child(Label(str(stats.get("otLosses", 0)), classes="stat-cell"))
                row.compose_add_child(Label(f"{gaa:.2f}" if gaa else "0.00", classes="stat-cell"))
                row.compose_add_child(Label(f"{sv_pct:.3f}" if sv_pct else ".000", classes="stat-cell"))
                row.compose_add_child(Label(str(stats.get("shutouts", 0)), classes="stat-cell"))
                section.compose_add_child(row)

    def _add_skater_stats(self, section: Vertical, season: dict, career: dict) -> None:
        """Add skater stats to a section."""
        header = Horizontal(classes="stats-header")
        for col in ["", "GP", "G", "A", "PTS", "+/-", "PIM", "PPG", "SHG"]:
            header.compose_add_child(Label(col, classes="stat-cell-wide" if not col else "stat-cell"))
        section.compose_add_child(header)

        for label, stats in [("This Season", season), ("Career", career)]:
            if stats:
                row = Horizontal(classes="stats-row")
                row.compose_add_child(Label(label, classes="stat-cell-wide"))
                row.compose_add_child(Label(str(stats.get("gamesPlayed", 0)), classes="stat-cell"))
                row.compose_add_child(Label(str(stats.get("goals", 0)), classes="stat-cell"))
                row.compose_add_child(Label(str(stats.get("assists", 0)), classes="stat-cell"))
                row.compose_add_child(Label(str(stats.get("points", 0)), classes="stat-cell"))
                row.compose_add_child(Label(str(stats.get("plusMinus", 0)), classes="stat-cell"))
                row.compose_add_child(Label(str(stats.get("pim", 0)), classes="stat-cell"))
                row.compose_add_child(Label(str(stats.get("powerPlayGoals", 0)), classes="stat-cell"))
                row.compose_add_child(Label(str(stats.get("shorthandedGoals", 0)), classes="stat-cell"))
                section.compose_add_child(row)

    def _build_gamelog_section(self, is_goalie: bool) -> Vertical | None:
        """Build the game log section."""
        game_log = self.game_log.get("gameLog", [])
        if not game_log:
            return None

        gamelog_section = Vertical(classes="stats-section")
        gamelog_section.compose_add_child(Static("Recent Games", classes="section-header"))

        if is_goalie:
            cols = ["Date", "Opp", "Dec", "GA", "SA", "SV%", "TOI"]
        else:
            cols = ["Date", "Opp", "G", "A", "PTS", "+/-", "SOG", "TOI"]

        header = Horizontal(classes="stats-header")
        for col in cols:
            header.compose_add_child(Label(col, classes="stat-cell-wide" if col == "Date" else "stat-cell"))
        gamelog_section.compose_add_child(header)

        for game in game_log[:10]:
            row = Horizontal(classes="game-log-row")
            row.compose_add_child(Label(game.get("gameDate", ""), classes="stat-cell-wide"))
            row.compose_add_child(Label(game.get("opponentAbbrev", ""), classes="stat-cell"))

            if is_goalie:
                row.compose_add_child(Label(game.get("decision", "-"), classes="stat-cell"))
                row.compose_add_child(Label(str(game.get("goalsAgainst", 0)), classes="stat-cell"))
                row.compose_add_child(Label(str(game.get("shotsAgainst", 0)), classes="stat-cell"))
                sv_pct = game.get("savePctg", 0)
                row.compose_add_child(Label(f"{sv_pct:.3f}" if sv_pct else ".000", classes="stat-cell"))
            else:
                row.compose_add_child(Label(str(game.get("goals", 0)), classes="stat-cell"))
                row.compose_add_child(Label(str(game.get("assists", 0)), classes="stat-cell"))
                row.compose_add_child(Label(str(game.get("points", 0)), classes="stat-cell"))
                row.compose_add_child(Label(str(game.get("plusMinus", 0)), classes="stat-cell"))
                row.compose_add_child(Label(str(game.get("shots", 0)), classes="stat-cell"))

            row.compose_add_child(Label(game.get("toi", "0:00"), classes="stat-cell"))
            gamelog_section.compose_add_child(row)

        return gamelog_section

    def action_back(self) -> None:
        """Go back."""
        self.app.pop_screen()

    def action_refresh(self) -> None:
        """Manually refresh player data."""
        self.client.clear_cache()
        self.load_player_data()
        self.notify("Refreshed")

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
