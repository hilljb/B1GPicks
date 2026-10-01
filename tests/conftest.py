"""Shared pytest fixtures.

Fixture HTML files in ``tests/fixtures/`` are trimmed copies of real ESPN pages
(captured 2026-10-01). They keep only the parts of the ``__espnfitt__`` blob
that the parsers read.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
import requests

from b1gpicks import Scraper
from b1gpicks.espn import extract_page_data

FIXTURES = Path(__file__).parent / "fixtures"

FOOTBALL_SCHEDULE_URL = "https://www.espn.com/college-football/schedule/_/group/5"
FOOTBALL_GAME_URL = "https://www.espn.com/college-football/game/_/gameId/401858476/penn-state-northwestern"


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--run-network", action="store_true", help="run tests that contact espn.com")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-network"):
        return
    skip = pytest.mark.skip(reason="needs --run-network")
    for item in items:
        if "network" in item.keywords:
            item.add_marker(skip)


def read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text()


@pytest.fixture
def load_fixture() -> Callable[[str], dict]:
    """Return a function that loads a fixture file's ``__espnfitt__`` data."""
    return lambda name: extract_page_data(read_fixture(name))


def make_response(url: str, body: str, status: int = 200) -> requests.Response:
    response = requests.Response()
    response.url = url
    response.status_code = status
    response._content = body.encode()
    response.encoding = "utf-8"
    return response


class FakeESPN:
    """Stands in for ``Scraper.session.get``, serving fixture files by URL."""

    def __init__(self, routes: dict[str, str]) -> None:
        self.routes = routes
        self.requested: list[str] = []

    def __call__(self, url: str, **kwargs: object) -> requests.Response:
        self.requested.append(url)
        if url not in self.routes:
            return make_response(url, "Not Found", status=404)
        return make_response(url, read_fixture(self.routes[url]))


@pytest.fixture
def fake_espn(monkeypatch: pytest.MonkeyPatch) -> Callable[..., tuple[Scraper, FakeESPN]]:
    """Factory returning a no-delay :class:`Scraper` whose requests hit ``routes``."""

    def factory(routes: dict[str, str], sport: str = "football") -> tuple[Scraper, FakeESPN]:
        scraper = Scraper(sport, delay=0)
        fake = FakeESPN(routes)
        monkeypatch.setattr(scraper.session, "get", fake)
        return scraper, fake

    return factory
