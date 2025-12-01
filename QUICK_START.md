# Quick Start Guide

## Setup (First Time Only)

```bash
# 1. Create the conda environment
conda env create -f environment.yml

# 2. Activate it
conda activate b1gpicks

# 3. Verify installation
python verify_setup.py
```

## Running the Scraper

### Option 1: Use the Example Script (Easiest)

```bash
conda activate b1gpicks
python examples/scrape_predictors.py
```

This will:
- Scrape the next 3 days of Big Ten basketball games
- Extract win probability percentages for each game
- Display results in the terminal
- Save results to a timestamped JSON file

### Option 2: Custom Python Script

```python
from datetime import datetime
from b1gpicks import Scraper

# Create scraper
with Scraper() as scraper:
    # Scrape next 3 days
    results = scraper.scrape_games_by_date_range(
        start_date=datetime.now(),
        num_days=3,
        delay_between_pages=1.5,
        delay_between_games=1.0
    )
    
    # Process results
    for day in results:
        print(f"\nDate: {day['date']}")
        for game in day['games']:
            print(f"  {game['away_team']} @ {game['home_team']}")
            if game['away_win_pct']:
                print(f"    {game['away_team']}: {game['away_win_pct']}%")
                print(f"    {game['home_team']}: {game['home_win_pct']}%")
```

### Option 3: Scrape a Specific Date

```python
from datetime import datetime
from b1gpicks import Scraper

# Scrape December 2, 2025
with Scraper() as scraper:
    url = scraper.get_schedule_url(datetime(2025, 12, 2))
    games = scraper.get_games_from_schedule(url)
    
    for game in games:
        print(f"{game['away_team']} @ {game['home_team']}")
        predictor = scraper.get_game_predictor(game['game_url'])
        if predictor:
            print(f"  {predictor['away_team']}: {predictor['away_win_pct']}%")
            print(f"  {predictor['home_team']}: {predictor['home_win_pct']}%")
```

## Output Format

The scraper returns data in this structure:

```python
[
    {
        "date": "2025-12-02",
        "games": [
            {
                "away_team": "Campbell",
                "home_team": "Penn State",
                "game_url": "https://www.espn.com/...",
                "away_win_pct": 9.3,
                "home_win_pct": 90.7
            },
            # ... more games
        ]
    },
    # ... more days
]
```

## Common Tasks

### Change Number of Days to Scrape

```python
results = scraper.scrape_games_by_date_range(num_days=7)  # Scrape 7 days
```

### Adjust Delay Times (Be Respectful!)

```python
results = scraper.scrape_games_by_date_range(
    delay_between_pages=2.0,   # Wait 2 seconds between schedule pages
    delay_between_games=1.5    # Wait 1.5 seconds between game pages
)
```

### Save to CSV

```python
import csv

with open('predictors.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Date', 'Away Team', 'Home Team', 'Away %', 'Home %'])
    
    for day in results:
        for game in day['games']:
            writer.writerow([
                day['date'],
                game['away_team'],
                game['home_team'],
                game.get('away_win_pct', ''),
                game.get('home_win_pct', '')
            ])
```

### Scrape a Different Conference

```python
# Change group parameter (7 = Big Ten)
url = scraper.get_schedule_url(datetime.now(), group=2)  # ACC
url = scraper.get_schedule_url(datetime.now(), group=23) # SEC
```

Common conference IDs:
- 2 = ACC
- 4 = Big East
- 5 = Big 12
- 7 = Big Ten (default)
- 8 = Big 12
- 23 = SEC

## Troubleshooting

### "No games found"
- Check that you're looking at the right date
- Verify the conference has games scheduled that day
- Try visiting the ESPN URL directly in a browser to confirm

### "Predictor not available"
- Predictors may not be available until closer to game time
- Some games may not have predictors (check ESPN's website)
- The scraper will set percentages to `None` if unavailable

### Rate Limiting
- If you get connection errors, increase the delay times
- ESPN may temporarily block rapid requests
- Wait a few minutes and try again with longer delays

## Need Help?

See:
- `README.md` - Full documentation
- `IMPLEMENTATION_NOTES.md` - Technical details and debugging
- `FIXES.md` - Recent bug fixes and solutions

