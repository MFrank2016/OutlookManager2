# End-to-End Performance Optimization Design

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 降低账户/邮件相关接口耗时与前端页面加载耗时，重点优化数据库查询路径、批量写入效率和前端重复请求。

**Architecture:** 采用“数据库执行路径优化 + 后端请求链路瘦身 + 前端请求策略收敛”的三层方案。数据库侧优先确保查询命中复合索引并减少无效扫描；后端侧在权限过滤与批量写入处减少 CPU/IO 放大；前端侧通过 Query 缓存策略与避免强制刷新降低冗余网络与渲染开销。

**Tech Stack:** FastAPI, psycopg2/SQLite, DAO 模式, Next.js App Router, TanStack Query, Zustand。

## Bottleneck Analysis

1. 账户查询存在“先查再过滤”的权限路径，普通用户请求会产生额外数据加载。
2. 邮件缓存写入与批量导入项写入使用逐条 `execute`，高并发时事务内 SQL 往返次数偏高。
3. 索引虽较多，但部分高频筛选条件缺少对应复合索引（如刷新状态 + 刷新时间、账户 + 时间排序）。
4. 前端在账户页与邮件页存在重复请求和不必要的强制刷新路径，放大后端压力并增加首屏等待。

## Optimization Strategy

1. **SQL / DAO 优化**
   - 在账户筛选 DAO 增加 `allowed_emails` 条件，直接在 SQL 层做权限收敛。
   - 将邮件缓存批量 upsert、批量导入项写入改为 `executemany`。
2. **索引优化**
   - SQLite 与 PostgreSQL 同步补齐复合索引，覆盖刷新状态、时间排序、分享码活跃状态等查询。
3. **后端链路优化**
   - 保持轻量日志中间件与压缩策略；为静态资源添加缓存头，降低重复加载开销。
4. **前端请求优化**
   - 统一 QueryClient 默认策略，减少窗口聚焦/重连等无效 refetch。
   - 去除账户页手动 `refetch` 的重复触发路径。
   - 邮件页改为“手动刷新时强制一次”而非默认每次强制刷新。

## Validation

1. `pytest -q tests/test_query_performance_guards.py`
2. `env DB_TYPE=sqlite pytest -q tests/test_cache_optimization.py`
3. `cd frontend && npm run lint`
