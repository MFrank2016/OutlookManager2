# OutlookManager2 Compose Helper Hardening and Guardrails Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 提升 `scripts/compose-up.sh` 的稳健性，并为当前活跃部署入口建立防回退测试护栏。

**Architecture:** 先在 `tests/test_compose_up_script.py` 里锁住 helper 的新行为，再以最小改动扩展 `scripts/compose-up.sh` 支持精确 env 读取、`--no-build` 和 `--logs-on-fail`；随后把 helper 进阶用法下沉到 `README_DOCKER.md`，最后为当前活跃部署入口文件补负向/正向 guardrails，防止未来回退到旧 `/api` 健康检查或旧 `.env` 主路径。

**Tech Stack:** Bash, Docker Compose, pytest, Python pathlib/subprocess, Markdown

### Task 1: 收紧 helper 的 env 解析并支持 `--no-build`

**Files:**
- Modify: `tests/test_compose_up_script.py`
- Modify: `scripts/compose-up.sh`

**Step 1: Write the failing tests**

在 `tests/test_compose_up_script.py` 新增两个最小回归：

```python
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
```

第二个测试的核心是：如果脚本仍然 `source` 整份 env，`UNUSED_VALUE=$(exit 99)` 会把脚本打爆；如果只解析 3 个键，则测试会通过。

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest tests/test_compose_up_script.py -q
```

Expected: FAIL，当前 helper 还不支持 `--no-build`，并且仍 `source` 整份 `.env.compose.local`。

**Step 3: Write minimal implementation**

在 `scripts/compose-up.sh` 中：

- 新增 `read_env_value()` 小函数，只解析：
  - `PORT`
  - `FRONTEND_PORT`
  - `POSTGRES_PORT`
- 删除对整个 env 的 `source`
- 新增参数解析：
  - `--no-build`
- 默认仍执行：
  - `docker compose --env-file .env.compose.local up -d --build`
- 如果启用 `--no-build`，改为：
  - `docker compose --env-file .env.compose.local up -d`

保持脚本单文件、无额外依赖、参数解析简单直接。

**Step 4: Run test to verify it passes**

Run:

```bash
python3 -m pytest tests/test_compose_up_script.py -q
bash -n scripts/compose-up.sh
```

Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_compose_up_script.py scripts/compose-up.sh
git commit -m "feat: harden compose helper env parsing"
```

### Task 2: 增加 `--logs-on-fail` 并锁定失败日志输出

**Files:**
- Modify: `tests/test_compose_up_script.py`
- Modify: `scripts/compose-up.sh`

**Step 1: Write the failing test**

继续在 `tests/test_compose_up_script.py` 新增：

```python
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
```

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest tests/test_compose_up_script.py -q
```

Expected: FAIL，当前 helper 探活失败时不会自动抓日志。

**Step 3: Write minimal implementation**

在 `scripts/compose-up.sh` 中：

- 新增参数：
  - `--logs-on-fail`
- 在 `wait_for_url` 或最终失败路径中接入：
  - `docker compose logs --tail=40 outlook-email-api`
  - `docker compose logs --tail=40 outlook-email-frontend`
  - `docker compose logs --tail=40 postgresql`
- 保持默认行为不冗长：
  - 只有显式启用 `--logs-on-fail` 时才自动抓日志

**Step 4: Run test to verify it passes**

Run:

```bash
python3 -m pytest tests/test_compose_up_script.py -q
bash -n scripts/compose-up.sh
```

Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_compose_up_script.py scripts/compose-up.sh
git commit -m "feat: add compose helper failure logs"
```

### Task 3: 在 Docker 运维文档承接 helper 进阶用法

**Files:**
- Modify: `tests/test_env_examples.py`
- Modify: `README_DOCKER.md`

**Step 1: Write the failing test**

在 `tests/test_env_examples.py` 中新增：

```python
def test_docker_readme_mentions_helper_advanced_flags():
    text = Path("README_DOCKER.md").read_text(encoding="utf-8")

    assert "./scripts/compose-up.sh --no-build" in text
    assert "./scripts/compose-up.sh --logs-on-fail" in text
```

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest tests/test_env_examples.py -q
```

Expected: FAIL，当前 Docker 运维手册还没承接 helper 的进阶用法。

**Step 3: Write minimal implementation**

更新 `README_DOCKER.md`：

- 在 helper 脚本 section 下新增两个用法示例：
  - `./scripts/compose-up.sh --no-build`
  - `./scripts/compose-up.sh --logs-on-fail`
- 简洁解释：
  - `--no-build` 适合已经 build 过的日常重拉
  - `--logs-on-fail` 适合快速排障
- 不要把这些说明挪到根 `README.md`

**Step 4: Run test to verify it passes**

Run:

```bash
python3 -m pytest tests/test_env_examples.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_env_examples.py README_DOCKER.md
git commit -m "docs: document compose helper advanced flags"
```

### Task 4: 为当前活跃部署入口建立 guardrails

**Files:**
- Create: `tests/test_active_deploy_guardrails.py`

**Step 1: Write the failing test**

新增 `tests/test_active_deploy_guardrails.py`：

```python
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
```

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest tests/test_active_deploy_guardrails.py -q
```

Expected: 如果当前活跃入口文件仍有旧命令/旧健康检查语义，则 FAIL；若已经干净，则可把这一步视为“先写测试并看到它在当前基线上通过”。

**Step 3: Write minimal implementation**

如果测试已通过，则这一步不改业务文件，只保留新护栏测试。

如果有活跃入口文件仍残留旧命令或 `/api` 健康检查语义，则只修正被测试命中的那些活跃文件，不扩大到全仓文档。

**Step 4: Run tests to verify it passes**

Run:

```bash
python3 -m pytest tests/test_active_deploy_guardrails.py tests/test_env_examples.py tests/test_compose_up_script.py tests/test_healthcheck_config.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_active_deploy_guardrails.py tests/test_env_examples.py tests/test_compose_up_script.py README_DOCKER.md scripts/compose-up.sh
git commit -m "test: add deploy entrypoint guardrails"
```
