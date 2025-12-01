# Implementation Notes

This document provides technical details about how the ESPN scraper works and how to debug or modify it if needed.

## How It Works

### 1. URL Generation

The `get_schedule_url()` method generates ESPN schedule URLs in this format:
```
https://www.espn.com/mens-college-basketball/schedule/_/date/YYYYMMDD/group/7
```

- `date`: The date in YYYYMMDD format (e.g., 20251201 for December 1, 2025)
- `group`: Conference/division ID (7 = Big Ten)

### 2. Schedule Page Scraping

The `get_games_from_schedule()` method parses the schedule page to extract:
- Game URLs (found in the time column links)
- Team names (visitor and home)

**Key HTML Elements:**
- Schedule table: `<tbody class="Table__TBODY">`
- Game rows: `<tr>` elements within the table body
- Time/link cell: `<td class="date__col">` containing an `<a>` tag
- Teams cell: `<td class="teams__col">` containing team links

**Handling "No Games":**
The scraper checks for a "No Data Available" div and returns an empty list if present.

### 3. Game Predictor Scraping

The `get_game_predictor()` method extracts win probabilities from individual game pages.

**Strategy:**
1. Search the entire page for percentage patterns (e.g., "9.3%", "90.7%")
2. Extract team names from the matchup header
3. Match the first two percentages found with the two teams

**Why This Approach:**
ESPN's page structure can vary and the predictor data isn't always in a consistent location. Using a pattern-based search for percentage values is more robust than targeting specific CSS classes that might change.

### 4. Multi-Day Scraping

The `scrape_games_by_date_range()` method orchestrates the entire process:
1. Generate date range (default: 3 days starting from today)
2. For each date:
   - Get the schedule page
   - Extract all games
   - For each game, fetch the predictor data
   - Add delays between requests (be respectful to ESPN's servers)

## Debugging

### If Games Aren't Being Found

1. **Check if ESPN changed their HTML structure:**
   ```python
   from b1gpicks import Scraper
   
   with Scraper() as scraper:
       url = "https://www.espn.com/mens-college-basketball/schedule/_/date/20251202/group/7"
       soup = scraper.get_soup(url)
       
       # Save the HTML to a file for inspection
       with open('schedule_page.html', 'w') as f:
           f.write(soup.prettify())
   ```

2. **Inspect the saved HTML file** to find:
   - The table structure
   - CSS classes for game rows, time cells, and team cells
   - Update the selectors in `get_games_from_schedule()` if needed

### If Predictors Aren't Being Found

1. **Check a specific game page:**
   ```python
   from b1gpicks import Scraper
   
   with Scraper() as scraper:
       url = "https://www.espn.com/mens-college-basketball/game/_/gameId/401827278"
       soup = scraper.get_soup(url)
       
       # Save the HTML
       with open('game_page.html', 'w') as f:
           f.write(soup.prettify())
       
       # Search for percentages
       import re
       percentages = soup.find_all(string=re.compile(r'\d+\.\d+%'))
       print("Found percentages:", [str(p).strip() for p in percentages])
   ```

2. **Check the output** to see if:
   - Percentages are being found
   - They're in the expected format
   - There are exactly two percentages (one for each team)

3. **If percentages aren't found**, inspect the HTML to see:
   - Where the predictor data is located
   - What format it's in (might be in JavaScript, hidden elements, etc.)
   - Update `get_game_predictor()` accordingly

### Common Issues

**Issue:** Percentages found but not matched correctly
- **Solution:** Check that the regex pattern `r'\d+\.\d+%'` matches ESPN's format
- ESPN might use integer percentages like "91%" instead of "90.7%"
- Update the regex to `r'\d+(?:\.\d+)?%'` to handle both formats

**Issue:** Request timeout or connection errors
- **Solution:** Increase delays between requests or the timeout value
- ESPN might be rate-limiting if requests are too frequent

**Issue:** User agent not working
- **Solution:** Update the Chrome version in the user agent string
- Check current Chrome version on a Mac: https://www.whatismybrowser.com/

## Modifying the Scraper

### Scraping Different Conferences

Change the `group` parameter when generating URLs:
```python
url = Scraper.get_schedule_url(date, group=5)  # Different conference
```

Conference IDs:
- 1 = America East
- 2 = American Athletic
- 3 = ACC
- 4 = Atlantic Sun
- 5 = Big 12
- 6 = Big East
- 7 = Big Ten (default)
- ... (find others by inspecting ESPN's site)

### Adding More Data Points

Modify `get_game_predictor()` to extract additional information:
- Game score (if game has started)
- Betting lines
- Team stats
- Rankings

Example:
```python
def get_game_predictor(self, game_url: str, delay: float = 1) -> Optional[Dict[str, Any]]:
    # ... existing code ...
    
    # Add extraction of rankings
    rankings = soup.find_all('div', class_='Rank')
    if len(rankings) >= 2:
        result['away_rank'] = rankings[0].get_text(strip=True)
        result['home_rank'] = rankings[1].get_text(strip=True)
    
    return result
```

### Adjusting Delays

If you're getting rate-limited, increase delays:
```python
results = scraper.scrape_games_by_date_range(
    delay_between_pages=2.0,  # Increase from default 1.0
    delay_between_games=1.5   # Increase from default 1.0
)
```

### Storing Data Differently

The example script saves to JSON, but you can modify it to:
- Save to CSV
- Store in a database
- Send to an API
- Create a pandas DataFrame for analysis

## ESPN's Terms of Service

**Important:** Always respect ESPN's Terms of Service and robots.txt. This scraper:
- Uses reasonable delays between requests
- Identifies itself with a standard browser user agent
- Only accesses publicly available data

For production use or frequent scraping, consider:
- Using ESPN's official API (if available)
- Caching results to minimize requests
- Running scrapes during off-peak hours
- Adding longer delays between requests

## Additional Resources

- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Requests Documentation](https://requests.readthedocs.io/)
- [Chrome DevTools](https://developer.chrome.com/docs/devtools/) - for inspecting page structure

