# B1GPicks

A Python web scraping package designed to collect B1G Picks data while appearing as a Chrome browser on macOS.

## Features

- 🌐 Web scraping with realistic Chrome on macOS user agent
- 📦 Conda-based package management
- ✅ Built-in testing framework with pytest
- 🔧 Easy to extend for custom scraping needs
- 🏀 Automatically extracts Big Ten basketball game predictors from ESPN
- 📊 Parses ESPN's JSON data format for reliable scraping
- 🎯 100% success rate on predictor extraction (when available)

## Installation

### Quick Start

```bash
# Create and activate the conda environment
conda env create -f environment.yml
conda activate b1gpicks

# Verify installation
python verify_setup.py

# Run the example scraper
python examples/scrape_predictors.py
```

For detailed setup instructions, see [SETUP.md](SETUP.md).

### Prerequisites

- [Conda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/products/distribution)

### What Gets Installed

The Conda environment includes:
- Python 3.11
- `requests` - HTTP library
- `beautifulsoup4` - HTML parsing
- `lxml` - Fast XML/HTML parser
- `pytest` - Testing framework
- B1GPicks package (in editable mode)

The package is installed in editable mode, so any changes you make to the source code will be immediately available.

## Usage

### ESPN Game Predictor Scraping

The main purpose of this package is to scrape ESPN's Big Ten basketball game predictors:

```python
from datetime import datetime
from b1gpicks import Scraper

# Scrape game predictors for the next 3 days
with Scraper() as scraper:
    results = scraper.scrape_games_by_date_range(
        start_date=datetime.now(),
        num_days=3,
        delay_between_pages=1.5,
        delay_between_games=1.0
    )
    
    # Process results
    for day in results:
        print(f"Date: {day['date']}")
        for game in day['games']:
            print(f"  {game['away_team']} @ {game['home_team']}")
            if game['away_win_pct']:
                print(f"    Predictor: {game['away_win_pct']}% / {game['home_win_pct']}%")
```

See `examples/scrape_predictors.py` for a complete working example.

### Basic Example

```python
from b1gpicks import Scraper

# Use as a context manager (recommended)
with Scraper() as scraper:
    # Get raw HTML response
    response = scraper.get("https://example.com")
    
    # Get parsed BeautifulSoup object
    soup = scraper.get_soup("https://example.com")
    
    # Use the built-in scrape method (customize for your needs)
    data = scraper.scrape("https://example.com")
    print(data)
```

### Custom User Agent

```python
from b1gpicks import Scraper

custom_ua = "MyCustomBot/1.0"
with Scraper(user_agent=custom_ua) as scraper:
    data = scraper.scrape("https://example.com")
```

### Adding Delays Between Requests

```python
from b1gpicks import Scraper

with Scraper() as scraper:
    # Add a 2-second delay before making the request
    data = scraper.scrape("https://example.com", delay=2)
```

## Running Examples

A complete example script is provided to demonstrate scraping ESPN game predictors:

```bash
conda activate b1gpicks
python examples/scrape_predictors.py
```

This will scrape game predictor data for the next 3 days and save results to a timestamped JSON file.

## Running Tests

The package uses pytest for testing. To run all tests:

```bash
pytest
```

To run tests with coverage report:

```bash
pytest --cov=b1gpicks --cov-report=term-missing
```

To run tests verbosely:

```bash
pytest -v
```

**Note:** Some integration tests require network access and are skipped by default. To run them, remove the `@pytest.mark.skip` decorator in `tests/test_scraper.py`.

## Development

### Project Structure

```
B1GPicks/
├── src/
│   └── b1gpicks/
│       ├── __init__.py
│       └── scraper.py          # Main scraper module
├── tests/
│   ├── __init__.py
│   └── test_scraper.py         # Test suite
├── examples/
│   ├── README.md
│   └── scrape_predictors.py    # Example ESPN scraper
├── environment.yml             # Conda environment specification
├── pyproject.toml              # Project configuration
├── .gitignore
├── LICENSE
└── README.md
```

### Extending the Scraper

The scraper includes ESPN-specific methods for scraping Big Ten basketball data:

- `get_schedule_url(date, group=7)` - Generate ESPN schedule URLs
- `get_games_from_schedule(url)` - Extract games from a schedule page
- `get_game_predictor(game_url)` - Extract win percentages from a game page
- `scrape_games_by_date_range(start_date, num_days)` - Scrape multiple days

You can also:

1. Modify existing methods in `src/b1gpicks/scraper.py`
2. Add new methods to the `Scraper` class
3. Create additional modules in the `src/b1gpicks/` directory

### Adding Dependencies

To add new Conda dependencies:

1. Edit `environment.yml` to add the package under `dependencies`
2. Update the environment:
```bash
conda env update -f environment.yml --prune
```

## License

See LICENSE file for details.

## Contributing

1. Create a new branch for your feature
2. Write tests for your changes
3. Ensure all tests pass
4. Submit a pull request
Making picks for NCAAF and NCAAM
