# Examples

## `scrape_predictors.py`

Prints Big Ten picks from ESPN's Matchup Predictor. It is a thin wrapper around
the `b1gpicks` command and accepts the same options.

```bash
conda activate b1gpicks

python examples/scrape_predictors.py                      # current football week
python examples/scrape_predictors.py --week 6             # a specific week
python examples/scrape_predictors.py --sport basketball   # next 3 days of basketball
python examples/scrape_predictors.py --help               # all options
```

Results are printed as a table and saved as JSON in `data/`. Use `--no-save`
to skip the file, or `-o path.json` to choose where it goes. See the
[main README](../README.md) for the output format and the Python API.

The `game_predictors_*.json` files in this directory are saved output from the
2025-26 basketball season, kept for reference. They use the older 0.1.0 format.
