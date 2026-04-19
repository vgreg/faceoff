# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Faceoff is a terminal TUI app for watching NHL hockey games, written in Python 3.10+ using Textual and managed with uv.

## Common Commands

```bash
# Install dependencies and pre-commit hooks
make install

# Run the app
uv run faceoff

# Run all code quality checks (pre-commit + type checking)
make check

# Run tests with doctests
make test

# Build wheel distribution
make build

# Serve documentation locally at http://localhost:8000
make docs
```

### Direct Commands

```bash
# Run a single test file
uv run python -m pytest tests/test_foo.py

# Run type checker
uv run ty check

# Run linter/formatter
uv run ruff check .
uv run ruff format .

# Test across Python versions (3.10-3.14)
tox
```

## Architecture

```
src/faceoff/
├── __init__.py          # Package version
├── cli.py               # Entry point (faceoff command, argparse for --refresh-interval)
├── app.py               # Main Textual App class
├── api/
│   ├── __init__.py
│   └── client.py        # NHL API async client with caching
├── screens/
│   ├── __init__.py
│   ├── schedule.py      # Game schedule browser (main screen)
│   ├── game.py          # Game detail view with play-by-play
│   ├── pregame.py       # Pre-game matchup preview
│   ├── standings.py     # League standings view (Wild Card/Division/Conference/League tabs)
│   ├── stats.py         # Skater and goalie stats leaders
│   ├── teams.py         # Team browser and team detail screens
│   └── player.py        # Player profile view
└── widgets/
    ├── __init__.py
    ├── game_card.py     # Game card for schedule list
    ├── scoreboard.py    # Score display widget
    └── play_by_play.py  # Play-by-play event list
```

### Key Components

- **NHLClient** (`api/client.py`): Async HTTP client (httpx.AsyncClient) for `api-web.nhle.com/v1` with response caching and redirect following. All `get_*` methods are async — always `await` them from inside screen workers.
- **ScheduleScreen**: Main screen showing games for a date with responsive grid layout, supports date navigation (h/l keys) and navigation to Standings/Stats/Teams screens
- **GameScreen**: Shows scoreboard, goals, team game stats, and play-by-play with auto-refresh for live and pre-game states. Team stats pulled from the `/gamecenter/{id}/right-rail` endpoint.
- **PreGameScreen**: Matchup preview shown for games in `FUT` or `PRE` state
- **StandingsScreen**: League standings with Wild Card, Division, Conference, and League tabs
- **StatsScreen**: Skater and goalie stats leaders
- **TeamsScreen / TeamDetailScreen**: Team browser and per-team detail (roster + schedule)
- **PlayerScreen**: Player profile (career and game log)
- **GameCard**: Individual game card widget with local time display and timezone abbreviation

### Data Flow

1. CLI parses `--refresh-interval` (default 30s, min 5s) and instantiates FaceoffApp
2. App launches ScheduleScreen with shared NHLClient
3. ScheduleScreen fetches schedule and renders GameCard widgets in a responsive grid
4. Selecting a live/completed game pushes GameScreen, which fetches boxscore, play-by-play, landing, and right-rail team stats
5. Selecting a future/pre-game game pushes PreGameScreen; postponed/cancelled games show a notification
6. Live and pre-game GameScreens auto-refresh every `refresh_interval` seconds; ScheduleScreen refreshes on the same interval

### UI Features

- **Responsive Layout**: Game cards automatically arrange in rows based on terminal width (29 chars per card)
- **Resize Handling**: Cards reflow when terminal is resized
- **Time Display**: UTC times converted to local time with timezone abbreviation (e.g., "7:00 PM EST")
- **Game State Notifications**: Friendly messages for future, postponed, or cancelled games

## Key Tools & Configuration

- **TUI Framework:** Textual
- **NHL API:** Direct httpx.AsyncClient calls to `api-web.nhle.com/v1` (NHLClient wraps httpx directly; `nhl-stats-api-client` is listed as a dependency but not imported)
- **Package manager:** uv (use `uv run` to execute commands)
- **Linting/formatting:** ruff (line length 120, strict ruleset)
- **Type checking:** ty
- **Pre-commit:** Runs ruff, file validators, and formatters on commit

## CI/CD

GitHub Actions runs on PRs and main branch:
1. Pre-commit checks and lock file validation
2. Tests across Python 3.10-3.14
3. Documentation build verification

Releases are automated via GitHub release tags, publishing to PyPI.
