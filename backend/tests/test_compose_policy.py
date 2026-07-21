"""Static policy checks for the host-only Compose deployment."""

from pathlib import Path

COMPOSE = Path(__file__).resolve().parents[2] / "docker-compose.yml"


def test_every_published_port_uses_loopback_bind_setting() -> None:
    lines = COMPOSE.read_text(encoding="utf-8").splitlines()
    published = [line.strip() for line in lines if line.strip().startswith('- "${')]
    assert published
    assert all("${SERVICE_BIND_HOST:-127.0.0.1}:" in line for line in published)


def test_persistence_and_restart_policy_are_v2_safe() -> None:
    compose = COMPOSE.read_text(encoding="utf-8")
    assert "restart: always" not in compose
    assert compose.count("restart: unless-stopped") == 11
    assert "opensearch_data:" not in compose
    assert "pgadmin_data:" not in compose
    assert "redisinsight_data:" not in compose
    for directory in ("opensearch", "pgadmin", "redisinsight"):
        assert f"${{INFRA_PERSIST_DIR}}/{directory}:" in compose
    persistent_mounts = [
        line for line in compose.splitlines() if line.strip().startswith("- ${INFRA_PERSIST_DIR}/")
    ]
    assert len(persistent_mounts) == 9
    image_lines = [line.strip() for line in compose.splitlines() if line.strip().startswith("image:")]
    assert len(image_lines) == 11
    assert all("@sha256:" in line for line in image_lines)
