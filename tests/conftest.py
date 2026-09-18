"""Release/CI runs may not silently skip the original Lupa execution module."""
import importlib.util
import os

import pytest


def pytest_sessionstart(session):
    if os.environ.get("TOME_REQUIRE_LUA_TESTS") == "1" and importlib.util.find_spec("lupa") is None:
        raise pytest.UsageError('Lupa is required for release tests. Run: python -m pip install -e ".[test]"')
