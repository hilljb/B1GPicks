# Changelog

## 0.2.0 - 2026-10-01

### Added

- College football support, using ESPN's weekly Big Ten schedule (group 5).
  Football is now the default sport.
- The `b1gpicks` command, with options for `--sport`, `--week`, `--year`,
  `--postseason`, `--date`, `--days`, `--timezone`, `--json`, `--output`, and
  `--no-save`. `examples/scrape_predictors.py` wraps the same command.
- A pick for each game (the team with the higher win probability), shown in
  the table and saved in the JSON output.
- Team rankings, local start times, game status, and neutral-site handling.
- Typed result models: `Schedule`, `Game`, `Team`, and `Prediction`.
- Throttling between requests, plus retries with backoff for 429/5xx responses.
- Offline unit tests based on trimmed real ESPN pages, and live tests that run
  with `pytest --run-network`.

### Changed

- Schedules and predictions are now read from ESPN's embedded `__espnfitt__`
  JSON. The schedule parser reads `page.content.events`. The predictor parser
  reads `gamepackage.mtchpPrdctr` and matches each percentage to the home or
  away team using the `isHome` flag, instead of relying on SVG element order.
- `Scraper` now takes a sport, `Scraper("football")` or
  `Scraper("basketball")`. The old date-based methods
  (`get_schedule_url`, `get_games_from_schedule`, `get_game_predictor`, and
  `scrape_games_by_date_range`) are replaced by `get_schedule`,
  `get_prediction`, `get_picks`, and `get_picks_for_dates`.
- JSON output goes to `data/` (git-ignored) instead of the working directory.
- Removed the dependencies on `beautifulsoup4` and `lxml`.

### Fixed

- Schedule scraping returned no games because ESPN moved events out of
  `page.content.schedule`.
- Game predictor scraping returned `None`, and could swap the home and away
  percentages.
- `Accept-Encoding` no longer advertises Brotli (`br`), which `requests` cannot
  decode without an extra package.

### Removed

- `debug_espn.py`, `verify_setup.py`, and the separate SETUP, QUICK_START,
  FIXES, IMPLEMENTATION_NOTES, and TEST_RESULTS documents. Their still-relevant
  content is now in the README.

## 0.1.0 - 2025-12-01

- Initial release: Big Ten men's basketball Matchup Predictor scraper.
