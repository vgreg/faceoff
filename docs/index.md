# Faceoff

<p align="center">
  <img src="assets/faceoff_logo.png" alt="Faceoff Logo" width="200">
</p>

A terminal user interface (TUI) application for following NHL hockey games in real-time.

## Features

- **Live Game Schedule**: Browse NHL games by date with easy navigation (previous/next day)
- **Real-time Updates**: Auto-refreshing scores for live games
- **Game Details**: View play-by-play, box scores, and scoring summaries for in-progress and completed games
- **Pre-Game Preview**: View matchup data including goalie comparison and skater leaders for upcoming games
- **League Standings**: View current NHL standings with multiple views (Wild Card, Division, Conference, League)
- **Player Stats Leaders**: View top players in various statistical categories for skaters and goalies
- **Team Browser**: Browse all NHL teams, view rosters, and team schedules
- **Player Profiles**: View detailed player information, career stats, and game logs
- **Responsive Layout**: Game cards and standings automatically arrange based on terminal width
- **Local Time Display**: Game times shown in your local timezone with timezone abbreviation

## Screenshot

![Faceoff Screenshot](assets/screenshot.png)

## Quick Start

### Installation

The easiest way to run Faceoff is with `uvx`:

```bash
uvx faceoff
```

Or install with pip:

```bash
pip install faceoff
faceoff
```

## Navigation

### Schedule Screen (Main Screen)

| Key | Action |
|-----|--------|
| `Arrow keys` | Navigate between game cards |
| `h` | Previous day |
| `l` | Next day |
| `t` | Jump to today |
| `s` | View standings |
| `p` | View player stats |
| `m` | Browse teams |
| `r` | Refresh |
| `Enter` | Select game (for live/completed games) |
| `q` | Quit |

### Game Screen

| Key | Action |
|-----|--------|
| `b` or `Escape` | Back to schedule |
| `r` | Refresh |
| `Tab` | Switch between tabs (Play-by-Play, Box Score, Summary) |
| `q` | Quit |

### Pre-Game Screen

| Key | Action |
|-----|--------|
| `b` or `Escape` | Back to schedule |
| `r` | Refresh |
| `q` | Quit |

### Standings Screen

| Key | Action |
|-----|--------|
| `Tab` | Switch between views (Wild Card, Division, Conference, League) |
| `Up/Down` or `j/k` | Scroll standings |
| `b` or `Escape` | Back to schedule |
| `r` | Refresh |
| `q` | Quit |

### Stats Screen

| Key | Action |
|-----|--------|
| `Tab` | Switch between Skaters and Goalies |
| `b` or `Escape` | Back to schedule |
| `r` | Refresh |
| `q` | Quit |

### Teams Screen

| Key | Action |
|-----|--------|
| `Arrow keys` | Navigate between team cards |
| `Enter` | Select team to view details |
| `b` or `Escape` | Back to schedule |
| `r` | Refresh |
| `q` | Quit |

### Team Detail Screen

| Key | Action |
|-----|--------|
| `Tab` | Switch between Roster and Schedule |
| `Enter` | Select player to view profile |
| `b` or `Escape` | Back to teams |
| `r` | Refresh |
| `q` | Quit |

### Player Screen

| Key | Action |
|-----|--------|
| `Tab` | Switch between Info, Stats, and Game Log |
| `b` or `Escape` | Back |
| `r` | Refresh |
| `q` | Quit |

## Acknowledgments

This project was inspired by [Playball](https://github.com/paaatrick/playball), a similar terminal application for following MLB baseball games.

### Built With

- **[Textual](https://github.com/Textualize/textual)** - The modern TUI framework for Python that powers the user interface
- **[nhl-stats-api-client](https://github.com/nhl-stats-api-client)** - Python client for accessing NHL API data

## Disclaimer

This project is not affiliated with, endorsed by, or in any way officially connected with the National Hockey League (NHL), any of its teams, or any of its affiliates. All NHL logos, trademarks, and data are the property of the NHL and its teams.

This application uses publicly available NHL API data for informational and educational purposes only.
