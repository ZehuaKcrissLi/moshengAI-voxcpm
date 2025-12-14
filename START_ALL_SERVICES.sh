#!/bin/bash
# MoshengAI 一键启动所有服务

echo "🚀 启动 MoshengAI 所有服务"
echo "================================"

cd /scratch/kcriss/MoshengAI
source .venv/bin/activate

# 停止现有服务
echo "停止现有服务..."
pkill -f "uvicorn.*33000" 2>/dev/null
pkill -f "uvicorn.*8000" 2>/dev/null
pkill -f "next dev" 2>/dev/null
pkill -f "next start" 2>/dev/null
pkill -f "monitor_web.py" 2>/dev/null
sleep 3

# 启动后端（开发模式，支持自动重载）
echo "启动后端服务 (33000端口，开发模式)..."
nohup python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 33000 --reload > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
sleep 5

# 检查后端
if curl -s http://localhost:33000/health > /dev/null 2>&1; then
    echo "✅ 后端启动成功 (PID: $BACKEND_PID)"
else
    echo "❌ 后端启动失败，查看日志: tail -f /tmp/backend.log"
fi

# 启动前端（开发模式，支持热重载）
echo "启动前端服务 (38000端口，开发模式)..."
cd frontend

# 使用开发模式运行（支持热重载，显示调试工具）
nohup npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
sleep 8

# 检查前端
if ss -tlnp 2>/dev/null | grep -q :38000; then
    echo "✅ 前端启动成功 (PID: $FRONTEND_PID)"
else
    echo "❌ 前端启动失败，查看日志: tail -f /tmp/frontend.log"
fi

# 启动监控面板
echo "启动监控面板 (33001端口)..."
nohup python3 monitor_web.py > /tmp/monitor.log 2>&1 &
MONITOR_PID=$!
sleep 3

# 检查监控面板
if ss -tlnp 2>/dev/null | grep -q :33001; then
    echo "✅ 监控面板启动成功 (PID: $MONITOR_PID)"
else
    echo "❌ 监控面板启动失败，查看日志: tail -f /tmp/monitor.log"
fi

echo "================================"
echo "✅ 启动完成！"
echo ""
echo "📱 访问地址："
echo "  主应用: http://localhost:38000"
echo "  后端API: http://localhost:33000/docs"
echo "  监控面板: http://localhost:33001"
echo ""
echo "📊 快速检查: ./quick_check.sh"
echo "📝 查看日志:"
echo "  tail -f /tmp/backend.log"
echo "  tail -f /tmp/frontend.log"
echo "  tail -f /tmp/monitor.log"
echo "================================"



