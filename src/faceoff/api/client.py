"""NHL API client wrapper with caching and convenience methods."""

from datetime import datetime
from typing import Any

import httpx


class NHLClient:
    """Client for NHL API with caching and convenience methods."""

    BASE_URL = "https://api-web.nhle.com/v1"

    def __init__(self) -> None:
        self._http = httpx.Client(
            timeout=30.0,
            headers={"User-Agent": "Faceoff/1.0"},
            follow_redirects=True,
        )
        self._cache: dict[str, tuple[float, Any]] = {}
        self._cache_ttl = 30.0  # seconds

    def _get(self, endpoint: str, cache_ttl: float | None = None) -> Any:
        """Make a GET request with optional caching."""
        url = f"{self.BASE_URL}{endpoint}"
        ttl = cache_ttl if cache_ttl is not None else self._cache_ttl

        # Check cache
        if url in self._cache:
            cached_time, cached_data = self._cache[url]
            if datetime.now().timestamp() - cached_time < ttl:
                return cached_data

        response = self._http.get(url)
        response.raise_for_status()
        data = response.json()

        # Update cache
        self._cache[url] = (datetime.now().timestamp(), data)
        return data

    def get_schedule(self, date: str | None = None) -> dict[str, Any]:
        """Get schedule for a specific date or today.

        Args:
            date: Date in YYYY-MM-DD format, or None for today

        Returns:
            Schedule data including games for the week
        """
        if date:
            return self._get(f"/schedule/{date}")
        return self._get("/schedule/now")

    def get_scoreboard(self) -> dict[str, Any]:
        """Get current scoreboard with live game data."""
        return self._get("/scoreboard/now", cache_ttl=10.0)

    def get_game_boxscore(self, game_id: int) -> dict[str, Any]:
        """Get box score for a specific game."""
        return self._get(f"/gamecenter/{game_id}/boxscore", cache_ttl=10.0)

    def get_game_play_by_play(self, game_id: int) -> dict[str, Any]:
        """Get play-by-play data for a specific game."""
        return self._get(f"/gamecenter/{game_id}/play-by-play", cache_ttl=10.0)

    def get_game_landing(self, game_id: int) -> dict[str, Any]:
        """Get landing page data for a specific game (summary info)."""
        return self._get(f"/gamecenter/{game_id}/landing", cache_ttl=10.0)

    def get_standings(self, date: str | None = None) -> dict[str, Any]:
        """Get standings for a specific date or current."""
        if date:
            return self._get(f"/standings/{date}")
        return self._get("/standings/now")

    def get_skater_stats_leaders(self) -> dict[str, Any]:
        """Get current skater stats leaders."""
        return self._get("/skater-stats-leaders/current")

    def get_goalie_stats_leaders(self) -> dict[str, Any]:
        """Get current goalie stats leaders."""
        return self._get("/goalie-stats-leaders/current")

    def get_team_roster(self, team_abbrev: str) -> dict[str, Any]:
        """Get current roster for a team."""
        return self._get(f"/roster/{team_abbrev}/current")

    def get_team_schedule(self, team_abbrev: str) -> dict[str, Any]:
        """Get current week schedule for a team."""
        return self._get(f"/club-schedule/{team_abbrev}/week/now")

    def get_team_month_schedule(self, team_abbrev: str, month: str | None = None) -> dict[str, Any]:
        """Get month schedule for a team (includes past games).

        Args:
            team_abbrev: Team abbreviation (e.g., 'TOR')
            month: Month in YYYY-MM format, or None for current month

        Returns:
            Schedule data for the month including past and future games
        """
        if month:
            return self._get(f"/club-schedule/{team_abbrev}/month/{month}")
        from datetime import datetime

        current_month = datetime.now().strftime("%Y-%m")
        return self._get(f"/club-schedule/{team_abbrev}/month/{current_month}")

    def get_team_stats(self, team_abbrev: str) -> dict[str, Any]:
        """Get current stats for a team's players."""
        return self._get(f"/club-stats/{team_abbrev}/now")

    def get_player_landing(self, player_id: int) -> dict[str, Any]:
        """Get landing page data for a player."""
        return self._get(f"/player/{player_id}/landing")

    def get_player_game_log(self, player_id: int) -> dict[str, Any]:
        """Get game log for a player in current season."""
        return self._get(f"/player/{player_id}/game-log/now")

    def clear_cache(self) -> None:
        """Clear the response cache."""
        self._cache.clear()

    def close(self) -> None:
        """Close the HTTP client."""
        self._http.close()
