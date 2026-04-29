# OutlookManager2 Docs and Deploy Convergence Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把 `OutlookManager2` 的文档与部署入口收敛成 compose-first 的单主路径体验，补齐统一启动脚本与可复制的排障路径，同时保留远程 PostgreSQL 高级模式。

**Architecture:** 先用 pytest 锁定 README / Docker 文档 / 高级模式文档 / 启动脚本的目标行为，再分四轮推进：根 README compose-first、活跃文档与兼容 env 语义收敛、`scripts/compose-up.sh` 落地、最后把脚本接回文档主路径并做串行回归。全程不碰业务 API，只改文档、轻量 Bash 脚本和文档回归测试。

**Tech Stack:** Markdown, Bash, Docker Compose, pytest, Python pathlib/subprocess

### Task 1: 重写根 README 为 compose-first 主入口

**Files:**
- Modify: `tests/test_env_examples.py`
- Modify: `README.md`

**Step 1: Write the failing test**

在 `tests/test_env_examples.py` 中新增一个 README 结构断言，锁定“主路径优先、远程模式下沉”的目标：

```python
def test_root_readme_promotes_compose_first_and_advanced_mode_handoff():
    readme_text = Path("README.md").read_text(encoding="utf-8")

    assert "## 推荐路径：先用本地 Docker Compose 栈跑起来" in readme_text
    assert "## 高级模式：远程 PostgreSQL / 只跑后端" in readme_text
    assert "docker compose --env-file .env.compose.local up -d --build" in readme_text
    assert "docs/LOCAL_DEVELOPMENT.md" in readme_text
    assert readme_text.index("## 推荐路径：先用本地 Docker Compose 栈跑起来") < readme_text.index(
        "## 高级模式：远程 PostgreSQL / 只跑后端"
    )
```

保留现有 `test_split_env_examples_exist_with_distinct_modes()`，不要删掉现有 env split 回归。

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest tests/test_env_examples.py -q
```

Expected: FAIL，提示当前 `README.md` 还没有新的 compose-first / 高级模式 section 结构。

**Step 3: Write minimal implementation**

重写 `README.md`，但只做根入口收敛，不在这一轮引入脚本：

- 增加 `## 推荐路径：先用本地 Docker Compose 栈跑起来`
- 在该 section 内保留：
  - `cp .env.compose.example .env.compose.local`
  - `docker compose --env-file .env.compose.local up -d --build`
  - `docker compose ps`
  - `curl http://127.0.0.1:8000/healthz`
- 增加 `## 高级模式：远程 PostgreSQL / 只跑后端`
- 明确跳转到 `docs/LOCAL_DEVELOPMENT.md`
- 把“数据库密码串用历史”这类背景内容下沉到 FAQ / 后半段，不要挡住首屏主路径

README 首屏必须满足：先让用户跑起来，再解释为什么会有第二种模式。

**Step 4: Run test to verify it passes**

Run:

```bash
python3 -m pytest tests/test_env_examples.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_env_examples.py README.md
git commit -m "docs: make root readme compose first"
```

### Task 2: 收敛活跃文档与兼容 env 语义

**Files:**
- Modify: `tests/test_env_examples.py`
- Modify: `README_DOCKER.md`
- Modify: `docs/LOCAL_DEVELOPMENT.md`
- Modify: `env.example`
- Modify: `docker/docker.env.example`
- Modify: `DOCKER_UPDATE_GUIDE.md`

**Step 1: Write the failing tests**

继续在 `tests/test_env_examples.py` 增加 4 组断言：

```python
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
```

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest tests/test_env_examples.py -q
```

Expected: FAIL，当前活跃文档和 `docker/docker.env.example` 仍保留旧 `.env` 主路径叙事。

**Step 3: Write minimal implementation**

按“单一事实来源”原则收敛：

- `README_DOCKER.md`
  - 改成纯运维手册
  - 开头显式写：首次启动请先看 `README.md`
  - 只保留 compose 栈运维命令
- `docs/LOCAL_DEVELOPMENT.md`
  - 开头显式写：这是高级模式
  - 强调适用场景：远程 PostgreSQL / 只跑后端
- `env.example`
  - 保持为远程 PostgreSQL 兼容模板，但进一步弱化“主入口”语义
- `docker/docker.env.example`
  - 不删除，先改成历史兼容说明
  - 顶部加粗提醒：当前 compose 主路径使用 `.env.compose.local`
  - 删除或替换 `cp docker/docker.env.example .env` 的主路径指导
- `DOCKER_UPDATE_GUIDE.md`
  - 不再保留一整套陈旧首启流程
  - 改成桥接文档：把首次启动导向 `README.md`，把 compose 运维导向 `README_DOCKER.md`，把远程库模式导向 `docs/LOCAL_DEVELOPMENT.md`

这一轮重点是清掉“活跃文档”的冲突，不强求一次修完所有历史说明文档。

**Step 4: Run test to verify it passes**

Run:

```bash
python3 -m pytest tests/test_env_examples.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_env_examples.py README_DOCKER.md docs/LOCAL_DEVELOPMENT.md env.example docker/docker.env.example DOCKER_UPDATE_GUIDE.md
git commit -m "docs: align deploy docs and env semantics"
```

### Task 3: 新增 compose-up 启动脚本与回归测试

**Files:**
- Create: `tests/test_compose_up_script.py`
- Create: `scripts/compose-up.sh`

**Step 1: Write the failing tests**

在 `tests/test_compose_up_script.py` 中新增两个最小回归：

```python
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
```

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest tests/test_compose_up_script.py -q
```

Expected: FAIL，提示 `scripts/compose-up.sh` 尚不存在。

**Step 3: Write minimal implementation**

新增 `scripts/compose-up.sh`，要求：

- 使用 `bash`，开头 `set -euo pipefail`
- 通过脚本自身路径定位 repo root
- 检查：
  - `docker` 命令存在
  - `curl` 命令存在
  - `.env.compose.local` 存在
- 如 env 缺失，打印：
  - `cp .env.compose.example .env.compose.local`
  - 并退出 `1`
- 读取 `.env.compose.local` 中的：
  - `PORT`
  - `FRONTEND_PORT`
  - `POSTGRES_PORT`
- 执行：
  - `docker compose --env-file .env.compose.local up -d --build`
  - `docker compose ps`
  - `curl -fsS http://127.0.0.1:${PORT}/healthz`
  - `curl -fsS http://127.0.0.1:${FRONTEND_PORT}`
- 成功后打印：
  - Frontend 地址
  - API 地址
  - PostgreSQL host 端口
  - 常用日志命令

保持脚本“薄、稳、直给”，不要自动生成 env 文件，也不要内嵌复杂等待器。

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
git commit -m "feat: add compose startup helper"
```

### Task 4: 把 compose-up 脚本接回主文档并做最终回归

**Files:**
- Modify: `tests/test_env_examples.py`
- Modify: `README.md`
- Modify: `README_DOCKER.md`

**Step 1: Write the failing test**

继续在 `tests/test_env_examples.py` 增加 helper script 接线断言：

```python
def test_compose_docs_reference_helper_script():
    root_readme = Path("README.md").read_text(encoding="utf-8")
    docker_readme = Path("README_DOCKER.md").read_text(encoding="utf-8")

    assert "./scripts/compose-up.sh" in root_readme
    assert "./scripts/compose-up.sh" in docker_readme
    assert "docker compose --env-file .env.compose.local up -d --build" in docker_readme
```

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest tests/test_env_examples.py -q
```

Expected: FAIL，当前 README 体系还没有把 `compose-up.sh` 明确接为推荐入口。

**Step 3: Write minimal implementation**

更新文档接线：

- `README.md`
  - 把 `./scripts/compose-up.sh` 写成“最快启动”的首选命令
  - 保留原始 compose 命令作为手动备用方案
  - 在“遇到问题先看这里”中给出：
    - `docker compose ps`
    - `docker compose logs -f outlook-email-api`
    - `docker compose logs -f outlook-email-frontend`
    - `docker compose logs -f postgresql`
- `README_DOCKER.md`
  - 在开头增加 helper script 入口
  - 保留运维命令的 raw compose 版本，避免脚本覆盖全部运维场景

**Step 4: Run tests to verify everything passes**

Run:

```bash
python3 -m pytest tests/test_env_examples.py tests/test_compose_up_script.py tests/test_healthcheck_config.py -q
python3 -m pytest tests/test_pytest_collection_boundary.py -q
```

Expected: PASS

如果时间允许，再做一个内容检查：

```bash
rg -n "cp docker/docker.env.example \.env|http://localhost:8000/api" README.md README_DOCKER.md docs/LOCAL_DEVELOPMENT.md DOCKER_UPDATE_GUIDE.md docker/docker.env.example
```

Expected: 无命中过时主路径；`/api` 不再作为健康检查文档入口。

**Step 5: Commit**

```bash
git add tests/test_env_examples.py README.md README_DOCKER.md
git commit -m "docs: wire compose helper into deployment docs"
```
