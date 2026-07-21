"""Convergent, allow-listed Docker action tests without a live daemon."""

import pytest

from infra_docker import DockerClient


class FakeContainer:
    """Small Docker container fake with observable state transitions."""

    def __init__(self, name: str, running: bool = False) -> None:
        self.name = name
        self.attrs = {
            "State": {
                "Running": running,
                "Status": "running" if running else "exited",
                "StartedAt": "before",
            }
        }

    def start(self) -> None:
        self.attrs["State"].update(Running=True, Status="running", StartedAt="started")

    def stop(self) -> None:
        self.attrs["State"].update(Running=False, Status="exited")

    def restart(self) -> None:
        self.attrs["State"].update(Running=True, Status="running", StartedAt="restarted")

    def reload(self) -> None:
        return None


@pytest.mark.asyncio
async def test_stop_waits_for_exited_state(monkeypatch: pytest.MonkeyPatch) -> None:
    container = FakeContainer("infra-qdrant", running=True)
    monkeypatch.setattr(DockerClient, "get_container", classmethod(lambda cls, target: container))

    result = await DockerClient.perform_action("infra-qdrant", "stop")

    assert result == {
        "name": "infra-qdrant",
        "state": "exited",
        "healthy": False,
        "health": "none",
    }


@pytest.mark.asyncio
async def test_unrelated_container_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    container = FakeContainer("unrelated-production-container", running=True)
    monkeypatch.setattr(DockerClient, "get_container", classmethod(lambda cls, target: container))

    with pytest.raises(LookupError, match="Infra Hub container not found"):
        await DockerClient.perform_action("unrelated-production-container", "stop")


@pytest.mark.asyncio
async def test_invalid_transition_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    container = FakeContainer("infra-qdrant", running=False)
    monkeypatch.setattr(DockerClient, "get_container", classmethod(lambda cls, target: container))

    with pytest.raises(ValueError, match="incompatible state"):
        await DockerClient.perform_action("infra-qdrant", "stop")
