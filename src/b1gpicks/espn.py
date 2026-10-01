"""Parsers for ESPN schedule and game pages.

ESPN renders its pages client-side from a JSON blob assigned to
``window['__espnfitt__']`` in an inline ``<script>`` tag. Every function in this
module works from that blob, which is far more stable than the rendered HTML.

Relevant locations within the blob:

* Schedule pages: ``page.content.events`` maps ``YYYYMMDD`` date keys (US/Eastern)
  to lists of events. ``page.content.requestedDates`` and ``page.content.calendar``
  describe which week is being shown (football).
* Game pages: ``page.content.gamepackage.mtchpPrdctr.teams`` holds the Matchup
  Predictor, one entry per team with ``value`` (percent) and ``isHome``.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any

from .models import Game, Prediction, Schedule, Team
from .sports import ESPN_BASE_URL, ScheduleType, Sport

_FITT_MARKER = re.compile(r"""window\[\s*['"]__espnfitt__['"]\s*\]\s*=\s*""")
_UNRANKED = {0, 99}


class ESPNParseError(ValueError):
    """Raised when an ESPN page does not contain the expected embedded data."""


def extract_page_data(html: str) -> dict[str, Any]:
    """Extract the ``window['__espnfitt__']`` JSON object from an ESPN page.

    Raises:
        ESPNParseError: If the blob is missing or is not valid JSON.
    """
    match = _FITT_MARKER.search(html)
    if not match:
        raise ESPNParseError("ESPN page data (window['__espnfitt__']) not found")
    try:
        data, _ = json.JSONDecoder().raw_decode(html, match.end())
    except json.JSONDecodeError as exc:
        raise ESPNParseError(f"ESPN page data is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ESPNParseError("ESPN page data is not a JSON object")
    return data


def _content(data: dict[str, Any]) -> dict[str, Any]:
    content = data.get("page", {}).get("content")
    if not isinstance(content, dict):
        raise ESPNParseError("ESPN page data has no page.content section")
    return content


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _parse_team(competitor: dict[str, Any]) -> Team:
    rank = competitor.get("rank")
    try:
        rank = int(rank) if rank is not None else None
    except (TypeError, ValueError):
        rank = None
    name = competitor.get("displayName") or competitor.get("name") or ""
    return Team(
        id=str(competitor.get("id", "")),
        name=name,
        short_name=competitor.get("location") or competitor.get("shortDisplayName") or name,
        abbreviation=competitor.get("abbrev", ""),
        rank=None if rank in _UNRANKED else rank,
    )


def _absolute_url(link: str) -> str:
    return link if link.startswith("http") else f"{ESPN_BASE_URL}{link}"


def parse_event(event: dict[str, Any]) -> Game | None:
    """Convert one schedule event into a :class:`Game`, or ``None`` if incomplete."""
    competitors = event.get("competitors") or []
    home = next((c for c in competitors if c.get("isHome")), None)
    away = next((c for c in competitors if not c.get("isHome")), None)
    link = event.get("link")
    if home is None or away is None or not link:
        return None
    status = event.get("status") or {}
    return Game(
        id=str(event.get("id", "")),
        away=_parse_team(away),
        home=_parse_team(home),
        start_time=_parse_time(event.get("date")),
        status=status.get("state", ""),
        status_detail=status.get("detail", ""),
        url=_absolute_url(link),
        neutral_site=bool(event.get("neutralSite", False)),
    )


def date_range_label(date_keys: Iterable[str]) -> str:
    """Format ``YYYYMMDD`` keys as ``"YYYY-MM-DD"`` or ``"YYYY-MM-DD to YYYY-MM-DD"``."""
    keys = sorted(date_keys)
    first, last = (f"{k[:4]}-{k[4:6]}-{k[6:]}" for k in (keys[0], keys[-1]))
    return first if first == last else f"{first} to {last}"


def _week_label(content: dict[str, Any], season_type: int | None, week: int | None) -> str | None:
    if week is None:
        return None
    for group in content.get("calendar") or []:
        if not isinstance(group, dict) or str(group.get("value")) != str(season_type):
            continue
        for entry in group.get("entries") or []:
            if str(entry.get("value")) == str(week):
                return entry.get("label")
    return f"Week {week}"


def parse_schedule(
    data: dict[str, Any],
    sport: Sport,
    *,
    dates: Iterable[str] | None = None,
) -> Schedule:
    """Parse ESPN schedule page data into a :class:`Schedule`.

    Args:
        data: Page data from :func:`extract_page_data`.
        sport: The sport the page belongs to.
        dates: Optional ``YYYYMMDD`` keys to keep. ESPN's daily (basketball)
            pages include neighboring days, so callers can restrict to the
            requested date.

    Raises:
        ESPNParseError: If the page has no schedule content.
    """
    content = _content(data)
    events_by_date = content.get("events") or {}
    if not isinstance(events_by_date, dict):
        raise ESPNParseError("Unexpected format for schedule events")

    wanted = set(dates) if dates is not None else None
    games: dict[str, Game] = {}
    for date_key in sorted(events_by_date):
        if wanted is not None and date_key not in wanted:
            continue
        for event in events_by_date[date_key] or []:
            game = parse_event(event)
            if game is not None:
                games.setdefault(game.id, game)

    ordered = sorted(
        games.values(),
        key=lambda g: (g.start_time is None, g.start_time or datetime.max.replace(tzinfo=timezone.utc)),
    )

    requested = content.get("requestedDates") or {}
    year = requested.get("year")
    week = requested.get("week")
    season_type = requested.get("seasontype", requested.get("seasonType"))

    if sport.schedule_type is ScheduleType.WEEKLY and week is not None:
        label = f"{year} {_week_label(content, season_type, week)}".strip()
    elif wanted:
        label = date_range_label(wanted)
    else:
        label = "Current schedule"

    return Schedule(
        sport=sport.key,
        label=label,
        games=ordered,
        year=year,
        week=week,
        season_type=season_type,
    )


def parse_prediction(data: dict[str, Any]) -> Prediction | None:
    """Extract ESPN's Matchup Predictor from game page data.

    Returns:
        The prediction, or ``None`` if the page has no predictor (ESPN removes
        it once a game is final, and it may be missing for some matchups).
    """
    gamepackage = _content(data).get("gamepackage") or {}
    teams = (gamepackage.get("mtchpPrdctr") or {}).get("teams") or []

    home_pct = away_pct = None
    for team in teams:
        value = team.get("value", team.get("percentage"))
        try:
            pct = float(value)
        except (TypeError, ValueError):
            continue
        if team.get("isHome"):
            home_pct = pct
        else:
            away_pct = pct

    if home_pct is None or away_pct is None:
        return None
    return Prediction(away_win_pct=away_pct, home_win_pct=home_pct)
