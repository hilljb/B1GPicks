"""Tests for the Scraper HTTP client (network calls are faked)."""

from datetime import date

import pytest
import requests

from b1gpicks import BASKETBALL, FOOTBALL, Scraper
from b1gpicks.espn import parse_schedule

from .conftest import FOOTBALL_GAME_URL, FOOTBALL_SCHEDULE_URL


class TestInit:
    def test_defaults(self):
        with Scraper() as scraper:
            assert scraper.sport is FOOTBALL
            assert scraper.user_agent == Scraper.DEFAULT_USER_AGENT
            assert "Macintosh" in scraper.user_agent and "Chrome" in scraper.user_agent
            assert scraper.timeout == 30
            assert scraper.session.headers["User-Agent"] == Scraper.DEFAULT_USER_AGENT

    def test_options(self):
        with Scraper("ncaab", user_agent="CustomBot/1.0", timeout=60, delay=0) as scraper:
            assert scraper.sport is BASKETBALL
            assert scraper.session.headers["User-Agent"] == "CustomBot/1.0"
            assert scraper.timeout == 60

    def test_does_not_request_brotli(self):
        # requests cannot decode brotli without an extra dependency.
        with Scraper() as scraper:
            assert "br" not in scraper.session.headers["Accept-Encoding"]

    def test_schedule_url(self):
        with Scraper() as scraper:
            assert scraper.schedule_url(week=6, year=2026).endswith("/week/6/year/2026/seasontype/2/group/5")

    def test_invalid_url_raises(self):
        with Scraper(delay=0, retries=0) as scraper:
            with pytest.raises(requests.RequestException):
                scraper.get("not-a-valid-url")


class TestThrottle:
    def test_sleeps_between_requests(self, monkeypatch):
        sleeps = []
        clock = iter([100.0, 100.2, 101.0])
        monkeypatch.setattr("b1gpicks.scraper.time.monotonic", lambda: next(clock))
        monkeypatch.setattr("b1gpicks.scraper.time.sleep", sleeps.append)
        scraper = Scraper(delay=1.0)
        scraper._throttle()
        scraper._throttle()
        assert sleeps == [pytest.approx(0.8)]


class TestFootball:
    def test_get_schedule(self, fake_espn):
        scraper, fake = fake_espn({FOOTBALL_SCHEDULE_URL: "football_schedule.html"})
        schedule = scraper.get_schedule()
        assert fake.requested == [FOOTBALL_SCHEDULE_URL]
        assert schedule.label == "2026 Week 5"
        assert len(schedule.games) == 8

    def test_get_prediction(self, fake_espn):
        scraper, _ = fake_espn({FOOTBALL_GAME_URL: "football_game.html"})
        prediction = scraper.get_prediction(FOOTBALL_GAME_URL)
        assert (prediction.away_win_pct, prediction.home_win_pct) == (55.8, 44.2)

    def test_get_picks(self, fake_espn, load_fixture):
        game_urls = [g.url for g in parse_schedule(load_fixture("football_schedule.html"), FOOTBALL).games]
        routes = {FOOTBALL_SCHEDULE_URL: "football_schedule.html", **dict.fromkeys(game_urls, "football_game.html")}
        scraper, fake = fake_espn(routes)
        seen = []
        schedule = scraper.get_picks(on_game=seen.append)
        assert fake.requested == [FOOTBALL_SCHEDULE_URL, *game_urls]
        assert seen == schedule.games
        assert all(g.prediction is not None for g in schedule.games)
        assert schedule.games[0].pick.short_name == "Penn State"
        assert schedule.games[0].pick_win_pct == 55.8

    def test_http_error_propagates(self, fake_espn):
        scraper, _ = fake_espn({})
        with pytest.raises(requests.HTTPError):
            scraper.get_schedule()

    def test_add_predictions_skips_final_games(self, fake_espn):
        scraper, fake = fake_espn({FOOTBALL_SCHEDULE_URL: "football_schedule.html", FOOTBALL_GAME_URL: "football_game.html"})
        schedule = scraper.get_schedule()
        for game in schedule.games[1:]:
            game.status = "post"
        scraper.add_predictions(schedule)
        assert fake.requested == [FOOTBALL_SCHEDULE_URL, FOOTBALL_GAME_URL]
        assert schedule.games[0].prediction is not None
        assert all(g.prediction is None for g in schedule.games[1:])

    def test_dates_not_supported(self):
        with Scraper(delay=0) as scraper, pytest.raises(ValueError, match="by week"):
            scraper.get_picks_for_dates(date(2026, 10, 3))


class TestBasketball:
    def test_get_picks_for_dates(self, fake_espn):
        routes = {
            BASKETBALL.schedule_url(on_date=date(2026, 2, 10)): "basketball_schedule.html",
            BASKETBALL.schedule_url(on_date=date(2026, 2, 11)): "basketball_schedule.html",
        }
        scraper, fake = fake_espn(routes, sport="basketball")
        schedule = scraper.get_picks_for_dates(date(2026, 2, 10), num_days=2)
        assert schedule.label == "2026-02-10 to 2026-02-11"
        assert len(schedule.games) == 6
        # All fixture games are final, so no game pages are requested.
        assert fake.requested == list(routes)

    def test_num_days_must_be_positive(self):
        with Scraper("basketball", delay=0) as scraper, pytest.raises(ValueError):
            scraper.get_picks_for_dates(num_days=0)
