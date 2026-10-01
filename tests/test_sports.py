"""Tests for sport definitions and schedule URLs."""

from datetime import date

import pytest

from b1gpicks import BASKETBALL, FOOTBALL, get_sport


class TestFootballUrls:
    def test_current_week(self):
        assert FOOTBALL.schedule_url() == "https://www.espn.com/college-football/schedule/_/group/5"

    def test_specific_week_defaults_to_regular_season(self):
        assert FOOTBALL.schedule_url(week=6, year=2026) == (
            "https://www.espn.com/college-football/schedule/_/week/6/year/2026/seasontype/2/group/5"
        )

    def test_postseason_week(self):
        url = FOOTBALL.schedule_url(week=1, year=2026, season_type=3)
        assert url.endswith("/week/1/year/2026/seasontype/3/group/5")

    def test_custom_group(self):
        assert FOOTBALL.schedule_url(group=8).endswith("/group/8")

    def test_week_requires_year(self):
        with pytest.raises(ValueError, match="year"):
            FOOTBALL.schedule_url(week=6)

    def test_year_requires_week(self):
        with pytest.raises(ValueError, match="week"):
            FOOTBALL.schedule_url(year=2026)

    def test_rejects_date(self):
        with pytest.raises(ValueError, match="weekly"):
            FOOTBALL.schedule_url(on_date=date(2026, 10, 3))


class TestBasketballUrls:
    def test_today(self):
        assert BASKETBALL.schedule_url() == "https://www.espn.com/mens-college-basketball/schedule/_/group/7"

    def test_specific_date(self):
        assert BASKETBALL.schedule_url(on_date=date(2026, 1, 5)) == (
            "https://www.espn.com/mens-college-basketball/schedule/_/date/20260105/group/7"
        )

    def test_rejects_week(self):
        with pytest.raises(ValueError, match="daily"):
            BASKETBALL.schedule_url(week=3)


class TestGetSport:
    @pytest.mark.parametrize("name", ["football", "Football", "ncaaf", "cfb"])
    def test_football_aliases(self, name):
        assert get_sport(name) is FOOTBALL

    @pytest.mark.parametrize("name", ["basketball", "ncaab", "NCAAM", "mbb"])
    def test_basketball_aliases(self, name):
        assert get_sport(name) is BASKETBALL

    def test_passthrough(self):
        assert get_sport(FOOTBALL) is FOOTBALL

    def test_unknown(self):
        with pytest.raises(ValueError, match="Unknown sport"):
            get_sport("hockey")
