import asyncio
import re
from pathlib import Path

from main import app


def _find_route(path: str):
    return next((route for route in app.routes if getattr(route, "path", None) == path), None)


def _extract_healthcheck_paths(text: str) -> list[str]:
    return re.findall(r"urlopen\('http://localhost:8000([^']*)'", text)


def test_healthz_route_is_registered_with_minimal_payload():
    route = _find_route("/healthz")

    assert route is not None
    assert "GET" in route.methods
    assert asyncio.run(route.endpoint()) == {"status": "ok"}


def test_container_healthchecks_use_healthz_endpoint():
    dockerfile_paths = _extract_healthcheck_paths(
        Path("docker/Dockerfile").read_text(encoding="utf-8")
    )
    compose_paths = _extract_healthcheck_paths(
        Path("docker-compose.yml").read_text(encoding="utf-8")
    )

    assert dockerfile_paths == ["/healthz"]
    assert compose_paths == ["/healthz"]


def test_api_dockerfile_pins_base_image_digest():
    dockerfile_text = Path("docker/Dockerfile").read_text(encoding="utf-8")
    first_from = next(
        line.strip() for line in dockerfile_text.splitlines() if line.strip().startswith("FROM ")
    )

    assert "@sha256:" in first_from


def test_api_dockerfile_copies_microsoft_access_package():
    dockerfile_text = Path("docker/Dockerfile").read_text(encoding="utf-8")

    assert "COPY microsoft_access/ ./microsoft_access/" in dockerfile_text
