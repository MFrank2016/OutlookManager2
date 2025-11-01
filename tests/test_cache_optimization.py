#!/usr/bin/env python3
"""
缓存优化功能测试

测试LRU缓存、压缩、预热、统计等功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db
from datetime import datetime
import time


def test_compression():
    """测试正文压缩功能"""
    print("\n=== 测试正文压缩 ===")
    
    # 测试短文本（不压缩）
    short_text = "Hello World"
    compressed = db.compress_text(short_text)
    assert compressed == short_text, "短文本不应被压缩"
    print("✅ 短文本不压缩: PASS")
    
    # 测试长文本（压缩）
    long_text = "A" * 2000  # 2KB文本
    compressed = db.compress_text(long_text)
    assert len(compressed) < len(long_text), "长文本应该被压缩"
    print(f"✅ 长文本压缩: {len(long_text)} -> {len(compressed)} bytes ({(1-len(compressed)/len(long_text))*100:.1f}% 减少)")
    
    # 测试解压缩
    decompressed = db.decompress_text(compressed)
    assert decompressed == long_text, "解压缩后应该恢复原文本"
    print("✅ 解压缩正确: PASS")
    
    # 测试未压缩文本的解压缩（应该返回原文本）
    uncompressed_result = db.decompress_text(short_text)
    assert uncompressed_result == short_text, "未压缩文本应该直接返回"
    print("✅ 未压缩文本处理: PASS")


def test_lru_fields():
    """测试LRU相关字段"""
    print("\n=== 测试LRU字段 ===")
    
    # 检查数据库表是否有LRU字段
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 检查 emails_cache 表
        cursor.execute("PRAGMA table_info(emails_cache)")
        columns = {row[1] for row in cursor.fetchall()}
        assert 'access_count' in columns, "emails_cache 应该有 access_count 字段"
        assert 'last_accessed_at' in columns, "emails_cache 应该有 last_accessed_at 字段"
        assert 'cache_size' in columns, "emails_cache 应该有 cache_size 字段"
        print("✅ emails_cache 表有所有LRU字段: PASS")
        
        # 检查 email_details_cache 表
        cursor.execute("PRAGMA table_info(email_details_cache)")
        columns = {row[1] for row in cursor.fetchall()}
        assert 'access_count' in columns, "email_details_cache 应该有 access_count 字段"
        assert 'last_accessed_at' in columns, "email_details_cache 应该有 last_accessed_at 字段"
        assert 'body_size' in columns, "email_details_cache 应该有 body_size 字段"
        print("✅ email_details_cache 表有所有LRU字段: PASS")


def test_indexes():
    """测试性能索引"""
    print("\n=== 测试性能索引 ===")
    
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 获取所有索引
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = {row[0] for row in cursor.fetchall()}
        
        # 检查必要的索引
        required_indexes = [
            'idx_emails_cache_folder',
            'idx_emails_cache_from_email',
            'idx_emails_cache_subject',
            'idx_emails_cache_account_folder',
            'idx_email_details_cache_message',
            'idx_emails_cache_last_accessed',
            'idx_email_details_cache_last_accessed'
        ]
        
        for index_name in required_indexes:
            assert index_name in indexes, f"缺少索引: {index_name}"
            print(f"✅ 索引存在: {index_name}")


def test_cache_size_check():
    """测试缓存大小检查"""
    print("\n=== 测试缓存大小检查 ===")
    
    stats = db.check_cache_size()
    
    assert 'db_size_mb' in stats, "应该返回数据库大小"
    assert 'emails_cache' in stats, "应该返回邮件列表缓存统计"
    assert 'details_cache' in stats, "应该返回邮件详情缓存统计"
    
    print(f"✅ 数据库大小: {stats['db_size_mb']} MB")
    print(f"✅ 邮件列表缓存: {stats['emails_cache']['count']} 条")
    print(f"✅ 邮件详情缓存: {stats['details_cache']['count']} 条")
    print(f"✅ 使用率: {stats['size_usage_percent']}%")


def test_lru_cleanup():
    """测试LRU清理策略"""
    print("\n=== 测试LRU清理 ===")
    
    # 先添加一些测试数据
    test_emails = []
    for i in range(100):
        test_emails.append({
            'message_id': f'test-{i}',
            'folder': 'INBOX',
            'subject': f'Test Email {i}',
            'from_email': f'test{i}@example.com',
            'date': datetime.now().isoformat(),
            'is_read': False,
            'has_attachments': False,
            'sender_initial': 'T',
            'verification_code': None
        })
    
    # 缓存测试邮件
    db.cache_emails('test@example.com', test_emails)
    print(f"✅ 添加了 {len(test_emails)} 条测试邮件")
    
    # 获取清理前的统计
    stats_before = db.check_cache_size()
    count_before = stats_before['emails_cache']['count']
    print(f"✅ 清理前记录数: {count_before}")
    
    # 执行LRU清理
    result = db.cleanup_lru_cache()
    print(f"✅ LRU清理结果: 删除 {result['deleted_emails']} 条邮件记录")
    print(f"✅ LRU清理结果: 删除 {result['deleted_details']} 条详情记录")
    
    # 清理测试数据
    db.clear_email_cache_db('test@example.com')
    print("✅ 清理测试数据完成")


def test_email_detail_compression():
    """测试邮件详情压缩"""
    print("\n=== 测试邮件详情压缩 ===")
    
    # 创建测试邮件详情（大正文）
    test_detail = {
        'message_id': 'test-compression-1',
        'subject': 'Test Compression',
        'from_email': 'test@example.com',
        'to_email': 'recipient@example.com',
        'date': datetime.now().isoformat(),
        'body_plain': 'A' * 5000,  # 5KB纯文本
        'body_html': '<html><body>' + 'B' * 5000 + '</body></html>',  # 5KB HTML
        'verification_code': None
    }
    
    # 缓存邮件详情
    success = db.cache_email_detail('test@example.com', test_detail)
    assert success, "缓存邮件详情应该成功"
    print("✅ 邮件详情已缓存（带压缩）")
    
    # 获取缓存的邮件详情
    cached_detail = db.get_cached_email_detail('test@example.com', 'test-compression-1')
    assert cached_detail is not None, "应该能获取缓存的邮件详情"
    assert cached_detail['body_plain'] == test_detail['body_plain'], "纯文本应该正确解压"
    assert cached_detail['body_html'] == test_detail['body_html'], "HTML应该正确解压"
    print("✅ 邮件详情正确解压并返回")
    
    # 清理测试数据
    db.clear_email_cache_db('test@example.com')
    print("✅ 清理测试数据完成")


def test_access_count_update():
    """测试访问计数更新"""
    print("\n=== 测试访问计数更新 ===")
    
    # 添加测试邮件
    test_emails = [{
        'message_id': 'test-access-1',
        'folder': 'INBOX',
        'subject': 'Test Access Count',
        'from_email': 'test@example.com',
        'date': datetime.now().isoformat(),
        'is_read': False,
        'has_attachments': False,
        'sender_initial': 'T',
        'verification_code': None
    }]
    
    db.cache_emails('test@example.com', test_emails)
    print("✅ 测试邮件已缓存")
    
    # 多次访问邮件
    for i in range(3):
        emails, total = db.get_cached_emails('test@example.com', page=1, page_size=10)
        time.sleep(0.1)  # 确保时间戳不同
    
    # 检查访问计数
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT access_count, last_accessed_at 
            FROM emails_cache 
            WHERE email_account = ? AND message_id = ?
        """, ('test@example.com', 'test-access-1'))
        row = cursor.fetchone()
        
        assert row is not None, "应该能找到测试邮件"
        access_count = row[0]
        last_accessed = row[1]
        
        assert access_count >= 3, f"访问计数应该>=3，实际为 {access_count}"
        assert last_accessed is not None, "最后访问时间应该被记录"
        print(f"✅ 访问计数正确更新: {access_count} 次")
        print(f"✅ 最后访问时间: {last_accessed}")
    
    # 清理测试数据
    db.clear_email_cache_db('test@example.com')
    print("✅ 清理测试数据完成")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("缓存优化功能测试")
    print("=" * 60)
    
    try:
        test_compression()
        test_lru_fields()
        test_indexes()
        test_cache_size_check()
        test_lru_cleanup()
        test_email_detail_compression()
        test_access_count_update()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 测试错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

