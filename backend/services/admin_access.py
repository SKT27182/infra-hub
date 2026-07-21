"""Shared admin UI access metadata for infra service dashboards."""

from typing import Any


def admin_access_block(
    *,
    url: str,
    instructions: list[str],
    login: dict[str, str] | None = None,
    api_key_required: bool = False,
) -> dict[str, Any]:
    """Build a consistent admin_access payload for service get_info responses."""
    block: dict[str, Any] = {
        "url": url,
        "instructions": instructions,
        "api_key_required": api_key_required,
    }
    if login:
        block["login"] = login
    return block
