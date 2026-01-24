"""Standings screen for viewing league standings."""

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, Static, TabbedContent, TabPane

from faceoff.api import NHLClient


class StandingsScreen(Screen):
    """Screen for viewing NHL standings."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape,b", "back", "Back"),
        Binding("r", "refresh", "Refresh"),
        Binding("q", "quit", "Quit"),
        Binding("up,k", "scroll_up", "Scroll Up", show=False),
        Binding("down,j", "scroll_down", "Scroll Down", show=False),
    ]

    # Minimum width to display conferences side-by-side
    # Each conference needs ~70 chars (rank:4 + name:24 + gp:6 + w:6 + l:6 + otl:6 + pts:6 + pct:8 + padding)
    # Two conferences side-by-side need ~150 chars total
    SIDE_BY_SIDE_MIN_WIDTH = 150

    DEFAULT_CSS = """
    StandingsScreen {
        background: $surface;
    }

    StandingsScreen .standings-header {
        width: 100%;
        height: 3;
        align: center middle;
        text-style: bold;
        border-bottom: solid $primary;
    }

    StandingsScreen .standings-tabs {
        width: 100%;
        height: 1fr;
    }

    StandingsScreen .standings-container {
        width: 100%;
        height: 1fr;
        padding: 1;
    }

    StandingsScreen .conference-row {
        width: 100%;
        height: auto;
    }

    StandingsScreen .conference-section {
        width: 1fr;
        height: auto;
        padding: 0 1;
    }

    StandingsScreen .conference-header {
        width: 100%;
        height: 1;
        text-style: bold;
        text-align: center;
        background: $primary;
        margin-bottom: 1;
    }

    StandingsScreen .division-section {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }

    StandingsScreen .division-header {
        width: 100%;
        height: 1;
        text-style: bold;
        background: $surface-lighten-1;
        padding: 0 1;
    }

    StandingsScreen .team-row {
        width: 100%;
        height: 1;
        padding: 0 1;
    }

    StandingsScreen .team-row:hover {
        background: $surface-lighten-2;
    }

    StandingsScreen .team-rank {
        width: 4;
        text-align: right;
    }

    StandingsScreen .team-name {
        width: 24;
        padding-left: 1;
    }

    StandingsScreen .team-gp {
        width: 6;
        text-align: center;
    }

    StandingsScreen .team-wins {
        width: 6;
        text-align: center;
    }

    StandingsScreen .team-losses {
        width: 6;
        text-align: center;
    }

    StandingsScreen .team-otl {
        width: 6;
        text-align: center;
    }

    StandingsScreen .team-points {
        width: 6;
        text-align: center;
        text-style: bold;
    }

    StandingsScreen .team-pct {
        width: 8;
        text-align: center;
    }

    StandingsScreen .header-row {
        width: 100%;
        height: 1;
        padding: 0 1;
        text-style: bold;
        color: $text-muted;
    }

    StandingsScreen .loading {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    StandingsScreen .wild-card-header {
        width: 100%;
        height: 1;
        text-style: bold italic;
        background: $warning 20%;
        padding: 0 1;
        margin-top: 1;
    }

    StandingsScreen .league-section {
        width: 100%;
        height: auto;
        padding: 0 1;
    }
    """

    def __init__(self, client: NHLClient, **kwargs) -> None:
        super().__init__(**kwargs)
        self.client = client
        self.standings: list = []
        self._last_width: int = 0

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("NHL Standings", classes="standings-header")
        with TabbedContent(classes="standings-tabs"):
            with (
                TabPane("Wild Card", id="tab-wildcard"),
                VerticalScroll(id="wildcard-container", classes="standings-container"),
            ):
                yield Label("Loading...", classes="loading")
            with (
                TabPane("Division", id="tab-division"),
                VerticalScroll(id="division-container", classes="standings-container"),
            ):
                yield Label("Loading...", classes="loading")
            with (
                TabPane("Conference", id="tab-conference"),
                VerticalScroll(id="conference-container", classes="standings-container"),
            ):
                yield Label("Loading...", classes="loading")
            with (
                TabPane("League", id="tab-league"),
                VerticalScroll(id="league-container", classes="standings-container"),
            ):
                yield Label("Loading...", classes="loading")
        yield Footer()

    def on_mount(self) -> None:
        """Load standings when screen is mounted."""
        self.load_standings()

    def load_standings(self) -> None:
        """Load standings from API."""
        self.run_worker(self._fetch_standings())

    async def _fetch_standings(self) -> None:
        """Fetch standings from the API."""
        try:
            data = self.client.get_standings()
            self.standings = data.get("standings", [])
            self._update_all_views()
        except Exception as e:
            self.notify(f"Error loading standings: {e}", severity="error")

    def _update_all_views(self) -> None:
        """Update all standings views."""
        self._update_wildcard_view()
        self._update_division_view()
        self._update_conference_view()
        self._update_league_view()

    def _update_wildcard_view(self) -> None:  # noqa: C901
        """Update the wild card standings view."""
        container = self.query_one("#wildcard-container", VerticalScroll)
        container.remove_children()

        if not self.standings:
            container.mount(Label("No standings data available"))
            return

        # Group by conference and division
        conferences: dict[str, dict[str, list]] = {}
        wild_cards: dict[str, list] = {}

        for team in self.standings:
            conf_name = team.get("conferenceName", "Unknown")
            div_name = team.get("divisionName", "Unknown")

            if conf_name not in conferences:
                conferences[conf_name] = {}
                wild_cards[conf_name] = []

            if div_name not in conferences[conf_name]:
                conferences[conf_name][div_name] = []

            div_rank = team.get("divisionSequence", 0)
            if div_rank <= 3:
                conferences[conf_name][div_name].append(team)
            else:
                wild_cards[conf_name].append(team)

        # Create conference sections
        conf_sections = []
        for conf_name in sorted(conferences.keys()):
            conf_section = Vertical(classes="conference-section")
            conf_section.compose_add_child(Static(f"{conf_name} Conference", classes="conference-header"))
            conf_section.compose_add_child(self._create_header_row())

            for div_name in sorted(conferences[conf_name].keys()):
                div_section = Vertical(classes="division-section")
                div_section.compose_add_child(Static(div_name, classes="division-header"))

                teams = sorted(conferences[conf_name][div_name], key=lambda t: t.get("divisionSequence", 99))
                for team in teams:
                    div_section.compose_add_child(self._create_team_row(team))

                conf_section.compose_add_child(div_section)

            if wild_cards[conf_name]:
                conf_section.compose_add_child(Static("Wild Card", classes="wild-card-header"))
                wc_teams = sorted(wild_cards[conf_name], key=lambda t: t.get("wildcardSequence", 99))
                for team in wc_teams:
                    conf_section.compose_add_child(self._create_team_row(team, is_wild_card=True))

            conf_sections.append(conf_section)

        # Render side-by-side or stacked based on terminal width
        if self._is_wide_enough() and len(conf_sections) == 2:
            row = Horizontal(classes="conference-row")
            for section in conf_sections:
                row.compose_add_child(section)
            container.mount(row)
        else:
            for section in conf_sections:
                container.mount(section)

    def _update_division_view(self) -> None:  # noqa: C901
        """Update the division standings view."""
        container = self.query_one("#division-container", VerticalScroll)
        container.remove_children()

        if not self.standings:
            container.mount(Label("No standings data available"))
            return

        # Group by conference and division
        conferences: dict[str, dict[str, list]] = {}
        for team in self.standings:
            conf_name = team.get("conferenceName", "Unknown")
            div_name = team.get("divisionName", "Unknown")
            if conf_name not in conferences:
                conferences[conf_name] = {}
            if div_name not in conferences[conf_name]:
                conferences[conf_name][div_name] = []
            conferences[conf_name][div_name].append(team)

        # Create conference sections (each with its divisions)
        conf_sections = []
        for conf_name in sorted(conferences.keys()):
            conf_section = Vertical(classes="conference-section")

            for div_name in sorted(conferences[conf_name].keys()):
                div_section = Vertical(classes="division-section")
                div_section.compose_add_child(Static(div_name, classes="conference-header"))
                div_section.compose_add_child(self._create_header_row())

                teams = sorted(conferences[conf_name][div_name], key=lambda t: t.get("divisionSequence", 99))
                for i, team in enumerate(teams, 1):
                    div_section.compose_add_child(self._create_team_row(team, rank=i))

                conf_section.compose_add_child(div_section)

            conf_sections.append(conf_section)

        # Render side-by-side or stacked based on terminal width
        if self._is_wide_enough() and len(conf_sections) == 2:
            row = Horizontal(classes="conference-row")
            for section in conf_sections:
                row.compose_add_child(section)
            container.mount(row)
        else:
            for section in conf_sections:
                container.mount(section)

    def _update_conference_view(self) -> None:
        """Update the conference standings view."""
        container = self.query_one("#conference-container", VerticalScroll)
        container.remove_children()

        if not self.standings:
            container.mount(Label("No standings data available"))
            return

        # Group by conference
        conferences: dict[str, list] = {}
        for team in self.standings:
            conf_name = team.get("conferenceName", "Unknown")
            if conf_name not in conferences:
                conferences[conf_name] = []
            conferences[conf_name].append(team)

        # Create conference sections
        conf_sections = []
        for conf_name in sorted(conferences.keys()):
            conf_section = Vertical(classes="conference-section")
            conf_section.compose_add_child(Static(f"{conf_name} Conference", classes="conference-header"))
            conf_section.compose_add_child(self._create_header_row())

            teams = sorted(conferences[conf_name], key=lambda t: t.get("conferenceSequence", 99))
            for i, team in enumerate(teams, 1):
                conf_section.compose_add_child(self._create_team_row(team, rank=i))

            conf_sections.append(conf_section)

        # Render side-by-side or stacked based on terminal width
        if self._is_wide_enough() and len(conf_sections) == 2:
            row = Horizontal(classes="conference-row")
            for section in conf_sections:
                row.compose_add_child(section)
            container.mount(row)
        else:
            for section in conf_sections:
                container.mount(section)

    def _update_league_view(self) -> None:
        """Update the league-wide standings view."""
        container = self.query_one("#league-container", VerticalScroll)
        container.remove_children()

        if not self.standings:
            container.mount(Label("No standings data available"))
            return

        league_section = Vertical(classes="league-section")
        league_section.compose_add_child(Static("NHL Standings", classes="conference-header"))
        league_section.compose_add_child(self._create_header_row())

        teams = sorted(self.standings, key=lambda t: t.get("leagueSequence", 99))
        for i, team in enumerate(teams, 1):
            league_section.compose_add_child(self._create_team_row(team, rank=i))

        container.mount(league_section)

    def _create_header_row(self) -> Horizontal:
        """Create the header row for standings."""
        row = Horizontal(classes="header-row")
        row.compose_add_child(Label("#", classes="team-rank"))
        row.compose_add_child(Label("Team", classes="team-name"))
        row.compose_add_child(Label("GP", classes="team-gp"))
        row.compose_add_child(Label("W", classes="team-wins"))
        row.compose_add_child(Label("L", classes="team-losses"))
        row.compose_add_child(Label("OTL", classes="team-otl"))
        row.compose_add_child(Label("PTS", classes="team-points"))
        row.compose_add_child(Label("PCT", classes="team-pct"))
        return row

    def _create_team_row(self, team: dict, is_wild_card: bool = False, rank: int | None = None) -> Horizontal:
        """Create a row for a single team."""
        row = Horizontal(classes="team-row")

        if rank is not None:
            display_rank = rank
        elif is_wild_card:
            display_rank = team.get("wildcardSequence", "-")
        else:
            display_rank = team.get("divisionSequence", "-")

        team_name = team.get("teamAbbrev", {}).get("default", "???")
        gp = team.get("gamesPlayed", 0)
        wins = team.get("wins", 0)
        losses = team.get("losses", 0)
        otl = team.get("otLosses", 0)
        points = team.get("points", 0)
        pct = team.get("pointPctg", 0)

        row.compose_add_child(Label(str(display_rank), classes="team-rank"))
        row.compose_add_child(Label(team_name, classes="team-name"))
        row.compose_add_child(Label(str(gp), classes="team-gp"))
        row.compose_add_child(Label(str(wins), classes="team-wins"))
        row.compose_add_child(Label(str(losses), classes="team-losses"))
        row.compose_add_child(Label(str(otl), classes="team-otl"))
        row.compose_add_child(Label(str(points), classes="team-points"))
        row.compose_add_child(Label(f"{pct:.3f}", classes="team-pct"))

        return row

    def _get_active_container(self) -> VerticalScroll | None:
        """Get the currently active tab's scroll container."""
        try:
            tabs = self.query_one(TabbedContent)
            active_tab = tabs.active
            if active_tab == "tab-wildcard":
                return self.query_one("#wildcard-container", VerticalScroll)
            elif active_tab == "tab-division":
                return self.query_one("#division-container", VerticalScroll)
            elif active_tab == "tab-conference":
                return self.query_one("#conference-container", VerticalScroll)
            elif active_tab == "tab-league":
                return self.query_one("#league-container", VerticalScroll)
        except Exception:
            return None
        return None

    def _is_wide_enough(self) -> bool:
        """Check if screen is wide enough for side-by-side layout."""
        return self.size.width >= self.SIDE_BY_SIDE_MIN_WIDTH

    def on_resize(self, event) -> None:
        """Handle terminal resize to reflow layout."""
        if not self.standings:
            return
        new_width = self.size.width
        # Check if we crossed the threshold
        was_wide = self._last_width >= self.SIDE_BY_SIDE_MIN_WIDTH
        is_wide = new_width >= self.SIDE_BY_SIDE_MIN_WIDTH
        if was_wide != is_wide:
            self._last_width = new_width
            self._update_all_views()

    def action_scroll_up(self) -> None:
        """Scroll the active standings container up."""
        container = self._get_active_container()
        if container:
            container.scroll_up(animate=False)

    def action_scroll_down(self) -> None:
        """Scroll the active standings container down."""
        container = self._get_active_container()
        if container:
            container.scroll_down(animate=False)

    def action_back(self) -> None:
        """Go back to schedule."""
        self.app.pop_screen()

    def action_refresh(self) -> None:
        """Manually refresh standings."""
        self.client.clear_cache()
        self.load_standings()
        self.notify("Refreshed")

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
