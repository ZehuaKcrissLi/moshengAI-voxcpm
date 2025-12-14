#!/usr/bin/env python3
"""
MoshengAI 数据库管理工具
用法：python manage_db.py <command> [args]
"""
import sqlite3
import sys
from datetime import datetime

DB_PATH = '/scratch/kcriss/MoshengAI/mosheng.db'

def list_users(limit=20):
    """列出所有用户"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT id, email, provider, credits_balance, is_admin, created_at 
        FROM users 
        ORDER BY created_at DESC 
        LIMIT {limit}
    """)
    
    print("\n📊 用户列表")
    print("-" * 110)
    print(f"{'ID':<38} {'邮箱':<30} {'提供商':<10} {'积分':<10} {'管理员':<8} {'创建时间'}")
    print("-" * 110)
    
    for row in cursor.fetchall():
        user_id, email, provider, credits, is_admin, created_at = row
        admin_str = "✅" if is_admin else ""
        print(f"{user_id[:36]:<38} {email:<30} {provider:<10} {credits:<10} {admin_str:<8} {created_at[:19]}")
    
    conn.close()

def add_credits(email, amount):
    """给用户充值"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 先查询当前积分
    cursor.execute("SELECT credits_balance FROM users WHERE email = ?", (email,))
    result = cursor.fetchone()
    if not result:
        print(f"❌ 用户不存在: {email}")
        conn.close()
        return
    
    old_balance = result[0]
    
    cursor.execute("UPDATE users SET credits_balance = credits_balance + ? WHERE email = ?", (amount, email))
    conn.commit()
    
    cursor.execute("SELECT credits_balance FROM users WHERE email = ?", (email,))
    new_balance = cursor.fetchone()[0]
    
    print(f"✅ 充值成功！")
    print(f"   用户: {email}")
    print(f"   原积分: {old_balance}")
    print(f"   充值: {amount}")
    print(f"   新积分: {new_balance}")
    
    conn.close()

def set_admin(email, is_admin=True):
    """设置管理员权限"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_admin = ? WHERE email = ?", (1 if is_admin else 0, email))
    conn.commit()
    if cursor.rowcount > 0:
        print(f"✅ 已将 {email} 设置为{'管理员' if is_admin else '普通用户'}")
    else:
        print(f"❌ 用户不存在: {email}")
    conn.close()

def list_tasks(user_email=None, limit=20):
    """列出任务"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if user_email:
        cursor.execute("""
            SELECT t.id, u.email, t.text, t.status, t.cost, t.created_at
            FROM tasks t
            JOIN users u ON t.user_id = u.id
            WHERE u.email = ?
            ORDER BY t.created_at DESC
            LIMIT ?
        """, (user_email, limit))
    else:
        cursor.execute("""
            SELECT t.id, u.email, t.text, t.status, t.cost, t.created_at
            FROM tasks t
            LEFT JOIN users u ON t.user_id = u.id
            ORDER BY t.created_at DESC
            LIMIT ?
        """, (limit,))
    
    print("\n📝 任务列表")
    print("-" * 130)
    print(f"{'任务ID':<38} {'用户':<25} {'文本':<25} {'状态':<12} {'费用':<8} {'创建时间'}")
    print("-" * 130)
    
    tasks = cursor.fetchall()
    if not tasks:
        print("  暂无任务记录")
    else:
        for row in tasks:
            task_id, email, text, status, cost, created_at = row
            email = email or "匿名"
            text_short = (text[:22] + '...') if len(text) > 25 else text
            print(f"{task_id[:36]:<38} {email:<25} {text_short:<25} {status:<12} {cost:<8} {created_at[:19]}")
    
    conn.close()

def stats():
    """统计信息"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 用户统计
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(credits_balance) FROM users")
    total_credits = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE provider='local'")
    local_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin=1")
    admin_users = cursor.fetchone()[0]
    
    # 任务统计
    cursor.execute("SELECT COUNT(*) FROM tasks")
    total_tasks = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*), status FROM tasks GROUP BY status")
    task_stats = cursor.fetchall()
    
    cursor.execute("SELECT SUM(cost) FROM tasks WHERE status='COMPLETED'")
    total_revenue = cursor.fetchone()[0] or 0
    
    # 今日统计
    cursor.execute("SELECT COUNT(*) FROM users WHERE DATE(created_at) = DATE('now')")
    today_new_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE DATE(created_at) = DATE('now')")
    today_tasks = cursor.fetchone()[0]
    
    print("\n" + "=" * 60)
    print("📊 MoshengAI 系统统计")
    print("=" * 60)
    
    print("\n👥 用户统计")
    print("-" * 60)
    print(f"  总用户数：{total_users:,}")
    print(f"    ├─ 邮箱注册：{local_users:,}")
    print(f"    ├─ OAuth登录：{total_users - local_users:,}")
    print(f"    └─ 管理员：{admin_users:,}")
    print(f"  今日新增：{today_new_users:,}")
    
    print(f"\n💰 积分统计")
    print("-" * 60)
    print(f"  系统总积分池：{total_credits:,}")
    print(f"  已消耗积分：{total_revenue:,}")
    print(f"  平均每用户：{total_credits/total_users if total_users > 0 else 0:.1f}")
    
    print(f"\n📝 任务统计")
    print("-" * 60)
    print(f"  总任务数：{total_tasks:,}")
    for count, status in task_stats:
        print(f"    ├─ {status}: {count:,}")
    print(f"  今日任务：{today_tasks:,}")
    if total_tasks > 0:
        success_count = next((c for c, s in task_stats if s == 'COMPLETED'), 0)
        print(f"  成功率：{success_count/total_tasks*100:.1f}%")
    
    print("\n" + "=" * 60)
    print(f"⏰ 统计时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")
    
    conn.close()

def search_user(keyword):
    """搜索用户"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, email, provider, credits_balance, created_at 
        FROM users 
        WHERE email LIKE ?
        ORDER BY created_at DESC
    """, (f'%{keyword}%',))
    
    print(f"\n🔍 搜索结果：'{keyword}'")
    print("-" * 100)
    results = cursor.fetchall()
    if not results:
        print("  未找到匹配用户")
    else:
        for row in results:
            user_id, email, provider, credits, created_at = row
            print(f"  {email} | 积分: {credits} | 创建: {created_at[:19]}")
    
    conn.close()

def help_info():
    """显示帮助信息"""
    print("""
MoshengAI 数据库管理工具
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 命令列表：

  用户管理：
    list                         列出所有用户
    search <关键词>              搜索用户
    credits <email> <数量>       给用户充值积分
    admin <email>                设置为管理员
    
  任务管理：
    tasks                        列出所有任务
    tasks <email>                列出某用户的任务
    
  系统管理：
    stats                        查看系统统计
    help                         显示此帮助

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 使用示例：

  # 查看所有用户
  python manage_db.py list
  
  # 搜索用户
  python manage_db.py search test
  
  # 给用户充值1000积分
  python manage_db.py credits test@example.com 1000
  
  # 设置管理员
  python manage_db.py admin test@example.com
  
  # 查看统计
  python manage_db.py stats
  
  # 查看所有任务
  python manage_db.py tasks
  
  # 查看某用户的任务
  python manage_db.py tasks test@example.com

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        help_info()
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    try:
        if cmd == 'list':
            list_users()
        elif cmd == 'search':
            if len(sys.argv) < 3:
                print("❌ 用法: python manage_db.py search <关键词>")
                sys.exit(1)
            search_user(sys.argv[2])
        elif cmd == 'tasks':
            user_email = sys.argv[2] if len(sys.argv) > 2 else None
            list_tasks(user_email)
        elif cmd == 'credits':
            if len(sys.argv) < 4:
                print("❌ 用法: python manage_db.py credits <email> <amount>")
                sys.exit(1)
            add_credits(sys.argv[2], int(sys.argv[3]))
        elif cmd == 'admin':
            if len(sys.argv) < 3:
                print("❌ 用法: python manage_db.py admin <email>")
                sys.exit(1)
            set_admin(sys.argv[2])
        elif cmd == 'stats':
            stats()
        elif cmd == 'help':
            help_info()
        else:
            print(f"❌ 未知命令: {cmd}")
            print("运行 'python manage_db.py help' 查看帮助")
            sys.exit(1)
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)

