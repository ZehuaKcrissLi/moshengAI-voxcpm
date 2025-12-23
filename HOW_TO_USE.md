# 🚀 MoshengAI 使用指南

## 📱 立即开始

### 1️⃣ 启动所有服务
```bash
cd /scratch/kcriss/MoshengAI
./START_ALL_SERVICES.sh
```

等待15-20秒，看到：
```
✅ 启动完成！
  主应用: http://localhost:33000
  后端API: http://localhost:38000/docs
  监控面板: http://localhost:33001
```

---

### 2️⃣ 访问监控面板

**监控面板地址**: `http://localhost:33001`

如果通过SSH：
```bash
ssh -L 33001:localhost:33001 -L 33000:localhost:33000 -L 38000:localhost:38000 kcriss@10.212.227.125
```

在浏览器打开: `http://localhost:33001`

**你将看到**：
- 🟢/🔴 服务状态指示灯
- 📊 CPU/内存/GPU实时图表
- 📝 后端和前端日志滚动显示
- 📈 数据库统计（用户数/任务数/积分）
- 🎯 系统健康评分

---

### 3️⃣ 测试主应用

访问 `http://localhost:33000`

**测试流程**：
1. 点击右上角 "Log in"
2. 点击 "Sign Up" 注册
3. 输入：
   - Email: `your@email.com`
   - Password: `yourpassword123`（至少8位）
4. 点击 "Sign Up"
5. ✅ 自动登录，左侧显示100 credits

---

## 📊 查看系统状态

### 快速检查
```bash
./quick_check.sh
```

输出示例：
```
✅ 后端运行中 (8000端口)
✅ 前端运行中 (3000端口)
⚠️ TTS引擎未运行（兼容性问题）
🎮 GPU利用率: 0%
💾 数据库: 24K
```

---

### 查看数据库
```bash
python3 manage_db.py stats
```

输出示例：
```
📊 MoshengAI 系统统计
━━━━━━━━━━━━━━━━━━━━━━
👥 用户统计
  总用户数：4
  今日新增：4
💰 积分统计
  系统总积分池：400
  已消耗积分：0
```

---

### 查看日志
```bash
# 后端日志
tail -f /tmp/backend.log

# 查看错误
grep -i error /tmp/backend.log | tail -20

# 查看TTS相关
grep -i tts /tmp/backend.log | tail -20
```

---

## 🛠️ 常用操作

### 给用户充值
```bash
python3 manage_db.py credits test@example.com 1000
```

### 设置管理员
```bash
python3 manage_db.py admin test@example.com
```

### 查看用户列表
```bash
python3 manage_db.py list
```

### 查看任务
```bash
python3 manage_db.py tasks
```

### 搜索用户
```bash
python3 manage_db.py search test
```

---

## 🔧 故障排查

### 服务无法启动
```bash
# 停止所有服务
./STOP_ALL_SERVICES.sh

# 清理进程
pkill -f "uvicorn\|next dev\|monitor_web"

# 重新启动
./START_ALL_SERVICES.sh

# 查看日志
tail -f /tmp/backend.log
```

### 端口被占用
```bash
# 查看占用情况
ss -tlnp | grep -E ":(33000|33001|38000)"

# 杀死进程
lsof -ti:38000 | xargs kill -9
lsof -ti:33000 | xargs kill -9
lsof -ti:33001 | xargs kill -9
```

### TTS不工作
**这是已知问题**，原因：transformers版本兼容性

**临时方案**：
- 系统其他功能（注册/登录/积分）完全正常
- 可以先完善UI和业务逻辑
- TTS问题需要进一步调试或等待IndexTTS更新

---

## 📈 系统监控

### Web监控面板（推荐）
```
http://localhost:33001
```
- 每2秒自动刷新
- 可视化图表
- 实时日志

### 命令行监控
```bash
python3 monitor_dashboard.py
```
- 每5秒刷新
- 终端内显示

### API监控
```bash
curl http://localhost:38000/monitor/health/detailed | python3 -m json.tool
```

---

## 💾 数据管理

### 备份数据库
```bash
cp mosheng.db backups/mosheng_$(date +%Y%m%d).db
```

### 清理卡住的任务
```bash
cd /scratch/kcriss/MoshengAI
source .venv/bin/activate
python3 << 'EOF'
import sqlite3
from datetime import datetime

conn = sqlite3.connect('mosheng.db')
cursor = conn.cursor()

cursor.execute("""
    UPDATE tasks 
    SET status = 'FAILED', 
        error_message = 'TTS引擎暂时不可用',
        completed_at = ?
    WHERE status = 'PROCESSING'
""", (datetime.now().isoformat(),))

print(f"✅ 已处理 {cursor.rowcount} 个卡住的任务")
conn.commit()
conn.close()
EOF
```

---

## 🎯 下一步

### 完善系统
1. 修复TTS引擎兼容性
2. 添加支付接口
3. 实现OAuth登录
4. 优化UI/UX

### 准备上线
1. 配置域名和HTTPS
2. 切换到PostgreSQL
3. 配置Cloudflare Tunnel
4. 设置监控告警

---

## 📞 获取帮助

### 查看文档
```bash
ls -lh documents/
cat documents/MONITOR_WEB_GUIDE.md
```

### 查看日志
```bash
tail -f /tmp/backend.log
tail -f /tmp/frontend.log
tail -f /tmp/monitor.log
```

### 运行测试
```bash
bash /tmp/test_api.sh
```

---

**🎉 恭喜！MoshengAI MVP系统已基本完成！**

**访问监控面板查看实时状态**: http://localhost:33001











