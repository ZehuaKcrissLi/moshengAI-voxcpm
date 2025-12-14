# MoshengAI 监控运维指南

## 🎯 问题诊断：TTS服务为何不工作

### **当前问题**
```
❌ TTS引擎初始化失败
原因：transformers版本兼容性问题
错误：cannot import name 'isin_mps_friendly' from 'transformers.pytorch_utils'

症状：
- 任务卡在 PROCESSING 状态
- 积分已扣除但音频无法生成
- 前端一直轮询等待
```

### **临时解决方案**
IndexTTS的transformers版本(4.40.0)与最新版本不兼容，需要降级或等待IndexTTS更新。

---

## 📊 监控系统使用指南

我为你创建了**三种**监控方式：

### **方式1：实时监控仪表板（推荐）**

#### 启动监控面板
```bash
cd /scratch/kcriss/MoshengAI
source .venv/bin/activate
python3 monitor_dashboard.py
```

#### 功能特性
- ✅ 每5秒自动刷新
- ✅ 服务状态（后端/前端/TTS/数据库）
- ✅ CPU/内存/磁盘使用率
- ✅ GPU状态（温度/利用率/显存）
- ✅ 数据库统计（用户/任务/积分）
- ✅ 最近任务列表
- ✅ 健康评分和问题列表

#### 界面示例
```
================================================================================
                        MoshengAI 系统监控仪表板
================================================================================
⏰ 更新时间: 2025-12-13 04:30:15
🟡 系统健康评分: 70/100 (DEGRADED)
================================================================================

📊 服务状态:
  ✅ 后端服务 (FastAPI)
  ✅ 前端服务 (Next.js)
  ❌ TTS引擎
  ✅ 数据库

💻 系统资源:
  CPU: 15.3%
  内存: 12.5GB / 64.0GB (19.5%)
  磁盘: 450.2GB / 1000.0GB (45.0%)

🎮 GPU状态:
  GPU 0: NVIDIA GeForce RTX 3090
    温度: 45°C | 利用率: 0%
    显存: 0.5GB / 24.0GB (2.1%)

📚 数据库统计:
  用户总数: 4
  积分池: 400
  今日任务: 2
  数据库大小: 0.02MB

⚠️  当前问题:
  • TTS引擎未运行
```

---

### **方式2：API接口监控**

#### 健康检查端点
```bash
# 简单健康检查
curl http://localhost:8000/health

# 详细健康检查
curl http://localhost:8000/monitor/health/detailed | python3 -m json.tool

# 系统资源
curl http://localhost:8000/monitor/system | python3 -m json.tool

# 服务状态
curl http://localhost:8000/monitor/services | python3 -m json.tool

# 数据库统计
curl http://localhost:8000/monitor/stats/database | python3 -m json.tool
```

#### 返回示例
```json
{
  "status": "degraded",
  "health_score": 70,
  "issues": [
    "TTS引擎未运行"
  ],
  "system": {
    "cpu_percent": 15.3,
    "memory_percent": 19.5,
    "gpu_available": true,
    "gpu_info": [...]
  },
  "services": {
    "backend": true,
    "frontend": true,
    "tts_engine": false,
    "database": true
  }
}
```

---

### **方式3：日志查看**

#### 后端日志
```bash
# 实时查看
tail -f /tmp/backend.log

# 查看最近100行
tail -100 /tmp/backend.log

# 查看错误
tail -200 /tmp/backend.log | grep -i error

# API查看
curl http://localhost:8000/monitor/logs/backend?lines=50
```

#### 前端日志
```bash
# 实时查看
tail -f /tmp/frontend.log

# API查看
curl http://localhost:8000/monitor/logs/frontend?lines=50
```

#### 常用日志命令
```bash
# 查看TTS相关日志
grep -i tts /tmp/backend.log | tail -20

# 查看今天的错误
grep -i error /tmp/backend.log | grep "$(date +%Y-%m-%d)"

# 统计HTTP状态码
grep "HTTP/1.1" /tmp/backend.log | awk '{print $9}' | sort | uniq -c

# 查看最慢的请求
grep "in [0-9]" /tmp/backend.log | sort -t' ' -k7 -n | tail -10
```

---

## 🖥️ 系统资源监控

### **GPU监控**

#### 实时监控
```bash
# 每秒刷新
watch -n 1 nvidia-smi

# 简洁模式
watch -n 1 'nvidia-smi --query-gpu=temperature.gpu,utilization.gpu,memory.used,memory.total --format=csv'
```

#### GPU使用历史
```bash
# 记录GPU使用情况
while true; do
  echo "$(date +%Y-%m-%d\ %H:%M:%S) $(nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader,nounits)" >> /tmp/gpu_usage.log
  sleep 60
done &
```

### **CPU/内存监控**

```bash
# htop（推荐）
htop

# top
top

# 查看进程资源
ps aux --sort=-%mem | head -20  # 内存占用最高
ps aux --sort=-%cpu | head -20  # CPU占用最高
```

### **磁盘监控**

```bash
# 磁盘使用
df -h

# 查找大文件
du -h /scratch/kcriss/MoshengAI | sort -h | tail -20

# inode使用
df -i
```

---

## 📈 监控脚本集合

### **创建系统监控脚本**

```bash
cat > /scratch/kcriss/MoshengAI/check_system.sh << 'EOF'
#!/bin/bash
echo "🔍 MoshengAI 系统快速检查"
echo "================================"

# 后端
if pgrep -f "uvicorn.*8000" > /dev/null; then
    echo "✅ 后端运行中"
else
    echo "❌ 后端未运行"
fi

# 前端
if ss -tlnp 2>/dev/null | grep -q :3000; then
    echo "✅ 前端运行中"
else
    echo "❌ 前端未运行"
fi

# GPU
if command -v nvidia-smi >/dev/null 2>&1; then
    GPU_UTIL=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | head -1)
    echo "🎮 GPU利用率: ${GPU_UTIL}%"
else
    echo "⚠️  GPU不可用"
fi

# 数据库
if [ -f /scratch/kcriss/MoshengAI/mosheng.db ]; then
    DB_SIZE=$(du -h /scratch/kcriss/MoshengAI/mosheng.db | cut -f1)
    echo "💾 数据库大小: $DB_SIZE"
else
    echo "❌ 数据库文件不存在"
fi

# 磁盘
DISK_USAGE=$(df -h /scratch | awk 'NR==2 {print $5}')
echo "💿 磁盘使用: $DISK_USAGE"

echo "================================"
EOF

chmod +x /scratch/kcriss/MoshengAI/check_system.sh
```

---

## 🚨 告警设置

### **创建告警脚本**

```bash
cat > /scratch/kcriss/MoshengAI/alert_monitor.sh << 'EOF'
#!/bin/bash
# 监控关键指标并发送告警

# CPU阈值
CPU_THRESHOLD=90
# 内存阈值
MEM_THRESHOLD=90
# GPU温度阈值
GPU_TEMP_THRESHOLD=85

while true; do
    # 检查CPU
    CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    if (( $(echo "$CPU > $CPU_THRESHOLD" | bc -l) )); then
        echo "⚠️  [$(date)] CPU使用率过高: ${CPU}%" >> /tmp/alerts.log
    fi
    
    # 检查内存
    MEM=$(free | grep Mem | awk '{print ($3/$2) * 100.0}')
    if (( $(echo "$MEM > $MEM_THRESHOLD" | bc -l) )); then
        echo "⚠️  [$(date)] 内存使用率过高: ${MEM}%" >> /tmp/alerts.log
    fi
    
    # 检查GPU温度
    if command -v nvidia-smi >/dev/null 2>&1; then
        GPU_TEMP=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits | head -1)
        if [ "$GPU_TEMP" -gt "$GPU_TEMP_THRESHOLD" ]; then
            echo "🔥 [$(date)] GPU温度过高: ${GPU_TEMP}°C" >> /tmp/alerts.log
        fi
    fi
    
    sleep 60
done
EOF

chmod +x /scratch/kcriss/MoshengAI/alert_monitor.sh
```

运行告警监控：
```bash
nohup /scratch/kcriss/MoshengAI/alert_monitor.sh > /dev/null 2>&1 &
```

查看告警：
```bash
tail -f /tmp/alerts.log
```

---

## 📊 性能分析

### **请求性能分析**

```bash
# 分析请求响应时间
grep "GET\|POST" /tmp/backend.log | \
  awk '{print $NF}' | \
  sort -n | \
  awk '{sum+=$1; count++} END {print "平均响应时间:", sum/count*1000, "ms"}'
```

### **任务成功率**

```bash
cd /scratch/kcriss/MoshengAI
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('mosheng.db')
cursor = conn.cursor()

cursor.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status")
stats = {row[0]: row[1] for row in cursor.fetchall()}

total = sum(stats.values())
if total > 0:
    success_rate = (stats.get('COMPLETED', 0) / total) * 100
    print(f"任务成功率: {success_rate:.1f}%")
    print(f"总任务: {total}")
    for status, count in stats.items():
        print(f"  {status}: {count} ({count/total*100:.1f}%)")

conn.close()
EOF
```

---

## 🛠️ 故障排查流程

### **1. 后端无响应**
```bash
# 检查进程
ps aux | grep uvicorn

# 查看日志
tail -50 /tmp/backend.log

# 重启后端
pkill -f "uvicorn.*8000"
cd /scratch/kcriss/MoshengAI
source .venv/bin/activate
nohup python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
```

### **2. TTS生成失败**
```bash
# 检查TTS引擎日志
grep -i "tts\|transform" /tmp/backend.log | tail -20

# 检查任务状态
python3 manage_db.py tasks

# 检查GPU
nvidia-smi
```

### **3. 数据库锁死**
```bash
# 检查数据库大小
ls -lh /scratch/kcriss/MoshengAI/mosheng.db

# 优化数据库
cd /scratch/kcriss/MoshengAI
source .venv/bin/activate
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('mosheng.db')
conn.execute('VACUUM')
conn.close()
print("✅ 数据库已优化")
EOF
```

---

## 📅 定时监控任务

### **设置cron任务**

```bash
# 编辑crontab
crontab -e

# 添加以下内容：

# 每小时记录系统状态
0 * * * * /scratch/kcriss/MoshengAI/check_system.sh >> /tmp/system_history.log 2>&1

# 每天凌晨2点备份数据库
0 2 * * * cp /scratch/kcriss/MoshengAI/mosheng.db /scratch/kcriss/MoshengAI/backups/mosheng_$(date +\%Y\%m\%d).db

# 每天凌晨3点清理7天前的日志
0 3 * * * find /tmp -name "*.log" -mtime +7 -delete
```

---

## 🎯 快速命令参考

| 功能 | 命令 |
|------|------|
| **监控仪表板** | `python3 monitor_dashboard.py` |
| **查看后端日志** | `tail -f /tmp/backend.log` |
| **查看前端日志** | `tail -f /tmp/frontend.log` |
| **GPU监控** | `watch -n 1 nvidia-smi` |
| **系统检查** | `./check_system.sh` |
| **数据库统计** | `python3 manage_db.py stats` |
| **健康检查API** | `curl localhost:8000/monitor/health/detailed` |
| **查看进程** | `htop` |

---

**监控系统已就绪！现在你可以随时掌握系统状态。** 🚀




