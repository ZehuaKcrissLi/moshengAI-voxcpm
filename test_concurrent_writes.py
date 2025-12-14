#!/usr/bin/env python3
"""
测试SQLite并发写入性能
模拟多用户同时注册
"""
import sqlite3
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import random

DB_PATH = '/scratch/kcriss/MoshengAI/test_concurrent.db'

def init_db():
    """初始化测试数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def register_user(user_id):
    """模拟用户注册"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        cursor = conn.cursor()
        
        start = time.time()
        email = f"user{user_id}@test.com"
        cursor.execute("INSERT INTO test_users (email) VALUES (?)", (email,))
        conn.commit()
        duration = time.time() - start
        
        conn.close()
        return True, duration
    except Exception as e:
        return False, str(e)

def test_concurrent_writes(num_users=50, num_threads=10):
    """测试并发写入"""
    print(f"\n{'='*60}")
    print(f"🧪 并发写入测试")
    print(f"{'='*60}")
    print(f"模拟用户数：{num_users}")
    print(f"并发线程数：{num_threads}")
    print(f"{'='*60}\n")
    
    # 清空测试表
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM test_users")
    conn.commit()
    conn.close()
    
    # 开始测试
    start_time = time.time()
    results = []
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(register_user, i) for i in range(num_users)]
        for future in futures:
            results.append(future.result())
    
    total_time = time.time() - start_time
    
    # 统计
    success_count = sum(1 for r, _ in results if r)
    failed_count = num_users - success_count
    durations = [d for r, d in results if r and isinstance(d, float)]
    
    print(f"📊 测试结果")
    print(f"{'-'*60}")
    print(f"总耗时：{total_time:.3f} 秒")
    print(f"成功：{success_count}/{num_users}")
    print(f"失败：{failed_count}/{num_users}")
    print(f"\n⚡ 性能指标")
    print(f"{'-'*60}")
    print(f"平均每次写入：{sum(durations)/len(durations)*1000:.2f} 毫秒")
    print(f"最快写入：{min(durations)*1000:.2f} 毫秒")
    print(f"最慢写入：{max(durations)*1000:.2f} 毫秒")
    print(f"吞吐量：{num_users/total_time:.1f} 次/秒")
    print(f"{'='*60}\n")
    
    # 验证数据
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM test_users")
    actual_count = cursor.fetchone()[0]
    conn.close()
    
    print(f"✅ 数据库实际记录数：{actual_count}")
    
    if actual_count == num_users:
        print(f"✅ 所有记录都成功写入，无冲突！\n")
    else:
        print(f"⚠️  期望 {num_users} 条，实际 {actual_count} 条\n")

if __name__ == '__main__':
    import os
    
    # 确保测试数据库存在
    init_db()
    
    # 测试不同并发级别
    print("\n" + "="*60)
    print("SQLite 并发性能测试")
    print("="*60)
    
    # 测试1：10个用户，5个并发
    test_concurrent_writes(num_users=10, num_threads=5)
    
    # 测试2：50个用户，10个并发
    test_concurrent_writes(num_users=50, num_threads=10)
    
    # 测试3：100个用户，20个并发
    test_concurrent_writes(num_users=100, num_threads=20)
    
    # 清理
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("✅ 测试完成，已清理测试数据库")

