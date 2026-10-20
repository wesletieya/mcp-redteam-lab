"""Fixtures : s'assurer que les donnees fictives existent avant les tests."""

from __future__ import annotations

import pytest

from data.generate import generate
from mcp_servers.common import SEED_DIR


@pytest.fixture(scope="session", autouse=True)
def _ensure_data():
    if not (SEED_DIR / "lab.db").exists():
        generate()
