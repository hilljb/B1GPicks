"""B1GPicks: Big Ten picks from ESPN's Matchup Predictor."""

__version__ = "0.2.0"

from .espn import ESPNParseError
from .models import Game, Prediction, Schedule, Team
from .scraper import Scraper
from .sports import BASKETBALL, FOOTBALL, Sport, get_sport

__all__ = [
    "BASKETBALL",
    "ESPNParseError",
    "FOOTBALL",
    "Game",
    "Prediction",
    "Schedule",
    "Scraper",
    "Sport",
    "Team",
    "get_sport",
]
