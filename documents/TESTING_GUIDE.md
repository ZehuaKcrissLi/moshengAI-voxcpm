# MoshengAI MVP 测试指南

## 🚀 快速测试流程

### 步骤1：检查服务状态

```bash
# 进入项目目录
cd /scratch/kcriss/MoshengAI

# 检查后端服务
curl http://localhost:8000/health
# 应该返回: {"status":"ok"}

# 检查前端服务
curl -s http://localhost:3000 | grep -q "Mosheng" && echo "✅ 前端运行中" || echo "❌ 前端未运行"

# 检查音色库
curl -s http://localhost:8000/voices/ | python3 -c "import sys,json; print(f'✅ {len(json.load(sys.stdin))} 个音色可用')"
```

### 步骤2：前端完整测试（推荐）

#### 2.1 访问前端界面
```bash
# 如果在服务器上，使用SSH端口转发
ssh -L 3000:localhost:3000 -L 8000:localhost:8000 kcriss@10.212.227.125

# 然后在本地浏览器访问
http://localhost:3000
```

#### 2.2 注册新账号
1. 点击右上角 **"Log in"** 按钮
2. 切换到 **"Sign Up"** 标签
3. 输入邮箱和密码（至少8位）
   - 例如：`test@example.com` / `password123`
4. 点击 **"Sign Up"**
5. ✅ 应该自动登录，左侧显示你的邮箱和 **100 credits**

#### 2.3 测试音频生成（需修复TTS引擎）
1. 点击底部输入框旁边的 **音色选择器**
2. 从抽屉中选择一个音色
3. 在输入框输入测试文字：`你好，这是一个测试`
4. 点击发送按钮
5. ✅ 应该看到积分扣除（约4-5积分）
6. ✅ 音频生成后自动播放

#### 2.4 测试登出和登录
1. 点击左侧边栏底部 **"Logout"** 按钮
2. 再次点击 **"Log in"**
3. 使用刚才的邮箱密码登录
4. ✅ 应该看到之前的对话历史和剩余积分

---

### 步骤3：后端API测试

创建测试脚本：

```bash
cat > /tmp/test_api.sh << 'EOF'
#!/bin/bash
set -e

API_URL="http://localhost:8000"
EMAIL="test_$(date +%s)@example.com"
PASSWORD="testpass123"

echo "======================================"
echo "MoshengAI API 功能测试"
echo "======================================"

# 1. 测试注册
echo -e "\n[1/6] 测试用户注册..."
REGISTER_RESULT=$(curl -s -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}")

echo "$REGISTER_RESULT" | python3 -m json.tool
USER_ID=$(echo "$REGISTER_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "✅ 注册成功，用户ID: $USER_ID"

# 2. 测试登录
echo -e "\n[2/6] 测试用户登录..."
LOGIN_RESULT=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$EMAIL&password=$PASSWORD")

TOKEN=$(echo "$LOGIN_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "✅ 登录成功，Token: ${TOKEN:0:50}..."

# 3. 测试获取用户信息
echo -e "\n[3/6] 测试获取用户信息..."
curl -s "$API_URL/auth/me" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo "✅ 获取用户信息成功"

# 4. 测试查询积分
echo -e "\n[4/6] 测试查询积分余额..."
BALANCE=$(curl -s "$API_URL/credits/balance" \
  -H "Authorization: Bearer $TOKEN")
echo "$BALANCE" | python3 -m json.tool
CREDITS=$(echo "$BALANCE" | python3 -c "import sys,json; print(json.load(sys.stdin)['balance'])")
echo "✅ 当前积分: $CREDITS"

# 5. 测试查询音色库
echo -e "\n[5/6] 测试查询音色库..."
VOICES=$(curl -s "$API_URL/voices/")
VOICE_COUNT=$(echo "$VOICES" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
FIRST_VOICE=$(echo "$VOICES" | python3 -c "import sys,json; v=json.load(sys.stdin); print(v[0]['id'] if v else '')")
echo "✅ 音色数量: $VOICE_COUNT"
echo "✅ 第一个音色ID: $FIRST_VOICE"

# 6. 测试提交TTS任务（需要TTS引擎正常运行）
echo -e "\n[6/6] 测试提交TTS生成任务..."
if [ -n "$FIRST_VOICE" ]; then
  TASK_RESULT=$(curl -s -X POST "$API_URL/tts/generate" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"text\": \"这是一个测试\", \"voice_id\": \"$FIRST_VOICE\"}" \
    2>&1)
  
  echo "$TASK_RESULT" | python3 -m json.tool 2>/dev/null || echo "$TASK_RESULT"
  
  if echo "$TASK_RESULT" | grep -q "task_id"; then
    TASK_ID=$(echo "$TASK_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['task_id'])")
    echo "✅ 任务提交成功，ID: $TASK_ID"
    
    # 查询任务状态
    echo -e "\n查询任务状态..."
    sleep 2
    curl -s "$API_URL/tts/status/$TASK_ID" \
      -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
    
    # 检查积分是否扣除
    echo -e "\n检查积分扣除..."
    NEW_BALANCE=$(curl -s "$API_URL/credits/balance" \
      -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; print(json.load(sys.stdin)['balance'])")
    DEDUCTED=$((CREDITS - NEW_BALANCE))
    echo "✅ 积分扣除: $DEDUCTED (剩余: $NEW_BALANCE)"
  else
    echo "⚠️  任务提交失败（可能是TTS引擎未运行）"
  fi
else
  echo "⚠️  跳过TTS测试（无可用音色）"
fi

echo -e "\n======================================"
echo "✅ 测试完成！"
echo "======================================"
EOF

chmod +x /tmp/test_api.sh
```

运行测试：

```bash
bash /tmp/test_api.sh
```

---

### 步骤4：数据库验证

```bash
# 查看数据库中的用户
cd /scratch/kcriss/MoshengAI
source .venv/bin/activate

python3 << 'EOF'
import asyncio
import sqlite3

conn = sqlite3.connect('mosheng.db')
cursor = conn.cursor()

print("📊 用户列表:")
print("-" * 80)
cursor.execute("SELECT id, email, provider, credits_balance, created_at FROM users")
for row in cursor.fetchall():
    print(f"ID: {row[0][:20]}... | 邮箱: {row[1]} | 提供商: {row[2]} | 积分: {row[3]} | 创建时间: {row[4]}")

print("\n📊 任务列表:")
print("-" * 80)
cursor.execute("SELECT id, user_id, text, status, cost, created_at FROM tasks")
tasks = cursor.fetchall()
if tasks:
    for row in tasks:
        print(f"ID: {row[0][:20]}... | 用户: {row[1][:20]}... | 文本: {row[2][:30]} | 状态: {row[3]} | 费用: {row[4]}")
else:
    print("暂无任务记录")

conn.close()
EOF
```

---

## 🔍 常见问题排查

### 问题1：后端未运行
```bash
# 检查端口
ss -tlnp | grep :8000

# 如果没有，启动后端
cd /scratch/kcriss/MoshengAI
source .venv/bin/activate
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 &

# 查看日志
tail -f /tmp/backend.log
```

### 问题2：前端未运行
```bash
# 检查端口
ss -tlnp | grep :3000

# 如果没有，启动前端
cd /scratch/kcriss/MoshengAI/frontend
npm run dev &
```

### 问题3：401 Unauthorized
**原因**：Token过期或无效

**解决**：
1. 前端重新登录
2. 或使用新的token测试

### 问题4：402 Insufficient Credits
**原因**：积分不足

**解决**：
```bash
# 方法1：创建新账号（自动100积分）

# 方法2：管理员手动充值（需先设置is_admin=1）
# 在数据库中：
sqlite3 /scratch/kcriss/MoshengAI/mosheng.db
UPDATE users SET is_admin=1 WHERE email='mvp@mosheng.ai';
.quit

# 然后调用充值API
TOKEN="你的管理员token"
curl -X POST http://localhost:8000/credits/add \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "目标用户ID", "amount": 1000, "reason": "测试充值"}'
```

### 问题5：TTS生成失败
**原因**：transformers版本兼容问题

**临时解决**：
```bash
# 查看错误日志
tail -100 /tmp/backend.log | grep -A 10 "TTS"

# 注意：当前TTS引擎有兼容性问题，不影响认证和积分测试
# 如需修复，可能需要调整transformers版本
```

---

## 📋 测试检查清单

### 后端功能
- [ ] 用户注册（邮箱+密码）
- [ ] 用户登录（返回JWT token）
- [ ] 获取当前用户信息
- [ ] 查询积分余额
- [ ] 查询音色库
- [ ] 提交TTS任务（需扣除积分）
- [ ] 查询任务状态
- [ ] 积分正确扣除

### 前端功能
- [ ] 注册界面正常显示
- [ ] 注册成功后自动登录
- [ ] 左侧显示用户信息和积分
- [ ] 音色选择器正常工作
- [ ] 发送按钮在未登录时提示登录
- [ ] 发送按钮在积分不足时提示充值
- [ ] 登出功能正常
- [ ] 登录后恢复用户状态

### OAuth预留接口（当前返回501）
- [ ] GET /auth/oauth/google/login - 返回501
- [ ] GET /auth/oauth/github/login - 返回501
- [ ] GET /auth/oauth/wechat/login - 返回501
- [ ] POST /auth/oauth/callback - 返回501

---

## 🎯 推荐测试顺序

### 方案A：快速验证（5分钟）
1. 运行后端API测试脚本 (`/tmp/test_api.sh`)
2. 检查所有API是否正常返回
3. 查看数据库是否有记录

### 方案B：完整用户流程（10分钟）
1. 启动SSH端口转发
2. 浏览器访问 `http://localhost:3000`
3. 完整走一遍：注册→登录→选音色→生成→登出→登录
4. 验证积分扣除和任务记录

### 方案C：压力测试（可选）
```bash
# 创建100个用户并发注册
for i in {1..100}; do
  curl -s -X POST http://localhost:8000/auth/register \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"user${i}@test.com\", \"password\": \"test1234\"}" &
done
wait

# 检查数据库
sqlite3 /scratch/kcriss/MoshengAI/mosheng.db "SELECT COUNT(*) FROM users;"
```

---

## 📊 预期结果

### 成功标准
- ✅ 所有后端API返回正确的HTTP状态码和JSON
- ✅ 用户注册后自动获得100积分
- ✅ JWT token验证正常工作
- ✅ 积分扣除逻辑正确
- ✅ 数据库正确保存用户和任务记录
- ✅ 前端登录流程完整无误

### 已知限制
- ⚠️ TTS引擎可能因transformers版本问题无法初始化
- ⚠️ OAuth功能为预留接口，返回501状态
- ⚠️ 支付功能未实现，需管理员手动充值

---

**祝测试顺利！如有问题请查看 `/tmp/backend.log` 日志文件。**

