"""Safety tests for destructive local cleanup."""

from pathlib import Path

import pytest

from scripts.validate_cleanup_target import validate_cleanup_target


@pytest.mark.parametrize("path", [Path("/"), Path.home(), Path("/tmp")])
def test_broad_cleanup_targets_are_rejected(path: Path) -> None:
    with pytest.raises(ValueError, match="broad"):
        validate_cleanup_target(path)
