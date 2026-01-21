"""Stats screen for viewing player statistics."""

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, Static, TabbedContent, TabPane

from faceoff.api import NHLClient


class StatsScreen(Screen):
    """Screen for viewing player stats leaders."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape,b", "back", "Back"),
        Binding("r", "refresh", "Refresh"),
        Binding("q", "quit", "Quit"),
        Binding("up,k", "scroll_up", "Scroll Up", show=False),
        Binding("down,j", "scroll_down", "Scroll Down", show=False),
    ]

    DEFAULT_CSS = """
    StatsScreen {
        background: $surface;
    }

    StatsScreen .stats-header {
        width: 100%;
        height: 3;
        align: center middle;
        text-style: bold;
        border-bottom: solid $primary;
    }

    StatsScreen .stats-tabs {
        width: 100%;
        height: 1fr;
    }

    StatsScreen .stats-container {
        width: 100%;
        height: 1fr;
        padding: 1;
    }

    StatsScreen .category-section {
        width: 100%;
        height: auto;
        margin-bottom: 2;
    }

    StatsScreen .category-header {
        width: 100%;
        height: 1;
        text-style: bold;
        text-align: center;
        background: $primary;
        margin-bottom: 1;
    }

    StatsScreen .stat-row {
        width: 100%;
        height: 1;
        padding: 0 1;
    }

    StatsScreen .stat-row:hover {
        background: $surface-lighten-2;
    }

    StatsScreen .stat-rank {
        width: 4;
        text-align: right;
    }

    StatsScreen .stat-player {
        width: 24;
        padding-left: 1;
    }

    StatsScreen .stat-team {
        width: 6;
        text-align: center;
    }

    StatsScreen .stat-pos {
        width: 4;
        text-align: center;
    }

    StatsScreen .stat-value {
        width: 8;
        text-align: right;
        text-style: bold;
    }

    StatsScreen .header-row {
        width: 100%;
        height: 1;
        padding: 0 1;
        text-style: bold;
        color: $text-muted;
    }

    StatsScreen .loading {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    StatsScreen .categories-row {
        width: 100%;
        height: auto;
    }

    StatsScreen .category-col {
        width: 1fr;
        height: auto;
        padding: 0 1;
    }
    """

    def __init__(self, client: NHLClient, **kwargs) -> None:
        super().__init__(**kwargs)
        self.client = client
        self.skater_stats: dict = {}
        self.goalie_stats: dict = {}

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("NHL Stats Leaders", classes="stats-header")
        with TabbedContent(classes="stats-tabs"):
            with (
                TabPane("Skaters", id="tab-skaters"),
                VerticalScroll(id="skaters-container", classes="stats-container"),
            ):
                yield Label("Loading...", classes="loading")
            with (
                TabPane("Goalies", id="tab-goalies"),
                VerticalScroll(id="goalies-container", classes="stats-container"),
            ):
                yield Label("Loading...", classes="loading")
        yield Footer()

    def on_mount(self) -> None:
        """Load stats when screen is mounted."""
        self.load_stats()

    def load_stats(self) -> None:
        """Load stats from API."""
        self.run_worker(self._fetch_stats())

    async def _fetch_stats(self) -> None:
        """Fetch stats from the API."""
        try:
            self.skater_stats = self.client.get_skater_stats_leaders()
            self.goalie_stats = self.client.get_goalie_stats_leaders()
            self._update_skaters_view()
            self._update_goalies_view()
        except Exception as e:
            self.notify(f"Error loading stats: {e}", severity="error")

    def _update_skaters_view(self) -> None:
        """Update the skaters stats view."""
        container = self.query_one("#skaters-container", VerticalScroll)
        container.remove_children()

        if not self.skater_stats:
            container.mount(Label("No stats data available"))
            return

        # Categories to display with their display names
        categories = [
            ("goals", "Goals"),
            ("assists", "Assists"),
            ("points", "Points"),
            ("plusMinus", "+/-"),
            ("goalsPp", "PP Goals"),
            ("goalsSh", "SH Goals"),
            ("penaltyMins", "PIM"),
            ("toi", "TOI/G"),
        ]

        # Create two-column layout
        row = Horizontal(classes="categories-row")

        left_col = Vertical(classes="category-col")
        right_col = Vertical(classes="category-col")

        for i, (key, display_name) in enumerate(categories):
            if key in self.skater_stats:
                section = self._create_category_section(display_name, self.skater_stats[key][:5], key)
                if i % 2 == 0:
                    left_col.compose_add_child(section)
                else:
                    right_col.compose_add_child(section)

        row.compose_add_child(left_col)
        row.compose_add_child(right_col)
        container.mount(row)

    def _update_goalies_view(self) -> None:
        """Update the goalies stats view."""
        container = self.query_one("#goalies-container", VerticalScroll)
        container.remove_children()

        if not self.goalie_stats:
            container.mount(Label("No goalie stats available"))
            return

        # Categories to display
        categories = [
            ("wins", "Wins"),
            ("savePctg", "Save %"),
            ("goalsAgainstAverage", "GAA"),
            ("shutouts", "Shutouts"),
        ]

        row = Horizontal(classes="categories-row")
        left_col = Vertical(classes="category-col")
        right_col = Vertical(classes="category-col")

        for i, (key, display_name) in enumerate(categories):
            if key in self.goalie_stats:
                section = self._create_category_section(display_name, self.goalie_stats[key][:5], key, is_goalie=True)
                if i % 2 == 0:
                    left_col.compose_add_child(section)
                else:
                    right_col.compose_add_child(section)

        row.compose_add_child(left_col)
        row.compose_add_child(right_col)
        container.mount(row)

    def _create_category_section(self, title: str, players: list, stat_key: str, is_goalie: bool = False) -> Vertical:
        """Create a section for a stat category."""
        section = Vertical(classes="category-section")
        section.compose_add_child(Static(title, classes="category-header"))

        # Header row
        header = Horizontal(classes="header-row")
        header.compose_add_child(Label("#", classes="stat-rank"))
        header.compose_add_child(Label("Player", classes="stat-player"))
        header.compose_add_child(Label("Team", classes="stat-team"))
        header.compose_add_child(Label("Pos", classes="stat-pos"))
        header.compose_add_child(Label("Value", classes="stat-value"))
        section.compose_add_child(header)

        for i, player in enumerate(players, 1):
            row = self._create_player_row(i, player, stat_key)
            section.compose_add_child(row)

        return section

    def _create_player_row(self, rank: int, player: dict, stat_key: str) -> Horizontal:
        """Create a row for a player."""
        row = Horizontal(classes="stat-row")

        first_name = player.get("firstName", {}).get("default", "")
        last_name = player.get("lastName", {}).get("default", "")
        name = f"{first_name[0]}. {last_name}" if first_name else last_name
        team = player.get("teamAbbrev", "???")
        pos = player.get("position", "?")
        value = player.get("value", 0)

        # Format value based on stat type
        if stat_key in ("savePctg",):
            value_str = f"{value:.3f}"
        elif stat_key in ("goalsAgainstAverage",):
            value_str = f"{value:.2f}"
        elif stat_key == "toi":
            # TOI is in seconds, convert to MM:SS
            mins = int(value) // 60
            secs = int(value) % 60
            value_str = f"{mins}:{secs:02d}"
        else:
            value_str = str(value)

        row.compose_add_child(Label(str(rank), classes="stat-rank"))
        row.compose_add_child(Label(name[:22], classes="stat-player"))
        row.compose_add_child(Label(team, classes="stat-team"))
        row.compose_add_child(Label(pos, classes="stat-pos"))
        row.compose_add_child(Label(value_str, classes="stat-value"))

        return row

    def action_back(self) -> None:
        """Go back to schedule."""
        self.app.pop_screen()

    def action_refresh(self) -> None:
        """Manually refresh stats."""
        self.client.clear_cache()
        self.load_stats()
        self.notify("Refreshed")

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

    def _get_active_scroll_container(self) -> VerticalScroll | None:
        """Get the currently active scroll container based on selected tab."""
        try:
            tabbed = self.query_one(TabbedContent)
            active_tab = tabbed.active
            if active_tab == "tab-skaters":
                return self.query_one("#skaters-container", VerticalScroll)
            elif active_tab == "tab-goalies":
                return self.query_one("#goalies-container", VerticalScroll)
        except Exception:
            return None
        return None

    def action_scroll_up(self) -> None:
        """Scroll the active container up."""
        container = self._get_active_scroll_container()
        if container:
            container.scroll_up(animate=False)

    def action_scroll_down(self) -> None:
        """Scroll the active container down."""
        container = self._get_active_scroll_container()
        if container:
            container.scroll_down(animate=False)
