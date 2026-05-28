"""Tests for infra-hub user roles and access."""

import pytest
from fastapi import HTTPException

from services.user_db import InfraUserRole


def test_infra_user_role_enum():
    assert InfraUserRole.SUPER_ADMIN.value == "SUPER_ADMIN"
    assert InfraUserRole.USER.value == "USER"


@pytest.mark.asyncio
async def test_require_super_admin_rejects_user_role():
    from services.auth import require_super_admin

    with pytest.raises(HTTPException) as exc:
        await require_super_admin({"id": 1, "email": "u@test.com", "role": "USER"})
    assert exc.value.status_code == 403
