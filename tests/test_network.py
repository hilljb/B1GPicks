"""Live tests against espn.com. Run with ``pytest --run-network``.

These verify that ESPN's page format still matches what the parsers expect.
They make real requests, so results depend on the current schedule.
"""

import pytest

from b1gpicks import Scraper

pytestmark = pytest.mark.network


def test_football_current_week():
    with Scraper("football") as scraper:
        schedule = scraper.get_schedule()
    assert schedule.year is not None
    assert schedule.label
    for game in schedule.games:
        assert game.url.startswith("https://www.espn.com/college-football/game/")
        assert game.away.name and game.home.name


def test_football_predictor_for_upcoming_game():
    with Scraper("football") as scraper:
        upcoming = [g for g in scraper.get_schedule().games if g.status == "pre"]
        if not upcoming:
            pytest.skip("no upcoming Big Ten football games this week")
        prediction = scraper.get_prediction(upcoming[0].url)
    assert prediction is not None
    assert 0 <= prediction.away_win_pct <= 100
    assert 0 <= prediction.home_win_pct <= 100
    assert prediction.away_win_pct + prediction.home_win_pct == pytest.approx(100, abs=0.2)


def test_basketball_schedule_page_parses():
    with Scraper("basketball") as scraper:
        schedule = scraper.get_schedule()
    assert isinstance(schedule.games, list)
