#!/bin/bash
# 快速系统检查脚本

echo "🔍 MoshengAI 快速系统检查"
echo "================================"

# 后端
if pgrep -f "uvicorn.*38000" > /dev/null; then
    echo "✅ 后端运行中 (38000端口)"
    HEALTH=$(curl -s http://localhost:38000/health 2>/dev/null)
    if [ "$HEALTH" = '{"status":"ok"}' ]; then
        echo "   └─ API响应正常"
    else
        echo "   └─ ⚠️  API无响应"
    fi
else
    echo "❌ 后端未运行"
fi

# 前端
if ss -tlnp 2>/dev/null | grep -q :33000; then
    echo "✅ 前端运行中 (33000端口)"
else
    echo "❌ 前端未运行"
fi

# TTS引擎
TTS_STATUS=$(curl -s http://localhost:38000/monitor/services 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('tts_engine', False))" 2>/dev/null)
if [ "$TTS_STATUS" = "True" ]; then
    echo "✅ TTS引擎正常"
else
    echo "❌ TTS引擎未运行"
fi

# GPU
if command -v nvidia-smi >/dev/null 2>&1; then
    GPU_UTIL=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits 2>/dev/null | head -1)
    GPU_TEMP=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits 2>/dev/null | head -1)
    if [ -n "$GPU_UTIL" ]; then
        echo "🎮 GPU利用率: ${GPU_UTIL}% | 温度: ${GPU_TEMP}°C"
    else
        echo "⚠️  GPU数据获取失败"
    fi
else
    echo "⚠️  GPU不可用"
fi

# 数据库
if [ -f /scratch/kcriss/MoshengAI/mosheng.db ]; then
    DB_SIZE=$(du -h /scratch/kcriss/MoshengAI/mosheng.db | cut -f1)
    echo "💾 数据库: $DB_SIZE"
else
    echo "❌ 数据库文件不存在"
fi

# 磁盘
DISK_USAGE=$(df -h /scratch 2>/dev/null | awk 'NR==2 {print $5}')
if [ -n "$DISK_USAGE" ]; then
    echo "💿 磁盘使用: $DISK_USAGE"
fi

echo "================================"
echo "📊 详细监控: python3 monitor_dashboard.py"
echo "📋 数据库管理: python3 manage_db.py stats"
echo "================================"










