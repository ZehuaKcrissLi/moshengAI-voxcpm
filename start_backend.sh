#!/bin/bash
# 启动 MoshengAI 后端服务的脚本

cd /scratch/kcriss/MoshengAI
export PYTHONPATH=/scratch/kcriss/MoshengAI:/scratch/kcriss/MoshengAI/index-tts

# 使用 index-tts 的 venv (它有正确的依赖)
exec /scratch/kcriss/MoshengAI/index-tts/.venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 38000 --reload

