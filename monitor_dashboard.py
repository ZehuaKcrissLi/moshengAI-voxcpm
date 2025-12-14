#!/usr/bin/env python3
"""
MoshengAI 监控仪表板
实时显示系统状态、服务健康、资源使用情况
"""
import requests
import time
import os
from datetime import datetime

API_URL = "http://localhost:8000"

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')

def get_status_icon(status):
    return "✅" if status else "❌"

def get_health_color(score):
    if score >= 80:
        return "🟢"
    elif score >= 50:
        return "🟡"
    else:
        return "🔴"

def display_dashboard():
    try:
        # 获取详细健康状态
        response = requests.get(f"{API_URL}/monitor/health/detailed", timeout=5)
        health = response.json()
        
        # 获取数据库统计
        response = requests.get(f"{API_URL}/monitor/stats/database", timeout=5)
        db_stats = response.json()
        
        clear_screen()
        
        print("=" * 80)
        print(f"{'MoshengAI 系统监控仪表板':^80}")
        print("=" * 80)
        print(f"⏰ 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{get_health_color(health['health_score'])} 系统健康评分: {health['health_score']}/100 ({health['status'].upper()})")
        print("=" * 80)
        
        # 服务状态
        services = health['services']
        print("\n📊 服务状态:")
        print("-" * 80)
        print(f"  {get_status_icon(services['backend'])} 后端服务 (FastAPI)")
        print(f"  {get_status_icon(services['frontend'])} 前端服务 (Next.js)")
        print(f"  {get_status_icon(services['tts_engine'])} TTS引擎")
        print(f"  {get_status_icon(services['database'])} 数据库")
        
        # 系统资源
        system = health['system']
        print("\n💻 系统资源:")
        print("-" * 80)
        print(f"  CPU: {system['cpu_percent']:.1f}% ", end="")
        print("🔥" if system['cpu_percent'] > 80 else "")
        
        print(f"  内存: {system['memory_used_gb']:.1f}GB / {system['memory_total_gb']:.1f}GB ({system['memory_percent']:.1f}%) ", end="")
        print("⚠️" if system['memory_percent'] > 80 else "")
        
        print(f"  磁盘: {system['disk_used_gb']:.1f}GB / {system['disk_total_gb']:.1f}GB ({system['disk_percent']:.1f}%) ", end="")
        print("⚠️" if system['disk_percent'] > 80 else "")
        
        # GPU信息
        if system['gpu_available'] and system['gpu_info']:
            print("\n🎮 GPU状态:")
            print("-" * 80)
            for gpu in system['gpu_info']:
                mem_used_gb = gpu['memory_used_mb'] / 1024
                mem_total_gb = gpu['memory_total_mb'] / 1024
                mem_percent = (gpu['memory_used_mb'] / gpu['memory_total_mb']) * 100
                print(f"  GPU {gpu['index']}: {gpu['name']}")
                print(f"    温度: {gpu['temperature']}°C | 利用率: {gpu['utilization']}%")
                print(f"    显存: {mem_used_gb:.1f}GB / {mem_total_gb:.1f}GB ({mem_percent:.1f}%)")
        else:
            print("\n🎮 GPU: 未检测到或不可用")
        
        # 数据库统计
        print("\n📚 数据库统计:")
        print("-" * 80)
        print(f"  用户总数: {db_stats['total_users']:,}")
        print(f"  积分池: {db_stats['total_credits']:,}")
        print(f"  今日任务: {db_stats['today_tasks']:,}")
        print(f"  数据库大小: {db_stats['database_size_mb']:.2f}MB")
        
        # 任务统计
        task_stats = db_stats['task_stats']
        if task_stats:
            print(f"\n  任务状态分布:")
            for status, count in task_stats.items():
                icon = "✅" if status == "COMPLETED" else "⏳" if status == "PROCESSING" else "📝" if status == "PENDING" else "❌"
                print(f"    {icon} {status}: {count}")
        
        # 最近任务
        recent_tasks = db_stats['recent_tasks']
        if recent_tasks:
            print(f"\n📝 最近任务 (最新{len(recent_tasks)}条):")
            print("-" * 80)
            for task in recent_tasks[:5]:
                status_icon = "✅" if task['status'] == "COMPLETED" else "⏳" if task['status'] == "PROCESSING" else "📝" if task['status'] == "PENDING" else "❌"
                print(f"  {status_icon} {task['id'][:20]}... | {task['status']:12} | {task['created_at'][:19]}")
                if task['error']:
                    print(f"      错误: {task['error'][:60]}...")
        
        # 问题列表
        if health['issues']:
            print("\n⚠️  当前问题:")
            print("-" * 80)
            for issue in health['issues']:
                print(f"  • {issue}")
        
        print("\n" + "=" * 80)
        print("💡 按 Ctrl+C 退出 | 每5秒自动刷新")
        print("=" * 80)
        
    except requests.exceptions.ConnectionError:
        clear_screen()
        print("❌ 无法连接到后端服务")
        print("请确保后端服务在运行：python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000")
    except Exception as e:
        clear_screen()
        print(f"❌ 错误: {e}")

def main():
    print("正在启动监控仪表板...")
    try:
        while True:
            display_dashboard()
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n\n👋 监控仪表板已停止")

if __name__ == '__main__':
    main()




