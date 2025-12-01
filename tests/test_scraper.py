"""Tests for the scraper module."""

import pytest
from datetime import datetime
from b1gpicks import Scraper


class TestScraper:
    """Test cases for the Scraper class."""
    
    def test_scraper_initialization(self):
        """Test that scraper initializes with default user agent."""
        scraper = Scraper()
        assert scraper.user_agent == Scraper.DEFAULT_USER_AGENT
        assert scraper.timeout == 30
        assert "Macintosh" in scraper.user_agent
        assert "Chrome" in scraper.user_agent
        scraper.close()
    
    def test_scraper_custom_user_agent(self):
        """Test that scraper can use a custom user agent."""
        custom_ua = "CustomBot/1.0"
        scraper = Scraper(user_agent=custom_ua)
        assert scraper.user_agent == custom_ua
        scraper.close()
    
    def test_scraper_custom_timeout(self):
        """Test that scraper can use a custom timeout."""
        scraper = Scraper(timeout=60)
        assert scraper.timeout == 60
        scraper.close()
    
    def test_scraper_headers(self):
        """Test that scraper sets up proper headers."""
        scraper = Scraper()
        assert 'User-Agent' in scraper.session.headers
        assert 'Accept' in scraper.session.headers
        assert 'Accept-Language' in scraper.session.headers
        assert scraper.session.headers['User-Agent'] == Scraper.DEFAULT_USER_AGENT
        scraper.close()
    
    def test_context_manager(self):
        """Test that scraper works as a context manager."""
        with Scraper() as scraper:
            assert scraper.session is not None
            assert scraper.user_agent == Scraper.DEFAULT_USER_AGENT
        # Session should be closed after exiting context
    
    def test_scraper_get_requires_valid_url(self):
        """Test that scraper.get() fails with invalid URL."""
        scraper = Scraper()
        with pytest.raises(Exception):  # Could be RequestException or similar
            scraper.get("not-a-valid-url")
        scraper.close()


class TestESPNMethods:
    """Test cases for ESPN-specific scraping methods."""
    
    def test_get_schedule_url_default_group(self):
        """Test generating schedule URL with default group (Big Ten)."""
        test_date = datetime(2025, 12, 1)
        url = Scraper.get_schedule_url(test_date)
        assert url == "https://www.espn.com/mens-college-basketball/schedule/_/date/20251201/group/7"
    
    def test_get_schedule_url_custom_group(self):
        """Test generating schedule URL with custom group."""
        test_date = datetime(2025, 12, 15)
        url = Scraper.get_schedule_url(test_date, group=5)
        assert url == "https://www.espn.com/mens-college-basketball/schedule/_/date/20251215/group/5"
    
    def test_get_schedule_url_date_formatting(self):
        """Test that dates are formatted correctly in URLs."""
        test_date = datetime(2025, 1, 5)  # Single digit month and day
        url = Scraper.get_schedule_url(test_date)
        assert "20250105" in url


class TestScraperIntegration:
    """Integration tests for the Scraper class (require network access)."""
    
    @pytest.mark.skip(reason="Requires network access - enable when needed")
    def test_scrape_example_website(self):
        """Test scraping a real website (example.com)."""
        with Scraper() as scraper:
            result = scraper.scrape("http://example.com")
            assert result['status'] == 'success'
            assert result['url'] == "http://example.com"
            assert 'title' in result
    
    @pytest.mark.skip(reason="Requires network access - enable when needed")
    def test_get_soup(self):
        """Test getting a BeautifulSoup object."""
        with Scraper() as scraper:
            soup = scraper.get_soup("http://example.com")
            assert soup.title is not None
            assert len(soup.title.string) > 0
    
    @pytest.mark.skip(reason="Requires network access - enable when needed")
    def test_get_games_from_schedule(self):
        """Test extracting games from ESPN schedule page."""
        with Scraper() as scraper:
            # Use a date that likely has games
            test_date = datetime(2025, 12, 2)
            url = Scraper.get_schedule_url(test_date)
            games = scraper.get_games_from_schedule(url, delay=0.5)
            
            # Should return a list (may be empty if no games)
            assert isinstance(games, list)
            
            # If games exist, check structure
            if games:
                game = games[0]
                assert 'away_team' in game
                assert 'home_team' in game
                assert 'game_url' in game
    
    @pytest.mark.skip(reason="Requires network access - enable when needed")
    def test_get_game_predictor(self):
        """Test extracting game predictor from ESPN game page."""
        with Scraper() as scraper:
            # This test requires a specific game URL
            # You'll need to update with a real game URL that has predictor data
            game_url = "https://www.espn.com/mens-college-basketball/game/_/gameId/401827278"
            predictor = scraper.get_game_predictor(game_url, delay=0.5)
            
            # Predictor may be None if not available yet
            if predictor:
                assert 'away_team' in predictor
                assert 'home_team' in predictor
                assert 'away_win_pct' in predictor
                assert 'home_win_pct' in predictor
                assert isinstance(predictor['away_win_pct'], float)
                assert isinstance(predictor['home_win_pct'], float)
    
    @pytest.mark.skip(reason="Requires network access - enable when needed")
    def test_scrape_games_by_date_range(self):
        """Test scraping multiple days of game data."""
        with Scraper() as scraper:
            results = scraper.scrape_games_by_date_range(
                start_date=datetime(2025, 12, 1),
                num_days=2,
                delay_between_pages=0.5,
                delay_between_games=0.5
            )
            
            assert isinstance(results, list)
            assert len(results) == 2
            
            for day_result in results:
                assert 'date' in day_result
                assert 'games' in day_result
                assert isinstance(day_result['games'], list)

