# B1GPicks

Big Ten picks for college football and men's basketball, based on ESPN's
**Matchup Predictor** win probabilities.

B1GPicks reads ESPN's Big Ten schedule, opens each game page, extracts the
Matchup Predictor percentages (ESPN FPI for football, BPI for basketball), and
prints a pick for every game: the team ESPN gives the higher chance to win.

```text
$ b1gpicks
Big Ten College Football picks: 2026 Week 5
Win probabilities from the ESPN Matchup Predictor. Times in MDT.

When                Matchup                      Away   Home  Pick
------------------  --------------------------  -----  -----  ---------------------
Fri Oct 2 6:00 PM   Penn State @ Northwestern   55.8%  44.2%  Penn State (55.8%)
Sat Oct 3 10:00 AM  Michigan @ Minnesota        75.6%  24.4%  Michigan (75.6%)
Sat Oct 3 10:30 AM  Michigan State @ Wisconsin  32.7%  67.3%  Wisconsin (67.3%)
Sat Oct 3 1:30 PM   #5 Ohio State @ #14 Iowa    82.9%  17.1%  #5 Ohio State (82.9%)
Sat Oct 3 2:00 PM   Maryland @ Nebraska          7.3%  92.7%  Nebraska (92.7%)
Sat Oct 3 2:15 PM   Purdue @ Illinois           18.9%  81.1%  Illinois (81.1%)
Sat Oct 3 5:30 PM   Washington @ #18 USC        16.2%  83.8%  #18 USC (83.8%)
Sat Oct 3 6:00 PM   #6 Indiana @ Rutgers        95.9%   4.1%  #6 Indiana (95.9%)

8 games, 8 with predictions.
```

## Installation

Requires Python 3.11+. With [Conda](https://docs.conda.io/en/latest/miniconda.html):

```bash
conda env create -f environment.yml
conda activate b1gpicks
```

Or with pip in any virtual environment:

```bash
pip install -e ".[dev]"
```

Both install the package in editable mode and add a `b1gpicks` command.
After pulling changes to `environment.yml`, run
`conda env update -f environment.yml --prune`.

## Usage

### Football (default)

```bash
b1gpicks                      # ESPN's current week
b1gpicks --week 6             # week 6 of the current season
b1gpicks --week 6 --year 2025 # a past season
b1gpicks --week 1 --postseason # bowl games
```

With no `--week`, ESPN chooses the current week, the same one shown at
<https://www.espn.com/college-football/schedule/_/group/5>.

### Basketball

ESPN organizes basketball schedules by day rather than by week:

```bash
b1gpicks --sport basketball                       # today plus the next 2 days
b1gpicks --sport basketball --date 2027-01-15 --days 7
```

### Output options

| Option | Description |
| --- | --- |
| `--timezone America/Denver` | Show times in a specific IANA timezone (default: system local time) |
| `--json` | Print JSON instead of the table |
| `-o picks.json` | Write the JSON results to a specific file |
| `--no-save` | Don't write a JSON file |
| `-q`, `--quiet` | Hide progress messages (written to stderr) |
| `--delay 2` | Minimum seconds between requests to ESPN (default: 1) |

By default, each run saves a JSON file to `data/`, for example
`data/football_2026-week-5_20261001_153000.json`. The `data/` directory is
git-ignored. Run `b1gpicks --help` for the full option list.

`python examples/scrape_predictors.py` is equivalent to `b1gpicks` and accepts
the same options.

### How picks are made

The pick is the team with the higher Matchup Predictor win probability. On an
exact 50/50 split, the home team is picked. Games are handled as follows:

- **Upcoming games:** show the predictor percentages and the pick.
- **Completed games:** show `Final` without fetching the game page, because
  ESPN removes the predictor once a game ends.
- **Missing predictor:** if ESPN hasn't published a predictor for a game yet,
  the row shows `No predictor available`.

### JSON format

```json
{
  "generated_at": "2026-10-01T15:38:31-06:00",
  "sport": "football",
  "label": "2026 Week 5",
  "year": 2026,
  "week": 5,
  "season_type": 2,
  "games": [
    {
      "game_id": "401858476",
      "away_team": "Penn State Nittany Lions",
      "home_team": "Northwestern Wildcats",
      "away_abbreviation": "PSU",
      "home_abbreviation": "NU",
      "away_rank": null,
      "home_rank": null,
      "start_time": "2026-10-03T00:00:00+00:00",
      "status": "pre",
      "status_detail": "Fri, October 2nd at 8:00 PM EDT",
      "neutral_site": false,
      "game_url": "https://www.espn.com/college-football/game/_/gameId/401858476/penn-state-northwestern",
      "away_win_pct": 55.8,
      "home_win_pct": 44.2,
      "pick": "Penn State Nittany Lions",
      "pick_win_pct": 55.8
    }
  ]
}
```

`start_time` is in UTC. `status` is ESPN's game state: `pre`, `in`, or `post`.
`season_type` is `2` for the regular season and `3` for the postseason.

## Python API

```python
from b1gpicks import Scraper

with Scraper("football") as scraper:
    schedule = scraper.get_picks()              # or get_picks(week=6, year=2026)

for game in schedule.games:
    if game.pick:
        print(f"{game.matchup}: {game.pick.label} ({game.pick_win_pct}%)")
```

| Method | Purpose |
| --- | --- |
| `Scraper(sport, delay=1.0, timeout=30, retries=3, user_agent=None)` | Create a client for `"football"` or `"basketball"` |
| `get_schedule(week=, year=, season_type=)` | Games for one football week, without predictions |
| `get_schedule(on_date=)` | Basketball games for one date, without predictions |
| `get_prediction(game_url)` | Matchup Predictor for one game page, as a `Prediction` or `None` |
| `get_picks(...)` | `get_schedule(...)` plus a prediction for each game |
| `get_picks_for_dates(start_date, num_days)` | Basketball games and predictions across several days |

Results are dataclasses (`Schedule`, `Game`, `Team`, `Prediction`), and each has
a `to_dict()` method for serialization. The `b1gpicks.espn` module contains the
parsing functions, which take page data and make no network calls.

## How it works

ESPN builds its pages in the browser from a JSON object embedded in each page
as `window['__espnfitt__']`. B1GPicks reads that JSON instead of the rendered
HTML, which is more reliable when ESPN changes its layout.

| Page | URL | Data used |
| --- | --- | --- |
| Football schedule | `/college-football/schedule/_/[week/{w}/year/{y}/seasontype/{t}/]group/5` | `page.content.events` |
| Basketball schedule | `/mens-college-basketball/schedule/_/[date/{YYYYMMDD}/]group/7` | `page.content.events` |
| Game page | `/{sport}/game/_/gameId/{id}` | `page.content.gamepackage.mtchpPrdctr.teams` |

In the predictor data, each team entry has a `value` (win percentage) and an
`isHome` flag. Percentages are matched to teams using `isHome`, not by position
on the page.

Group 5 is the Big Ten in football, and group 7 is the Big Ten in basketball.
Both lists include non-conference games that involve a Big Ten team.

Requests use a desktop Chrome user agent and are spaced at least one second
apart. Connection errors and HTTP 429/5xx responses are retried with backoff.
Please keep the delay reasonable.

## Development

```bash
pytest                      # unit tests (offline) with coverage
pytest --run-network        # also run live tests against espn.com
```

Unit tests run against trimmed copies of real ESPN pages in `tests/fixtures/`,
so they make no network calls. If ESPN changes its page format, the live tests
in `tests/test_network.py` will be the first to fail. Fix the parser in
`src/b1gpicks/espn.py`, then refresh the fixtures from current pages.

```text
src/b1gpicks/
├── cli.py       # `b1gpicks` command: argument parsing, table output, JSON files
├── espn.py      # parsing for ESPN page data (no network calls)
├── models.py    # Team, Game, Prediction, Schedule dataclasses
├── scraper.py   # HTTP client: throttling, retries, high-level fetch methods
└── sports.py    # football/basketball definitions and schedule URLs
tests/
├── fixtures/    # trimmed ESPN pages used by the unit tests
└── test_*.py
```

See [CHANGELOG.md](CHANGELOG.md) for release history.

## Disclaimer

This project is not affiliated with ESPN. It reads publicly available pages for
personal use. Respect ESPN's terms of service and keep request rates low.

## License

MIT. See [LICENSE](LICENSE).
