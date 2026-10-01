#!/usr/bin/env python
"""Print this week's Big Ten picks from ESPN's Matchup Predictor.

This is a thin wrapper around the ``b1gpicks`` command and accepts the same
options. Examples:

    python examples/scrape_predictors.py                     # current football week
    python examples/scrape_predictors.py --week 6            # a specific week
    python examples/scrape_predictors.py --sport basketball  # next 3 days of basketball

Run with ``--help`` for all options.
"""

import sys

from b1gpicks.cli import main

if __name__ == "__main__":
    sys.exit(main())
