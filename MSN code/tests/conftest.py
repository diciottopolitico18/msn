"""pytest setup: import paths and the --full option for the slow 10-seed test.

    pytest            # fast tests only (~30 s); the slow test is skipped with a message
    pytest --full     # also the 10-seed statistical check (a few minutes)
"""
import os
import sys

import pytest

CODE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CODE_DIR)
sys.path.insert(0, os.path.join(CODE_DIR, "analysis"))


def pytest_addoption(parser):
    parser.addoption("--full", action="store_true", help="also run the slow 10-seed baseline test")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--full"):
        return
    skip = pytest.mark.skip(reason="slow 10-seed check: run `pytest --full` to include it")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip)
