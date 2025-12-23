# Mosheng AI - 服务运行指南

## 系统状态 ✅ 完全运行中 - Bug已全部修复

### 后端服务 (TTS推理引擎)
**地址:** `http://localhost:38000`
**状态:** 🟢 运行中 **（2025-12-07 修复完成）**
**启动脚本:** `/scratch/kcriss/MoshengAI/start_backend.sh`

**🐛 已修复的Bug**: 
- ✅ IndexTTS2初始化缩进错误（infer_v2.py:79-83）
- ✅ 情感检测代码缩进错误（infer_v2.py:388-399）
- ✅ Transformers导入缩进错误（transformers_generation_utils.py）
- 详见: `/scratch/kcriss/MoshengAI/documents/BUGS_FIXED.md`

**已加载的模型组件:**
- GPT主生成模型 (UnifiedVoice)
- Semantic Codec (MaskGCT)
- S2Mel转换模型
- CAMPlus说话人嵌入
- BigVGAN高质量声码器
- QwenEmotion情感分析 (可选)

**API端点:**
- `GET /` - 服务欢迎信息
- `GET /health` - 健康检查
- `GET /voices/` - 获取所有可用音色列表
- `POST /tts/generate` - 提交TTS生成任务
  ```json
  {
    "text": "你好世界",
    "voice_id": "female/女声1大气磁性.wav"
  }
  ```
- `GET /tts/status/{task_id}` - 查询任务状态
- `GET /static/generated/{filename}` - 下载生成的音频
- `GET /static/voices/{category}/{filename}` - 预览音色样本

**查看后端日志:**
```bash
# 方法1: 查看终端文件
cat /home/kcriss/.cursor/projects/scratch-kcriss/terminals/12.txt

# 方法2: 查看实时日志（如果使用 tee）
tail -f /tmp/tts_backend.log
```

### 前端服务 (WebApp)
**地址:** `http://localhost:33000`
**状态:** 🟢 运行中
**技术栈:** Next.js 16 + Tailwind CSS 4 + Framer Motion

**启动命令:**
```bash
cd /scratch/kcriss/MoshengAI/frontend && npm run dev
```

**功能特性:**
- 🎨 现代暗色主题 (类ChatGPT风格)
- 🎤 语音库抽屉式选择器 (男声/女声分类)
- 💬 对话式交互界面
- 🔊 内置音频播放器
- 💳 Credits积分系统
- 🔐 登录/注册模态框

**查看前端日志:**
```bash
cat /home/kcriss/.cursor/projects/scratch-kcriss/terminals/5.txt
```

## GPU使用情况
**设备检测:** TTS模型会自动检测CUDA/MPS/CPU
- 当前配置使用: **CUDA (GPU加速)**
- FP16优化: 启用

**验证GPU使用:**
```bash
nvidia-smi  # 查看GPU占用
```

## 使用方法

### 1. 访问Web界面
打开浏览器访问: `http://localhost:33000`

### 2. 操作流程
1. 点击底部 "Change Voice" 按钮
2. 在Voice Lab中选择音色（可播放预览）
3. 在主界面文本框输入想要合成的文字
4. 点击发送按钮 (右下角)
5. 等待生成（会显示加载动画）
6. 音频生成后自动播放

### 3. API直接调用示例
```bash
# 1. 获取音色列表
curl http://localhost:38000/voices/

# 2. 提交生成任务
curl -X POST http://localhost:38000/tts/generate \
  -H "Content-Type: application/json" \
  -d '{"text":"欢迎使用魔声AI", "voice_id":"female/女声1大气磁性.wav"}'

# 返回: {"task_id":"xxx","status":"queued"}

# 3. 轮询任务状态
curl http://localhost:38000/tts/status/xxx

# 当status="completed"时，通过output_url下载音频
```

## 故障排查

### 后端无法启动
```bash
# 1. 检查端口占用
lsof -i :38000

# 2. 清理端口
fuser -k 38000/tcp

# 3. 重启
/scratch/kcriss/MoshengAI/start_backend.sh
```

### 前端无法访问
```bash
# 检查端口
lsof -i :33000

# 重启前端
cd /scratch/kcriss/MoshengAI/frontend && npm run dev
```

### TTS生成卡在processing
- **原因:** QwenEmotion模型加载失败时会禁用情感分析但继续工作
- **查看日志:** `tail -f /home/kcriss/.cursor/projects/scratch-kcriss/terminals/12.txt`
- **验证模型:** 确认所有checkpoints存在于 `index-tts/checkpoints/`

## 技术架构总结

```
用户浏览器 (localhost:33000)
    ↓
Next.js Frontend (Tailwind + Zustand)
    ↓ HTTP REST API
FastAPI Backend (localhost:38000)
    ↓ asyncio.Queue
TTS Worker (单GPU队列处理)
    ↓
IndexTTS2 (GPU推理)
    ├─ GPT Token生成
    ├─ Semantic2Mel转换
    └─ BigVGAN声码器
    ↓
音频文件 (storage/generated/)
    ↓ HTTP Static
用户浏览器播放
```

## 下一步待完成功能
- [ ] PostgreSQL数据库集成 (当前使用内存存储)
- [ ] 用户认证系统 (Google/WeChat OAuth)
- [ ] 支付系统集成 (Credits充值)
- [ ] 管理后台看板
- [ ] Docker容器化部署
- [ ] Cloudflare Tunnel公网访问
- [ ] S3音频存储备份
- [ ] Prometheus监控

---
**最后更新:** 2025-12-06
**状态:** ✅ MVP完全可用，核心TTS功能正常运行

