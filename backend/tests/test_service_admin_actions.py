"""Service-level status and actions for detachable admin containers."""

from typing import Any

import pytest
from fastapi import HTTPException

from infra_docker import DockerClient
from routers import services as services_router
from services.base import BaseService


class FakeContainer:
    """Minimal Docker container used by service status tests."""

    def __init__(self, name: str, status: str, health: str | None = None) -> None:
        self.name = name
        self.status = status
        self.short_id = f"id-{name}"
        state: dict[str, Any] = {"Running": status == "running"}
        if health is not None:
            state["Health"] = {"Status": health}
        self.attrs = {
            "State": state,
            "NetworkSettings": {"Ports": {}},
        }


class ExampleService(BaseService):
    """Concrete service fixture with a detachable admin UI."""

    name = "example"
    display_name = "Example"
    container_name = "infra-example"
    admin_container: str | None = "infra-example-admin"
    admin_url = "http://127.0.0.1:1234"

    async def get_info(self) -> dict[str, Any]:
        return {}


class EmbeddedAdminService(ExampleService):
    """Service fixture whose admin UI is part of its primary container."""

    name = "embedded"
    admin_container = None


def install_containers(
    monkeypatch: pytest.MonkeyPatch, containers: dict[str, FakeContainer]
) -> None:
    """Install a deterministic name-based Docker lookup."""
    monkeypatch.setattr(
        DockerClient,
        "get_container",
        classmethod(lambda cls, target: containers.get(target)),
    )


@pytest.mark.parametrize(
    ("status", "health", "running", "healthy"),
    [
        ("running", "healthy", True, True),
        ("running", "unhealthy", True, False),
        ("exited", None, False, False),
    ],
)
def test_admin_status_is_serialized(
    monkeypatch: pytest.MonkeyPatch,
    status: str,
    health: str | None,
    running: bool,
    healthy: bool,
) -> None:
    install_containers(
        monkeypatch,
        {
            "infra-example": FakeContainer("infra-example", "running", "healthy"),
            "infra-example-admin": FakeContainer(
                "infra-example-admin", status, health
            ),
        },
    )

    admin = ExampleService().get_status().admin

    assert admin is not None
    assert admin.container_name == "infra-example-admin"
    assert admin.status == status
    assert admin.running is running
    assert admin.healthy is healthy


def test_missing_admin_container_has_not_found_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_containers(
        monkeypatch,
        {"infra-example": FakeContainer("infra-example", "running", "healthy")},
    )

    admin = ExampleService().get_status().admin

    assert admin is not None
    assert admin.status == "not_found"
    assert admin.running is False


def test_embedded_admin_has_no_separate_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_containers(
        monkeypatch,
        {"infra-example": FakeContainer("infra-example", "running", "healthy")},
    )

    assert EmbeddedAdminService().get_status().admin is None


@pytest.mark.asyncio
async def test_admin_action_targets_only_admin_container(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_containers(
        monkeypatch,
        {"infra-example": FakeContainer("infra-example", "running", "healthy")},
    )
    calls: list[tuple[str, str, bool]] = []

    async def perform_action(
        cls: type[DockerClient],
        target: str,
        action: str,
        timeout: float = 30.0,
        allow_already_target: bool = False,
    ) -> dict[str, Any]:
        calls.append((target, action, allow_already_target))
        return {"name": target, "state": "running"}

    monkeypatch.setattr(DockerClient, "perform_action", classmethod(perform_action))

    result = await ExampleService().admin_action("start")

    assert result["name"] == "infra-example-admin"
    assert calls == [("infra-example-admin", "start", True)]


@pytest.mark.asyncio
async def test_admin_start_requires_running_primary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_containers(
        monkeypatch,
        {"infra-example": FakeContainer("infra-example", "exited")},
    )

    with pytest.raises(ValueError, match="must be running"):
        await ExampleService().admin_action("start")


@pytest.mark.asyncio
async def test_admin_stop_does_not_require_running_primary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_containers(monkeypatch, {})

    async def perform_action(
        cls: type[DockerClient],
        target: str,
        action: str,
        timeout: float = 30.0,
        allow_already_target: bool = False,
    ) -> dict[str, Any]:
        return {"name": target, "state": "exited"}

    monkeypatch.setattr(DockerClient, "perform_action", classmethod(perform_action))

    result = await ExampleService().admin_action("stop")

    assert result["state"] == "exited"


@pytest.mark.asyncio
async def test_embedded_admin_action_is_rejected() -> None:
    with pytest.raises(LookupError, match="no separate admin container"):
        await EmbeddedAdminService().admin_action("start")


@pytest.mark.asyncio
async def test_grouped_restart_starts_a_stopped_admin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_containers(
        monkeypatch,
        {
            "infra-example": FakeContainer("infra-example", "running", "healthy"),
            "infra-example-admin": FakeContainer("infra-example-admin", "exited"),
        },
    )
    calls: list[tuple[str, str]] = []

    async def perform_action(
        cls: type[DockerClient],
        target: str,
        action: str,
        timeout: float = 30.0,
        allow_already_target: bool = False,
    ) -> dict[str, Any]:
        calls.append((target, action))
        return {"name": target, "state": "running"}

    monkeypatch.setattr(DockerClient, "perform_action", classmethod(perform_action))

    await ExampleService().action("restart")

    assert calls == [
        ("infra-example", "restart"),
        ("infra-example-admin", "start"),
    ]


@pytest.mark.asyncio
async def test_admin_router_maps_primary_dependency_to_conflict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_containers(
        monkeypatch,
        {"infra-example": FakeContainer("infra-example", "exited")},
    )
    monkeypatch.setitem(services_router.SERVICES, "example", ExampleService())

    with pytest.raises(HTTPException) as caught:
        await services_router._admin_action("example", "start")

    assert caught.value.status_code == 409
    assert "must be running" in str(caught.value.detail)


@pytest.mark.asyncio
async def test_admin_router_rejects_service_without_companion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(
        services_router.SERVICES, "embedded", EmbeddedAdminService()
    )

    with pytest.raises(HTTPException) as caught:
        await services_router._admin_action("embedded", "stop")

    assert caught.value.status_code == 404
    assert "no separate admin container" in str(caught.value.detail)
