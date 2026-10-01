"""Tests for the command-line interface."""

import json
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from b1gpicks import FOOTBALL, Prediction, Scraper, cli
from b1gpicks.espn import parse_schedule

DENVER = ZoneInfo("America/Denver")


@pytest.fixture
def schedule(load_fixture):
    schedule = parse_schedule(load_fixture("football_schedule.html"), FOOTBALL)
    schedule.games[0].prediction = Prediction(away_win_pct=55.8, home_win_pct=44.2)
    schedule.games[1].status = "post"
    schedule.games[1].status_detail = "Final/OT"
    return schedule


class TestFormatPicks:
    def test_header(self, schedule):
        lines = cli.format_picks(schedule, DENVER).splitlines()
        assert lines[0] == "Big Ten College Football picks: 2026 Week 5"
        assert "America/Denver" in lines[1]

    def test_pick_row_in_local_time(self, schedule):
        text = cli.format_picks(schedule, DENVER)
        row = next(line for line in text.splitlines() if "Penn State @ Northwestern" in line)
        assert row.startswith("Fri Oct 2 6:00 PM")
        assert "55.8%" in row and "44.2%" in row
        assert row.endswith("Penn State (55.8%)")

    def test_final_and_missing_rows(self, schedule):
        text = cli.format_picks(schedule, DENVER)
        assert "Final/OT" in text
        assert "No predictor available" in text

    def test_summary(self, schedule):
        assert cli.format_picks(schedule, DENVER).endswith("8 games, 1 with predictions.")

    def test_no_games(self, schedule):
        schedule.games = []
        assert cli.format_picks(schedule, DENVER).endswith("No games found.")


def test_default_output_path(schedule):
    path = cli.default_output_path(schedule, now=datetime(2026, 10, 1, 15, 30, 0))
    assert str(path) == "data/football_2026-week-5_20261001_153000.json"


def test_save_json(schedule, tmp_path):
    path = cli.save_json(schedule, tmp_path / "nested" / "picks.json")
    data = json.loads(path.read_text())
    assert data["label"] == "2026 Week 5"
    assert data["games"][0]["pick"] == "Penn State Nittany Lions"
    assert "generated_at" in data


class TestMain:
    @pytest.fixture
    def calls(self, monkeypatch, schedule):
        """Replace network-backed Scraper methods and record their arguments."""
        recorded = {}

        def get_picks(self, **kwargs):
            recorded["get_picks"] = kwargs
            return schedule

        def get_picks_for_dates(self, start_date, num_days, **kwargs):
            recorded["get_picks_for_dates"] = (start_date, num_days)
            schedule.sport = "basketball"
            return schedule

        monkeypatch.setattr(Scraper, "get_picks", get_picks)
        monkeypatch.setattr(Scraper, "get_picks_for_dates", get_picks_for_dates)
        return recorded

    def test_current_week(self, calls, capsys, tmp_path):
        out = tmp_path / "out.json"
        assert cli.main(["-q", "-o", str(out), "--timezone", "America/Denver"]) == 0
        assert calls["get_picks"]["week"] is None
        assert calls["get_picks"]["year"] is None
        assert calls["get_picks"]["season_type"] is None
        assert "Penn State (55.8%)" in capsys.readouterr().out
        assert json.loads(out.read_text())["week"] == 5

    def test_specific_week(self, calls):
        assert cli.main(["-q", "--no-save", "--week", "6", "--year", "2026"]) == 0
        kwargs = calls["get_picks"]
        assert (kwargs["week"], kwargs["year"], kwargs["season_type"]) == (6, 2026, 2)

    def test_postseason_defaults_year(self, calls):
        assert cli.main(["-q", "--no-save", "--week", "1", "--postseason"]) == 0
        assert calls["get_picks"]["season_type"] == 3
        assert calls["get_picks"]["year"] == cli.default_season_year()

    @pytest.mark.parametrize(
        ("today", "expected"),
        [(date(2026, 10, 1), 2026), (date(2027, 1, 10), 2026), (date(2026, 8, 29), 2026)],
    )
    def test_default_season_year(self, today, expected):
        assert cli.default_season_year(today) == expected

    def test_json_output(self, calls, capsys):
        assert cli.main(["-q", "--no-save", "--json"]) == 0
        assert json.loads(capsys.readouterr().out)["label"] == "2026 Week 5"

    def test_basketball(self, calls):
        assert cli.main(["-q", "--no-save", "-s", "ncaab", "-d", "2026-02-10", "-n", "2"]) == 0
        start, days = calls["get_picks_for_dates"]
        assert (start.isoformat(), days) == ("2026-02-10", 2)

    def test_progress_goes_to_stderr(self, calls, capsys):
        assert cli.main(["--no-save"]) == 0
        captured = capsys.readouterr()
        assert "Fetching Big Ten College Football schedule" in captured.err
        assert "Fetching" not in captured.out

    @pytest.mark.parametrize(
        "argv",
        [
            ["--sport", "hockey"],
            ["--date", "2026-10-03"],
            ["-s", "basketball", "--week", "3"],
            ["--year", "2026"],
            ["--postseason"],
            ["-s", "basketball", "--days", "0"],
            ["--date", "10/03/2026", "-s", "basketball"],
            ["--timezone", "Mars/Olympus"],
        ],
    )
    def test_invalid_arguments(self, argv, calls):
        with pytest.raises(SystemExit) as exc:
            cli.main(argv)
        assert exc.value.code == 2

    def test_request_failure(self, monkeypatch, capsys):
        import requests

        def boom(self, **kwargs):
            raise requests.ConnectionError("offline")

        monkeypatch.setattr(Scraper, "get_picks", boom)
        assert cli.main(["-q", "--no-save"]) == 1
        assert "request to ESPN failed" in capsys.readouterr().err
