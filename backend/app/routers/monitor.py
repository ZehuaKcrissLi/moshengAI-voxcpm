"""
系统监控API
提供服务状态、资源使用、日志查看等功能
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import psutil
import os
import subprocess
import sqlite3
from datetime import datetime, timedelta
import asyncio

router = APIRouter()

class SystemStatus(BaseModel):
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    gpu_available: bool
    gpu_info: List[Dict[str, Any]] = []

class ServiceStatus(BaseModel):
    backend: bool
    frontend: bool
    tts_engine: bool
    database: bool

class LogEntry(BaseModel):
    timestamp: str
    level: str
    message: str

@router.get("/system", response_model=SystemStatus)
async def get_system_status():
    """获取系统资源使用情况"""
    # CPU和内存
    cpu_percent = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # GPU信息
    gpu_available = False
    gpu_info = []
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.total', '--format=csv,noheader,nounits'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            gpu_available = True
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 6:
                        gpu_info.append({
                            'index': int(parts[0]),
                            'name': parts[1],
                            'temperature': float(parts[2]),
                            'utilization': float(parts[3]),
                            'memory_used_mb': float(parts[4]),
                            'memory_total_mb': float(parts[5])
                        })
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass
    
    return SystemStatus(
        cpu_percent=cpu_percent,
        memory_percent=memory.percent,
        memory_used_gb=memory.used / (1024**3),
        memory_total_gb=memory.total / (1024**3),
        disk_percent=disk.percent,
        disk_used_gb=disk.used / (1024**3),
        disk_total_gb=disk.total / (1024**3),
        gpu_available=gpu_available,
        gpu_info=gpu_info
    )

@router.get("/services", response_model=ServiceStatus)
async def get_service_status():
    """检查各服务运行状态"""
    # 检查后端（自己）
    backend = True  # 如果能调用这个API，说明后端在运行
    
    # 检查前端
    frontend = False
    try:
        result = subprocess.run(['ss', '-tlnp'], capture_output=True, text=True, timeout=2)
        frontend = ':3000' in result.stdout
    except:
        pass
    
    # 检查TTS引擎
    tts_engine = False
    try:
        # 尝试导入VoxCPM engine
        try:
            from backend.app.core.tts_wrapper_voxcpm import voxcpm_engine as engine
        except:
            from backend.app.core.tts_wrapper import tts_engine as engine
        tts_engine = engine.model is not None
    except:
        pass
    
    # 检查数据库
    database = False
    try:
        db_path = '/scratch/kcriss/MoshengAI/mosheng.db'
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            conn.execute("SELECT 1")
            conn.close()
            database = True
    except:
        pass
    
    return ServiceStatus(
        backend=backend,
        frontend=frontend,
        tts_engine=tts_engine,
        database=database
    )

@router.get("/logs/backend")
async def get_backend_logs(lines: int = 100):
    """获取后端日志"""
    log_file = '/tmp/backend.log'
    if not os.path.exists(log_file):
        raise HTTPException(status_code=404, detail="Log file not found")
    
    try:
        result = subprocess.run(
            ['tail', '-n', str(lines), log_file],
            capture_output=True,
            text=True,
            timeout=5
        )
        return {"logs": result.stdout}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs/frontend")
async def get_frontend_logs(lines: int = 100):
    """获取前端日志"""
    log_file = '/tmp/frontend.log'
    if not os.path.exists(log_file):
        raise HTTPException(status_code=404, detail="Log file not found")
    
    try:
        result = subprocess.run(
            ['tail', '-n', str(lines), log_file],
            capture_output=True,
            text=True,
            timeout=5
        )
        return {"logs": result.stdout}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/database")
async def get_database_stats():
    """获取数据库统计"""
    db_path = '/scratch/kcriss/MoshengAI/mosheng.db'
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="Database not found")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 用户统计
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(credits_balance) FROM users")
    total_credits = cursor.fetchone()[0] or 0
    
    # 任务统计
    cursor.execute("SELECT COUNT(*), status FROM tasks GROUP BY status")
    task_stats = {status: count for count, status in cursor.fetchall()}
    
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE DATE(created_at) = DATE('now')")
    today_tasks = cursor.fetchone()[0]
    
    # 最近任务
    cursor.execute("""
        SELECT id, status, created_at, error_message 
        FROM tasks 
        ORDER BY created_at DESC 
        LIMIT 10
    """)
    recent_tasks = [
        {
            'id': row[0],
            'status': row[1],
            'created_at': row[2],
            'error': row[3]
        }
        for row in cursor.fetchall()
    ]
    
    conn.close()
    
    return {
        'total_users': total_users,
        'total_credits': total_credits,
        'task_stats': task_stats,
        'today_tasks': today_tasks,
        'recent_tasks': recent_tasks,
        'database_size_mb': os.path.getsize(db_path) / (1024**2)
    }

@router.get("/health/detailed")
async def detailed_health_check():
    """详细健康检查"""
    system = await get_system_status()
    services = await get_service_status()
    
    # 综合健康评分
    health_score = 100
    issues = []
    
    if system.cpu_percent > 90:
        health_score -= 20
        issues.append("CPU使用率过高")
    
    if system.memory_percent > 90:
        health_score -= 20
        issues.append("内存使用率过高")
    
    if system.disk_percent > 90:
        health_score -= 10
        issues.append("磁盘空间不足")
    
    if not services.tts_engine:
        health_score -= 30
        issues.append("TTS引擎未运行")
    
    if not services.frontend:
        health_score -= 15
        issues.append("前端服务未运行")
    
    if not services.database:
        health_score -= 25
        issues.append("数据库不可用")
    
    status = "healthy" if health_score >= 80 else "degraded" if health_score >= 50 else "unhealthy"
    
    return {
        'status': status,
        'health_score': health_score,
        'issues': issues,
        'system': system,
        'services': services,
        'timestamp': datetime.now().isoformat()
    }

