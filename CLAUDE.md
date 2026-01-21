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

# Test across Python versions (3.9-3.13)
tox
```

## Architecture

```
src/faceoff/
├── __init__.py          # Package version
├── cli.py               # Entry point (faceoff command)
├── app.py               # Main Textual App class
├── api/
│   ├── __init__.py
│   └── client.py        # NHL API client with caching
├── screens/
│   ├── __init__.py
│   ├── schedule.py      # Game schedule browser (main screen)
│   ├── game.py          # Game detail view with play-by-play
│   └── standings.py     # League standings view
└── widgets/
    ├── __init__.py
    ├── game_card.py     # Game card for schedule list
    ├── scoreboard.py    # Score display widget
    └── play_by_play.py  # Play-by-play event list
```

### Key Components

- **NHLClient** (`api/client.py`): HTTP client wrapper around NHL API with response caching and redirect following
- **ScheduleScreen**: Main screen showing today's games with responsive grid layout, supports date navigation (h/l keys)
- **GameScreen**: Shows scoreboard, play-by-play, box score tabs with auto-refresh for live games
- **StandingsScreen**: Division standings by conference
- **GameCard**: Individual game card widget with local time display and timezone abbreviation

### Data Flow

1. App launches ScheduleScreen with shared NHLClient
2. ScheduleScreen fetches schedule and renders GameCard widgets in a responsive grid
3. Selecting a live/completed game pushes GameScreen, which fetches boxscore and play-by-play
4. Selecting a future game shows a notification with game time instead of opening GameScreen
5. Live games auto-refresh every 10 seconds; schedule refreshes every 30 seconds

### UI Features

- **Responsive Layout**: Game cards automatically arrange in rows based on terminal width (29 chars per card)
- **Resize Handling**: Cards reflow when terminal is resized
- **Time Display**: UTC times converted to local time with timezone abbreviation (e.g., "7:00 PM EST")
- **Game State Notifications**: Friendly messages for future, postponed, or cancelled games

## Key Tools & Configuration

- **TUI Framework:** Textual
- **NHL API:** nhl-stats-api-client (wrapped in custom client)
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
