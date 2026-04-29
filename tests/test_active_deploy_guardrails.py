from pathlib import Path

ACTIVE_DOCS = [
    Path("README.md"),
    Path("README_DOCKER.md"),
    Path("docs/LOCAL_DEVELOPMENT.md"),
    Path("DOCKER_UPDATE_GUIDE.md"),
    Path("env.example"),
    Path("docker/docker.env.example"),
]


def test_active_docs_do_not_point_back_to_legacy_env_entrypoint():
    for path in ACTIVE_DOCS:
        text = path.read_text(encoding="utf-8")
        assert "cp docker/docker.env.example .env" not in text, path


def test_active_docs_use_healthz_as_healthcheck_entrypoint():
    healthcheck_docs = [
        Path("README.md"),
        Path("README_DOCKER.md"),
        Path("docs/LOCAL_DEVELOPMENT.md"),
        Path("DOCKER_UPDATE_GUIDE.md"),
    ]
    for path in healthcheck_docs:
        text = path.read_text(encoding="utf-8")
        assert "http://localhost:8000/api" not in text, path


def test_active_root_entrypoints_still_reference_compose_helper():
    root_readme = Path("README.md").read_text(encoding="utf-8")
    docker_readme = Path("README_DOCKER.md").read_text(encoding="utf-8")

    assert "./scripts/compose-up.sh" in root_readme
    assert "./scripts/compose-up.sh" in docker_readme
