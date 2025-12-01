-- PostgreSQL索引定义
-- 根据PostgreSQL最佳实践设计

-- ============================================================================
-- B-tree索引（默认，用于等值和范围查询）
-- ============================================================================

-- accounts 表索引
CREATE INDEX IF NOT EXISTS idx_accounts_email ON accounts(email);
CREATE INDEX IF NOT EXISTS idx_accounts_refresh_status ON accounts(refresh_status);
CREATE INDEX IF NOT EXISTS idx_accounts_api_method ON accounts(api_method);

-- users 表索引
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- system_config 表索引
CREATE INDEX IF NOT EXISTS idx_config_key ON system_config(key);

-- emails_cache 表索引
CREATE INDEX IF NOT EXISTS idx_emails_cache_account ON emails_cache(email_account);
CREATE INDEX IF NOT EXISTS idx_emails_cache_folder ON emails_cache(folder);
CREATE INDEX IF NOT EXISTS idx_emails_cache_from_email ON emails_cache(from_email);
CREATE INDEX IF NOT EXISTS idx_emails_cache_subject ON emails_cache(subject);
CREATE INDEX IF NOT EXISTS idx_emails_cache_date ON emails_cache(date);

-- email_details_cache 表索引
CREATE INDEX IF NOT EXISTS idx_email_details_cache_account ON email_details_cache(email_account);
CREATE INDEX IF NOT EXISTS idx_email_details_cache_message ON email_details_cache(message_id);

-- share_tokens 表索引
CREATE INDEX IF NOT EXISTS idx_share_tokens_token ON share_tokens(token);
CREATE INDEX IF NOT EXISTS idx_share_tokens_account ON share_tokens(email_account_id);
CREATE INDEX IF NOT EXISTS idx_share_tokens_is_active ON share_tokens(is_active);

-- batch_import_tasks 表索引
CREATE INDEX IF NOT EXISTS idx_batch_import_tasks_task_id ON batch_import_tasks(task_id);
CREATE INDEX IF NOT EXISTS idx_batch_import_tasks_status ON batch_import_tasks(status);

-- batch_import_task_items 表索引
CREATE INDEX IF NOT EXISTS idx_batch_import_task_items_task_id ON batch_import_task_items(task_id);
CREATE INDEX IF NOT EXISTS idx_batch_import_task_items_status ON batch_import_task_items(status);

-- ============================================================================
-- 复合索引（多列查询优化）
-- ============================================================================

-- emails_cache 复合索引
CREATE INDEX IF NOT EXISTS idx_emails_cache_account_folder ON emails_cache(email_account, folder);
CREATE INDEX IF NOT EXISTS idx_emails_cache_account_date ON emails_cache(email_account, date DESC);
CREATE INDEX IF NOT EXISTS idx_emails_cache_account_folder_date ON emails_cache(email_account, folder, date DESC);

-- email_details_cache 复合索引
CREATE INDEX IF NOT EXISTS idx_email_details_cache_account_message ON email_details_cache(email_account, message_id);

-- ============================================================================
-- 部分索引（减少索引大小）
-- ============================================================================

-- 仅索引未读邮件
CREATE INDEX IF NOT EXISTS idx_emails_cache_unread ON emails_cache(email_account, folder, date DESC) 
    WHERE is_read = FALSE;

-- 仅索引待刷新账户
CREATE INDEX IF NOT EXISTS idx_accounts_pending_refresh ON accounts(email, refresh_status) 
    WHERE refresh_status = 'pending';

-- 仅索引活跃的分享令牌
CREATE INDEX IF NOT EXISTS idx_share_tokens_active ON share_tokens(token, email_account_id) 
    WHERE is_active = TRUE;

-- ============================================================================
-- GIN索引（JSONB字段）
-- ============================================================================

-- accounts 表 JSONB 字段索引
CREATE INDEX IF NOT EXISTS idx_accounts_tags_gin ON accounts USING GIN (tags);

-- users 表 JSONB 字段索引
CREATE INDEX IF NOT EXISTS idx_users_bound_accounts_gin ON users USING GIN (bound_accounts);
CREATE INDEX IF NOT EXISTS idx_users_permissions_gin ON users USING GIN (permissions);

-- batch_import_tasks 表 JSONB 字段索引
CREATE INDEX IF NOT EXISTS idx_batch_import_tasks_tags_gin ON batch_import_tasks USING GIN (tags);

-- ============================================================================
-- 表达式索引（函数查询优化）
-- ============================================================================

-- 不区分大小写的邮箱搜索
CREATE INDEX IF NOT EXISTS idx_emails_cache_from_email_lower ON emails_cache(LOWER(from_email));

-- 日期范围查询优化（将TIMESTAMP转换为DATE）
CREATE INDEX IF NOT EXISTS idx_emails_cache_date_date ON emails_cache((date::date));

-- ============================================================================
-- 覆盖索引（INCLUDE子句，PostgreSQL 11+）
-- ============================================================================

-- emails_cache 覆盖索引，避免回表查询
CREATE INDEX IF NOT EXISTS idx_emails_cache_account_folder_include ON emails_cache(email_account, folder) 
    INCLUDE (subject, date, is_read, has_attachments);

-- ============================================================================
-- LRU缓存相关索引
-- ============================================================================

-- emails_cache LRU索引
CREATE INDEX IF NOT EXISTS idx_emails_cache_last_accessed ON emails_cache(last_accessed_at) 
    WHERE last_accessed_at IS NOT NULL;

-- email_details_cache LRU索引
CREATE INDEX IF NOT EXISTS idx_email_details_cache_last_accessed ON email_details_cache(last_accessed_at) 
    WHERE last_accessed_at IS NOT NULL;

-- ============================================================================
-- 性能优化说明
-- ============================================================================
-- 1. 主键和唯一约束自动创建B-tree索引
-- 2. 复合索引的顺序很重要：最常用的查询条件放在前面
-- 3. 部分索引可以减少索引大小，提高写入性能
-- 4. GIN索引适用于JSONB字段的查询
-- 5. 表达式索引可以优化函数查询
-- 6. 覆盖索引可以减少回表查询，提高查询性能
-- 7. 定期执行 VACUUM ANALYZE 以保持索引统计信息最新

