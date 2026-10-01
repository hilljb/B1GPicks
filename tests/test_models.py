"""Tests for data models and pick selection."""

from datetime import datetime, timezone

import pytest

from b1gpicks import Game, Prediction, Schedule, Team

AWAY = Team(id="213", name="Penn State Nittany Lions", short_name="Penn State", abbreviation="PSU")
HOME = Team(id="77", name="Northwestern Wildcats", short_name="Northwestern", abbreviation="NU", rank=12)


def make_game(prediction=None, status="pre"):
    return Game(
        id="401858476",
        away=AWAY,
        home=HOME,
        start_time=datetime(2026, 10, 3, tzinfo=timezone.utc),
        status=status,
        status_detail="Fri, October 2nd at 8:00 PM EDT",
        url="https://www.espn.com/college-football/game/_/gameId/401858476",
        prediction=prediction,
    )


def test_team_label():
    assert AWAY.label == "Penn State"
    assert HOME.label == "#12 Northwestern"


@pytest.mark.parametrize(
    ("away", "home", "expected_pick", "expected_pct"),
    [
        (55.8, 44.2, AWAY, 55.8),
        (20.0, 80.0, HOME, 80.0),
        (50.0, 50.0, HOME, 50.0),
    ],
)
def test_pick(away, home, expected_pick, expected_pct):
    game = make_game(Prediction(away_win_pct=away, home_win_pct=home))
    assert game.pick == expected_pick
    assert game.pick_win_pct == expected_pct


def test_no_prediction_means_no_pick():
    game = make_game()
    assert game.pick is None
    assert game.pick_win_pct is None


def test_is_final():
    assert make_game(status="post").is_final
    assert not make_game(status="pre").is_final


def test_game_to_dict():
    data = make_game(Prediction(55.8, 44.2)).to_dict()
    assert data["away_team"] == "Penn State Nittany Lions"
    assert data["home_rank"] == 12
    assert data["start_time"] == "2026-10-03T00:00:00+00:00"
    assert data["away_win_pct"] == 55.8
    assert data["pick"] == "Penn State Nittany Lions"
    assert data["pick_win_pct"] == 55.8


def test_game_to_dict_without_prediction():
    data = make_game().to_dict()
    assert data["away_win_pct"] is None
    assert data["pick"] is None


def test_schedule_to_dict():
    schedule = Schedule(sport="football", label="2026 Week 5", games=[make_game()], year=2026, week=5, season_type=2)
    data = schedule.to_dict()
    assert data["label"] == "2026 Week 5"
    assert data["week"] == 5
    assert len(data["games"]) == 1
