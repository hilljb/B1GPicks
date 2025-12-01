# Bug Fixes - December 1, 2025

## Issue

The scraper was not finding any games from ESPN's schedule pages, even though games were clearly visible on the website.

## Root Cause

ESPN uses a JavaScript-based single-page application (SPA) that embeds schedule data in JSON format within `<script>` tags, rather than rendering it as static HTML table elements. The original scraper was looking for HTML table elements that don't exist in ESPN's current implementation.

## Solution

### 1. Schedule Page Scraping (Fixed)

**Problem:** The scraper was looking for `<tbody class="Table__TBODY">` and `<td class="teams__col">` elements that don't exist.

**Fix:** Updated `get_games_from_schedule()` to:
- Extract JSON data from the `window['__espnfitt__']` script tag
- Parse the JSON structure to find game events with team information
- Fall back to HTML parsing if JSON extraction fails
- Added a `_get_games_from_html()` helper method as a fallback

**Result:** Now successfully finds all games on the schedule page.

### 2. Game Predictor Scraping (Fixed)

**Problem:** The scraper was looking for percentage values in text format (e.g., "90.7%"), but ESPN stores them differently.

**Fix:** Updated `get_game_predictor()` to use multiple extraction methods:
1. **Method 1:** Text search for percentages with "%" symbol
2. **Method 2:** Extract from SVG `<path>` elements' `value` attributes (primary method for ESPN)
3. **Method 3:** Search for `winPercentage` in embedded JSON

**Critical Fix:** ESPN's SVG elements appear in HOME-AWAY order, but team names in the title are in AWAY-HOME format. The code now correctly swaps the percentages to match the team order.

**Result:** Now successfully extracts predictor percentages with correct team assignment.

## Test Results

```
✓ Schedule scraping: 5/5 games found for Dec 2, 2025
✓ Predictor extraction: 8/8 games (100% success rate)
✓ Correct team assignment: Campbell 9.3%, Penn State 90.7%
```

## Files Modified

- `src/b1gpicks/scraper.py`
  - `get_games_from_schedule()` - Complete rewrite to parse JSON
  - `_get_games_from_html()` - New fallback method
  - `get_game_predictor()` - Enhanced with multiple extraction methods

## ESPN's Current Page Structure

### Schedule Pages
- Data embedded in: `window['__espnfitt__'] = {...}`
- Path to games: `page.content.schedule.events[]`
- Each event has: `competitors[]` with `displayName` and `isHome` flag

### Game Pages
- Predictor percentages stored in: SVG `<path value="90.7">` attributes
- Order: Home team first, away team second
- Team names in title: "Away @ Home" format
- Requires percentage order swap to match teams correctly

## Future Considerations

If ESPN changes their page structure again:
1. Check the `window['__espnfitt__']` JSON structure
2. Look for alternative JSON data sources in other `<script>` tags  
3. The HTML fallback method may help if they revert to server-side rendering
4. Consider using ESPN's API if one becomes available

