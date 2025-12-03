-- PostgreSQL数据库Schema定义
-- 基于SQLite结构转换，不使用外键约束

-- 创建 accounts 表
CREATE TABLE IF NOT EXISTS accounts (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    refresh_token TEXT NOT NULL,
    client_id VARCHAR(255) NOT NULL,
    tags JSONB DEFAULT '[]'::jsonb,
    last_refresh_time TIMESTAMP,
    next_refresh_time TIMESTAMP,
    refresh_status VARCHAR(50) DEFAULT 'pending',
    refresh_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_token TEXT,
    token_expires_at TIMESTAMP,
    api_method VARCHAR(50) DEFAULT 'imap'
);

-- 创建 users 表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('admin', 'user')),
    bound_accounts JSONB DEFAULT '[]'::jsonb,
    permissions JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- 创建 system_config 表
CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建 emails_cache 表
CREATE TABLE IF NOT EXISTS emails_cache (
    id SERIAL PRIMARY KEY,
    email_account VARCHAR(255) NOT NULL,
    message_id VARCHAR(500) NOT NULL,
    folder VARCHAR(100) NOT NULL,
    subject TEXT,
    from_email VARCHAR(255),
    date TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE,
    has_attachments BOOLEAN DEFAULT FALSE,
    sender_initial VARCHAR(10),
    verification_code TEXT,
    body_preview TEXT,
    access_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP,
    cache_size INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(email_account, message_id)
);

-- 创建 email_details_cache 表
CREATE TABLE IF NOT EXISTS email_details_cache (
    id SERIAL PRIMARY KEY,
    email_account VARCHAR(255) NOT NULL,
    message_id VARCHAR(500) NOT NULL,
    subject TEXT,
    from_email VARCHAR(255),
    to_email TEXT,
    date TIMESTAMP,
    body_plain TEXT,
    body_html TEXT,
    verification_code TEXT,
    access_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP,
    body_size INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(email_account, message_id)
);

-- 创建 share_tokens 表
CREATE TABLE IF NOT EXISTS share_tokens (
    id SERIAL PRIMARY KEY,
    token VARCHAR(255) UNIQUE NOT NULL,
    email_account_id VARCHAR(255) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    subject_keyword TEXT,
    sender_keyword TEXT,
    expiry_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    max_emails INTEGER DEFAULT 10
);

-- 创建 batch_import_tasks 表
CREATE TABLE IF NOT EXISTS batch_import_tasks (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(255) UNIQUE NOT NULL,
    total_count INTEGER NOT NULL,
    success_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    processed_count INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    api_method VARCHAR(50) DEFAULT 'imap',
    tags JSONB DEFAULT '[]'::jsonb,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- 创建 batch_import_task_items 表
-- 注意：不使用外键约束，在应用层维护数据一致性
CREATE TABLE IF NOT EXISTS batch_import_task_items (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    refresh_token TEXT NOT NULL,
    client_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'success', 'failed')),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

-- 创建 SQL 查询历史记录表
CREATE TABLE IF NOT EXISTS sql_query_history (
    id SERIAL PRIMARY KEY,
    sql_query TEXT NOT NULL,
    result_count INTEGER,
    execution_time_ms INTEGER,
    status VARCHAR(50) DEFAULT 'success' CHECK (status IN ('success', 'error')),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- 创建 SQL 查询收藏表
CREATE TABLE IF NOT EXISTS sql_query_favorites (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    sql_query TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_sql_query_history_created_at ON sql_query_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sql_query_history_created_by ON sql_query_history(created_by);
CREATE INDEX IF NOT EXISTS idx_sql_query_favorites_created_by ON sql_query_favorites(created_by);

