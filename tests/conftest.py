"""Shared fixtures: the toy experiment package in tests/toy_experiment."""

import pytest

from toy_experiment.cfg import FRAME_IDS, GRAMMAR, PRETERMINALS, RULES  # noqa: F401
from toy_experiment.lexicon import LEXICON
from toy_experiment.splits import SPLITS


@pytest.fixture
def grammar():
    return GRAMMAR


@pytest.fixture
def lexicon():
    return LEXICON


@pytest.fixture
def spec():
    return SPLITS
