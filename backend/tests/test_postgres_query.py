"""Unit tests for PostgresService.query cursor handling."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.postgres import PostgresService


class _FakeRecord(dict[str, Any]):
    """dict subclass compatible with dict(row) conversion used by query()."""


class _CursorFactory:
    """Mirrors asyncpg: cursor() returns an awaitable factory, not a Cursor."""

    def __init__(self, cursor: AsyncMock) -> None:
        self._cursor = cursor

    def __await__(self):
        async def _resolve() -> AsyncMock:
            return self._cursor

        return _resolve().__await__()


@pytest.mark.asyncio
async def test_query_select_awaits_cursor_factory_before_fetch() -> None:
    """statement.cursor() returns a CursorFactory; it must be awaited before .fetch()."""
    service = PostgresService()
    row = _FakeRecord(table_name="users")

    cursor = AsyncMock()
    cursor.fetch = AsyncMock(return_value=[row])

    statement = MagicMock()
    statement.get_attributes.return_value = ("table_name",)
    statement.cursor = MagicMock(return_value=_CursorFactory(cursor))

    @asynccontextmanager
    async def transaction():
        yield

    conn = AsyncMock()
    conn.prepare = AsyncMock(return_value=statement)
    conn.execute = AsyncMock()
    conn.transaction = transaction
    conn.close = AsyncMock()

    with patch("services.postgres.asyncpg.connect", AsyncMock(return_value=conn)):
        result = await service.query(
            "SELECT table_name FROM information_schema.tables",
            database="rootagent",
        )

    assert result["success"] is True
    assert result["database"] == "rootagent"
    assert result["row_count"] == 1
    assert result["columns"] == ["table_name"]
    assert result["rows"] == [{"table_name": "users"}]
    statement.cursor.assert_called_once_with()
    cursor.fetch.assert_awaited_once_with(501)


@pytest.mark.asyncio
async def test_query_non_select_uses_execute() -> None:
    service = PostgresService()

    statement = MagicMock()
    statement.get_attributes.return_value = ()

    conn = AsyncMock()
    conn.prepare = AsyncMock(return_value=statement)
    conn.execute = AsyncMock(return_value="UPDATE 1")
    conn.close = AsyncMock()

    with patch("services.postgres.asyncpg.connect", AsyncMock(return_value=conn)):
        result = await service.query(
            "UPDATE users SET active = true WHERE id = 1",
            database="rootagent",
        )

    assert result["success"] is True
    assert result["command"] == "UPDATE 1"
    assert result["rows"] == []
    assert result["row_count"] == 0
    conn.execute.assert_awaited()


@pytest.mark.asyncio
async def test_query_rejects_multiple_statements() -> None:
    service = PostgresService()
    result = await service.query("SELECT 1; SELECT 2", database="rootagent")
    assert result["success"] is False
    assert "single" in result["error"].lower()
