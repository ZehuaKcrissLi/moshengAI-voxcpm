#!/bin/bash
# MoshengAI 服务状态快速检查脚本

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                    MoshengAI 服务状态                             ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# 前端检查
echo "📱 前端服务:"
if ss -tlnp 2>/dev/null | grep -q :33000; then
    echo "   ✅ 运行中 (端口 33000)"
    curl -s -o /dev/null -w "   HTTP状态: %{http_code}\n" http://localhost:33000
else
    echo "   ❌ 未运行"
fi
echo ""

# 后端检查
echo "🔧 后端服务:"
if ss -tlnp 2>/dev/null | grep -q :38000; then
    echo "   ✅ 运行中 (端口 38000)"
    HEALTH=$(curl -s http://localhost:38000/health 2>/dev/null)
    echo "   健康状态: $HEALTH"
else
    echo "   ❌ 未运行"
fi
echo ""

# GPU 检查
echo "🖥️  GPU 检查:"
if command -v nvidia-smi >/dev/null 2>&1; then
    GPU_INFO=$(nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used,memory.free --format=csv,noheader 2>/dev/null)
    if [ -n "$GPU_INFO" ]; then
        GPU_COUNT=$(echo "$GPU_INFO" | wc -l)
        echo "   ✅ 检测到 $GPU_COUNT 块 NVIDIA GPU:"
        echo "$GPU_INFO" | while IFS=',' read -r NAME DRIVER TOTAL USED FREE; do
            echo "      型号: $NAME | 驱动: $DRIVER | 显存: $USED/$TOTAL (已用/总), 空闲: $FREE"
        done
    else
        echo "   ⚠️  未检测到可用的NVIDIA GPU（nvidia-smi 未报告GPU）"
    fi
else
    echo "   ⚠️  未安装 nvidia-smi，无法检测GPU"
fi
echo ""

# 音色库检查
echo "🎤 音色库:"
VOICE_COUNT=$(curl -s http://localhost:38000/voices/ 2>/dev/null | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
if [ "$VOICE_COUNT" -gt "0" ]; then
    echo "   ✅ $VOICE_COUNT 个音色可用"
else
    echo "   ⚠️  音色库未加载"
fi
echo ""

# 访问地址
echo "🌐 访问地址:"
echo "   本地: http://localhost:33000"
echo "   内网: http://10.212.227.125:33000"
echo ""

# SSH端口转发提示
echo "💡 从Mac访问:"
echo "   ssh -L 33000:localhost:33000 -L 38000:localhost:38000 kcriss@10.212.227.125"
echo "   然后浏览器访问: http://localhost:33000"
echo ""

echo "═══════════════════════════════════════════════════════════════════"

