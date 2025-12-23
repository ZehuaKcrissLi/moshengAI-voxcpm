# 🎯 监控系统使用总结

## 📊 你现在有4种监控方式

### **1️⃣ 实时监控仪表板（最推荐）**
```bash
cd /scratch/kcriss/MoshengAI
source .venv/bin/activate
python3 monitor_dashboard.py
```
- 每5秒自动刷新
- 显示服务状态、CPU/内存/GPU、数据库统计
- 按 Ctrl+C 退出

---

### **2️⃣ 快速状态检查**
```bash
./quick_check.sh
```
- 1秒钟快速查看所有服务状态
- 适合快速诊断问题

---

### **3️⃣ Web API监控**
```bash
# 健康检查
curl http://localhost:38000/monitor/health/detailed | python3 -m json.tool

# 系统资源
curl http://localhost:38000/monitor/system | python3 -m json.tool

# 服务状态
curl http://localhost:38000/monitor/services | python3 -m json.tool

# 数据库统计
curl http://localhost:38000/monitor/stats/database | python3 -m json.tool

# 查看后端日志
curl http://localhost:38000/monitor/logs/backend?lines=50

# 查看前端日志
curl http://localhost:38000/monitor/logs/frontend?lines=50
```

---

### **4️⃣ 数据库管理工具**
```bash
# 系统统计
python3 manage_db.py stats

# 列出用户
python3 manage_db.py list

# 查看任务
python3 manage_db.py tasks

# 给用户充值
python3 manage_db.py credits test@example.com 1000
```

---

## 📝 日志查看位置

### **后端日志**
```bash
# 实时查看
tail -f /tmp/backend.log

# 查看最近100行
tail -100 /tmp/backend.log

# 查看错误
grep -i error /tmp/backend.log | tail -20

# 查看TTS相关
grep -i tts /tmp/backend.log | tail -20
```

### **前端日志**
```bash
# 实时查看
tail -f /tmp/frontend.log

# 查看最近50行
tail -50 /tmp/frontend.log
```

### **系统日志**
```bash
# 查看系统消息
dmesg | tail -50

# 查看服务日志
journalctl -u your-service -n 50
```

---

## 🚨 当前问题诊断

### **TTS服务不工作的原因**

**问题**：
```
❌ TTS引擎初始化失败
错误：cannot import name 'isin_mps_friendly' from 'transformers.pytorch_utils'
```

**根本原因**：
- IndexTTS要求 `transformers==4.40.0`
- 这个版本与最新的transformers API不兼容
- 缺少 `isin_mps_friendly` 函数

**解决方案**（3选1）：

#### **方案1：等待IndexTTS更新（推荐）**
- IndexTTS团队会修复兼容性问题
- 关注项目更新：https://github.com/X-LANCE/Index-TTS

#### **方案2：降级transformers到4.36.0**
```bash
cd /scratch/kcriss/MoshengAI
source .venv/bin/activate

# 备份当前环境
cp pyproject.toml pyproject.toml.backup

# 修改transformers版本
sed -i 's/transformers==4.40.0/transformers==4.36.0/' pyproject.toml

# 重新安装
uv sync

# 重启后端
pkill -f "uvicorn.*38000"
nohup python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 38000 > /tmp/backend.log 2>&1 &

# 查看日志确认TTS是否初始化成功
tail -f /tmp/backend.log
```

#### **方案3：暂时禁用TTS功能测试其他部分**
认证、积分、数据库管理功能都正常工作，可以先完善其他部分。

---

## 🔄 任务卡住问题处理

**症状**：
- 任务状态一直是 PROCESSING
- 积分已扣除
- 前端一直轮询等待

**解决**：
```bash
# 1. 查看卡住的任务
python3 manage_db.py tasks

# 2. 手动标记为失败（需要手动编辑数据库）
cd /scratch/kcriss/MoshengAI
source .venv/bin/activate
python3 << 'EOF'
import sqlite3
from datetime import datetime

conn = sqlite3.connect('mosheng.db')
cursor = conn.cursor()

# 将所有PROCESSING状态的任务标记为FAILED
cursor.execute("""
    UPDATE tasks 
    SET status = 'FAILED', 
        error_message = 'TTS引擎未运行',
        completed_at = ?
    WHERE status = 'PROCESSING'
""", (datetime.now().isoformat(),))

affected = cursor.rowcount
conn.commit()
conn.close()

print(f"✅ 已将 {affected} 个卡住的任务标记为失败")
EOF

# 3. 可选：退还积分
python3 << 'EOF'
import sqlite3

conn = sqlite3.connect('mosheng.db')
cursor = conn.cursor()

# 获取失败任务的用户和费用
cursor.execute("""
    SELECT user_id, SUM(cost) 
    FROM tasks 
    WHERE status = 'FAILED' AND error_message = 'TTS引擎未运行'
    GROUP BY user_id
""")

for user_id, total_cost in cursor.fetchall():
    cursor.execute("""
        UPDATE users 
        SET credits_balance = credits_balance + ?
        WHERE id = ?
    """, (total_cost, user_id))
    print(f"✅ 已退还用户 {user_id[:20]}... {total_cost} 积分")

conn.commit()
conn.close()
EOF
```

---

## 🖥️ GPU/CPU/内存监控

### **GPU实时监控**
```bash
# 方式1：nvidia-smi实时更新
watch -n 1 nvidia-smi

# 方式2：简洁模式
watch -n 1 'nvidia-smi --query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.total --format=csv'

# 方式3：记录GPU使用历史
while true; do
  echo "$(date +%Y-%m-%d\ %H:%M:%S) $(nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader,nounits)" >> /tmp/gpu_history.log
  sleep 60
done &

# 查看历史
tail -f /tmp/gpu_history.log
```

### **CPU/内存监控**
```bash
# htop（最推荐）
htop

# top
top

# 查看内存占用最高的进程
ps aux --sort=-%mem | head -20

# 查看CPU占用最高的进程
ps aux --sort=-%cpu | head -20
```

### **磁盘监控**
```bash
# 磁盘使用
df -h

# 查找大文件
du -h /scratch/kcriss/MoshengAI | sort -h | tail -20

# 查看inode使用
df -i
```

---

## 🛠️ 常用维护命令

### **重启服务**
```bash
# 重启后端
pkill -f "uvicorn.*38000"
cd /scratch/kcriss/MoshengAI
source .venv/bin/activate
nohup python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 38000 > /tmp/backend.log 2>&1 &

# 重启前端
pkill -f "next dev"
cd /scratch/kcriss/MoshengAI/frontend
nohup npm run dev > /tmp/frontend.log 2>&1 &
```

### **检查端口占用**
```bash
# 查看8000端口
ss -tlnp | grep 38000

# 查看3000端口
ss -tlnp | grep 33000

# 查看所有监听端口
ss -tlnp
```

### **清理日志**
```bash
# 清空日志（保留文件）
> /tmp/backend.log
> /tmp/frontend.log

# 或删除日志
rm /tmp/backend.log /tmp/frontend.log
```

### **数据库维护**
```bash
# 数据库优化
cd /scratch/kcriss/MoshengAI
source .venv/bin/activate
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('mosheng.db')
conn.execute('VACUUM')
conn.close()
print("✅ 数据库已优化")
EOF

# 备份数据库
cp mosheng.db mosheng_backup_$(date +%Y%m%d).db
```

---

## 📋 快速参考卡

| 功能 | 命令 |
|------|------|
| **实时监控仪表板** | `python3 monitor_dashboard.py` |
| **快速状态检查** | `./quick_check.sh` |
| **查看后端日志** | `tail -f /tmp/backend.log` |
| **查看前端日志** | `tail -f /tmp/frontend.log` |
| **GPU监控** | `watch -n 1 nvidia-smi` |
| **CPU/内存监控** | `htop` |
| **数据库统计** | `python3 manage_db.py stats` |
| **健康检查API** | `curl localhost:38000/monitor/health/detailed` |
| **查看任务** | `python3 manage_db.py tasks` |
| **给用户充值** | `python3 manage_db.py credits EMAIL AMOUNT` |

---

## 🎯 下一步行动

### **立即可做**
1. ✅ 运行 `./quick_check.sh` 查看当前状态
2. ✅ 运行 `python3 monitor_dashboard.py` 实时监控
3. ✅ 检查日志：`tail -f /tmp/backend.log`

### **修复TTS（可选）**
1. 尝试降级transformers（方案2）
2. 或等待IndexTTS更新
3. 或先完善认证和积分系统

### **优化系统**
1. 设置定时备份（cron任务）
2. 配置告警脚本
3. 添加性能监控

---

**所有监控工具已就绪！祝你运维顺利！** 🚀











