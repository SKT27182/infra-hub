"""Static policy checks for the host-only Compose deployment."""

import re
from pathlib import Path

COMPOSE = Path(__file__).resolve().parents[2] / "docker-compose.yml"
MAKEFILE = COMPOSE.with_name("Makefile")


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


def test_detachable_admin_services_are_default_stopped() -> None:
    compose = COMPOSE.read_text(encoding="utf-8")
    makefile = MAKEFILE.read_text(encoding="utf-8")
    assert compose.count('profiles: ["admin"]') == 4
    for service in (
        "pgadmin",
        "redisinsight",
        "mongo-express",
        "opensearch-dashboards",
    ):
        match = re.search(rf"(?ms)^  {re.escape(service)}:\n(.*?)(?=^  \S|\Z)", compose)
        assert match is not None
        service_block = match.group(1)
        assert 'profiles: ["admin"]' in service_block
    assert "--profile admin create $(ADMIN_SERVICES)" in makefile
    assert "--profile admin stop $(ADMIN_SERVICES)" in makefile
