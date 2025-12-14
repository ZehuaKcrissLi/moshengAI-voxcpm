# 数据库管理指南

## 📊 当前项目数据库情况

### 数据库位置
- **路径**：`/scratch/kcriss/MoshengAI/mosheng.db`
- **类型**：SQLite 3
- **大小**：可以用 `ls -lh mosheng.db` 查看

### 数据表结构
```
users (用户表)
├── id              - 主键 (UUID)
├── email           - 邮箱 (唯一)
├── hashed_password - 加密密码
├── provider        - 登录方式 (local/google/github/wechat)
├── provider_user_id - OAuth用户ID
├── avatar          - 头像URL
├── credits_balance - 积分余额
├── is_admin        - 是否管理员
└── created_at      - 创建时间

tasks (任务表)
├── id              - 主键 (UUID)
├── user_id         - 用户ID (外键)
├── text            - 生成文本
├── voice_path      - 音色路径
├── status          - 状态 (PENDING/PROCESSING/COMPLETED/FAILED)
├── cost            - 消耗积分
├── output_url      - 生成音频URL
├── error_message   - 错误信息
├── created_at      - 创建时间
└── completed_at    - 完成时间
```

---

## 🛠️ 方式1：命令行管理（当前可用）

### 使用Python脚本
创建管理脚本 `manage_db.py`：

```python
#!/usr/bin/env python3
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
    print("-" * 100)
    print(f"{'ID':<40} {'邮箱':<30} {'提供商':<10} {'积分':<10} {'管理员':<8} {'创建时间'}")
    print("-" * 100)
    
    for row in cursor.fetchall():
        user_id, email, provider, credits, is_admin, created_at = row
        admin_str = "✅" if is_admin else ""
        print(f"{user_id[:36]:<40} {email:<30} {provider:<10} {credits:<10} {admin_str:<8} {created_at[:19]}")
    
    conn.close()

def add_credits(email, amount):
    """给用户充值"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET credits_balance = credits_balance + ? WHERE email = ?", (amount, email))
    conn.commit()
    if cursor.rowcount > 0:
        print(f"✅ 成功给 {email} 充值 {amount} 积分")
    else:
        print(f"❌ 用户不存在: {email}")
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
    print("-" * 120)
    print(f"{'任务ID':<40} {'用户':<25} {'文本':<25} {'状态':<12} {'费用':<8} {'创建时间'}")
    print("-" * 120)
    
    for row in cursor.fetchall():
        task_id, email, text, status, cost, created_at = row
        email = email or "匿名"
        text_short = (text[:22] + '...') if len(text) > 25 else text
        print(f"{task_id[:36]:<40} {email:<25} {text_short:<25} {status:<12} {cost:<8} {created_at[:19]}")
    
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
    
    # 任务统计
    cursor.execute("SELECT COUNT(*) FROM tasks")
    total_tasks = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*), status FROM tasks GROUP BY status")
    task_stats = cursor.fetchall()
    
    cursor.execute("SELECT SUM(cost) FROM tasks WHERE status='COMPLETED'")
    total_revenue = cursor.fetchone()[0] or 0
    
    print("\n📊 系统统计")
    print("-" * 60)
    print(f"总用户数：{total_users}")
    print(f"  - 邮箱注册：{local_users}")
    print(f"  - OAuth登录：{total_users - local_users}")
    print(f"\n总积分池：{total_credits:,}")
    print(f"\n总任务数：{total_tasks}")
    for count, status in task_stats:
        print(f"  - {status}: {count}")
    print(f"\n总收入（已消耗积分）：{total_revenue:,}")
    print("-" * 60)
    
    conn.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python manage_db.py list                    # 列出用户")
        print("  python manage_db.py tasks                   # 列出任务")
        print("  python manage_db.py tasks user@email.com    # 列出某用户的任务")
        print("  python manage_db.py credits user@email.com 100  # 充值")
        print("  python manage_db.py admin user@email.com    # 设为管理员")
        print("  python manage_db.py stats                   # 统计信息")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'list':
        list_users()
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
    else:
        print(f"❌ 未知命令: {cmd}")
```

### 使用示例
```bash
cd /scratch/kcriss/MoshengAI

# 列出所有用户
source .venv/bin/activate
python manage_db.py list

# 给用户充值
python manage_db.py credits test@example.com 1000

# 设置管理员
python manage_db.py admin test@example.com

# 查看统计
python manage_db.py stats

# 列出所有任务
python manage_db.py tasks

# 列出某用户的任务
python manage_db.py tasks test@example.com
```

---

## 🖥️ 方式2：SQLite GUI工具

### 选项A：DB Browser for SQLite（推荐）
**最流行的SQLite可视化工具**

**安装**：
```bash
# Ubuntu/Debian
sudo apt install sqlitebrowser

# macOS
brew install --cask db-browser-for-sqlite

# Windows
# 下载：https://sqlitebrowser.org/
```

**使用**：
1. 打开 DB Browser
2. File → Open Database → 选择 `mosheng.db`
3. 可视化查看、编辑、导出数据

### 选项B：在线工具
```bash
# 下载数据库到本地
scp kcriss@10.212.227.125:/scratch/kcriss/MoshengAI/mosheng.db ./

# 使用在线工具打开
# https://sqliteviewer.app/
# https://inloop.github.io/sqlite-viewer/
```

---

## 🌐 方式3：Web管理后台（生产环境推荐）

### 选项A：自建管理后台

创建 `backend/app/routers/admin.py`：

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.deps import get_current_admin_user
from backend.app.db.database import get_db
from backend.app.db.models import User, Task

router = APIRouter()

@router.get("/users")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理员：列出所有用户"""
    from sqlalchemy.future import select
    result = await db.execute(
        select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    return users

@router.patch("/users/{user_id}/credits")
async def update_user_credits(
    user_id: str,
    credits_delta: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理员：修改用户积分"""
    from backend.app.db.crud_user import update_user_credits
    user = await update_user_credits(db, user_id, credits_delta)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# ... 更多管理接口
```

### 选项B：使用现成的管理框架

#### 1. **FastAPI Admin**
```bash
pip install fastapi-admin
```

#### 2. **SQLAdmin**（推荐）
```python
# 安装
pip install sqladmin

# 在 main.py 中添加
from sqladmin import Admin, ModelView
from backend.app.db.models import User, Task

admin = Admin(app, engine)

class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.credits_balance, User.created_at]
    can_create = False
    can_edit = True
    can_delete = False

class TaskAdmin(ModelView, model=Task):
    column_list = [Task.id, Task.user_id, Task.status, Task.cost, Task.created_at]
    can_create = False
    can_edit = True
    can_delete = False

admin.add_view(UserAdmin)
admin.add_view(TaskAdmin)

# 访问：http://localhost:8000/admin
```

#### 3. **Django Admin**（如果你更喜欢Django）
很多公司用Django专门做管理后台，FastAPI做API服务。

---

## 🏢 生产环境最佳实践

### 1. **数据库选择**

#### MVP阶段（当前）
- ✅ **SQLite**：简单、够用、零配置
- 适合：< 100k 用户，< 10 请求/秒

#### 成长阶段
- ✅ **PostgreSQL**：最推荐
  - 可靠、功能强大、开源
  - 支持JSON、全文搜索、地理位置等
  - 大公司常用：Instagram、Uber、Spotify

```python
# 切换到PostgreSQL只需修改.env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/mosheng
```

#### 大规模阶段
- ✅ **PostgreSQL主从复制**
- ✅ **MySQL（如果团队更熟悉）**
- ✅ **数据库集群**（PgBouncer、Patroni）

### 2. **管理工具选择**

| 阶段 | 工具 | 适用场景 |
|------|------|---------|
| **开发** | Python脚本 | 快速调试 |
| **内部** | DB Browser / Adminer | 技术团队使用 |
| **运营** | 自建后台 | 运营人员充值、查询 |
| **生产** | SQLAdmin / 定制后台 | 完整权限管理 |

### 3. **常见管理需求**

```python
# 用户管理
- 查看用户列表（搜索、过滤、排序）
- 手动充值积分
- 设置管理员权限
- 查看用户消费记录
- 封禁/解封用户

# 任务管理
- 查看所有生成任务
- 失败任务重试
- 删除违规内容
- 查看热门文本

# 财务管理
- 充值记录
- 消费统计
- 收入报表

# 系统监控
- 数据库大小
- 活跃用户数
- 任务成功率
- 平均生成时间
```

### 4. **安全建议**

```python
# ✅ 必须做
1. 管理后台必须登录认证
2. 只有管理员可访问
3. 所有操作记录日志
4. 敏感操作二次确认
5. 定期备份数据库

# ⚠️ 不要做
1. 不要直接暴露管理后台到公网
2. 不要使用默认密码
3. 不要给所有人管理员权限
4. 不要在生产环境随意删除数据
```

---

## 💾 数据备份方案

### 自动备份脚本
```bash
#!/bin/bash
# backup_db.sh

DB_PATH="/scratch/kcriss/MoshengAI/mosheng.db"
BACKUP_DIR="/scratch/kcriss/MoshengAI/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/mosheng_$DATE.db"

mkdir -p $BACKUP_DIR

# 备份
cp $DB_PATH $BACKUP_FILE

# 压缩
gzip $BACKUP_FILE

# 只保留最近7天的备份
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "✅ 备份完成: $BACKUP_FILE.gz"
```

### 定时备份（crontab）
```bash
# 每天凌晨3点备份
0 3 * * * /scratch/kcriss/MoshengAI/backup_db.sh
```

---

## 🔍 常用SQL查询

```sql
-- 查看用户总数
SELECT COUNT(*) FROM users;

-- 查看活跃用户（有任务的用户）
SELECT DISTINCT u.email, COUNT(t.id) as task_count
FROM users u
JOIN tasks t ON u.id = t.user_id
GROUP BY u.email
ORDER BY task_count DESC;

-- 查看收入统计
SELECT 
    DATE(created_at) as date,
    COUNT(*) as tasks,
    SUM(cost) as revenue
FROM tasks
WHERE status = 'COMPLETED'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- 查找大户（消费最多的用户）
SELECT u.email, SUM(t.cost) as total_spent
FROM users u
JOIN tasks t ON u.id = t.user_id
WHERE t.status = 'COMPLETED'
GROUP BY u.email
ORDER BY total_spent DESC
LIMIT 10;

-- 查看失败任务
SELECT u.email, t.text, t.error_message, t.created_at
FROM tasks t
JOIN users u ON t.user_id = u.id
WHERE t.status = 'FAILED'
ORDER BY t.created_at DESC;
```

---

## 📊 推荐的管理流程

### 日常运营
1. **早上**：查看统计 `python manage_db.py stats`
2. **处理工单**：用户充值、问题排查
3. **监控任务**：检查失败率
4. **晚上**：备份数据库

### 每周
1. 分析用户增长趋势
2. 查看热门音色
3. 优化性能瓶颈
4. 更新统计报表

### 每月
1. 财务对账
2. 清理过期数据
3. 数据库优化（VACUUM、索引）
4. 备份归档

---

## 🚀 快速开始

创建管理工具：
```bash
cd /scratch/kcriss/MoshengAI
cat > manage_db.py << 'EOF'
[上面的Python脚本内容]
EOF

chmod +x manage_db.py

# 试试看
python manage_db.py stats
```

---

**总结**：
- **现在（MVP）**：Python脚本 + SQLite够用
- **短期（运营）**：加个SQLAdmin web界面
- **长期（规模化）**：PostgreSQL + 定制后台 + 监控系统

需要我帮你实现哪个方案？

