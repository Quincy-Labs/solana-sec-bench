import shutil
from pathlib import Path

import pytest

from solana_bench.chain import SolanaChain

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"

HAVE_TOOLCHAIN = shutil.which("cargo") is not None and shutil.which("cargo-build-sbf") is not None


def pytest_collection_modifyitems(items):
    if HAVE_TOOLCHAIN:
        return
    skip = pytest.mark.skip(reason="cargo build-sbf not installed")
    for item in items:
        if "toolchain" in item.keywords:
            item.add_marker(skip)


@pytest.fixture
def chain():
    return SolanaChain()
