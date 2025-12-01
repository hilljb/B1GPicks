# Setup Instructions

Follow these steps to set up the B1GPicks package and start scraping ESPN game predictors.

## Prerequisites

You need to have Conda installed. If you don't have it:
- [Miniconda](https://docs.conda.io/en/latest/miniconda.html) (recommended, lightweight)
- [Anaconda](https://www.anaconda.com/products/distribution) (includes many additional packages)

## Step-by-Step Setup

### 1. Create the Conda Environment

From the project root directory (`B1GPicks/`), run:

```bash
conda env create -f environment.yml
```

This will:
- Create a new conda environment named `b1gpicks`
- Install Python 3.11
- Install all required dependencies (requests, beautifulsoup4, lxml, pytest, etc.)
- Install the B1GPicks package in editable mode

**Note:** This may take a few minutes as conda resolves dependencies and downloads packages.

### 2. Activate the Environment

```bash
conda activate b1gpicks
```

You should see `(b1gpicks)` appear at the beginning of your command prompt.

### 3. Verify Installation

Run the quick test script:

```bash
python quick_test.py
```

You should see output like:
```
✓ Successfully imported Scraper from b1gpicks
✓ Successfully initialized Scraper
✓ Successfully generated schedule URL
✓ Context manager works correctly

All basic tests passed! The package is ready to use.
```

### 4. Run the Example Script

Try scraping some game predictor data:

```bash
python examples/scrape_predictors.py
```

This will scrape ESPN's Big Ten basketball schedule for the next 3 days and save the results to a JSON file.

**Note:** This requires network access and will make requests to ESPN's website. Be respectful and use appropriate delays between requests.

### 5. Run the Test Suite

```bash
pytest
```

This will run all unit tests. Integration tests that require network access are skipped by default.

To run with coverage:

```bash
pytest --cov=b1gpicks --cov-report=term-missing
```

## Troubleshooting

### "conda: command not found"

You need to install Conda. See the Prerequisites section above.

### "No module named 'b1gpicks'"

Make sure you:
1. Created the conda environment: `conda env create -f environment.yml`
2. Activated the environment: `conda activate b1gpicks`

### Environment already exists

If you need to recreate the environment:

```bash
conda env remove -n b1gpicks
conda env create -f environment.yml
```

### Updating the environment

If you add new dependencies to `environment.yml`:

```bash
conda activate b1gpicks
conda env update -f environment.yml --prune
```

## What's Next?

Now you're ready to:
- Run `python examples/scrape_predictors.py` to collect game predictor data
- Modify the scraper in `src/b1gpicks/scraper.py` for your specific needs
- Write your own scripts using the B1GPicks package
- Add new tests in `tests/`

For more details, see the main [README.md](README.md).

