#!/usr/bin/env python3
"""
MoshengAI Web监控面板
实时显示系统状态、日志、资源使用情况
运行在33001端口
包含数据库管理功能
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import psutil
import subprocess
import os
import asyncio
import json
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
import urllib.request
from sqlalchemy import select, update, delete, func

from backend.app.db.database import AsyncSessionLocal
from backend.app.db.models import User as DbUser, Task as DbTask
from backend.app.db.crud_credits import apply_credit_transaction

app = FastAPI(title="MoshengAI Monitor")

# WebSocket连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# Database models
class UserUpdate(BaseModel):
    email: Optional[str] = None
    credits_balance: Optional[int] = None
    is_admin: Optional[bool] = None

class CreditsUpdate(BaseModel):
    amount: int
    reason: str = "Manual adjustment"

def get_system_info():
    """获取系统信息"""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # GPU信息
    gpu_info = []
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.total', 
             '--format=csv,noheader,nounits'],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
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
    except:
        pass
    
    return {
        'cpu_percent': cpu_percent,
        'memory_percent': memory.percent,
        'memory_used_gb': memory.used / (1024**3),
        'memory_total_gb': memory.total / (1024**3),
        'disk_percent': disk.percent,
        'disk_used_gb': disk.used / (1024**3),
        'disk_total_gb': disk.total / (1024**3),
        'gpu_info': gpu_info
    }

# TTS引擎状态缓存（避免频繁HTTP请求）
_tts_engine_cache = {'status': False, 'timestamp': 0}
_tts_cache_ttl = 10  # 缓存10秒

def get_services_status():
    """获取服务状态"""
    backend = False
    frontend = False
    
    try:
        result = subprocess.run(['ss', '-tlnp'], capture_output=True, text=True, timeout=2)
        backend = ':38000' in result.stdout
        frontend = ':33000' in result.stdout
    except:
        pass
    
    # TTS引擎状态 - 使用缓存机制减少HTTP请求频率
    global _tts_engine_cache, _tts_cache_ttl
    tts_engine = False
    
    current_time = datetime.now().timestamp()
    # 如果缓存未过期，直接使用缓存
    if current_time - _tts_engine_cache['timestamp'] < _tts_cache_ttl:
        tts_engine = _tts_engine_cache['status']
    else:
        # 缓存过期，通过HTTP请求获取真实状态
        try:
            with urllib.request.urlopen('http://localhost:38000/monitor/services', timeout=2) as resp:
                if resp.status != 200:
                    raise ValueError("non-200 response")
                data = json.loads(resp.read().decode("utf-8"))
                tts_engine = data.get('tts_engine', False)
                # 更新缓存
                _tts_engine_cache = {
                    'status': tts_engine,
                    'timestamp': current_time
                }
        except Exception:
            # 请求失败，使用缓存值（即使过期）
            tts_engine = _tts_engine_cache['status']
    
    return {
        'backend': backend,
        'frontend': frontend,
        'tts_engine': tts_engine
    }

async def get_database_stats():
    """
    获取数据库统计（v0.1：使用 SQLAlchemy AsyncSession，兼容 Postgres）。
    """
    try:
        async with AsyncSessionLocal() as db:
            total_users = (await db.execute(select(func.count(DbUser.id)))).scalar_one()
            total_credits = (await db.execute(select(func.coalesce(func.sum(DbUser.credits_balance), 0)))).scalar_one()
            total_tasks = (await db.execute(select(func.count(DbTask.id)))).scalar_one()

            task_stats_rows = (
                await db.execute(select(DbTask.status, func.count(DbTask.id)).group_by(DbTask.status))
            ).all()
            task_stats = {status: count for status, count in task_stats_rows}

            today_tasks = (
                await db.execute(
                    select(func.count(DbTask.id)).where(func.date(DbTask.created_at) == func.current_date())
                )
            ).scalar_one()
        
        return {
            'total_users': total_users,
            'total_credits': total_credits,
            'total_tasks': total_tasks,
            'task_stats': task_stats,
            'today_tasks': today_tasks,
                'database_size_mb': 0.0
        }
    except:
        return {}

def get_recent_logs(log_file, lines=50):
    """获取最近的日志"""
    if not os.path.exists(log_file):
        return []
    
    try:
        result = subprocess.run(['tail', '-n', str(lines), log_file], 
                              capture_output=True, text=True, timeout=2)
        return result.stdout.strip().split('\n')
    except:
        return []

# Database Management APIs
@app.get("/api/users")
async def get_users():
    """获取所有用户列表"""
    async with AsyncSessionLocal() as db:
        rows = (
            await db.execute(
                select(DbUser).order_by(DbUser.created_at.desc())
            )
        ).scalars().all()
        users = [
            {
                'id': u.id,
                'email': u.email,
                'provider': u.provider,
                'credits_balance': u.credits_balance,
                'is_admin': u.is_admin,
                'created_at': u.created_at.isoformat() if u.created_at else None
            }
            for u in rows
        ]
    return {'users': users}

@app.get("/api/users/{user_id}")
async def get_user(user_id: str):
    """获取单个用户信息"""
    async with AsyncSessionLocal() as db:
        user = (
            await db.execute(select(DbUser).where(DbUser.id == user_id))
        ).scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            'id': user.id,
            'email': user.email,
            'provider': user.provider,
            'credits_balance': user.credits_balance,
            'is_admin': user.is_admin,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }

@app.put("/api/users/{user_id}")
async def update_user(user_id: str, update: UserUpdate):
    """更新用户信息"""
    async with AsyncSessionLocal() as db:
        user = (
            await db.execute(select(DbUser).where(DbUser.id == user_id))
        ).scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if update.email is None and update.credits_balance is None and update.is_admin is None:
            raise HTTPException(status_code=400, detail="No fields to update")

        if update.email is not None:
            user.email = update.email
        if update.is_admin is not None:
            user.is_admin = update.is_admin

        # credits_balance uses ledger adjustment (absolute -> delta)
        if update.credits_balance is not None:
            delta = int(update.credits_balance) - int(user.credits_balance)
            if delta != 0:
                result = await apply_credit_transaction(
                    db=db,
                    user_id=user.id,
                    amount=delta,
                    kind="ADJUSTMENT",
                    reason="Monitor: set credits_balance",
                )
                if result is None:
                    raise HTTPException(status_code=400, detail="Insufficient credits for adjustment")

        await db.commit()
        return {'message': 'User updated successfully'}

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: str):
    """删除用户"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(delete(DbUser).where(DbUser.id == user_id))
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
        await db.commit()
        return {'message': 'User deleted successfully'}

@app.post("/api/users/{user_id}/credits")
async def update_user_credits(user_id: str, update: CreditsUpdate):
    """更新用户积分"""
    async with AsyncSessionLocal() as db:
        user = (
            await db.execute(select(DbUser).where(DbUser.id == user_id))
        ).scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        old_balance = int(user.credits_balance)
        result = await apply_credit_transaction(
            db=db,
            user_id=user.id,
            amount=int(update.amount),
            kind="ADJUSTMENT",
            reason=update.reason,
        )
        if result is None:
            raise HTTPException(status_code=400, detail="Insufficient credits")
        _, new_balance = result
        await db.commit()
        return {
            'message': f'Credits updated: {int(update.amount):+d}',
            'old_balance': old_balance,
            'new_balance': new_balance,
            'reason': update.reason
        }

@app.get("/api/tasks")
async def get_tasks(limit: int = 100, offset: int = 0):
    """获取任务列表"""
    if limit <= 0:
        raise HTTPException(status_code=400, detail="limit must be positive")
    if limit > 500:
        raise HTTPException(status_code=400, detail="limit too large")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset must be non-negative")

    async with AsyncSessionLocal() as db:
        rows = (
            await db.execute(
                select(DbTask)
                .order_by(DbTask.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        ).scalars().all()
        total = (await db.execute(select(func.count(DbTask.id)))).scalar_one()

        tasks = []
        for t in rows:
            text_value = t.text or ""
            tasks.append({
                'id': t.id,
                'user_id': t.user_id,
                'text': (text_value[:50] + '...') if len(text_value) > 50 else text_value,
                'status': t.status,
                'cost': t.cost,
                'output_url': t.output_url,
                'error_message': t.error_message,
                'created_at': t.created_at.isoformat() if t.created_at else None,
                'completed_at': t.completed_at.isoformat() if t.completed_at else None
            })

        return {'tasks': tasks, 'total': total}

@app.get("/", response_class=HTMLResponse)
async def get_monitor_page():
    """监控页面HTML - 包含数据库管理界面"""
    html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MoshengAI 监控面板</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0a0a0a;
            color: #e0e0e0;
            padding: 20px;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1800px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            padding: 30px 0;
            border-bottom: 2px solid #1a1a1a;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #1a1a1a;
        }
        
        .tab {
            padding: 12px 24px;
            background: transparent;
            border: none;
            color: #888;
            cursor: pointer;
            font-size: 1em;
            border-bottom: 2px solid transparent;
            transition: all 0.3s;
        }
        
        .tab.active {
            color: #667eea;
            border-bottom-color: #667eea;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: #1a1a1a;
            border-radius: 12px;
            padding: 24px;
            border: 1px solid #2a2a2a;
            transition: all 0.3s ease;
        }
        
        .card:hover {
            border-color: #3a3a3a;
            transform: translateY(-2px);
        }
        
        .card-title {
            font-size: 1.1em;
            font-weight: 600;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .card-title::before {
            content: '';
            width: 4px;
            height: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 2px;
        }
        
        .table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        
        .table th, .table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #2a2a2a;
        }
        
        .table th {
            color: #888;
            font-weight: 600;
            font-size: 0.9em;
        }
        
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9em;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
        }
        
        .btn-primary:hover {
            background: #5568d3;
        }
        
        .btn-danger {
            background: #f44336;
            color: white;
        }
        
        .btn-danger:hover {
            background: #d32f2f;
        }
        
        .btn-small {
            padding: 4px 8px;
            font-size: 0.8em;
        }
        
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 1000;
        }
        
        .modal.active {
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .modal-content {
            background: #1a1a1a;
            border-radius: 12px;
            padding: 24px;
            max-width: 500px;
            width: 90%;
            border: 1px solid #2a2a2a;
        }
        
        .form-group {
            margin-bottom: 16px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #888;
            font-size: 0.9em;
        }
        
        .form-group input {
            width: 100%;
            padding: 10px;
            background: #0a0a0a;
            border: 1px solid #2a2a2a;
            border-radius: 6px;
            color: #e0e0e0;
            font-size: 1em;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #2a2a2a;
        }
        
        .metric:last-child {
            border-bottom: none;
        }
        
        .metric-label {
            color: #999;
            font-size: 0.9em;
        }
        
        .metric-value {
            font-weight: 600;
            font-size: 1.1em;
        }
        
        .progress-bar {
            height: 8px;
            background: #2a2a2a;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 8px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s ease;
        }
        
        .service-status {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 0;
        }
        
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }
        
        .status-online {
            background: #4caf50;
            box-shadow: 0 0 10px rgba(76, 175, 80, 0.5);
        }
        
        .status-offline {
            background: #f44336;
            box-shadow: 0 0 10px rgba(244, 67, 54, 0.5);
        }
        
        .log-container {
            grid-column: 1 / -1;
        }
        
        .log-box {
            background: #0d0d0d;
            border: 1px solid #2a2a2a;
            border-radius: 8px;
            padding: 16px;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 0.85em;
            max-height: 400px;
            overflow-y: auto;
            line-height: 1.8;
        }
        
        .log-line {
            color: #b0b0b0;
            margin: 2px 0;
        }
        
        .log-error {
            color: #f44336;
        }
        
        .log-info {
            color: #4caf50;
        }
        
        .log-warning {
            color: #ffc107;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 MoshengAI 监控面板</h1>
            <div class="timestamp" id="timestamp">加载中...</div>
        </div>
        
        <div class="tabs">
            <button class="tab active" onclick="switchTab('monitor')">📊 系统监控</button>
            <button class="tab" onclick="switchTab('users')">👥 用户管理</button>
            <button class="tab" onclick="switchTab('tasks')">📝 任务管理</button>
        </div>
        
        <!-- 系统监控标签页 -->
        <div id="monitor-tab" class="tab-content active">
        <div class="grid">
            <!-- 服务状态 -->
            <div class="card">
                <div class="card-title">📊 服务状态</div>
                <div class="service-status">
                    <div class="status-indicator" id="backend-status"></div>
                    <span>后端服务 (FastAPI)</span>
                </div>
                <div class="service-status">
                    <div class="status-indicator" id="frontend-status"></div>
                    <span>前端服务 (Next.js)</span>
                </div>
                <div class="service-status">
                    <div class="status-indicator" id="tts-status"></div>
                    <span>TTS引擎</span>
                </div>
            </div>
            
            <!-- 系统资源 -->
            <div class="card">
                <div class="card-title">💻 系统资源</div>
                <div class="metric">
                    <span class="metric-label">CPU</span>
                    <span class="metric-value" id="cpu-value">0%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="cpu-bar" style="width: 0%"></div>
                </div>
                <div class="metric" style="margin-top: 16px;">
                    <span class="metric-label">内存</span>
                    <span class="metric-value" id="memory-value">0%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="memory-bar" style="width: 0%"></div>
                </div>
                <div class="metric" style="margin-top: 16px;">
                    <span class="metric-label">磁盘</span>
                    <span class="metric-value" id="disk-value">0%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="disk-bar" style="width: 0%"></div>
                </div>
            </div>
            
            <!-- 数据库统计 -->
            <div class="card">
                <div class="card-title">📚 数据库</div>
                <div class="metric">
                    <span class="metric-label">用户总数</span>
                    <span class="metric-value" id="total-users">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">积分池</span>
                    <span class="metric-value" id="total-credits">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">今日任务</span>
                    <span class="metric-value" id="today-tasks">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">总任务数</span>
                    <span class="metric-value" id="total-tasks">0</span>
                </div>
            </div>
        </div>
        
        <!-- 后端日志 -->
        <div class="grid log-container">
            <div class="card">
                <div class="card-title">📝 后端日志（实时）</div>
                <div class="log-box" id="backend-logs">等待日志...</div>
                </div>
            </div>
        </div>
        
        <!-- 用户管理标签页 -->
        <div id="users-tab" class="tab-content">
            <div class="card">
                <div class="card-title">👥 用户管理</div>
                <button class="btn btn-primary" onclick="loadUsers()">刷新列表</button>
                <table class="table" id="users-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>邮箱</th>
                            <th>积分</th>
                            <th>管理员</th>
                            <th>注册时间</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody id="users-tbody">
                        <tr><td colspan="6">加载中...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- 任务管理标签页 -->
        <div id="tasks-tab" class="tab-content">
            <div class="card">
                <div class="card-title">📝 任务管理</div>
                <button class="btn btn-primary" onclick="loadTasks()">刷新列表</button>
                <table class="table" id="tasks-table">
                    <thead>
                        <tr>
                            <th>任务ID</th>
                            <th>用户ID</th>
                            <th>文本</th>
                            <th>状态</th>
                            <th>消耗积分</th>
                            <th>创建时间</th>
                        </tr>
                    </thead>
                    <tbody id="tasks-tbody">
                        <tr><td colspan="6">加载中...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <!-- 编辑用户模态框 -->
    <div id="edit-user-modal" class="modal">
        <div class="modal-content">
            <h2 style="margin-bottom: 20px;">编辑用户</h2>
            <div class="form-group">
                <label>邮箱</label>
                <input type="email" id="edit-email" />
            </div>
            <div class="form-group">
                <label>积分</label>
                <input type="number" id="edit-credits" />
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="edit-is-admin" />
                    管理员
                </label>
            </div>
            <div style="display: flex; gap: 10px; margin-top: 20px;">
                <button class="btn btn-primary" onclick="saveUser()">保存</button>
                <button class="btn" onclick="closeEditModal()">取消</button>
            </div>
        </div>
    </div>
    
    <!-- 调整积分模态框 -->
    <div id="adjust-credits-modal" class="modal">
        <div class="modal-content">
            <h2 style="margin-bottom: 20px;">调整积分</h2>
            <div class="form-group">
                <label>调整数量（正数为增加，负数为减少）</label>
                <input type="number" id="adjust-amount" />
            </div>
            <div class="form-group">
                <label>原因</label>
                <input type="text" id="adjust-reason" value="Manual adjustment" />
            </div>
            <div style="display: flex; gap: 10px; margin-top: 20px;">
                <button class="btn btn-primary" onclick="saveCreditsAdjustment()">确认</button>
                <button class="btn" onclick="closeCreditsModal()">取消</button>
            </div>
        </div>
    </div>
    
    <script>
        let ws;
        let currentEditUserId = null;
        let currentAdjustUserId = null;
        
        function switchTab(tabName) {
            // 更新标签按钮
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            event.target.classList.add('active');
            
            // 更新内容
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            document.getElementById(tabName + '-tab').classList.add('active');
            
            // 加载对应数据
            if (tabName === 'users') {
                loadUsers();
            } else if (tabName === 'tasks') {
                loadTasks();
            }
        }
        
        function connectWebSocket() {
            ws = new WebSocket('ws://localhost:33001/ws');
            
            ws.onopen = () => {
                console.log('✅ WebSocket连接已建立');
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (document.getElementById('monitor-tab').classList.contains('active')) {
                updateUI(data);
                }
            };
            
            ws.onclose = () => {
                console.log('❌ WebSocket连接已断开，3秒后重连...');
                setTimeout(connectWebSocket, 33000);
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket错误:', error);
            };
        }
        
        function updateUI(data) {
            document.getElementById('timestamp').textContent = new Date().toLocaleString('zh-CN');
            
            updateServiceStatus('backend-status', data.services?.backend);
            updateServiceStatus('frontend-status', data.services?.frontend);
            updateServiceStatus('tts-status', data.services?.tts_engine);
            
            if (data.system) {
                updateMetric('cpu', data.system.cpu_percent);
                updateMetric('memory', data.system.memory_percent);
                updateMetric('disk', data.system.disk_percent);
            }
            
            if (data.database) {
                document.getElementById('total-users').textContent = data.database.total_users?.toLocaleString() || '0';
                document.getElementById('total-credits').textContent = data.database.total_credits?.toLocaleString() || '0';
                document.getElementById('today-tasks').textContent = data.database.today_tasks || '0';
                document.getElementById('total-tasks').textContent = data.database.total_tasks || '0';
            }
            
            if (data.backend_logs) {
                updateLogs('backend-logs', data.backend_logs);
            }
        }
        
        function updateServiceStatus(id, status) {
            const el = document.getElementById(id);
            if (el) {
                el.className = status ? 'status-indicator status-online' : 'status-indicator status-offline';
            }
        }
        
        function updateMetric(name, value) {
            const valueEl = document.getElementById(`${name}-value`);
            const barEl = document.getElementById(`${name}-bar`);
            if (valueEl && barEl) {
                valueEl.textContent = `${value.toFixed(1)}%`;
                barEl.style.width = `${value}%`;
            }
        }
        
        function updateLogs(id, logs) {
            const el = document.getElementById(id);
            if (el && logs) {
                const logsHtml = logs.slice(-30).map(line => {
                    let className = 'log-line';
                    if (line.toLowerCase().includes('error') || line.toLowerCase().includes('failed')) {
                        className += ' log-error';
                    } else if (line.toLowerCase().includes('info') || line.toLowerCase().includes('success')) {
                        className += ' log-info';
                    } else if (line.toLowerCase().includes('warning') || line.toLowerCase().includes('warn')) {
                        className += ' log-warning';
                    }
                    return `<div class="${className}">${escapeHtml(line)}</div>`;
                }).join('');
                el.innerHTML = logsHtml || '<div class="log-line">暂无日志</div>';
                el.scrollTop = el.scrollHeight;
            }
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        async function loadUsers() {
            try {
                const response = await fetch('/api/users');
                const data = await response.json();
                const tbody = document.getElementById('users-tbody');
                
                if (data.users && data.users.length > 0) {
                    tbody.innerHTML = data.users.map(user => `
                        <tr>
                            <td>${user.id.substring(0, 8)}...</td>
                            <td>${user.email}</td>
                            <td>${user.credits_balance}</td>
                            <td>${user.is_admin ? '是' : '否'}</td>
                            <td>${new Date(user.created_at).toLocaleString('zh-CN')}</td>
                            <td>
                                <button class="btn btn-primary btn-small" onclick="editUser('${user.id}')">编辑</button>
                                <button class="btn btn-primary btn-small" onclick="adjustCredits('${user.id}')">调整积分</button>
                                <button class="btn btn-danger btn-small" onclick="deleteUser('${user.id}')">删除</button>
                            </td>
                        </tr>
                    `).join('');
                } else {
                    tbody.innerHTML = '<tr><td colspan="6">暂无用户</td></tr>';
                }
            } catch (error) {
                console.error('Failed to load users:', error);
                document.getElementById('users-tbody').innerHTML = '<tr><td colspan="6">加载失败</td></tr>';
            }
        }
        
        async function loadTasks() {
            try {
                const response = await fetch('/api/tasks?limit=100');
                const data = await response.json();
                const tbody = document.getElementById('tasks-tbody');
                
                if (data.tasks && data.tasks.length > 0) {
                    tbody.innerHTML = data.tasks.map(task => `
                        <tr>
                            <td>${task.id.substring(0, 8)}...</td>
                            <td>${task.user_id.substring(0, 8)}...</td>
                            <td>${task.text || ''}</td>
                            <td>${task.status}</td>
                            <td>${task.cost}</td>
                            <td>${new Date(task.created_at).toLocaleString('zh-CN')}</td>
                        </tr>
                    `).join('');
            } else {
                    tbody.innerHTML = '<tr><td colspan="6">暂无任务</td></tr>';
                }
            } catch (error) {
                console.error('Failed to load tasks:', error);
                document.getElementById('tasks-tbody').innerHTML = '<tr><td colspan="6">加载失败</td></tr>';
            }
        }
        
        async function editUser(userId) {
            try {
                const response = await fetch(`/api/users/${userId}`);
                const user = await response.json();
                
                currentEditUserId = userId;
                document.getElementById('edit-email').value = user.email;
                document.getElementById('edit-credits').value = user.credits_balance;
                document.getElementById('edit-is-admin').checked = user.is_admin;
                document.getElementById('edit-user-modal').classList.add('active');
            } catch (error) {
                alert('加载用户信息失败: ' + error.message);
            }
        }
        
        async function saveUser() {
            if (!currentEditUserId) return;
            
            try {
                const update = {
                    email: document.getElementById('edit-email').value,
                    credits_balance: parseInt(document.getElementById('edit-credits').value),
                    is_admin: document.getElementById('edit-is-admin').checked
                };
                
                const response = await fetch(`/api/users/${currentEditUserId}`, {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(update)
                });
                
                if (response.ok) {
                    alert('用户更新成功');
                    closeEditModal();
                    loadUsers();
                } else {
                    const error = await response.json();
                    alert('更新失败: ' + error.detail);
                }
            } catch (error) {
                alert('更新失败: ' + error.message);
            }
        }
        
        function closeEditModal() {
            document.getElementById('edit-user-modal').classList.remove('active');
            currentEditUserId = null;
        }
        
        function adjustCredits(userId) {
            currentAdjustUserId = userId;
            document.getElementById('adjust-amount').value = '';
            document.getElementById('adjust-reason').value = 'Manual adjustment';
            document.getElementById('adjust-credits-modal').classList.add('active');
        }
        
        async function saveCreditsAdjustment() {
            if (!currentAdjustUserId) return;
            
            try {
                const amount = parseInt(document.getElementById('adjust-amount').value);
                const reason = document.getElementById('adjust-reason').value;
                
                if (!amount) {
                    alert('请输入调整数量');
                    return;
                }
                
                const response = await fetch(`/api/users/${currentAdjustUserId}/credits`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({amount, reason})
                });
                
                if (response.ok) {
                    const data = await response.json();
                    alert(`积分调整成功！\\n旧余额: ${data.old_balance}\\n新余额: ${data.new_balance}`);
                    closeCreditsModal();
                    loadUsers();
                } else {
                    const error = await response.json();
                    alert('调整失败: ' + error.detail);
                }
            } catch (error) {
                alert('调整失败: ' + error.message);
            }
        }
        
        function closeCreditsModal() {
            document.getElementById('adjust-credits-modal').classList.remove('active');
            currentAdjustUserId = null;
        }
        
        async function deleteUser(userId) {
            if (!confirm('确定要删除这个用户吗？此操作不可恢复！')) return;
            
            try {
                const response = await fetch(`/api/users/${userId}`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    alert('用户删除成功');
                    loadUsers();
                } else {
                    const error = await response.json();
                    alert('删除失败: ' + error.detail);
                }
            } catch (error) {
                alert('删除失败: ' + error.message);
            }
        }
        
        // 启动WebSocket连接
        connectWebSocket();
        
        // 页面加载时加载用户列表
        window.addEventListener('load', () => {
            if (document.getElementById('users-tab').classList.contains('active')) {
                loadUsers();
            }
        });
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点，实时推送监控数据"""
    await manager.connect(websocket)
    try:
        while True:
            # 收集所有监控数据
            data = {
                'system': get_system_info(),
                'services': get_services_status(),
                'database': await get_database_stats(),
                'backend_logs': get_recent_logs('/tmp/backend.log', 50),
                'frontend_logs': get_recent_logs('/tmp/frontend.log', 50),
                'timestamp': datetime.now().isoformat()
            }
            
            # 发送数据
            await websocket.send_json(data)
            
            # 等待2秒
            await asyncio.sleep(2)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == '__main__':
    print("🚀 启动MoshengAI监控面板...")
    print("📊 访问地址: http://localhost:33001")
    print("━" * 60)
    uvicorn.run(app, host="0.0.0.0", port=33001, log_level="info")
