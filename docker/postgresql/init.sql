-- PostgreSQL数据库初始化脚本
-- 设置字符集和时区

-- 设置时区
SET timezone = 'Asia/Shanghai';

-- 设置客户端编码
SET client_encoding = 'UTF8';

-- 创建扩展（如果需要）
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- 用于文本相似度搜索

-- 配置pg_hba.conf以允许远程连接
-- 注意：这个配置会在容器启动时通过环境变量和命令参数自动应用
-- 如果需要更精细的控制，可以在容器启动后手动编辑pg_hba.conf

-- 注意：表结构将在应用启动时通过 init_database() 函数创建
-- 这里只做基础配置

