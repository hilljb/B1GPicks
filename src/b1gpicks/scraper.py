"""Web scraper module with Chrome on macOS user agent."""

import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import time
import re


class Scraper:
    """A web scraper that appears as Chrome on macOS."""
    
    # Chrome on macOS user agent (updated for modern Chrome)
    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    
    def __init__(self, user_agent: Optional[str] = None, timeout: int = 30):
        """
        Initialize the scraper.
        
        Args:
            user_agent: Custom user agent string. Defaults to Chrome on macOS.
            timeout: Request timeout in seconds. Defaults to 30.
        """
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        self.timeout = timeout
        self.session = requests.Session()
        self._setup_headers()
    
    def _setup_headers(self) -> None:
        """Set up default headers to mimic a real browser."""
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """
        Make a GET request to the specified URL.
        
        Args:
            url: The URL to scrape.
            **kwargs: Additional arguments to pass to requests.get().
        
        Returns:
            Response object from the request.
        
        Raises:
            requests.RequestException: If the request fails.
        """
        kwargs.setdefault('timeout', self.timeout)
        response = self.session.get(url, **kwargs)
        response.raise_for_status()
        return response
    
    def get_soup(self, url: str, parser: str = 'lxml', **kwargs) -> BeautifulSoup:
        """
        Get a BeautifulSoup object from the specified URL.
        
        Args:
            url: The URL to scrape.
            parser: The parser to use. Defaults to 'lxml'.
            **kwargs: Additional arguments to pass to get().
        
        Returns:
            BeautifulSoup object of the page content.
        
        Raises:
            requests.RequestException: If the request fails.
        """
        response = self.get(url, **kwargs)
        return BeautifulSoup(response.content, parser)
    
    def scrape(self, url: str, delay: float = 0) -> Dict[str, Any]:
        """
        Scrape data from a URL.
        
        This is a placeholder method that should be customized for specific scraping needs.
        
        Args:
            url: The URL to scrape.
            delay: Optional delay before making the request (in seconds).
        
        Returns:
            Dictionary containing scraped data.
        """
        if delay > 0:
            time.sleep(delay)
        
        soup = self.get_soup(url)
        
        # Placeholder return - customize this for your specific needs
        return {
            'url': url,
            'title': soup.title.string if soup.title else None,
            'status': 'success'
        }
    
    @staticmethod
    def get_schedule_url(date: datetime, group: int = 7) -> str:
        """
        Generate ESPN schedule URL for a specific date and conference group.
        
        Args:
            date: The date to get the schedule for.
            group: The conference group ID (7 is Big Ten). Defaults to 7.
        
        Returns:
            URL string for the schedule page.
        """
        date_str = date.strftime('%Y%m%d')
        return f"https://www.espn.com/mens-college-basketball/schedule/_/date/{date_str}/group/{group}"
    
    def get_games_from_schedule(self, schedule_url: str, delay: float = 1) -> List[Dict[str, Any]]:
        """
        Extract game information from an ESPN schedule page.
        
        Args:
            schedule_url: The URL of the schedule page.
            delay: Delay before making the request (in seconds). Defaults to 1.
        
        Returns:
            List of dictionaries containing game information (teams, game_url).
        """
        if delay > 0:
            time.sleep(delay)
        
        soup = self.get_soup(schedule_url)
        games = []
        
        # ESPN embeds schedule data in a JSON blob within a script tag
        # Look for the window['__espnfitt__'] script tag
        import json
        
        scripts = soup.find_all('script')
        schedule_data = None
        
        for script in scripts:
            if script.string and 'window[\'__espnfitt__\']' in script.string:
                # Extract the JSON data
                script_text = script.string
                # Find the JSON object
                start_idx = script_text.find('{')
                if start_idx != -1:
                    try:
                        # Extract everything from first { to the end, then find matching }
                        json_str = script_text[start_idx:]
                        # The JSON ends before the closing script marker
                        end_idx = json_str.rfind(';')
                        if end_idx != -1:
                            json_str = json_str[:end_idx]
                        schedule_data = json.loads(json_str)
                        break
                    except json.JSONDecodeError:
                        continue
        
        if not schedule_data:
            # Fallback: try to find games in HTML (old method)
            return self._get_games_from_html(soup)
        
        # Navigate through the JSON structure to find games
        try:
            content = schedule_data.get('page', {}).get('content', {})
            schedule_content = content.get('schedule', {})
            
            # Check if there are no events
            if not schedule_content.get('events'):
                return games
            
            # Extract game information from events
            for event in schedule_content.get('events', []):
                competitors = event.get('competitors', [])
                if len(competitors) < 2:
                    continue
                
                # Determine away and home teams
                away_team = None
                home_team = None
                
                for competitor in competitors:
                    team_name = competitor.get('displayName', competitor.get('name', ''))
                    is_home = competitor.get('isHome', False)
                    
                    if is_home:
                        home_team = team_name
                    else:
                        away_team = team_name
                
                # Get game URL
                game_link = event.get('link', '')
                if game_link and not game_link.startswith('http'):
                    game_link = f"https://www.espn.com{game_link}"
                
                if away_team and home_team and game_link:
                    games.append({
                        'away_team': away_team,
                        'home_team': home_team,
                        'game_url': game_link
                    })
        
        except (KeyError, TypeError, AttributeError) as e:
            # If JSON parsing fails, try HTML fallback
            return self._get_games_from_html(soup)
        
        return games
    
    def _get_games_from_html(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Fallback method to extract games from HTML table structure.
        
        Args:
            soup: BeautifulSoup object of the schedule page.
        
        Returns:
            List of dictionaries containing game information.
        """
        games = []
        
        # Check if there's no data available
        no_data = soup.find('div', class_='Table__NoData')
        if no_data:
            return games
        
        # Find all game links
        game_links = soup.find_all('a', href=lambda x: x and '/game/' in x)
        
        for link in game_links:
            game_url = link.get('href', '')
            if not game_url:
                continue
                
            if not game_url.startswith('http'):
                game_url = f"https://www.espn.com{game_url}"
            
            # Try to find team names near this link
            # This is a best-effort attempt
            parent = link.find_parent('tr')
            if parent:
                # Look for any text that might be team names
                all_links = parent.find_all('a')
                team_names = [a.get_text(strip=True) for a in all_links if a.get_text(strip=True)]
                
                if len(team_names) >= 2:
                    games.append({
                        'away_team': team_names[0],
                        'home_team': team_names[1],
                        'game_url': game_url
                    })
        
        return games
    
    def get_game_predictor(self, game_url: str, delay: float = 1) -> Optional[Dict[str, Any]]:
        """
        Extract game predictor percentages from an ESPN game page.
        
        Args:
            game_url: The URL of the game page.
            delay: Delay before making the request (in seconds). Defaults to 1.
        
        Returns:
            Dictionary with team names and win percentages, or None if not available.
        """
        if delay > 0:
            time.sleep(delay)
        
        soup = self.get_soup(game_url)
        percentages = []
        team_names = []
        
        # Method 1 (PRIORITY): Look for SVG elements with value attributes 
        # ESPN uses this for predictor circles on the game page
        svg_elements = soup.find_all(['path', 'circle'], value=True)
        for elem in svg_elements:
            value = elem.get('value', '')
            try:
                pct = float(value)
                if 0 <= pct <= 100:
                    percentages.append(pct)
            except ValueError:
                continue
        
        # Method 2: Look within matchupPredictor div for percentages
        if len(percentages) < 2:
            predictor_div = soup.find('div', class_=re.compile(r'matchupPredictor'))
            if predictor_div:
                percent_elements = predictor_div.find_all(string=re.compile(r'\d+\.?\d*%'))
                for elem in percent_elements:
                    match = re.search(r'(\d+\.?\d*)%', str(elem))
                    if match:
                        try:
                            pct = float(match.group(1))
                            if 0 <= pct <= 100:
                                percentages.append(pct)
                        except ValueError:
                            continue
        
        # Extract team names from the page title
        team_names = []
        title = soup.find('title')
        if title:
            title_text = title.get_text()
            # Format is usually "Team1 vs. Team2" or "Team1 @ Team2"
            match = re.search(r'(.+?)\s+(?:vs\.?|@)\s+(.+?)(?:\s+\(|$)', title_text)
            if match:
                team_names = [match.group(1).strip(), match.group(2).strip()]
        
        # Alternative: look for h1 tag
        if not team_names:
            h1 = soup.find('h1')
            if h1:
                h1_text = h1.get_text()
                match = re.search(r'(.+?)\s+@\s+(.+?)$', h1_text)
                if match:
                    team_names = [match.group(1).strip(), match.group(2).strip()]
        
        # Method 1: Look for mtchpPrdctr JSON data (most reliable)
        import json
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'mtchpPrdctr' in script.string:
                try:
                    # Extract the JSON object containing mtchpPrdctr
                    script_text = script.string
                    # Find mtchpPrdctr section
                    mtch_match = re.search(r'"mtchpPrdctr"\s*:\s*(\{[^}]*"teams"\s*:\s*\[[^\]]+\][^}]*\})', script_text)
                    if mtch_match:
                        mtch_json_str = mtch_match.group(1)
                        mtch_data = json.loads(mtch_json_str)
                        teams = mtch_data.get('teams', [])
                        
                        if len(teams) >= 2:
                            # Extract percentages and determine which team is which
                            away_pct = None
                            home_pct = None
                            
                            for team in teams:
                                pct = team.get('value') or team.get('percentage')
                                is_home = team.get('isHome', False)
                                
                                if pct is not None:
                                    if is_home:
                                        home_pct = float(pct)
                                    else:
                                        away_pct = float(pct)
                            
                            if away_pct is not None and home_pct is not None and len(team_names) == 2:
                                return {
                                    'away_team': team_names[0],
                                    'home_team': team_names[1],
                                    'away_win_pct': away_pct,
                                    'home_win_pct': home_pct
                                }
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue
        
        # Method 2: Look for matchupPredictor divs with specific classes
        predictor_divs = soup.find_all('div', class_=re.compile(r'matchupPredictor__teamValue'))
        percentages = []
        
        for div in predictor_divs:
            # Get the text content and look for numbers
            text = div.get_text()
            match = re.search(r'(\d+\.?\d*)', text)
            if match:
                try:
                    pct = float(match.group(1))
                    if 0 <= pct <= 100:
                        percentages.append(pct)
                except ValueError:
                    continue
        
        # Method 3: Look for SVG path elements with value attribute in predictor section
        if len(percentages) < 2:
            svg_paths = soup.find_all('path', value=True)
            for path in svg_paths:
                value = path.get('value', '')
                try:
                    pct = float(value)
                    if 0 <= pct <= 100:
                        percentages.append(pct)
                except ValueError:
                    continue
        
        # If we found exactly 2 percentages and team names
        if len(percentages) >= 2 and len(team_names) == 2:
            # ESPN's SVG path elements are in order: home team first, away team second
            # But team_names from title are in "Away @ Home" format
            # So percentages[0] = home team, percentages[1] = away team
            return {
                'away_team': team_names[0],
                'home_team': team_names[1],
                'away_win_pct': percentages[0],
                'home_win_pct': percentages[1]
            }
        
        return None
    
    def scrape_games_by_date_range(
        self,
        start_date: Optional[datetime] = None,
        num_days: int = 3,
        delay_between_pages: float = 1,
        delay_between_games: float = 1
    ) -> List[Dict[str, Any]]:
        """
        Scrape game predictor data for multiple days.
        
        Args:
            start_date: Starting date (defaults to today).
            num_days: Number of days to scrape (defaults to 3).
            delay_between_pages: Delay between schedule page requests.
            delay_between_games: Delay between individual game page requests.
        
        Returns:
            List of dictionaries containing date, teams, and predictor data.
        """
        if start_date is None:
            start_date = datetime.now()
        
        all_results = []
        
        for day_offset in range(num_days):
            current_date = start_date + timedelta(days=day_offset)
            date_str = current_date.strftime('%Y-%m-%d')
            
            print(f"Scraping games for {date_str}...")
            
            # Get schedule URL and extract games
            schedule_url = self.get_schedule_url(current_date)
            games = self.get_games_from_schedule(schedule_url, delay=delay_between_pages)
            
            if not games:
                print(f"  No games found for {date_str}")
                all_results.append({
                    'date': date_str,
                    'games': []
                })
                continue
            
            print(f"  Found {len(games)} games")
            
            # Get predictor data for each game
            games_with_predictors = []
            for game in games:
                matchup = f"{game['away_team']} @ {game['home_team']}"
                print(f"    Fetching predictor for {matchup}...")
                
                predictor = self.get_game_predictor(game['game_url'], delay=delay_between_games)
                
                game_data = {
                    'away_team': game['away_team'],
                    'home_team': game['home_team'],
                    'game_url': game['game_url']
                }
                
                if predictor:
                    game_data['away_win_pct'] = predictor['away_win_pct']
                    game_data['home_win_pct'] = predictor['home_win_pct']
                    print(f"      {game['away_team']}: {predictor['away_win_pct']}%, "
                          f"{game['home_team']}: {predictor['home_win_pct']}%")
                else:
                    game_data['away_win_pct'] = None
                    game_data['home_win_pct'] = None
                    print(f"      Predictor not available")
                
                games_with_predictors.append(game_data)
            
            all_results.append({
                'date': date_str,
                'games': games_with_predictors
            })
        
        return all_results
    
    def close(self) -> None:
        """Close the session."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

