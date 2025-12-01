# Examples

This directory contains example scripts demonstrating how to use the B1GPicks scraper.

## scrape_predictors.py

Scrapes ESPN game predictor percentages for Big Ten basketball games over the next several days.

### Usage

```bash
# Make sure the conda environment is activated
conda activate b1gpicks

# Run the script
python examples/scrape_predictors.py
```

The script will:
1. Scrape the schedule for the next 3 days (configurable)
2. For each game, extract the win probability percentages
3. Display results in a readable format
4. Save results to a timestamped JSON file

### Output Format

The script produces both console output and a JSON file with the following structure:

```json
[
  {
    "date": "2025-12-01",
    "games": [
      {
        "away_team": "Campbell",
        "home_team": "Penn State",
        "game_url": "https://www.espn.com/mens-college-basketball/game/_/gameId/401827278",
        "away_win_pct": 9.3,
        "home_win_pct": 90.7
      }
    ]
  }
]
```

### Customization

You can modify the script to:
- Change the number of days to scrape (`num_days` variable)
- Adjust delay times between requests (be respectful to ESPN's servers)
- Start from a different date
- Change the output format
- Filter or process the data differently

