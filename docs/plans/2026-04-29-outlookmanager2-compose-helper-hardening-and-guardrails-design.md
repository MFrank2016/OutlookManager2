# OutlookManager2 Compose Helper 稳健性与 Guardrails 设计

## 背景

上一轮 `docs/deploy convergence` 已经把 `OutlookManager2` 的部署入口收敛到一套更清晰的模型：

- `README.md` 负责首次启动
- `README_DOCKER.md` 负责本地 compose 运维
- `docs/LOCAL_DEVELOPMENT.md` 负责远程 PostgreSQL / 只跑后端高级模式
- `scripts/compose-up.sh` 负责最快启动路径

这一步已经解决了“新用户不知道从哪里开始”的核心问题，但还留下两个明显的后续优化点：

1. `scripts/compose-up.sh` 目前已经可用，但还不够“稳定主入口”。
2. 这轮收敛结果虽然已有部分测试覆盖，但还没有形成足够清晰的长期防回退护栏。

换句话说，当前状态是：

- 部署真相已经重新定义
- 入口已经开始统一
- 但“入口本身的稳健性”和“新真相的长期约束”还需要补一轮加固

因此，下一轮优化不再聚焦大规模文档改造，而是聚焦：

- 让 helper 更稳
- 让关键文档与脚本行为不容易被后续改坏

## 目标

本次设计聚焦两件事：

1. 把 `scripts/compose-up.sh` 从“可用 helper”升级为“更稳的部署主入口”。
2. 为当前真实生效的部署入口建立测试护栏，防止后续回退到旧 `/api` 健康检查、旧 `.env` 主路径或丢失 helper 主入口。

本次设计**不**包含：

- 再做一轮全仓历史文档清理
- 修改业务 API、本地数据库逻辑、Docker 镜像结构
- 把 helper 做成复杂运维框架
- 对整个 `docs/` 目录做全量静态审查并一刀切失败

## 设计原则

### 1. Helper 继续保持“薄”

`compose-up.sh` 可以更稳，但不能膨胀成新的复杂系统。

本轮允许加入的能力应满足：

- 单文件 Bash 可读
- 不引入额外二进制依赖
- 只解决高价值、重复性强的问题

### 2. 稳健性优先于功能面扩张

比起再加更多参数，本轮更重要的是：

- env 解析更稳
- 探活失败输出更有指向性
- 使用者能更快判断“为什么没起来”

### 3. Guardrails 只盯活跃入口

测试护栏应只覆盖当前真实入口文件：

- `README.md`
- `README_DOCKER.md`
- `docs/LOCAL_DEVELOPMENT.md`
- `DOCKER_UPDATE_GUIDE.md`
- `env.example`
- `docker/docker.env.example`
- `scripts/compose-up.sh`

不要对整个 `docs/` 做全仓 grep 式禁止，否则历史文档、报告文档、设计文档会制造大量误报。

### 4. 回归测试要锁“关键真相”，不是锁全部文案

对文档来说，应锁下面这些高价值事实：

- 主启动入口继续引用 `./scripts/compose-up.sh`
- 健康检查入口继续是 `/healthz`
- compose 主路径继续是 `.env.compose.local`
- 远程模式继续是 `.env.remote-db.example`
- helper 在失败时能提供更有用的诊断输出

不需要把每一段文案都做成脆弱断言。

## 当前问题归纳

### 1. `compose-up.sh` 仍然用 `source` 解析 env

当前 helper 会直接 `source .env.compose.local`，这在当前示例文件下是可用的，但存在一个结构性问题：

- Docker Compose 的 env 文件语义与 shell `source` 不是完全等价
- 将来如果 `.env.compose.local` 中出现更复杂字符，helper 行为可能和 `docker compose --env-file` 不一致

这类问题短期不一定爆炸，但它让 helper 的稳定性依赖于“所有人都记得写 shell-safe env”。

### 2. 失败输出仍不够指向性

helper 已经补上 bounded retry，但最终失败时，仍然需要用户自己再去查日志。

这意味着：

- 脚本能发现失败
- 但不能足够快地帮助用户判断失败面

对“最快启动入口”来说，这一步还可以更友好。

### 3. 回归护栏还不够系统

当前已有两类测试：

- `tests/test_env_examples.py`
- `tests/test_compose_up_script.py`

它们已经能挡住部分回退，但还缺两层保护：

- 对活跃部署文档的 `/healthz` / `.env.compose.local` / helper 主路径语义统一保护
- 对 helper 新参数和失败输出行为的保护

## 总体方案

### 一、Helper 稳健性二期

本轮 helper 只补三项能力。

#### 1. 只解析需要的 3 个 env 键

不再 `source` 整个 `.env.compose.local`，而是只解析：

- `PORT`
- `FRONTEND_PORT`
- `POSTGRES_PORT`

推荐实现为脚本内的 `read_env_value KEY FILE` 小函数，通过 `grep` / `cut` / `sed` 这种 shell 原生命令完成简单提取。

目标不是支持所有 `.env` 花样，而是：

- 与当前 compose 示例保持一致
- 避免把 shell 执行语义带进部署入口
- 降低将来 env 文件中出现副作用的风险

#### 2. 增加 `--no-build`

当前 helper 适合首次启动，但对日常“我只是想再拉起来一次”来说，每次都 build 会偏重。

因此推荐增加：

- `./scripts/compose-up.sh --no-build`

语义：

- 跳过 `up -d --build`
- 改为执行：
  - `docker compose --env-file .env.compose.local up -d`

这能覆盖高频日常场景，又不会引入复杂分支。

#### 3. 增加 `--logs-on-fail`

当前 helper 如果最终探活失败，应允许自动打印关键服务日志摘要。

推荐增加：

- `./scripts/compose-up.sh --logs-on-fail`

语义：

- 若最终失败，则自动打印：
  - `docker compose logs --tail=40 outlook-email-api`
  - `docker compose logs --tail=40 outlook-email-frontend`
  - `docker compose logs --tail=40 postgresql`

这不是为了替代完整排障，而是为了让“最快入口”在失败时也能给出更接近答案的第一屏反馈。

### 二、README_DOCKER 中承接 helper 进阶用法

根 `README.md` 仍保持简洁，不继续堆参数说明。

新的 helper 参数说明应下沉到：

- `README_DOCKER.md`

承接内容：

- `./scripts/compose-up.sh --no-build`
- `./scripts/compose-up.sh --logs-on-fail`
- 何时用 helper，何时直接用 raw compose

这样可以保持：

- `README.md` 仍然是“最快成功路径”
- `README_DOCKER.md` 负责“懂得更多以后怎么更顺手地运维”

### 三、Guardrails 自动化

#### 1. 活跃入口护栏

扩展现有文档测试，只覆盖当前真实入口文件。

建议锁定以下事实：

- `README.md` 继续保留 `./scripts/compose-up.sh`
- `README.md` 的主路径仍然使用 `/healthz`
- `README_DOCKER.md` 保留 helper 与 raw compose 双路径
- `docs/LOCAL_DEVELOPMENT.md` 继续指向 `.env.remote-db.example`
- `DOCKER_UPDATE_GUIDE.md` 继续是桥接而不是另一份首启教程
- `env.example` 继续明确“不是主入口”
- `docker/docker.env.example` 继续明确“历史兼容”

同时增加针对“活跃文档”的负向约束：

- 不再出现 `cp docker/docker.env.example .env`
- 不再把 `http://localhost:8000/api` 当成健康检查文档入口

#### 2. Helper 行为护栏

扩展 `tests/test_compose_up_script.py`，锁定：

- `--no-build` 会改用 `docker compose ... up -d`
- `--logs-on-fail` 在探活失败时会抓 3 组关键日志
- env 解析只读取需要的键，不执行整份 env 文件

测试继续使用 fake repo + fake `docker` / `curl` 的方式，不依赖真实 Docker 状态。

## 推荐实施顺序

建议按下面顺序推进：

1. 先改 `compose-up.sh` 的 env 解析与 `--no-build`
2. 再加 `--logs-on-fail`
3. 在 `README_DOCKER.md` 承接 helper 进阶用法
4. 最后补活跃入口与 helper 行为的 guardrails

这样可以先把 helper 的真实行为稳定下来，再去补对外说明和长期测试护栏。

## 验收标准

本轮完成后，应满足：

1. `compose-up.sh` 不再 `source` 整个 `.env.compose.local`
2. helper 支持 `--no-build`
3. helper 支持 `--logs-on-fail`
4. helper 失败时能直接给出关键日志摘要
5. 活跃部署文档继续统一指向 `/healthz` 与 `.env.compose.local`
6. 针对 helper 与活跃文档的 guardrails 测试全部通过

## 风险与边界

### 1. 风险：helper 参数继续膨胀

如果这轮再顺手加很多参数，helper 会从“薄入口”变成“运维框架”，与当前设计目标冲突。

所以本轮参数必须严格收敛在高价值、小规模增强上。

### 2. 风险：guardrails 扫描范围过大

如果对整个 `docs/` 目录做绝对禁止，会让历史方案文档、报告文档、计划文档不断制造误报。

因此 guardrails 必须只扫“活跃入口文件”。

### 3. 风险：过度锁文案

若测试直接锁大量自然语言，会让今后的正常文案优化也变得困难。

因此测试应锁关键事实与关键命令，不锁整段叙述。

## 最终结论

下一轮优化不应再做“大而散”的部署重构，而应做一次**稳固化**：

- 把 `compose-up.sh` 补成一个更稳的主入口
- 把当前这套部署真相做成明确的自动化护栏

一句话总结：

**这轮不是再定义新真相，而是让已经定义好的新真相更稳、更难被改坏。**
