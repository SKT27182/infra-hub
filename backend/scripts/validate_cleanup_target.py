"""Reject broad paths before destructive Infra Hub cleanup."""

from __future__ import annotations

import argparse
from pathlib import Path


def validate_cleanup_target(target: Path) -> Path:
    """Return a resolved dedicated target or raise for broad paths."""
    resolved = target.expanduser().resolve()
    forbidden = {Path("/"), Path.home(), Path.home().parent, Path("/tmp"), Path("/private/tmp")}
    if resolved in forbidden or len(resolved.parts) < 4:
        raise ValueError("Refusing to clean a broad INFRA_PERSIST_DIR")
    return resolved


def main() -> None:
    """Validate one cleanup target for the Makefile guard."""
    parser = argparse.ArgumentParser()
    parser.add_argument("target", type=Path)
    args = parser.parse_args()
    validate_cleanup_target(args.target)


if __name__ == "__main__":
    main()
