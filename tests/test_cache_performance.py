#!/usr/bin/env python3
"""
缓存性能测试

测试缓存命中率、响应时间、压缩率等性能指标
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db
from datetime import datetime
import time
import random
import string


def generate_random_text(length):
    """生成随机文本"""
    return ''.join(random.choices(string.ascii_letters + string.digits + ' ', k=length))


def test_cache_hit_rate():
    """测试缓存命中率"""
    print("\n=== 测试缓存命中率 ===")
    
    # 准备测试数据
    test_account = 'perf-test@example.com'
    test_emails = []
    
    for i in range(100):
        test_emails.append({
            'message_id': f'perf-test-{i}',
            'folder': 'INBOX',
            'subject': f'Performance Test {i}',
            'from_email': f'sender{i}@example.com',
            'date': datetime.now().isoformat(),
            'is_read': False,
            'has_attachments': False,
            'sender_initial': 'P',
            'verification_code': None
        })
    
    # 缓存邮件
    db.cache_emails(test_account, test_emails)
    print(f"✅ 已缓存 {len(test_emails)} 封测试邮件")
    
    # 测试缓存命中
    hit_count = 0
    total_requests = 50
    
    for _ in range(total_requests):
        emails, total = db.get_cached_emails(test_account, page=1, page_size=20)
        if emails:
            hit_count += 1
    
    hit_rate = (hit_count / total_requests) * 100
    print(f"✅ 缓存命中率: {hit_rate:.2f}% ({hit_count}/{total_requests})")
    
    assert hit_rate >= 80, f"缓存命中率应该>=80%，实际为 {hit_rate:.2f}%"
    
    # 清理测试数据
    db.clear_email_cache_db(test_account)
    print("✅ 清理测试数据完成")


def test_response_time():
    """测试响应时间对比"""
    print("\n=== 测试响应时间 ===")
    
    test_account = 'perf-test-time@example.com'
    
    # 准备大量测试数据
    test_emails = []
    for i in range(1000):
        test_emails.append({
            'message_id': f'time-test-{i}',
            'folder': 'INBOX',
            'subject': f'Time Test {i}',
            'from_email': f'sender{i}@example.com',
            'date': datetime.now().isoformat(),
            'is_read': False,
            'has_attachments': False,
            'sender_initial': 'T',
            'verification_code': None
        })
    
    # 测试写入时间
    start_time = time.time()
    db.cache_emails(test_account, test_emails)
    write_time = (time.time() - start_time) * 1000
    print(f"✅ 写入 {len(test_emails)} 条记录耗时: {write_time:.2f}ms")
    
    # 测试读取时间（多次取平均）
    read_times = []
    for _ in range(10):
        start_time = time.time()
        emails, total = db.get_cached_emails(test_account, page=1, page_size=100)
        read_time = (time.time() - start_time) * 1000
        read_times.append(read_time)
    
    avg_read_time = sum(read_times) / len(read_times)
    print(f"✅ 平均读取时间: {avg_read_time:.2f}ms")
    print(f"✅ 最快读取时间: {min(read_times):.2f}ms")
    print(f"✅ 最慢读取时间: {max(read_times):.2f}ms")
    
    assert avg_read_time < 100, f"平均读取时间应该<100ms，实际为 {avg_read_time:.2f}ms"
    
    # 测试搜索性能
    start_time = time.time()
    emails, total = db.get_cached_emails(
        test_account, 
        page=1, 
        page_size=100,
        sender_search='sender5'
    )
    search_time = (time.time() - start_time) * 1000
    print(f"✅ 搜索耗时: {search_time:.2f}ms (找到 {len(emails)} 条)")
    
    assert search_time < 200, f"搜索时间应该<200ms，实际为 {search_time:.2f}ms"
    
    # 清理测试数据
    db.clear_email_cache_db(test_account)
    print("✅ 清理测试数据完成")


def test_compression_ratio():
    """测试压缩率"""
    print("\n=== 测试压缩率 ===")
    
    test_account = 'perf-test-compress@example.com'
    
    # 测试不同大小的文本
    test_sizes = [1000, 5000, 10000, 50000]  # 字节
    
    for size in test_sizes:
        # 生成测试文本
        test_text = generate_random_text(size)
        original_size = len(test_text)
        
        # 压缩
        compressed = db.compress_text(test_text)
        compressed_size = len(compressed) if compressed else 0
        
        # 计算压缩率
        if compressed_size < original_size:
            compression_ratio = (1 - compressed_size / original_size) * 100
            print(f"✅ {original_size:6d} bytes -> {compressed_size:6d} bytes (压缩 {compression_ratio:.1f}%)")
        else:
            print(f"✅ {original_size:6d} bytes -> 未压缩（太小）")
        
        # 验证解压缩
        decompressed = db.decompress_text(compressed)
        assert decompressed == test_text, "解压缩后应该恢复原文本"
    
    # 测试实际邮件详情压缩
    print("\n测试实际邮件详情压缩:")
    
    test_detail = {
        'message_id': 'compress-test-1',
        'subject': 'Compression Test',
        'from_email': 'test@example.com',
        'to_email': 'recipient@example.com',
        'date': datetime.now().isoformat(),
        'body_plain': generate_random_text(10000),
        'body_html': '<html><body>' + generate_random_text(10000) + '</body></html>',
        'verification_code': None
    }
    
    original_body_size = len(test_detail['body_plain']) + len(test_detail['body_html'])
    
    # 缓存（会自动压缩）
    db.cache_email_detail(test_account, test_detail)
    
    # 查询实际存储大小
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT body_size, body_plain, body_html 
            FROM email_details_cache 
            WHERE email_account = ? AND message_id = ?
        """, (test_account, 'compress-test-1'))
        row = cursor.fetchone()
        
        if row:
            stored_size = row[0]
            stored_plain = len(row[1]) if row[1] else 0
            stored_html = len(row[2]) if row[2] else 0
            actual_stored_size = stored_plain + stored_html
            
            compression_ratio = (1 - actual_stored_size / original_body_size) * 100
            print(f"✅ 原始大小: {original_body_size} bytes")
            print(f"✅ 存储大小: {actual_stored_size} bytes")
            print(f"✅ 压缩率: {compression_ratio:.1f}%")
            print(f"✅ 记录的body_size: {stored_size} bytes")
            
            assert compression_ratio > 0, "应该有压缩效果"
    
    # 验证解压缩正确性
    cached_detail = db.get_cached_email_detail(test_account, 'compress-test-1')
    assert cached_detail is not None, "应该能获取缓存"
    assert cached_detail['body_plain'] == test_detail['body_plain'], "纯文本应该正确"
    assert cached_detail['body_html'] == test_detail['body_html'], "HTML应该正确"
    print("✅ 解压缩验证通过")
    
    # 清理测试数据
    db.clear_email_cache_db(test_account)
    print("✅ 清理测试数据完成")


def test_concurrent_access():
    """测试并发访问性能"""
    print("\n=== 测试并发访问性能 ===")
    
    test_account = 'perf-test-concurrent@example.com'
    
    # 准备测试数据
    test_emails = []
    for i in range(500):
        test_emails.append({
            'message_id': f'concurrent-test-{i}',
            'folder': 'INBOX',
            'subject': f'Concurrent Test {i}',
            'from_email': f'sender{i}@example.com',
            'date': datetime.now().isoformat(),
            'is_read': False,
            'has_attachments': False,
            'sender_initial': 'C',
            'verification_code': None
        })
    
    db.cache_emails(test_account, test_emails)
    print(f"✅ 已缓存 {len(test_emails)} 封测试邮件")
    
    # 模拟并发访问（顺序执行，但测试多次访问的性能）
    access_times = []
    for i in range(20):
        start_time = time.time()
        emails, total = db.get_cached_emails(
            test_account,
            page=random.randint(1, 5),
            page_size=100
        )
        access_time = (time.time() - start_time) * 1000
        access_times.append(access_time)
    
    avg_time = sum(access_times) / len(access_times)
    print(f"✅ 平均访问时间: {avg_time:.2f}ms")
    print(f"✅ 最快: {min(access_times):.2f}ms")
    print(f"✅ 最慢: {max(access_times):.2f}ms")
    print(f"✅ 标准差: {(sum((t - avg_time)**2 for t in access_times) / len(access_times))**0.5:.2f}ms")
    
    # 清理测试数据
    db.clear_email_cache_db(test_account)
    print("✅ 清理测试数据完成")


def run_all_tests():
    """运行所有性能测试"""
    print("=" * 60)
    print("缓存性能测试")
    print("=" * 60)
    
    try:
        test_cache_hit_rate()
        test_response_time()
        test_compression_ratio()
        test_concurrent_access()
        
        print("\n" + "=" * 60)
        print("✅ 所有性能测试通过！")
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

