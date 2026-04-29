import os
import stat
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_SOURCE = PROJECT_ROOT / "scripts" / "compose-up.sh"


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def _make_fake_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    (repo / "scripts" / "compose-up.sh").write_text(
        SCRIPT_SOURCE.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (repo / "scripts" / "compose-up.sh").chmod(0o755)
    (repo / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    (repo / ".env.compose.example").write_text("PORT=8000\n", encoding="utf-8")
    return repo


def test_compose_up_requires_env_file(tmp_path):
    repo = _make_fake_repo(tmp_path)

    result = subprocess.run(
        ["bash", "scripts/compose-up.sh"],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 1
    assert "cp .env.compose.example .env.compose.local" in (result.stdout + result.stderr)


def test_compose_up_runs_compose_and_health_checks(tmp_path):
    repo = _make_fake_repo(tmp_path)
    (repo / ".env.compose.local").write_text(
        "PORT=8000\nFRONTEND_PORT=3000\nPOSTGRES_PORT=55432\n",
        encoding="utf-8",
    )

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    calls_log = tmp_path / "calls.log"

    _write_executable(
        bin_dir / "docker",
        f"#!/bin/sh\necho docker \"$@\" >> \"{calls_log}\"\nexit 0\n",
    )
    _write_executable(
        bin_dir / "curl",
        f"#!/bin/sh\necho curl \"$@\" >> \"{calls_log}\"\nexit 0\n",
    )

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"

    result = subprocess.run(
        ["bash", "scripts/compose-up.sh"],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )

    assert result.returncode == 0, result.stdout + result.stderr

    calls = calls_log.read_text(encoding="utf-8")
    assert "compose --env-file .env.compose.local up -d --build" in calls
    assert "compose ps" in calls
    assert "http://127.0.0.1:8000/healthz" in calls
    assert "http://127.0.0.1:3000" in calls


def test_compose_up_retries_transient_health_check_failures(tmp_path):
    repo = _make_fake_repo(tmp_path)
    (repo / ".env.compose.local").write_text(
        "PORT=8000\nFRONTEND_PORT=3000\nPOSTGRES_PORT=55432\n",
        encoding="utf-8",
    )

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    calls_log = tmp_path / "calls.log"
    api_count_file = tmp_path / "api.count"
    frontend_count_file = tmp_path / "frontend.count"

    _write_executable(
        bin_dir / "docker",
        f"#!/bin/sh\necho docker \"$@\" >> \"{calls_log}\"\nexit 0\n",
    )
    _write_executable(
        bin_dir / "curl",
        f'''#!/bin/sh
echo curl "$@" >> "{calls_log}"
case "$*" in
  *"/healthz"*)
    count_file="{api_count_file}"
    fail_limit=2
    ;;
  *"http://127.0.0.1:3000"*)
    count_file="{frontend_count_file}"
    fail_limit=1
    ;;
  *)
    exit 1
    ;;
esac
count=0
if [ -f "$count_file" ]; then
  count=$(cat "$count_file")
fi
count=$((count + 1))
echo "$count" > "$count_file"
if [ "$count" -le "$fail_limit" ]; then
  exit 22
fi
exit 0
''',
    )

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"

    result = subprocess.run(
        ["bash", "scripts/compose-up.sh"],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )

    assert result.returncode == 0, result.stdout + result.stderr

    calls = calls_log.read_text(encoding="utf-8")
    assert calls.count("http://127.0.0.1:8000/healthz") == 3
    assert calls.count("http://127.0.0.1:3000") == 2


def test_compose_up_no_build_skips_rebuild(tmp_path):
    repo = _make_fake_repo(tmp_path)
    (repo / ".env.compose.local").write_text(
        "PORT=8000\nFRONTEND_PORT=3000\nPOSTGRES_PORT=55432\n",
        encoding="utf-8",
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    calls_log = tmp_path / "calls.log"

    _write_executable(
        bin_dir / "docker",
        f"#!/bin/sh\necho docker \"$@\" >> \"{calls_log}\"\nexit 0\n",
    )
    _write_executable(
        bin_dir / "curl",
        f"#!/bin/sh\necho curl \"$@\" >> \"{calls_log}\"\nexit 0\n",
    )

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"

    result = subprocess.run(
        ["bash", "scripts/compose-up.sh", "--no-build"],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )

    calls = calls_log.read_text(encoding="utf-8")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "compose --env-file .env.compose.local up -d\n" in calls
    assert "compose --env-file .env.compose.local up -d --build" not in calls


def test_compose_up_reads_required_env_keys_without_sourcing_whole_file(tmp_path):
    repo = _make_fake_repo(tmp_path)
    (repo / ".env.compose.local").write_text(
        "PORT=8000\nFRONTEND_PORT=3000\nPOSTGRES_PORT=55432\nUNUSED_VALUE=$(exit 99)\n",
        encoding="utf-8",
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    calls_log = tmp_path / "calls.log"

    _write_executable(
        bin_dir / "docker",
        f"#!/bin/sh\necho docker \"$@\" >> \"{calls_log}\"\nexit 0\n",
    )
    _write_executable(
        bin_dir / "curl",
        f"#!/bin/sh\necho curl \"$@\" >> \"{calls_log}\"\nexit 0\n",
    )

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"

    result = subprocess.run(
        ["bash", "scripts/compose-up.sh"],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_compose_up_logs_on_fail_emits_service_logs(tmp_path):
    repo = _make_fake_repo(tmp_path)
    (repo / ".env.compose.local").write_text(
        "PORT=8000\nFRONTEND_PORT=3000\nPOSTGRES_PORT=55432\n",
        encoding="utf-8",
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    calls_log = tmp_path / "calls.log"

    _write_executable(
        bin_dir / "docker",
        f'''#!/bin/sh
echo docker "$@" >> "{calls_log}"
exit 0
''',
    )
    _write_executable(
        bin_dir / "curl",
        f'''#!/bin/sh
echo curl "$@" >> "{calls_log}"
exit 22
''',
    )

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"

    result = subprocess.run(
        ["bash", "scripts/compose-up.sh", "--logs-on-fail"],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=20,
        env=env,
    )

    calls = calls_log.read_text(encoding="utf-8")
    assert result.returncode != 0
    assert "logs --tail=40 outlook-email-api" in calls
    assert "logs --tail=40 outlook-email-frontend" in calls
    assert "logs --tail=40 postgresql" in calls
