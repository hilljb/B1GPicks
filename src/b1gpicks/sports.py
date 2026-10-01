"""Sport definitions and ESPN schedule URL construction."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

ESPN_BASE_URL = "https://www.espn.com"


class ScheduleType(str, Enum):
    """How ESPN organizes a sport's schedule pages."""

    WEEKLY = "weekly"
    DAILY = "daily"


@dataclass(frozen=True)
class Sport:
    """An ESPN sport/league and the Big Ten conference group within it.

    Attributes:
        key: Short identifier used by this package and the CLI.
        name: Human-readable name.
        slug: ESPN URL path segment for the league.
        group: ESPN conference group ID for the Big Ten in this league.
        schedule_type: Whether ESPN pages the schedule by week or by date.
    """

    key: str
    name: str
    slug: str
    group: int
    schedule_type: ScheduleType

    def schedule_url(
        self,
        *,
        week: int | None = None,
        year: int | None = None,
        season_type: int | None = None,
        on_date: date | None = None,
        group: int | None = None,
    ) -> str:
        """Build the ESPN schedule URL for this sport.

        Weekly sports (football) accept ``week``, ``year``, and ``season_type``.
        With none of them, ESPN serves the current week. Daily sports
        (basketball) accept ``on_date``. With no date, ESPN serves today.

        Args:
            week: Week number within the season type (football only).
            year: Season year (football only). Required if ``week`` is given.
            season_type: ESPN season type: 2 = regular season, 3 = postseason
                (football only). Defaults to 2 when ``week`` is given.
            on_date: Date of the schedule page (basketball only).
            group: Override the conference group ID.

        Returns:
            The fully qualified schedule URL.

        Raises:
            ValueError: If arguments are inconsistent with the schedule type.
        """
        group = self.group if group is None else group
        base = f"{ESPN_BASE_URL}/{self.slug}/schedule/_"

        if self.schedule_type is ScheduleType.WEEKLY:
            if on_date is not None:
                raise ValueError(f"{self.name} schedules are weekly; use week= instead of on_date=")
            if week is None:
                if year is not None or season_type is not None:
                    raise ValueError("year/season_type require week to be set")
                return f"{base}/group/{group}"
            if year is None:
                raise ValueError("year is required when week is given")
            season_type = 2 if season_type is None else season_type
            return f"{base}/week/{week}/year/{year}/seasontype/{season_type}/group/{group}"

        if week is not None or year is not None or season_type is not None:
            raise ValueError(f"{self.name} schedules are daily; use on_date= instead of week/year")
        if on_date is None:
            return f"{base}/group/{group}"
        return f"{base}/date/{on_date.strftime('%Y%m%d')}/group/{group}"


FOOTBALL = Sport(
    key="football",
    name="College Football",
    slug="college-football",
    group=5,
    schedule_type=ScheduleType.WEEKLY,
)

BASKETBALL = Sport(
    key="basketball",
    name="Men's College Basketball",
    slug="mens-college-basketball",
    group=7,
    schedule_type=ScheduleType.DAILY,
)

SPORTS: dict[str, Sport] = {s.key: s for s in (FOOTBALL, BASKETBALL)}

_ALIASES = {
    "ncaaf": "football",
    "cfb": "football",
    "ncaab": "basketball",
    "ncaam": "basketball",
    "mbb": "basketball",
}


def get_sport(sport: str | Sport) -> Sport:
    """Resolve a sport key or alias (e.g. ``"football"``, ``"ncaaf"``) to a :class:`Sport`."""
    if isinstance(sport, Sport):
        return sport
    key = _ALIASES.get(sport.lower(), sport.lower())
    try:
        return SPORTS[key]
    except KeyError:
        valid = ", ".join(sorted([*SPORTS, *_ALIASES]))
        raise ValueError(f"Unknown sport {sport!r}; expected one of: {valid}") from None
