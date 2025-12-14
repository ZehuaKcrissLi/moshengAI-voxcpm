# 🖥️ Web监控面板使用指南

## ✅ 监控面板已部署

### 访问地址
```
http://localhost:3001
```

如果通过SSH端口转发：
```bash
ssh -L 3001:localhost:3001 -L 3000:localhost:3000 -L 8000:localhost:8000 kcriss@10.212.227.125
```
然后访问：`http://localhost:3001`

---

## 🚀 启动监控面板

```bash
cd /scratch/kcriss/MoshengAI
source .venv/bin/activate
python3 monitor_web.py
```

或者后台运行：
```bash
nohup python3 monitor_web.py > /tmp/monitor.log 2>&1 &
```

---

## 📊 监控面板功能

### 实时监控（每2秒刷新）
1. **服务状态**
   - ✅ 后端服务 (FastAPI)
   - ✅ 前端服务 (Next.js)
   - ❌ TTS引擎（当前有兼容性问题）

2. **系统资源**
   - CPU使用率（进度条显示）
   - 内存使用率
   - 磁盘使用率
   - 自动变色：绿色正常，黄色警告，红色危险

3. **GPU状态**（如有）
   - GPU型号
   - 温度
   - 利用率
   - 显存使用

4. **数据库统计**
   - 用户总数
   - 积分池
   - 今日任务数
   - 总任务数

5. **实时日志**
   - 后端日志（最近50行）
   - 前端日志（最近50行）
   - 自动滚动到最新
   - 颜色高亮：
     - 🔴 ERROR/FAILED - 红色
     - 🟢 INFO/SUCCESS - 绿色
     - 🟡 WARNING - 黄色

6. **健康评分**
   - 0-100分
   - ✅ 健康 (80-100)
   - ⚠️ 降级 (50-79)
   - ❌ 异常 (<50)

---

## 🛠️ TTS引擎问题诊断

### 当前状态
❌ **TTS引擎初始化失败**

### 问题分析
IndexTTS项目内部有多个transformers版本兼容性问题：
1. ✅ 已修复：`StaticCache` import
2. ❌ 仍存在：`isin_mps_friendly` 不存在
3. ❌ 仍存在：`ExtensionsTrie` 不存在

### 根本原因
IndexTTS的 `pyproject.toml` 要求 `transformers==4.52.1`，但项目代码实际上是针对旧版本编写的。

### 解决方案

#### **方案1：使用IndexTTS官方环境（推荐）**
```bash
cd /scratch/kcriss/MoshengAI/index-tts

# 创建独立环境
python3 -m venv tts_env
source tts_env/bin/activate

# 安装IndexTTS依赖
uv pip install -e .

# 测试TTS
python3 -c "from indextts.infer_v2 import IndexTTS2; print('✅ Import成功')"
```

然后修改 `backend/app/core/tts_wrapper.py` 使用独立环境。

#### **方案2：手动修复所有兼容性问题**
需要修复多个文件，工作量较大。

#### **方案3：暂时禁用TTS，先完善其他功能**
```python
# backend/app/main.py 中注释掉TTS初始化
# 专注于认证、积分、支付等功能
```

---

## 📝 日志查看

### 实时监控所有日志
```bash
# 方式1：Web监控面板
http://localhost:3001

# 方式2：命令行
tail -f /tmp/backend.log /tmp/frontend.log

# 方式3：分屏查看
tmux new-session \; \
  split-window -h \; \
  send-keys 'tail -f /tmp/backend.log' C-m \; \
  split-window -v \; \
  send-keys 'tail -f /tmp/frontend.log' C-m \; \
  select-pane -t 0
```

### 日志分析
```bash
# 查看后端错误
grep -i error /tmp/backend.log | tail -20

# 统计HTTP状态码
grep "HTTP/1.1" /tmp/backend.log | awk '{print $NF}' | sort | uniq -c

# 查看慢请求
grep "in [0-9]" /tmp/backend.log | awk '{if($NF~/[0-9]+ms/ && $NF>100) print}'

# 查看TTS相关日志
grep -i tts /tmp/backend.log
```

---

## 🎯 监控面板特性

### 自动化
- ✅ 每2秒自动刷新所有数据
- ✅ WebSocket实时推送
- ✅ 断线自动重连
- ✅ 日志自动滚动

### 可视化
- ✅ 美观的渐变色设计
- ✅ 进度条动态显示
- ✅ 状态指示灯（绿色/红色）
- ✅ 数字实时更新

### 响应式
- ✅ 自适应布局
- ✅ hover悬停效果
- ✅ 平滑动画过渡

---

## 🔧 维护命令

### 启动所有服务
```bash
#!/bin/bash
cd /scratch/kcriss/MoshengAI
source .venv/bin/activate

# 启动后端
nohup python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &

# 启动前端
cd frontend
nohup npm run dev > /tmp/frontend.log 2>&1 &
cd ..

# 启动监控面板
nohup python3 monitor_web.py > /tmp/monitor.log 2>&1 &

echo "✅ 所有服务已启动"
echo "前端: http://localhost:3000"
echo "后端: http://localhost:8000"
echo "监控: http://localhost:3001"
```

### 停止所有服务
```bash
pkill -f "uvicorn.*8000"
pkill -f "next dev"
pkill -f "monitor_web.py"
```

### 查看服务状态
```bash
./quick_check.sh
```

---

## 🌐 访问方式

### 本地（服务器上）
- 主应用：`http://localhost:3000`
- 后端API：`http://localhost:8000`
- 监控面板：`http://localhost:3001`

### 远程（通过SSH）
```bash
# 建立隧道
ssh -L 3000:localhost:3000 -L 8000:localhost:8000 -L 3001:localhost:3001 kcriss@10.212.227.125

# 然后访问
http://localhost:3001  # 监控面板
http://localhost:3000  # 主应用
```

### 内网（如果防火墙开放）
- `http://10.212.227.125:3001`

---

## 🎯 下一步建议

1. **立即**：访问 http://localhost:3001 查看监控面板
2. **短期**：修复TTS引擎兼容性（方案1或2）
3. **中期**：添加性能图表（CPU/内存历史曲线）
4. **长期**：集成Prometheus + Grafana专业监控

---

**监控面板已就绪！现在你可以实时看到所有系统状态了。** 🎉




