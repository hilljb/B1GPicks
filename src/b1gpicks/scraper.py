"""HTTP client for fetching Big Ten schedules and ESPN Matchup Predictor data."""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from . import espn
from .models import Game, Prediction, Schedule
from .sports import ScheduleType, Sport, get_sport

ProgressCallback = Callable[[Game], None]


class Scraper:
    """Fetches ESPN schedule and game pages for one sport.

    Requests are sent with a desktop Chrome (macOS) user agent, retried on
    transient errors, and spaced at least ``delay`` seconds apart.

    Example:
        >>> with Scraper("football") as scraper:          # doctest: +SKIP
        ...     schedule = scraper.get_picks()
        ...     for game in schedule.games:
        ...         print(game.matchup, game.pick_win_pct)
    """

    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    )

    def __init__(
        self,
        sport: str | Sport = "football",
        *,
        user_agent: str | None = None,
        timeout: float = 30,
        delay: float = 1.0,
        retries: int = 3,
    ) -> None:
        """
        Args:
            sport: ``"football"`` or ``"basketball"`` (or a :class:`Sport`).
            user_agent: Custom user agent. Defaults to Chrome on macOS.
            timeout: Per-request timeout in seconds.
            delay: Minimum seconds between consecutive requests.
            retries: Retries for connection errors and 429/5xx responses.
        """
        self.sport = get_sport(sport)
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        self.timeout = timeout
        self.delay = delay
        self._last_request: float | None = None

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate",
            }
        )
        retry = Retry(
            total=retries,
            backoff_factor=1.0,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    # ------------------------------------------------------------------ HTTP

    def _throttle(self) -> None:
        if self._last_request is not None and self.delay > 0:
            wait = self.delay - (time.monotonic() - self._last_request)
            if wait > 0:
                time.sleep(wait)
        self._last_request = time.monotonic()

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        """GET ``url`` (throttled), raising :class:`requests.HTTPError` on failure."""
        self._throttle()
        kwargs.setdefault("timeout", self.timeout)
        response = self.session.get(url, **kwargs)
        response.raise_for_status()
        return response

    def get_page_data(self, url: str) -> dict[str, Any]:
        """Fetch an ESPN page and return its embedded ``__espnfitt__`` JSON."""
        return espn.extract_page_data(self.get(url).text)

    # -------------------------------------------------------------- Schedule

    def schedule_url(self, **kwargs: Any) -> str:
        """Build a schedule URL for this scraper's sport. See :meth:`Sport.schedule_url`."""
        return self.sport.schedule_url(**kwargs)

    def get_schedule(
        self,
        *,
        week: int | None = None,
        year: int | None = None,
        season_type: int | None = None,
        on_date: date | None = None,
    ) -> Schedule:
        """Fetch one schedule page (without predictions).

        Football: pass ``week``/``year``/``season_type``, or nothing for the
        current week. Basketball: pass ``on_date``, or nothing for today.
        """
        url = self.schedule_url(week=week, year=year, season_type=season_type, on_date=on_date)
        dates = [on_date.strftime("%Y%m%d")] if on_date is not None else None
        return espn.parse_schedule(self.get_page_data(url), self.sport, dates=dates)

    # ------------------------------------------------------------ Predictions

    def get_prediction(self, game_url: str) -> Prediction | None:
        """Fetch a game page and return its Matchup Predictor, if present."""
        return espn.parse_prediction(self.get_page_data(game_url))

    def add_predictions(
        self,
        schedule: Schedule,
        *,
        include_final: bool = False,
        on_game: ProgressCallback | None = None,
    ) -> Schedule:
        """Populate ``prediction`` on each game in ``schedule`` (in place).

        Args:
            schedule: Schedule from :meth:`get_schedule`.
            include_final: Also fetch completed games. ESPN removes the
                predictor after a game ends, so this is off by default.
            on_game: Optional callback invoked after each game is processed.

        Returns:
            The same schedule, for chaining.
        """
        for game in schedule.games:
            if include_final or not game.is_final:
                game.prediction = self.get_prediction(game.url)
            if on_game is not None:
                on_game(game)
        return schedule

    def get_picks(
        self,
        *,
        week: int | None = None,
        year: int | None = None,
        season_type: int | None = None,
        on_date: date | None = None,
        on_game: ProgressCallback | None = None,
    ) -> Schedule:
        """Fetch a schedule page and the Matchup Predictor for each of its games."""
        schedule = self.get_schedule(week=week, year=year, season_type=season_type, on_date=on_date)
        return self.add_predictions(schedule, on_game=on_game)

    def get_picks_for_dates(
        self,
        start_date: date | None = None,
        num_days: int = 3,
        *,
        on_game: ProgressCallback | None = None,
    ) -> Schedule:
        """Fetch games and predictions over consecutive days (daily sports only).

        Args:
            start_date: First day (defaults to today).
            num_days: Number of days, including ``start_date``.
            on_game: Optional callback invoked after each game is processed.

        Raises:
            ValueError: If the sport is scheduled weekly (use :meth:`get_picks`).
        """
        if self.sport.schedule_type is not ScheduleType.DAILY:
            raise ValueError(f"{self.sport.name} is scheduled by week; use get_picks(week=...)")
        if num_days < 1:
            raise ValueError("num_days must be at least 1")

        start = start_date or date.today()
        days = [start + timedelta(days=i) for i in range(num_days)]
        games: dict[str, Game] = {}
        for day in days:
            for game in self.get_schedule(on_date=day).games:
                games.setdefault(game.id, game)

        label = espn.date_range_label(d.strftime("%Y%m%d") for d in days)
        schedule = Schedule(sport=self.sport.key, label=label, games=list(games.values()))
        return self.add_predictions(schedule, on_game=on_game)

    # -------------------------------------------------------------- Lifecycle

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self.session.close()

    def __enter__(self) -> Scraper:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
