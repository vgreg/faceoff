"""Pre-game screen for viewing game matchup preview."""

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, Static

from faceoff.api import NHLClient
from faceoff.widgets.game_card import get_local_time_with_tz


class PreGameScreen(Screen):
    """Screen for viewing pre-game matchup information."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape,b", "back", "Back"),
        Binding("r", "refresh", "Refresh"),
        Binding("q", "quit", "Quit"),
    ]

    DEFAULT_CSS = """
    PreGameScreen {
        background: $surface;
    }

    PreGameScreen .pregame-header {
        width: 100%;
        height: 3;
        align: center middle;
        text-style: bold;
        border-bottom: solid $primary;
    }

    PreGameScreen .matchup-container {
        width: 100%;
        height: 1fr;
        padding: 1;
    }

    PreGameScreen .game-info {
        width: 100%;
        height: auto;
        align: center middle;
        padding: 1;
        margin-bottom: 1;
    }

    PreGameScreen .game-time {
        text-style: bold;
        text-align: center;
        width: 100%;
    }

    PreGameScreen .venue {
        text-align: center;
        width: 100%;
        color: $text-muted;
    }

    PreGameScreen .teams-row {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }

    PreGameScreen .team-panel {
        width: 1fr;
        height: auto;
        border: solid $primary;
        padding: 1;
        margin: 0 1;
    }

    PreGameScreen .team-name {
        text-style: bold;
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }

    PreGameScreen .team-record {
        text-align: center;
        width: 100%;
        color: $text-muted;
        margin-bottom: 1;
    }

    PreGameScreen .section-header {
        text-style: bold;
        width: 100%;
        background: $surface-lighten-1;
        padding: 0 1;
        margin-top: 1;
    }

    PreGameScreen .goalie-row {
        width: 100%;
        height: auto;
        padding: 0 1;
    }

    PreGameScreen .goalie-name {
        width: 1fr;
    }

    PreGameScreen .goalie-stats {
        width: auto;
        text-align: right;
        color: $text-muted;
    }

    PreGameScreen .comparison-section {
        width: 100%;
        height: auto;
        border: solid $primary;
        padding: 1;
        margin-top: 1;
    }

    PreGameScreen .comparison-header {
        text-style: bold;
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }

    PreGameScreen .comparison-row {
        width: 100%;
        height: 1;
    }

    PreGameScreen .comp-away {
        width: 1fr;
        text-align: left;
    }

    PreGameScreen .comp-category {
        width: 12;
        text-align: center;
        text-style: bold;
    }

    PreGameScreen .comp-home {
        width: 1fr;
        text-align: right;
    }

    PreGameScreen .vs-label {
        text-align: center;
        width: auto;
        padding: 0 2;
    }

    PreGameScreen .loading {
        width: 100%;
        height: 100%;
        align: center middle;
    }
    """

    def __init__(self, client: NHLClient, game_id: int, game_data: dict, **kwargs) -> None:
        super().__init__(**kwargs)
        self.client = client
        self.game_id = game_id
        self.game_data = game_data
        self.landing: dict = {}

    def compose(self) -> ComposeResult:
        away = self.game_data.get("awayTeam", {}).get("abbrev", "???")
        home = self.game_data.get("homeTeam", {}).get("abbrev", "???")
        yield Header()
        yield Static(f"Pre-Game: {away} @ {home}", classes="pregame-header")
        with VerticalScroll(classes="matchup-container", id="matchup-container"):
            yield Label("Loading matchup data...", classes="loading")
        yield Footer()

    def on_mount(self) -> None:
        """Load matchup data when screen is mounted."""
        self.load_matchup_data()

    def load_matchup_data(self) -> None:
        """Load matchup data from API."""
        self.run_worker(self._fetch_matchup_data())

    async def _fetch_matchup_data(self) -> None:
        """Fetch matchup data from the API."""
        try:
            self.landing = self.client.get_game_landing(self.game_id)
            self._update_matchup_view()
        except Exception as e:
            self.notify(f"Error loading matchup: {e}", severity="error")

    def _update_matchup_view(self) -> None:
        """Update the matchup view with loaded data."""
        container = self.query_one("#matchup-container", VerticalScroll)
        container.remove_children()

        if not self.landing:
            container.mount(Label("No matchup data available"))
            return

        # Game info section
        game_info = Vertical(classes="game-info")
        start_time = self.landing.get("startTimeUTC", "")
        local_time = get_local_time_with_tz(start_time)
        venue = self.landing.get("venue", {}).get("default", "")
        venue_loc = self.landing.get("venueLocation", {}).get("default", "")

        game_info.compose_add_child(Static(f"Game Time: {local_time}", classes="game-time"))
        if venue:
            venue_text = f"{venue}, {venue_loc}" if venue_loc else venue
            game_info.compose_add_child(Static(venue_text, classes="venue"))
        container.mount(game_info)

        # Team panels
        teams_row = Horizontal(classes="teams-row")
        away_team = self.landing.get("awayTeam", {})
        home_team = self.landing.get("homeTeam", {})

        # Away team panel
        away_panel = self._create_team_panel(away_team, is_home=False)
        teams_row.compose_add_child(away_panel)

        # VS label
        vs_label = Static("@", classes="vs-label")
        teams_row.compose_add_child(vs_label)

        # Home team panel
        home_panel = self._create_team_panel(home_team, is_home=True)
        teams_row.compose_add_child(home_panel)

        container.mount(teams_row)

        # Matchup comparison section
        matchup = self.landing.get("matchup", {})
        if matchup:
            # Goalie comparison
            goalie_comp = matchup.get("goalieComparison", {})
            if goalie_comp:
                comp_section = self._create_goalie_comparison(goalie_comp)
                container.mount(comp_section)

            # Skater comparison (leaders)
            skater_comp = matchup.get("skaterComparison", {})
            if skater_comp:
                leaders = skater_comp.get("leaders", [])
                if leaders:
                    skater_section = self._create_skater_comparison(leaders)
                    container.mount(skater_section)

    def _create_team_panel(self, team: dict, is_home: bool) -> Vertical:
        """Create a team info panel."""
        panel = Vertical(classes="team-panel")

        name = team.get("commonName", {})
        if isinstance(name, dict):
            name = name.get("default", team.get("abbrev", "???"))
        abbrev = team.get("abbrev", "")
        record = team.get("record", "")

        panel.compose_add_child(Static(f"{name} ({abbrev})", classes="team-name"))
        if record:
            panel.compose_add_child(Static(f"Record: {record}", classes="team-record"))

        return panel

    def _create_goalie_comparison(self, goalie_comp: dict) -> Vertical:
        """Create goalie comparison section."""
        section = Vertical(classes="comparison-section")
        section.compose_add_child(Static("Goalie Matchup", classes="comparison-header"))

        away_team = goalie_comp.get("awayTeam", {})
        home_team = goalie_comp.get("homeTeam", {})

        away_goalies = away_team.get("leaders", [])
        home_goalies = home_team.get("leaders", [])

        # Show team goalie totals
        away_totals = away_team.get("teamTotals", {})
        home_totals = home_team.get("teamTotals", {})

        if away_totals or home_totals:
            row = Horizontal(classes="comparison-row")
            away_rec = away_totals.get("record", "-")
            home_rec = home_totals.get("record", "-")
            away_sv = away_totals.get("savePctg", 0)
            home_sv = home_totals.get("savePctg", 0)

            row.compose_add_child(Label(f"{away_rec} | SV%: {away_sv:.3f}", classes="comp-away"))
            row.compose_add_child(Label("Team", classes="comp-category"))
            row.compose_add_child(Label(f"SV%: {home_sv:.3f} | {home_rec}", classes="comp-home"))
            section.compose_add_child(row)

        # Show individual goalies
        max_goalies = max(len(away_goalies), len(home_goalies))
        for i in range(min(max_goalies, 2)):  # Show up to 2 goalies per team
            row = Horizontal(classes="comparison-row")

            if i < len(away_goalies):
                g = away_goalies[i]
                name = g.get("name", {}).get("default", "?")
                record = g.get("record", "-")
                gaa = g.get("gaa", 0)
                row.compose_add_child(Label(f"{name} ({record}, {gaa:.2f})", classes="comp-away"))
            else:
                row.compose_add_child(Label("", classes="comp-away"))

            row.compose_add_child(Label(f"G{i + 1}", classes="comp-category"))

            if i < len(home_goalies):
                g = home_goalies[i]
                name = g.get("name", {}).get("default", "?")
                record = g.get("record", "-")
                gaa = g.get("gaa", 0)
                row.compose_add_child(Label(f"({gaa:.2f}, {record}) {name}", classes="comp-home"))
            else:
                row.compose_add_child(Label("", classes="comp-home"))

            section.compose_add_child(row)

        return section

    def _create_skater_comparison(self, leaders: list) -> Vertical:
        """Create skater leaders comparison section."""
        section = Vertical(classes="comparison-section")
        section.compose_add_child(Static("Skater Leaders (Last 5 Games)", classes="comparison-header"))

        for leader in leaders[:5]:  # Show top 5 categories
            category = leader.get("category", "?")
            away_leader = leader.get("awayLeader", {})
            home_leader = leader.get("homeLeader", {})

            row = Horizontal(classes="comparison-row")

            # Away leader
            if away_leader:
                name = away_leader.get("name", {}).get("default", "?")
                value = away_leader.get("value", 0)
                row.compose_add_child(Label(f"{name}: {value}", classes="comp-away"))
            else:
                row.compose_add_child(Label("-", classes="comp-away"))

            # Category
            cat_display = category.replace("_", " ").title()
            row.compose_add_child(Label(cat_display[:10], classes="comp-category"))

            # Home leader
            if home_leader:
                name = home_leader.get("name", {}).get("default", "?")
                value = home_leader.get("value", 0)
                row.compose_add_child(Label(f"{value}: {name}", classes="comp-home"))
            else:
                row.compose_add_child(Label("-", classes="comp-home"))

            section.compose_add_child(row)

        return section

    def action_back(self) -> None:
        """Go back to schedule."""
        self.app.pop_screen()

    def action_refresh(self) -> None:
        """Manually refresh matchup data."""
        self.client.clear_cache()
        self.load_matchup_data()
        self.notify("Refreshed")

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
