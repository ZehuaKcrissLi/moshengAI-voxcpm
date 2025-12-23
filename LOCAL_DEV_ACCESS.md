# MoshengAI - 本地开发访问指南

## 🎯 当前服务状态

- **前端**: 运行在 `0.0.0.0:40004`
- **后端**: 运行在 `0.0.0.0:38000`
- **服务器IP**: `10.212.227.125`

---

## ✅ 访问方式

### 方案1：直接通过内网IP访问（推荐）

如果您的开发机器和服务器在同一局域网：

```
http://10.212.227.125:40004
```

**优点**：
- ✅ 简单直接
- ✅ 无需额外配置
- ✅ 性能最好

---

### 方案2：SSH端口转发（通用方案）

**适用场景**：
- 您的开发机器和服务器不在同一网络
- 需要通过SSH访问服务器
- 需要更安全的连接

#### 步骤：

1. **在您的开发机器**上打开终端（不是服务器上）

2. **运行SSH端口转发命令**：
```bash
ssh -L 33000:localhost:40004 -L 38000:localhost:38000 kcriss@10.212.227.125
```

3. **保持SSH窗口开启**（可以最小化）

4. **在浏览器访问**：
```
http://localhost:33000
```

**工作原理**：
```
您的浏览器 → localhost:33000 (本地)
              ↓ [SSH隧道]
服务器 → localhost:40004 (服务器上的前端)
       → localhost:38000 (服务器上的后端)
```

---

## 🔧 如果需要改回3000端口

```bash
# 停止当前服务
ps aux | grep "next dev" | awk '{print $2}' | xargs kill

# 在3000端口启动
cd /scratch/kcriss/MoshengAI/frontend
npm run dev
```

然后访问：
- 直接访问: `http://10.212.227.125:33000`
- SSH转发: `ssh -L 33000:localhost:33000 -L 38000:localhost:38000 kcriss@10.212.227.125`

---

## 📊 验证服务状态

### 在服务器上检查

```bash
# 检查端口监听
ss -tlnp | grep -E ':(40004|38000)'

# 检查进程
ps aux | grep -E "(next dev|uvicorn)"

# 本地测试
curl http://localhost:40004
curl http://localhost:38000/health
```

### 从开发机器检查

```bash
# 测试网络连通性
ping 10.212.227.125

# 测试端口（如果有telnet）
telnet 10.212.227.125 40004
telnet 10.212.227.125 38000
```

---

## 🐛 常见问题

### Q: `http://10.212.227.125:40004` 无法访问？

**检查1**: 您的开发机器和服务器是否在同一网络？
```bash
# 在开发机器上测试
ping 10.212.227.125
```

**检查2**: 服务是否真的在运行？
```bash
# 在服务器上检查
ss -tlnp | grep 40004
```

**解决**: 如果ping不通或不在同一网络，使用SSH端口转发（方案2）

---

### Q: SSH端口转发连接后，localhost:33000 还是无法访问？

**检查**: SSH隧道是否建立成功
```bash
# 在开发机器上，新开一个终端检查
lsof -i :33000   # Mac/Linux
netstat -ano | findstr :33000  # Windows
```

应该能看到SSH进程监听3000端口。

**解决**: 
1. 确保SSH命令中使用 `-L` 参数
2. 确保SSH窗口保持开启
3. 重新运行SSH命令

---

### Q: 前端打开了，但API调用失败？

**检查**: 后端是否运行
```bash
curl http://localhost:38000/health
# 应该返回: {"status":"ok"}
```

**解决**: 如果后端没运行，启动它
```bash
cd /scratch/kcriss/MoshengAI
bash ./start_backend.sh
```

---

## 🚀 完整使用流程

### 使用SSH端口转发（推荐）

1. **打开终端1**（在开发机器上）：
```bash
ssh -L 33000:localhost:40004 -L 38000:localhost:38000 kcriss@10.212.227.125
# 输入密码，保持连接
```

2. **打开浏览器**：
```
http://localhost:33000
```

3. **开始使用**：
   - 点击 "Change Voice" 选择音色
   - 输入文字
   - 点击发送生成语音

4. **结束时**：
   - 关闭浏览器
   - 在终端按 Ctrl+C 断开SSH

---

### 使用直接IP访问

1. **在浏览器打开**：
```
http://10.212.227.125:40004
```

2. **开始使用**（同上）

---

## 📁 相关文件

- **前端代码**: `/scratch/kcriss/MoshengAI/frontend/`
- **后端代码**: `/scratch/kcriss/MoshengAI/backend/`
- **启动脚本**: `/scratch/kcriss/MoshengAI/start_backend.sh`
- **配置文件**: `/scratch/kcriss/MoshengAI/frontend/src/lib/api.ts`

---

## 💡 提示

- API URL 已配置为自动适配，无需手动修改
- 音频预览和播放URL也已自动适配
- 服务器本地测试始终可用：`curl http://localhost:40004`

---

**现在您可以在开发机器上愉快地使用MoshengAI了！**

最后更新: 2025-12-07



