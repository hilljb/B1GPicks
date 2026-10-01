"""Command-line interface: ``b1gpicks`` prints ESPN Matchup Predictor picks."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Sequence
from datetime import date, datetime, tzinfo
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import requests

from . import __version__
from .espn import ESPNParseError
from .models import Game, Schedule
from .scraper import Scraper
from .sports import SPORTS, ScheduleType, get_sport

DEFAULT_OUTPUT_DIR = Path("data")


def _format_time(game: Game, tz: tzinfo | None) -> str:
    if game.start_time is None:
        return "TBD"
    local = game.start_time.astimezone(tz)
    return local.strftime("%a %b %d %I:%M %p").replace(" 0", " ")


def _format_pct(value: float | None) -> str:
    return "-" if value is None else f"{value:.1f}%"


def _pick_text(game: Game) -> str:
    if game.pick is not None:
        return f"{game.pick.label} ({game.pick_win_pct:.1f}%)"
    if game.is_final:
        return game.status_detail or "Final"
    return "No predictor available"


def format_picks(schedule: Schedule, tz: tzinfo | None = None) -> str:
    """Render a schedule's picks as a plain-text table.

    Args:
        schedule: Schedule with predictions populated.
        tz: Timezone for start times. Defaults to the system's local timezone.
    """
    sport = get_sport(schedule.sport)
    tz_name = getattr(tz, "key", None) or datetime.now().astimezone(tz).tzname()
    lines = [
        f"Big Ten {sport.name} picks: {schedule.label}",
        f"Win probabilities from the ESPN Matchup Predictor. Times in {tz_name}.",
        "",
    ]
    if not schedule.games:
        lines.append("No games found.")
        return "\n".join(lines)

    header = ("When", "Matchup", "Away", "Home", "Pick")
    rows = [
        (
            _format_time(g, tz),
            g.matchup,
            _format_pct(g.prediction.away_win_pct if g.prediction else None),
            _format_pct(g.prediction.home_win_pct if g.prediction else None),
            _pick_text(g),
        )
        for g in schedule.games
    ]
    widths = [max(len(r[i]) for r in (header, *rows)) for i in range(len(header))]
    align = ("<", "<", ">", ">", "<")

    def fmt(row: Sequence[str]) -> str:
        return "  ".join(f"{cell:{a}{w}}" for cell, a, w in zip(row, align, widths)).rstrip()

    lines.append(fmt(header))
    lines.append(fmt(["-" * w for w in widths]))
    lines.extend(fmt(r) for r in rows)

    predicted = sum(g.prediction is not None for g in schedule.games)
    lines += ["", f"{len(schedule.games)} games, {predicted} with predictions."]
    return "\n".join(lines)


def default_output_path(schedule: Schedule, now: datetime | None = None) -> Path:
    """Default JSON path, e.g. ``data/football_2026-week-5_20261001_153000.json``."""
    now = now or datetime.now()
    slug = re.sub(r"[^a-z0-9]+", "-", schedule.label.lower()).strip("-")
    return DEFAULT_OUTPUT_DIR / f"{schedule.sport}_{slug}_{now:%Y%m%d_%H%M%S}.json"


def save_json(schedule: Schedule, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"generated_at": datetime.now().astimezone().isoformat(), **schedule.to_dict()}
    path.write_text(json.dumps(payload, indent=2) + "\n")
    return path


def default_season_year(today: date | None = None) -> int:
    """Football season year for ``today``; January/February bowls belong to the prior season."""
    today = today or date.today()
    return today.year - 1 if today.month <= 2 else today.year


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid date {value!r}; expected YYYY-MM-DD") from None


def _parse_timezone(value: str) -> tzinfo:
    try:
        return ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError):
        raise argparse.ArgumentTypeError(f"unknown timezone {value!r}") from None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="b1gpicks",
        description="Print Big Ten picks based on ESPN's Matchup Predictor win probabilities.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "-s",
        "--sport",
        default="football",
        help=f"sport to scrape: {', '.join(SPORTS)} (aliases: ncaaf, ncaab). Default: football",
    )

    football = parser.add_argument_group("football options")
    football.add_argument("-w", "--week", type=int, help="week number (default: ESPN's current week)")
    football.add_argument("-y", "--year", type=int, help="season year (default: current season when --week is set)")
    football.add_argument(
        "--postseason", action="store_true", help="use the postseason calendar (bowls/CFP) for --week"
    )

    basketball = parser.add_argument_group("basketball options")
    basketball.add_argument("-d", "--date", type=_parse_date, help="first date, YYYY-MM-DD (default: today)")
    basketball.add_argument("-n", "--days", type=int, default=3, help="number of days to scrape (default: 3)")

    output = parser.add_argument_group("output options")
    output.add_argument(
        "--timezone", type=_parse_timezone, help="IANA timezone for game times, e.g. America/Denver (default: local)"
    )
    output.add_argument("-o", "--output", type=Path, help=f"JSON output path (default: {DEFAULT_OUTPUT_DIR}/...)")
    output.add_argument("--no-save", action="store_true", help="do not write a JSON file")
    output.add_argument("--json", action="store_true", help="print JSON to stdout instead of a table")
    output.add_argument("-q", "--quiet", action="store_true", help="suppress progress messages")
    output.add_argument(
        "--delay", type=float, default=1.0, help="minimum seconds between ESPN requests (default: 1.0)"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        sport = get_sport(args.sport)
    except ValueError as exc:
        parser.error(str(exc))

    weekly = sport.schedule_type is ScheduleType.WEEKLY
    if weekly and args.date is not None:
        parser.error("--date is only used for basketball; use --week for football")
    if not weekly and (args.week is not None or args.year is not None or args.postseason):
        parser.error("--week/--year/--postseason are only used for football; use --date/--days")
    if weekly and args.week is None and (args.year is not None or args.postseason):
        parser.error("--year/--postseason require --week")
    if args.days < 1:
        parser.error("--days must be at least 1")

    def progress(game: Game) -> None:
        if not args.quiet:
            print(f"  {game.matchup}: {_pick_text(game)}", file=sys.stderr)

    try:
        with Scraper(sport, delay=args.delay) as scraper:
            if not args.quiet:
                print(f"Fetching Big Ten {sport.name} schedule from ESPN...", file=sys.stderr)
            if weekly:
                schedule = scraper.get_picks(
                    week=args.week,
                    year=args.year if args.year is not None else (default_season_year() if args.week else None),
                    season_type=(3 if args.postseason else 2) if args.week is not None else None,
                    on_game=progress,
                )
            else:
                schedule = scraper.get_picks_for_dates(args.date, args.days, on_game=progress)
    except requests.RequestException as exc:
        print(f"error: request to ESPN failed: {exc}", file=sys.stderr)
        return 1
    except ESPNParseError as exc:
        print(f"error: could not read ESPN page: {exc}", file=sys.stderr)
        return 1

    if not args.quiet:
        print(file=sys.stderr)

    if args.json:
        print(json.dumps(schedule.to_dict(), indent=2))
    else:
        print(format_picks(schedule, args.timezone))

    if not args.no_save:
        path = save_json(schedule, args.output or default_output_path(schedule))
        if not args.quiet:
            print(f"\nSaved results to {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
