"""One-shot DB bootstrap for ``make db-bootstrap`` / ``make dev-local``."""

from __future__ import annotations

import asyncio
import sys


async def _run() -> None:
    from services.user_db import user_service

    await user_service.ensure_user_table()
    await user_service.ensure_default_admin_user()


def main() -> None:
    try:
        asyncio.run(_run())
    except Exception as exc:
        print(f"DB bootstrap failed: {exc}", file=sys.stderr)
        print(
            "If you changed POSTGRES_PASSWORD, wipe infra data and recreate:\n"
            "  make clean-hard && make up",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
