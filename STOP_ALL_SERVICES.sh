#!/bin/bash
# 停止所有MoshengAI服务

echo "🛑 停止 MoshengAI 所有服务"
echo "================================"

# 停止后端
BACKEND_PIDS=$(pgrep -f "uvicorn.*backend.app.main")
if [ -n "$BACKEND_PIDS" ]; then
    echo "停止后端服务..."
    pkill -f "uvicorn.*backend.app.main"
    echo "✅ 后端已停止"
else
    echo "ℹ️  后端未运行"
fi

# 停止前端
FRONTEND_PIDS=$(pgrep -f "next dev")
if [ -n "$FRONTEND_PIDS" ]; then
    echo "停止前端服务..."
    pkill -f "next dev"
    echo "✅ 前端已停止"
else
    echo "ℹ️  前端未运行"
fi

# 停止监控面板
MONITOR_PIDS=$(pgrep -f "monitor_web.py")
if [ -n "$MONITOR_PIDS" ]; then
    echo "停止监控面板..."
    pkill -f "monitor_web.py"
    echo "✅ 监控面板已停止"
else
    echo "ℹ️  监控面板未运行"
fi

sleep 2

echo "================================"
echo "✅ 所有服务已停止"
echo "================================"











