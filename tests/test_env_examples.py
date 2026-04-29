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
