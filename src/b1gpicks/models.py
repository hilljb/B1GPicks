"""Data models for games, predictions, and picks."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Team:
    """A team as listed by ESPN.

    Attributes:
        id: ESPN team ID.
        name: Full display name, e.g. ``"Penn State Nittany Lions"``.
        short_name: Short name, e.g. ``"Penn State"``.
        abbreviation: ESPN abbreviation, e.g. ``"PSU"``.
        rank: AP/CFP ranking, or ``None`` if unranked.
    """

    id: str
    name: str
    short_name: str
    abbreviation: str
    rank: int | None = None

    @property
    def label(self) -> str:
        """Short name with ranking prefix, e.g. ``"#5 Ohio State"``."""
        return f"#{self.rank} {self.short_name}" if self.rank else self.short_name


@dataclass(frozen=True)
class Prediction:
    """ESPN Matchup Predictor win probabilities (percent, 0-100)."""

    away_win_pct: float
    home_win_pct: float


@dataclass
class Game:
    """A scheduled game, optionally with ESPN's Matchup Predictor result.

    Attributes:
        id: ESPN game ID.
        away: Away (or listed-first, for neutral sites) team.
        home: Home (or listed-second, for neutral sites) team.
        start_time: Kickoff/tip time (timezone-aware, UTC), or ``None`` if TBD.
        status: ESPN game state: ``"pre"``, ``"in"``, or ``"post"``.
        status_detail: ESPN's human-readable status text.
        url: Absolute URL of the ESPN game page.
        neutral_site: Whether the game is at a neutral site.
        prediction: Matchup Predictor result, if available.
    """

    id: str
    away: Team
    home: Team
    start_time: datetime | None
    status: str
    status_detail: str
    url: str
    neutral_site: bool = False
    prediction: Prediction | None = field(default=None)

    @property
    def matchup(self) -> str:
        """Display string such as ``"Penn State @ Northwestern"``."""
        sep = "vs" if self.neutral_site else "@"
        return f"{self.away.label} {sep} {self.home.label}"

    @property
    def is_final(self) -> bool:
        return self.status == "post"

    @property
    def pick(self) -> Team | None:
        """The team ESPN gives the higher win probability (home team on an exact tie)."""
        if self.prediction is None:
            return None
        if self.prediction.away_win_pct > self.prediction.home_win_pct:
            return self.away
        return self.home

    @property
    def pick_win_pct(self) -> float | None:
        """Win probability of :attr:`pick`."""
        if self.prediction is None:
            return None
        return max(self.prediction.away_win_pct, self.prediction.home_win_pct)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-friendly dictionary."""
        pick = self.pick
        return {
            "game_id": self.id,
            "away_team": self.away.name,
            "home_team": self.home.name,
            "away_abbreviation": self.away.abbreviation,
            "home_abbreviation": self.home.abbreviation,
            "away_rank": self.away.rank,
            "home_rank": self.home.rank,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "status": self.status,
            "status_detail": self.status_detail,
            "neutral_site": self.neutral_site,
            "game_url": self.url,
            "away_win_pct": self.prediction.away_win_pct if self.prediction else None,
            "home_win_pct": self.prediction.home_win_pct if self.prediction else None,
            "pick": pick.name if pick else None,
            "pick_win_pct": self.pick_win_pct,
        }


@dataclass
class Schedule:
    """A page of ESPN schedule results.

    Attributes:
        sport: Sport key (``"football"`` or ``"basketball"``).
        label: Human-readable description, e.g. ``"2026 Week 5"``.
        games: Games on the page, ordered by start time.
        year: Season year, when known (football).
        week: Week number, when known (football).
        season_type: ESPN season type (2 = regular, 3 = postseason), when known.
    """

    sport: str
    label: str
    games: list[Game]
    year: int | None = None
    week: int | None = None
    season_type: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "sport": self.sport,
            "label": self.label,
            "year": self.year,
            "week": self.week,
            "season_type": self.season_type,
            "games": [g.to_dict() for g in self.games],
        }
