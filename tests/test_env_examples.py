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
