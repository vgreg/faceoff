"""Teams screen for browsing teams and viewing team details."""

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Footer, Header, Label, Static, TabbedContent, TabPane

from faceoff.api import NHLClient
from faceoff.widgets.game_card import get_local_time_with_tz

# Team card width (12) + margin (1) = 13 chars per card
TEAM_CARD_WIDTH = 13


class TeamCard(Widget):
    """A card widget for selecting a team."""

    DEFAULT_CSS = """
    TeamCard {
        width: 12;
        height: 3;
        border: solid $primary;
        padding: 0 1;
        margin: 0 1 1 0;
        content-align: center middle;
    }

    TeamCard:hover {
        border: solid $secondary;
    }

    TeamCard:focus {
        border: double $accent;
    }

    TeamCard .team-abbrev {
        text-align: center;
        text-style: bold;
    }
    """

    can_focus = True

    class Selected(Message):
        """Message sent when a team is selected."""

        def __init__(self, team_abbrev: str, team_name: str) -> None:
            self.team_abbrev = team_abbrev
            self.team_name = team_name
            super().__init__()

    def __init__(self, team_abbrev: str, team_name: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.team_abbrev = team_abbrev
        self.team_name = team_name

    def compose(self) -> ComposeResult:
        yield Label(self.team_abbrev, classes="team-abbrev")

    def on_click(self) -> None:
        self.post_message(self.Selected(self.team_abbrev, self.team_name))

    def on_key(self, event) -> None:
        if event.key == "enter":
            self.post_message(self.Selected(self.team_abbrev, self.team_name))
            event.stop()


class PlayerRow(Widget):
    """A clickable row for a player."""

    DEFAULT_CSS = """
    PlayerRow {
        width: 100%;
        height: 1;
        padding: 0 1;
    }

    PlayerRow:hover {
        background: $surface-lighten-2;
    }

    PlayerRow:focus {
        background: $primary 30%;
    }

    PlayerRow .player-number {
        width: 4;
        text-align: right;
    }

    PlayerRow .player-name {
        width: 1fr;
        padding-left: 1;
    }

    PlayerRow .player-pos {
        width: 4;
        text-align: center;
    }
    """

    can_focus = True

    class Selected(Message):
        """Message sent when a player is selected."""

        def __init__(self, player_id: int, player_name: str) -> None:
            self.player_id = player_id
            self.player_name = player_name
            super().__init__()

    def __init__(self, player_data: dict, **kwargs) -> None:
        super().__init__(**kwargs)
        self.player_data = player_data
        self.player_id = player_data.get("id", 0)

    def compose(self) -> ComposeResult:
        number = self.player_data.get("sweaterNumber", "-")
        first_name = self.player_data.get("firstName", {}).get("default", "")
        last_name = self.player_data.get("lastName", {}).get("default", "")
        pos = self.player_data.get("positionCode", "?")

        with Horizontal():
            yield Label(str(number), classes="player-number")
            yield Label(f"{first_name} {last_name}", classes="player-name")
            yield Label(pos, classes="player-pos")

    def on_click(self) -> None:
        first_name = self.player_data.get("firstName", {}).get("default", "")
        last_name = self.player_data.get("lastName", {}).get("default", "")
        self.post_message(self.Selected(self.player_id, f"{first_name} {last_name}"))

    def on_key(self, event) -> None:
        if event.key == "enter":
            first_name = self.player_data.get("firstName", {}).get("default", "")
            last_name = self.player_data.get("lastName", {}).get("default", "")
            self.post_message(self.Selected(self.player_id, f"{first_name} {last_name}"))
            event.stop()


class TeamsScreen(Screen):
    """Screen for browsing NHL teams."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape,b", "back", "Back"),
        Binding("r", "refresh", "Refresh"),
        Binding("q", "quit", "Quit"),
        Binding("left", "focus_prev_card", "Previous", show=False),
        Binding("right", "focus_next_card", "Next", show=False),
        Binding("up", "focus_card_above", "Up", show=False),
        Binding("down", "focus_card_below", "Down", show=False),
    ]

    DEFAULT_CSS = """
    TeamsScreen {
        background: $surface;
    }

    TeamsScreen .teams-header {
        width: 100%;
        height: 3;
        align: center middle;
        text-style: bold;
        border-bottom: solid $primary;
    }

    TeamsScreen .teams-container {
        width: 100%;
        height: 1fr;
        padding: 1;
    }

    TeamsScreen .teams-grid {
        width: 100%;
        height: auto;
    }

    TeamsScreen .teams-row {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }

    TeamsScreen .conference-label {
        width: 100%;
        text-style: bold;
        background: $primary;
        padding: 0 1;
        margin-bottom: 1;
    }

    TeamsScreen .loading {
        width: 100%;
        height: 100%;
        align: center middle;
    }
    """

    def __init__(self, client: NHLClient, **kwargs) -> None:
        super().__init__(**kwargs)
        self.client = client
        self.teams: list = []
        self._last_width: int = 0

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("NHL Teams", classes="teams-header")
        with (
            VerticalScroll(classes="teams-container", id="teams-container"),
            Vertical(classes="teams-grid", id="teams-grid"),
        ):
            yield Label("Loading...", classes="loading")
        yield Footer()

    def on_mount(self) -> None:
        """Load teams when screen is mounted."""
        self.load_teams()

    def load_teams(self) -> None:
        """Load teams from API."""
        self.run_worker(self._fetch_teams())

    async def _fetch_teams(self) -> None:
        """Fetch teams from the API (via standings)."""
        try:
            data = self.client.get_standings()
            self.teams = data.get("standings", [])
            self._update_teams_display()
        except Exception as e:
            self.notify(f"Error loading teams: {e}", severity="error")

    def _get_cards_per_row(self) -> int:
        """Calculate how many team cards fit per row based on container width."""
        try:
            scroll = self.query_one("#teams-container", VerticalScroll)
            available_width = scroll.size.width - 4  # Account for padding
            cards_per_row = max(1, available_width // TEAM_CARD_WIDTH)
        except Exception:
            return 6  # Default fallback
        else:
            return cards_per_row

    def _update_teams_display(self) -> None:
        """Update the teams grid."""
        grid = self.query_one("#teams-grid", Vertical)
        grid.remove_children()

        if not self.teams:
            grid.mount(Label("No teams data available"))
            return

        cards_per_row = self._get_cards_per_row()

        # Group by conference
        conferences: dict[str, list] = {}
        for team in self.teams:
            conf = team.get("conferenceName", "Unknown")
            if conf not in conferences:
                conferences[conf] = []
            conferences[conf].append(team)

        for conf_name in sorted(conferences.keys()):
            grid.mount(Static(f"{conf_name} Conference", classes="conference-label"))

            teams = sorted(conferences[conf_name], key=lambda t: t.get("teamAbbrev", {}).get("default", ""))

            # Create multiple rows based on cards_per_row
            for i in range(0, len(teams), cards_per_row):
                row_teams = teams[i : i + cards_per_row]
                row = Horizontal(classes="teams-row")

                for team in row_teams:
                    abbrev = team.get("teamAbbrev", {}).get("default", "???")
                    name = team.get("teamName", {}).get("default", abbrev)
                    card = TeamCard(abbrev, name)
                    row.compose_add_child(card)

                grid.mount(row)

    def on_resize(self, event) -> None:
        """Handle terminal resize to reflow team cards."""
        if not self.teams:
            return
        try:
            scroll = self.query_one("#teams-container", VerticalScroll)
            new_width = scroll.size.width
        except Exception:
            return
        if abs(new_width - self._last_width) >= TEAM_CARD_WIDTH:
            self._last_width = new_width
            self._update_teams_display()

    def on_team_card_selected(self, event: TeamCard.Selected) -> None:
        """Handle team selection."""
        self.app.push_screen(TeamDetailScreen(self.client, event.team_abbrev, event.team_name))

    def action_back(self) -> None:
        """Go back to schedule."""
        self.app.pop_screen()

    def action_refresh(self) -> None:
        """Manually refresh teams."""
        self.client.clear_cache()
        self.load_teams()
        self.notify("Refreshed")

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

    def _get_focused_card_index(self) -> int:
        """Get the index of the currently focused card, or -1 if none."""
        cards = list(self.query(TeamCard))
        for i, card in enumerate(cards):
            if card.has_focus:
                return i
        return -1

    def _focus_card_at_index(self, index: int) -> None:
        """Focus the card at the given index."""
        cards = list(self.query(TeamCard))
        if cards and 0 <= index < len(cards):
            cards[index].focus()

    def action_focus_prev_card(self) -> None:
        """Focus the previous team card."""
        idx = self._get_focused_card_index()
        if idx > 0:
            self._focus_card_at_index(idx - 1)
        elif idx == -1:
            # No card focused, focus the first one
            self._focus_card_at_index(0)

    def action_focus_next_card(self) -> None:
        """Focus the next team card."""
        idx = self._get_focused_card_index()
        cards = list(self.query(TeamCard))
        if idx < len(cards) - 1:
            self._focus_card_at_index(idx + 1)
        elif idx == -1 and cards:
            # No card focused, focus the first one
            self._focus_card_at_index(0)

    def action_focus_card_above(self) -> None:
        """Focus the team card above (previous row, same column)."""
        idx = self._get_focused_card_index()
        if idx < 0:
            self._focus_card_at_index(0)
            return
        cards_per_row = self._get_cards_per_row()
        new_idx = idx - cards_per_row
        if new_idx >= 0:
            self._focus_card_at_index(new_idx)

    def action_focus_card_below(self) -> None:
        """Focus the team card below (next row, same column)."""
        idx = self._get_focused_card_index()
        if idx < 0:
            self._focus_card_at_index(0)
            return
        cards = list(self.query(TeamCard))
        cards_per_row = self._get_cards_per_row()
        new_idx = idx + cards_per_row
        if new_idx < len(cards):
            self._focus_card_at_index(new_idx)


class TeamDetailScreen(Screen):
    """Screen for viewing team details."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape,b", "back", "Back"),
        Binding("r", "refresh", "Refresh"),
        Binding("q", "quit", "Quit"),
        Binding("up,k", "focus_prev_player", "Previous", show=False),
        Binding("down,j", "focus_next_player", "Next", show=False),
    ]

    DEFAULT_CSS = """
    TeamDetailScreen {
        background: $surface;
    }

    TeamDetailScreen .team-header {
        width: 100%;
        height: 3;
        align: center middle;
        text-style: bold;
        border-bottom: solid $primary;
    }

    TeamDetailScreen .detail-tabs {
        width: 100%;
        height: 1fr;
    }

    TeamDetailScreen .detail-container {
        width: 100%;
        height: 1fr;
        padding: 1;
    }

    TeamDetailScreen .section-header {
        width: 100%;
        height: 1;
        text-style: bold;
        background: $surface-lighten-1;
        padding: 0 1;
        margin-bottom: 1;
    }

    TeamDetailScreen .game-row {
        width: 100%;
        height: 1;
        padding: 0 1;
    }

    TeamDetailScreen .game-date {
        width: 12;
    }

    TeamDetailScreen .game-opponent {
        width: 1fr;
    }

    TeamDetailScreen .game-result {
        width: 10;
        text-align: right;
    }

    TeamDetailScreen .loading {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    TeamDetailScreen .position-section {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }
    """

    def __init__(self, client: NHLClient, team_abbrev: str, team_name: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.client = client
        self.team_abbrev = team_abbrev
        self.team_name = team_name
        self.roster: dict = {}
        self.schedule: dict = {}

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(f"{self.team_name} ({self.team_abbrev})", classes="team-header")
        with TabbedContent(classes="detail-tabs"):
            with TabPane("Roster", id="tab-roster"), VerticalScroll(id="roster-container", classes="detail-container"):
                yield Label("Loading...", classes="loading")
            with (
                TabPane("Schedule", id="tab-schedule"),
                VerticalScroll(id="schedule-container", classes="detail-container"),
            ):
                yield Label("Loading...", classes="loading")
        yield Footer()

    def on_mount(self) -> None:
        """Load team data when screen is mounted."""
        self.load_team_data()

    def load_team_data(self) -> None:
        """Load team data from API."""
        self.run_worker(self._fetch_team_data())

    async def _fetch_team_data(self) -> None:
        """Fetch team data from the API."""
        try:
            self.roster = self.client.get_team_roster(self.team_abbrev)
            self.schedule = self.client.get_team_month_schedule(self.team_abbrev)
            self._update_roster_view()
            self._update_schedule_view()
        except Exception as e:
            self.notify(f"Error loading team data: {e}", severity="error")

    def _update_roster_view(self) -> None:
        """Update the roster view."""
        container = self.query_one("#roster-container", VerticalScroll)
        container.remove_children()

        if not self.roster:
            container.mount(Label("No roster data available"))
            return

        positions = [
            ("forwards", "Forwards"),
            ("defensemen", "Defensemen"),
            ("goalies", "Goalies"),
        ]

        for key, label in positions:
            players = self.roster.get(key, [])
            if players:
                section = Vertical(classes="position-section")
                section.compose_add_child(Static(label, classes="section-header"))

                for player in sorted(players, key=lambda p: p.get("sweaterNumber", 99)):
                    section.compose_add_child(PlayerRow(player))

                container.mount(section)

    def _update_schedule_view(self) -> None:
        """Update the schedule view."""
        container = self.query_one("#schedule-container", VerticalScroll)
        container.remove_children()

        games = self.schedule.get("games", [])
        if not games:
            container.mount(Label("No scheduled games"))
            return

        # Separate completed and upcoming games
        completed_games = []
        upcoming_games = []
        for game in games:
            state = game.get("gameState", "FUT")
            if state in ("FINAL", "OFF"):
                completed_games.append(game)
            else:
                upcoming_games.append(game)

        # Take last 3 completed games + all upcoming
        recent_completed = completed_games[-3:] if completed_games else []
        display_games = recent_completed + upcoming_games

        if not display_games:
            container.mount(Label("No scheduled games"))
            return

        for game in display_games:
            row = Horizontal(classes="game-row")

            # Date
            start_time = game.get("startTimeUTC", "")
            local_time = get_local_time_with_tz(start_time)
            game_date = game.get("gameDate", "")

            # Opponent
            home = game.get("homeTeam", {}).get("abbrev", "???")
            away = game.get("awayTeam", {}).get("abbrev", "???")
            opponent = f"vs {away}" if home == self.team_abbrev else f"@ {home}"

            # Result/Time
            state = game.get("gameState", "FUT")
            if state in ("FINAL", "OFF"):
                home_score = game.get("homeTeam", {}).get("score", 0)
                away_score = game.get("awayTeam", {}).get("score", 0)
                if home == self.team_abbrev:
                    result = f"{'W' if home_score > away_score else 'L'} {home_score}-{away_score}"
                else:
                    result = f"{'W' if away_score > home_score else 'L'} {away_score}-{home_score}"
            elif state in ("LIVE", "CRIT"):
                result = "LIVE"
            else:
                result = local_time or "TBD"

            row.compose_add_child(Label(game_date, classes="game-date"))
            row.compose_add_child(Label(opponent, classes="game-opponent"))
            row.compose_add_child(Label(result, classes="game-result"))

            container.mount(row)

    def on_player_row_selected(self, event: PlayerRow.Selected) -> None:
        """Handle player selection."""
        from faceoff.screens.player import PlayerScreen

        self.app.push_screen(PlayerScreen(self.client, event.player_id, event.player_name))

    def action_back(self) -> None:
        """Go back."""
        self.app.pop_screen()

    def action_refresh(self) -> None:
        """Manually refresh team data."""
        self.client.clear_cache()
        self.load_team_data()
        self.notify("Refreshed")

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

    def _get_focused_player_index(self) -> int:
        """Get the index of the currently focused player row, or -1 if none."""
        rows = list(self.query(PlayerRow))
        for i, row in enumerate(rows):
            if row.has_focus:
                return i
        return -1

    def _focus_player_at_index(self, index: int) -> None:
        """Focus the player row at the given index and scroll into view."""
        rows = list(self.query(PlayerRow))
        if rows and 0 <= index < len(rows):
            rows[index].focus()
            rows[index].scroll_visible()

    def action_focus_prev_player(self) -> None:
        """Focus the previous player row."""
        idx = self._get_focused_player_index()
        if idx > 0:
            self._focus_player_at_index(idx - 1)
        elif idx == -1:
            # No player focused, focus the first one
            self._focus_player_at_index(0)

    def action_focus_next_player(self) -> None:
        """Focus the next player row."""
        idx = self._get_focused_player_index()
        rows = list(self.query(PlayerRow))
        if idx < len(rows) - 1:
            self._focus_player_at_index(idx + 1)
        elif idx == -1 and rows:
            # No player focused, focus the first one
            self._focus_player_at_index(0)
