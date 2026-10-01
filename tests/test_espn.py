"""Tests for ESPN page parsing."""

from datetime import datetime, timezone

import pytest

from b1gpicks import BASKETBALL, FOOTBALL, ESPNParseError
from b1gpicks.espn import date_range_label, extract_page_data, parse_event, parse_prediction, parse_schedule


class TestExtractPageData:
    def test_extracts_blob(self):
        html = "<script>window['__espnfitt__']={\"page\":{\"content\":{\"x\":1}}};</script>"
        assert extract_page_data(html) == {"page": {"content": {"x": 1}}}

    def test_ignores_trailing_script(self):
        html = "<script>window['__espnfitt__'] = {\"a\": \"};\"}; window.other = {};</script>"
        assert extract_page_data(html) == {"a": "};"}

    def test_double_quoted_key(self):
        assert extract_page_data('window["__espnfitt__"]={"a":1};') == {"a": 1}

    def test_missing_blob(self):
        with pytest.raises(ESPNParseError, match="not found"):
            extract_page_data("<html><body>Nothing here</body></html>")

    def test_invalid_json(self):
        with pytest.raises(ESPNParseError, match="not valid JSON"):
            extract_page_data("window['__espnfitt__']={broken;")


class TestFootballSchedule:
    @pytest.fixture
    def schedule(self, load_fixture):
        return parse_schedule(load_fixture("football_schedule.html"), FOOTBALL)

    def test_metadata(self, schedule):
        assert schedule.sport == "football"
        assert (schedule.year, schedule.week, schedule.season_type) == (2026, 5, 2)
        assert schedule.label == "2026 Week 5"

    def test_games(self, schedule):
        assert len(schedule.games) == 8
        assert all(g.prediction is None for g in schedule.games)

    def test_first_game_details(self, schedule):
        game = schedule.games[0]
        assert game.id == "401858476"
        assert game.away.name == "Penn State Nittany Lions"
        assert game.away.short_name == "Penn State"
        assert game.away.abbreviation == "PSU"
        assert game.home.name == "Northwestern Wildcats"
        assert game.start_time == datetime(2026, 10, 3, 0, 0, tzinfo=timezone.utc)
        assert game.status == "pre"
        assert game.url == "https://www.espn.com/college-football/game/_/gameId/401858476/penn-state-northwestern"
        assert game.matchup == "Penn State @ Northwestern"

    def test_sorted_by_start_time(self, schedule):
        times = [g.start_time for g in schedule.games]
        assert times == sorted(times)

    def test_rankings(self, schedule):
        ohio_state_iowa = next(g for g in schedule.games if g.away.short_name == "Ohio State")
        assert ohio_state_iowa.away.rank == 5
        assert ohio_state_iowa.home.rank == 14
        assert ohio_state_iowa.matchup == "#5 Ohio State @ #14 Iowa"
        penn_state = schedule.games[0]
        assert penn_state.away.rank is None

    def test_postseason_label_from_calendar(self, load_fixture):
        data = load_fixture("football_schedule.html")
        data["page"]["content"]["requestedDates"] = {"year": 2026, "seasontype": 3, "week": 1}
        assert parse_schedule(data, FOOTBALL).label == "2026 Bowls"

    def test_label_falls_back_without_calendar(self, load_fixture):
        data = load_fixture("football_schedule.html")
        del data["page"]["content"]["calendar"]
        assert parse_schedule(data, FOOTBALL).label == "2026 Week 5"

    def test_no_events(self):
        data = {"page": {"content": {"events": {}, "requestedDates": {"year": 2026, "seasontype": 3, "week": 1}}}}
        assert parse_schedule(data, FOOTBALL).games == []

    def test_missing_content(self):
        with pytest.raises(ESPNParseError):
            parse_schedule({"page": {}}, FOOTBALL)


class TestBasketballSchedule:
    def test_all_days(self, load_fixture):
        schedule = parse_schedule(load_fixture("basketball_schedule.html"), BASKETBALL)
        assert len(schedule.games) == 7
        assert all(g.is_final for g in schedule.games)

    def test_filter_to_requested_date(self, load_fixture):
        schedule = parse_schedule(load_fixture("basketball_schedule.html"), BASKETBALL, dates=["20260210"])
        assert len(schedule.games) == 2
        assert schedule.label == "2026-02-10"
        assert {g.home.short_name for g in schedule.games} == {"Nebraska", "Illinois"}


class TestParseEvent:
    def test_incomplete_event_is_skipped(self):
        assert parse_event({"id": "1", "competitors": [{"isHome": True}], "link": "/x"}) is None
        assert parse_event({"id": "1", "competitors": [{"isHome": True}, {"isHome": False}]}) is None

    def test_neutral_site_matchup(self):
        event = {
            "id": "1",
            "link": "https://www.espn.com/college-football/game/_/gameId/1",
            "neutralSite": True,
            "competitors": [
                {"id": "2", "displayName": "Home U", "location": "Home", "isHome": True, "rank": 99},
                {"id": "3", "displayName": "Away U", "location": "Away", "isHome": False, "rank": 0},
            ],
        }
        game = parse_event(event)
        assert game.matchup == "Away vs Home"
        assert game.start_time is None
        assert game.url == "https://www.espn.com/college-football/game/_/gameId/1"


class TestParsePrediction:
    def test_football_predictor(self, load_fixture):
        prediction = parse_prediction(load_fixture("football_game.html"))
        assert prediction.away_win_pct == 55.8  # Penn State (away)
        assert prediction.home_win_pct == 44.2  # Northwestern (home)

    def test_assigns_by_is_home_not_order(self):
        teams = [{"value": 30.0, "isHome": True}, {"value": 70.0, "isHome": False}]
        data = {"page": {"content": {"gamepackage": {"mtchpPrdctr": {"teams": teams}}}}}
        prediction = parse_prediction(data)
        assert (prediction.away_win_pct, prediction.home_win_pct) == (70.0, 30.0)

    def test_falls_back_to_percentage_field(self):
        teams = [{"percentage": "61.5", "isHome": False}, {"percentage": "38.5", "isHome": True}]
        data = {"page": {"content": {"gamepackage": {"mtchpPrdctr": {"teams": teams}}}}}
        assert parse_prediction(data).away_win_pct == 61.5

    def test_final_game_has_no_predictor(self, load_fixture):
        assert parse_prediction(load_fixture("basketball_game_final.html")) is None

    def test_incomplete_predictor(self):
        data = {"page": {"content": {"gamepackage": {"mtchpPrdctr": {"teams": [{"value": 50, "isHome": True}]}}}}}
        assert parse_prediction(data) is None


def test_date_range_label():
    assert date_range_label(["20261003"]) == "2026-10-03"
    assert date_range_label(["20261005", "20261003", "20261004"]) == "2026-10-03 to 2026-10-05"
