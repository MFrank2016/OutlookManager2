from pathlib import Path


def test_split_env_examples_exist_with_distinct_modes():
    compose_example = Path(".env.compose.example")
    remote_example = Path(".env.remote-db.example")

    assert compose_example.exists()
    assert remote_example.exists()

    compose_text = compose_example.read_text(encoding="utf-8")
    remote_text = remote_example.read_text(encoding="utf-8")

    assert "POSTGRES_PASSWORD=" in compose_text
    assert "DB_HOST=postgresql" not in remote_text
    assert "DB_PASSWORD=" in remote_text


def test_root_readme_mentions_both_env_modes():
    readme_text = Path("README.md").read_text(encoding="utf-8")

    assert ".env.compose.example" in readme_text
    assert ".env.remote-db.example" in readme_text


def test_root_readme_promotes_compose_first_and_advanced_mode_handoff():
    readme_text = Path("README.md").read_text(encoding="utf-8")

    assert "## 推荐路径：先用本地 Docker Compose 栈跑起来" in readme_text
    assert "## 高级模式：远程 PostgreSQL / 只跑后端" in readme_text
    assert "docker compose --env-file .env.compose.local up -d --build" in readme_text
    assert "docs/LOCAL_DEVELOPMENT.md" in readme_text
    assert readme_text.index("## 推荐路径：先用本地 Docker Compose 栈跑起来") < readme_text.index(
        "## 高级模式：远程 PostgreSQL / 只跑后端"
    )



def test_docker_readme_targets_compose_ops_only():
    text = Path("README_DOCKER.md").read_text(encoding="utf-8")

    assert "首次启动请先看 README.md" in text
    assert ".env.compose.local" in text
    assert "cp docker/docker.env.example .env" not in text


def test_local_development_is_clearly_advanced_mode():
    text = Path("docs/LOCAL_DEVELOPMENT.md").read_text(encoding="utf-8")

    assert "高级模式" in text
    assert ".env.remote-db.example" in text
    assert "只跑后端" in text


def test_legacy_docker_env_example_is_marked_historical():
    text = Path("docker/docker.env.example").read_text(encoding="utf-8")

    assert "历史兼容" in text
    assert ".env.compose.local" in text
    assert "cp docker/docker.env.example .env" not in text


def test_docker_update_guide_redirects_to_authoritative_docs():
    text = Path("DOCKER_UPDATE_GUIDE.md").read_text(encoding="utf-8")

    assert "README_DOCKER.md" in text
    assert "docs/LOCAL_DEVELOPMENT.md" in text
    assert "cp docker/docker.env.example .env" not in text


def test_compose_docs_reference_helper_script():
    root_readme = Path("README.md").read_text(encoding="utf-8")
    docker_readme = Path("README_DOCKER.md").read_text(encoding="utf-8")

    assert "./scripts/compose-up.sh" in root_readme
    assert "./scripts/compose-up.sh" in docker_readme
    assert "docker compose --env-file .env.compose.local up -d --build" in docker_readme

