# v0.1 TTS 验收标准（可重复）

## 端口口径（v0.1）
- 前端：`http://localhost:33000`
- 后端：`http://localhost:38000`
- 监控：`http://localhost:33001`

## 引擎选择（v0.1 定稿）
- **默认引擎：VoxCPM**
- **并发策略：单 GPU 单 worker 串行 + 队列排队**
  - API 请求快速返回 `task_id`
  - 推理由后台 worker 逐个处理（避免 GPU 争用导致尾延迟爆炸）

## 关键验收项

### A. 单条生成成功率
- **目标**：连续 **50** 次请求成功率 ≥ **98%**
- **判定**：`GET /tts/status/{task_id}` 返回 `status == "completed"` 视为成功；`failed` 视为失败，必须带 `error`

### B. 平均耗时（端到端）
- **目标**：在同一台机器同一模型权重下，文本长度约 100 字符的任务
  - **平均端到端耗时** ≤ **X 秒**
  - **P95** ≤ **Y 秒**
- **说明**：X/Y 由你在第一次基准跑完后写回这个文档（固化 v0.1 的基线）

### C. 并发行为（5 用户同时请求）
- **目标**：并发 5 个用户请求：
  - API 端快速返回（不会因为推理阻塞请求线程）
  - 任务进入队列，状态从 `pending/processing` 进展到 `completed/failed`
  - 系统不会崩溃（OOM / 进程退出）

## 推荐验证步骤（脚本化）

### 1) 启动服务
```bash
cd /scratch/kcriss/MoshengAI
./START_ALL_SERVICES.sh
```

### 2) 选一个 voice_id
从后端拿音色列表（需要先登录或改为公开接口时可直接请求）：
```bash
curl -s http://localhost:38000/voices/ | python3 -c "import sys,json;print(json.load(sys.stdin)[0]['id'])"
```

### 3) 跑基准脚本
```bash
source /scratch/kcriss/MoshengAI/.venv/bin/activate
python /scratch/kcriss/MoshengAI/tools/tts_benchmark.py \
  --base-url http://localhost:38000 \
  --email YOUR_EMAIL \
  --password YOUR_PASSWORD \
  --voice-id "female/xxx.wav" \
  --requests 50 \
  --concurrency 5
```

