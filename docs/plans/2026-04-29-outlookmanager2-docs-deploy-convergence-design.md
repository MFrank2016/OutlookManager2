# OutlookManager2 文档与部署收敛设计

## 背景

`OutlookManager2` 已经从旧版 `OutlookManager` 的单体形态，演进为一套更完整的平台化系统：

- 后端为 `FastAPI + DAO + SQLite/PostgreSQL 双存储支持`
- 前端为 `Next.js` 管理控制台
- 本地开发支持 `API + Frontend + PostgreSQL` 的 compose 栈
- 同时仍保留“直接运行 Python + 远程 PostgreSQL”的高级模式

能力变强之后，当前仓库的一个明显问题是：**对外使用面比系统本身更复杂**。

具体表现为：

1. 根 `README.md` 已经开始做模式分流，但主路径还不够强。
2. `README_DOCKER.md`、`docs/LOCAL_DEVELOPMENT.md`、`docker/docker.env.example` 之间仍有历史语义残留。
3. 用户打开仓库后，仍然需要自己判断：
   - 应该先看哪个文档
   - 应该复制哪个环境文件
   - 哪条命令是当前推荐入口
4. 失败后的排障路径还不够统一，容易出现“服务没起来，但不知道先看哪一个日志”。

相比之下，旧版 `OutlookManager` 最值得借鉴的不是技术结构，而是它的外部体验：

- 打开 README 就能看到最短启动路径
- 命令数量少
- 验活方式直给
- 出错后知道下一步看哪里

本次设计目标，就是把这种“极简入口 + 清晰排障”的体验，重新带回 `OutlookManager2`，但不退回旧项目的单体实现。

## 目标

本次收敛聚焦五件事：

1. 把本地 `docker compose` 栈确立为唯一主入口。
2. 把根文档、Docker 运维文档、远程数据库开发文档做职责切分。
3. 收敛环境文件语义，消除 `.env` / `.env.compose.local` / 旧 Docker env 说明的冲突。
4. 提供一条统一的启动与验活命令路径。
5. 把失败后的排障入口标准化，降低首次上手成本。

这次设计**不**包含：

- 改动业务 API 语义
- 回退到 `accounts.json` 单文件存储
- 回退到旧静态页面 UI
- 为了文档统一而重构当前平台化架构

本次设计是一次**对外使用面收敛**，不是架构回退。

## 设计原则

### 1. 主路径唯一

第一次打开仓库的用户，不应该在首页面对多个同级入口。

根 `README.md` 必须只承担一件事：

**让用户最快把本地 compose 栈跑起来。**

### 2. 高级模式下沉

远程 PostgreSQL 模式仍然保留，但它属于：

- 已知自己要做什么的开发者
- 只想单独跑后端服务的人
- 已经有现成远程库的人

因此它不应该与主路径并列展示，而应该明确标记为高级模式并下沉到次级文档。

### 3. 文档只保留单一事实来源

同一类信息只能有一个权威入口：

- 首次启动命令，以 `README.md` 为准
- Docker 运维命令，以 `README_DOCKER.md` 为准
- 远程库模式，以 `docs/LOCAL_DEVELOPMENT.md` 为准

其他文档只链接，不重复抄写一份变体。

### 4. 失败后必须给下一步动作

文档不能只告诉用户“执行什么命令”，还必须告诉用户：

- 什么算启动成功
- 哪一步失败时先看哪里
- 下一条排障命令是什么

### 5. 保留平台化能力，借鉴旧项目的易用性

本次只借旧项目的：

- 入口短
- 命令直给
- 验活清晰
- 排障友好

不借旧项目的：

- 单文件应用结构
- `accounts.json` 主存储
- root 容器 workaround
- 静态页实现本身

## 当前问题归纳

### 1. 文档入口分流不彻底

当前根 `README.md` 同时展示两种启动方式，虽然已经能表达差异，但主推荐路径还不够强，用户仍会在首页停下来判断：

- 我到底该走 compose 还是 Python
- 我是不是要先配置远程数据库

这与“首次使用尽快成功”的目标冲突。

### 2. 环境文件语义存在历史冲突

当前仓库中实际存在三种环境配置叙事：

- `.env.compose.example` → `.env.compose.local`
- `.env.remote-db.example` → `.env`
- `docker/docker.env.example` → `.env`

其中第三种是旧话术残留，会让用户重新回到“compose 也要复制 `.env`”的旧认知，增加混淆。

### 3. Docker 文档职责重叠

`README.md` 与 `README_DOCKER.md` 都在讲 compose 启动命令，但边界不够清晰：

- 有些信息重复
- 有些信息分散
- 有些信息没有明确说“这是首次启动还是日常运维”

### 4. 启动成功标准不够完整

当前文档主要强调 `/healthz`，但对于真实用户来说，成功至少应包括：

- 容器都已启动
- API 健康检查通过
- 前端首页可访问
- PostgreSQL 容器正常 ready

### 5. 故障排查路径不够标准化

当前文档虽然给了日志命令，但没有把“API 不通 / 前端不通 / 数据库没 ready”三类问题拆开写成固定的下一步动作。

## 总体方案

### 一、根 README 只保留本地 compose 主路径

根 `README.md` 收敛为“第一次跑起来”文档。

首页只保留下面这些内容：

1. 一句话介绍项目是什么。
2. 明确说明默认推荐方式是本地 compose 栈。
3. 前置依赖：Docker、Docker Compose。
4. 三步启动：
   - 复制 `.env.compose.example`
   - 执行 compose 启动命令
   - 打开访问地址
5. 三步验活：
   - `docker compose ps`
   - `curl /healthz`
   - 打开前端页面 / 登录页
6. 常用命令：停止、重建、查看日志。
7. 一条“高级模式入口”：如需远程 PostgreSQL 或只跑后端，请跳转 `docs/LOCAL_DEVELOPMENT.md`。

下面这些内容不应再挡在主路径前面：

- 数据库历史背景说明
- 远程 PostgreSQL 详细配置
- 长篇环境变量解释
- 复杂运维细节

它们可以保留，但应下沉到 README 后半段 FAQ，或移动到次级文档。

### 二、次级文档职责切分

#### 1. `README_DOCKER.md`

专门负责本地 compose 栈的日常运维，不重复首次启动说明。

应包含：

- 查看日志
- 重建镜像
- 重启单个服务
- 停止与清理
- 清理数据卷
- 更换端口
- 查看容器状态
- 数据卷 / 持久化说明
- 健康检查说明

它的定位不是“新手教程”，而是“本地 compose 运维手册”。

#### 2. `docs/LOCAL_DEVELOPMENT.md`

专门负责高级模式：

- 只跑后端
- 连接远程 PostgreSQL
- 本机安装 Python 依赖
- 解释 `.env` 的字段意义
- 处理数据库连接问题

首页第一屏就应明确写出：

> 只有当你要直连远程 PostgreSQL，或只跑后端服务时，才使用这份文档。

#### 3. 其他文档

其他文档如部署指南、升级说明、故障说明文档，不再重复写主启动命令，只通过链接引用权威入口。

### 三、统一启动入口脚本

建议新增一个轻量脚本，命名优先推荐：

- `scripts/compose-up.sh`

这个名字比 `dev-up.sh` 更直白，能够准确表达它是“本地 compose 栈启动入口”，也避免与未来可能存在的其他开发脚本混淆。

脚本职责只做以下几件事：

1. 检查 `docker` 与 `docker compose` 是否可用。
2. 检查 `.env.compose.local` 是否存在。
   - 若不存在，明确提示先从 `.env.compose.example` 复制。
3. 执行：
   ```bash
   docker compose --env-file .env.compose.local up -d --build
   ```
4. 启动后执行基础验活：
   - `docker compose ps`
   - 轮询 `http://127.0.0.1:8000/healthz`
   - 访问前端首页 `http://127.0.0.1:3000`
5. 打印结果摘要：
   - Frontend 地址
   - API 地址
   - PostgreSQL host 端口
   - 下一步常用命令

脚本不做复杂配置生成，不自动改用户文件，不引入交互式向导。目标是：

**薄、稳、直给。**

### 四、环境文件语义收敛

最终只保留两套清晰语义：

#### 1. 本地 compose 栈

- 模板：`.env.compose.example`
- 实际使用：`.env.compose.local`

只用于：

- 本地 `docker compose` 启动
- API / Frontend / PostgreSQL 联调

#### 2. 远程 PostgreSQL 模式

- 模板：`.env.remote-db.example`
- 实际使用：`.env`

只用于：

- `python main.py`
- 本地只跑 API
- 连接现有远程 PostgreSQL

#### 3. `docker/docker.env.example`

这是当前最容易制造歧义的历史文件。

推荐方案：

- **优先删除**，避免继续向用户暗示“compose 也应该复制 `.env`”

若短期出于兼容或历史保留原因暂时不能删，则至少要在文件顶部显式标注：

- 历史兼容用途
- 非主路径
- 当前 compose 模式请改用 `.env.compose.local`

本次设计倾向于：

**宁可减少文件，也不要保留歧义入口。**

### 五、标准化验活与排障路径

本地 compose 启动成功的标准，建议统一为四步：

1. `docker compose ps` 中三个核心服务都在运行：
   - `outlook-email-api`
   - `outlook-email-frontend`
   - `postgresql`
2. `curl http://127.0.0.1:8000/healthz` 返回成功。
3. 打开 `http://127.0.0.1:3000` 能加载前端页面。
4. PostgreSQL 容器为 healthy / ready。

对应的排障入口固定写进 README：

#### 1. API 不通

先执行：

```bash
docker compose logs -f outlook-email-api
```

#### 2. 前端不通

先执行：

```bash
docker compose logs -f outlook-email-frontend
```

#### 3. 数据库未 ready

先执行：

```bash
docker compose logs -f postgresql
```

#### 4. 不确定整体状态

先执行：

```bash
docker compose ps
```

这样文档就不再只是“命令列表”，而是变成一条可复用的故障分流路径。

## 文档结构建议

### `README.md` 建议结构

```text
项目简介
↓
为什么默认推荐本地 compose
↓
前置依赖
↓
3 步启动
↓
3 步验活
↓
访问地址
↓
常用命令
↓
遇到问题先看哪里
↓
高级模式入口（链接）
↓
FAQ / 背景说明
```

### `README_DOCKER.md` 建议结构

```text
文档定位说明
↓
日常操作命令
↓
日志查看
↓
重建 / 重启
↓
清理与数据卷
↓
端口修改
↓
健康检查与服务状态
↓
常见 Docker 问题
```

### `docs/LOCAL_DEVELOPMENT.md` 建议结构

```text
适用场景说明
↓
前置依赖
↓
复制 .env.remote-db.example
↓
配置远程数据库
↓
安装依赖并启动后端
↓
验活
↓
连接超时 / 认证失败 / 数据库不存在等问题
```

## 推荐实施顺序

建议按最小风险顺序落地：

1. 重写 `README.md`，先收敛主入口。
2. 整理 `README_DOCKER.md`，把运维内容完整承接过去。
3. 更新 `docs/LOCAL_DEVELOPMENT.md` 首页定位与用词，强化“高级模式”语义。
4. 删除或降级 `docker/docker.env.example` 的主路径叙事。
5. 新增 `scripts/compose-up.sh`。
6. 在文档中统一接入新脚本与验活路径。
7. 最后做一次真实启动验证，确保文档与运行结果一致。

## 验收标准

本次收敛完成后，应满足以下验收标准：

1. 新用户打开 `README.md`，无需阅读其他文档，也能完成本地 compose 栈首启。
2. `README.md` 首屏不再要求用户理解远程数据库模式。
3. 仓库中不再存在多个互相冲突的“主环境文件说明”。
4. 启动成功标准明确，至少覆盖容器、API、前端三个层面。
5. 每类常见故障都有直接可复制的第一条排障命令。
6. 其他部署文档不再重复抄写主路径，而是链接到权威入口。

## 风险与边界

### 1. 风险：旧文档残留造成反向引导

即使重写了根 README，只要仓库中仍存在旧说明文件并带有旧命令，用户仍可能被搜索命中后走偏。

因此本次收敛不能只改一个文件，必须同时做引用清理。

### 2. 风险：脚本与真实运行行为漂移

如果新增 `scripts/compose-up.sh` 但后续 compose 配置变化、脚本未同步，就会再次制造文档与运行不一致的问题。

因此脚本必须保持轻量，只封装真正稳定的主路径，不要内嵌太多业务细节。

### 3. 边界：本次不解决所有历史文档质量问题

仓库内现有文档较多，本次设计只聚焦：

- 主启动入口
- Docker 运维入口
- 远程库高级入口
- 环境文件语义统一

并不要求一次清理所有历史说明文档。

## 最终结论

`OutlookManager2` 应继续保持当前的平台化实现，但对外使用面应重新收敛成类似旧版 `OutlookManager` 的体验：

- 打开 README 就知道先做什么
- 默认只走一条本地 compose 主路径
- 高级模式下沉
- 验活标准明确
- 故障排查第一步直给

一句话总结：

**保留新项目的能力边界，重新找回旧项目的启动直觉。**
