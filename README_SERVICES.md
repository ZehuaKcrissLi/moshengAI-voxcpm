# 🚀 MoshengAI 服务启动指南

## ✅ 快速启动

### 一键启动所有服务
```bash
cd /scratch/kcriss/MoshengAI
./START_ALL_SERVICES.sh
```

### 一键停止所有服务
```bash
./STOP_ALL_SERVICES.sh
```

---

## 📊 服务列表

| 服务 | 端口 | 用途 | 状态 |
|------|------|------|------|
| **前端应用** | 3000 | 用户界面 | ✅ 正常 |
| **后端API** | 8000 | FastAPI服务 | ✅ 正常 |
| **监控面板** | 3001 | 实时监控 | ✅ 正常 |
| **TTS引擎** | - | 语音合成 | ⚠️ 兼容性问题 |

---

## 🌐 访问地址

### 本地访问（在服务器上）
```
主应用:     http://localhost:3000
后端API:    http://localhost:8000/docs
监控面板:   http://localhost:3001
```

### 远程访问（通过SSH端口转发）
```bash
# 在你的本地电脑上运行
ssh -L 3000:localhost:3000 -L 3001:localhost:3001 -L 8000:localhost:8000 kcriss@10.212.227.125

# 然后在浏览器访问
http://localhost:3000   # 主应用
http://localhost:3001   # 监控面板
http://localhost:8000   # 后端API
```

---

## 🖥️ 监控面板功能

### 访问监控面板
```
http://localhost:3001
```

### 功能特性
1. **实时刷新**（每2秒）
   - 服务状态（绿色=运行中，红色=停止）
   - CPU/内存/磁盘使用率
   - GPU状态（温度/利用率/显存）

2. **数据库统计**
   - 用户总数
   - 积分池
   - 今日任务数
   - 任务状态分布

3. **实时日志**
   - 后端日志（自动滚动）
   - 前端日志（自动滚动）
   - 颜色高亮：ERROR红色，INFO绿色，WARNING黄色

4. **健康评分**
   - 0-100分综合评分
   - 自动检测问题并列出

---

## 🔧 TTS引擎状态

### ⚠️ 当前问题
```
TTS引擎初始化失败 - transformers版本兼容性问题
原因：IndexTTS使用的transformers API在4.36版本中不完整
```

### 已尝试的修复
- ✅ 降级transformers到4.36.0
- ✅ 添加fallback实现：`isin_mps_friendly`
- ✅ 添加fallback实现：`ExtensionsTrie`
- ✅ 添加fallback实现：`is_hqq_available`
- ✅ 添加fallback实现：`is_optimum_quanto_available`
- ⏳ 仍需修复：`is_torchdynamo_compiling`（已在缓存中）

### 解决方案

#### **推荐方案：等待缓存清除后测试**
```bash
# 清理所有Python缓存
find /scratch/kcriss/MoshengAI -name "__pycache__" -type d -delete
find /scratch/kcriss/MoshengAI -name "*.pyc" -delete

# 重启服务
./STOP_ALL_SERVICES.sh
./START_ALL_SERVICES.sh

# 等待30秒让TTS初始化
sleep 30

# 查看日志
tail -100 /tmp/backend.log | grep TTS
```

#### **备用方案：使用IndexTTS官方测试脚本**
```bash
# 直接测试IndexTTS是否可用
cd /scratch/kcriss/MoshengAI/index-tts
source ../venv/bin/activate

python3 << 'EOF'
import sys
sys.path.insert(0, '.')

from indextts.infer_v2 import IndexTTS2

try:
    model = IndexTTS2(
        cfg_path="checkpoints/config.yaml",
        model_dir="checkpoints",
        use_fp16=True,
        device="cuda",
        use_cuda_kernel=False
    )
    print("✅ TTS模型加载成功！")
except Exception as e:
    print(f"❌ 加载失败: {e}")
EOF
```

---

## 📋 服务管理命令

### 查看服务状态
```bash
./quick_check.sh
```

### 查看进程
```bash
ps aux | grep -E "uvicorn|next|monitor" | grep -v grep
```

### 查看端口
```bash
ss -tlnp | grep -E ":(3000|3001|8000)"
```

### 查看日志
```bash
# 后端日志
tail -f /tmp/backend.log

# 前端日志  
tail -f /tmp/frontend.log

# 监控面板日志
tail -f /tmp/monitor.log

# 实时查看所有日志
tail -f /tmp/backend.log /tmp/frontend.log /tmp/monitor.log
```

---

## 🎯 典型使用流程

### 开发/调试流程
```bash
# 1. 启动所有服务
./START_ALL_SERVICES.sh

# 2. 打开监控面板
在浏览器访问: http://localhost:3001

# 3. 查看日志
tail -f /tmp/backend.log

# 4. 测试功能
访问主应用: http://localhost:3000

# 5. 停止服务
./STOP_ALL_SERVICES.sh
```

### 生产部署流程
```bash
# 1. 使用systemd管理服务
sudo systemctl start mosheng-backend
sudo systemctl start mosheng-frontend  
sudo systemctl start mosheng-monitor

# 2. 查看状态
sudo systemctl status mosheng-*

# 3. 查看日志
sudo journalctl -u mosheng-backend -f
```

---

## 🛠️ 故障排查

### 问题1：服务无法启动
```bash
# 查看详细日志
tail -100 /tmp/backend.log
tail -100 /tmp/frontend.log

# 检查端口占用
ss -tlnp | grep -E ":(3000|3001|8000)"

# 杀死占用进程
lsof -ti:8000 | xargs kill -9
```

### 问题2：TTS不工作
```bash
# 查看TTS加载日志
grep -i "tts\|transform" /tmp/backend.log | tail -30

# 检查GPU
nvidia-smi

# 查看卡住的任务
python3 manage_db.py tasks
```

### 问题3：监控面板打不开
```bash
# 检查3001端口
ss -tlnp | grep 3001

# 重启监控面板
pkill -f monitor_web.py
nohup python3 monitor_web.py > /tmp/monitor.log 2>&1 &

# 查看日志
tail -f /tmp/monitor.log
```

---

## 📚 相关文档

- `documents/MONITOR_WEB_GUIDE.md` - 监控面板详细指南
- `documents/MONITORING_GUIDE.md` - 监控系统使用指南
- `documents/DATABASE_MANAGEMENT_GUIDE.md` - 数据库管理
- `documents/TESTING_GUIDE.md` - 测试指南
- `documents/MVP_IMPLEMENTATION_COMPLETE.md` - MVP实施报告

---

**立即开始：运行 `./START_ALL_SERVICES.sh` 并访问 http://localhost:3001 查看监控面板！** 🚀




