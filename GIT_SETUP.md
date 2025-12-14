# MoshengAI Git 管理指南

## ✅ 当前状态

- **Git仓库**: 已初始化 ✅
- **最新提交**: `f7e053c - feat: Complete MoshengAI setup with all bug fixes`
- **提交文件数**: 51 个文件
- **代码行数**: 14,581+ 行
- **当前分支**: master
- **远程仓库**: ❌ 未配置

---

## 📊 已提交的内容

### 后端
- FastAPI 应用
- TTS 引擎集成
- 音色管理 API
- 异步任务队列

### 前端
- Next.js 16 应用
- React 19.2
- Tailwind CSS 4
- Framer Motion 动画
- 音色选择器
- TTS 生成界面

### 文档
- ACCESS_GUIDE.md - 完整访问指南
- BUGS_FIXED.md - Bug修复报告
- SYSTEM_SUMMARY.md - 系统总结
- NETWORK_TROUBLESHOOTING.md - 网络诊断
- SSH_TROUBLESHOOTING.md - SSH故障排查

### 配置
- Docker Compose 配置
- 启动脚本
- 服务状态检查脚本

---

## 🚀 如何添加远程仓库并Push

### 方案1：推送到 GitHub

#### 1. 创建GitHub仓库

访问 https://github.com/new 创建新仓库：
- 仓库名: `MoshengAI`
- 描述: `Magic Voice AI - Professional AI Voice Synthesis Service`
- 可见性: Private（推荐）或 Public
- **不要**勾选 "Initialize with README"（已有代码）

#### 2. 添加远程仓库

```bash
cd /scratch/kcriss/MoshengAI

# 添加远程仓库（替换YOUR_USERNAME）
git remote add origin git@github.com:YOUR_USERNAME/MoshengAI.git

# 或使用HTTPS
git remote add origin https://github.com/YOUR_USERNAME/MoshengAI.git
```

#### 3. 推送到GitHub

```bash
# 推送master分支
git push -u origin master
```

---

### 方案2：推送到 GitLab

#### 1. 创建GitLab项目

访问 https://gitlab.com/projects/new 创建项目

#### 2. 添加远程仓库

```bash
git remote add origin git@gitlab.com:YOUR_USERNAME/MoshengAI.git
# 或
git remote add origin https://gitlab.com/YOUR_USERNAME/MoshengAI.git
```

#### 3. 推送

```bash
git push -u origin master
```

---

### 方案3：推送到私有Git服务器

```bash
# 添加远程仓库
git remote add origin user@your-server.com:/path/to/MoshengAI.git

# 推送
git push -u origin master
```

---

## 🔑 SSH密钥配置（推荐）

如果使用SSH方式（`git@github.com`），需要配置SSH密钥：

### 1. 检查是否已有SSH密钥

```bash
ls -la ~/.ssh/id_*.pub
```

### 2. 如果没有，生成新密钥

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
# 或
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

### 3. 复制公钥

```bash
cat ~/.ssh/id_ed25519.pub
# 或
cat ~/.ssh/id_rsa.pub
```

### 4. 添加到GitHub/GitLab

- **GitHub**: Settings → SSH and GPG keys → New SSH key
- **GitLab**: Preferences → SSH Keys

---

## 📝 常用Git命令

### 查看状态

```bash
cd /scratch/kcriss/MoshengAI
git status
```

### 添加新文件

```bash
git add .
git commit -m "描述信息"
```

### 推送到远程

```bash
git push origin master
```

### 拉取更新

```bash
git pull origin master
```

### 查看日志

```bash
git log --oneline -10
```

### 查看远程仓库

```bash
git remote -v
```

### 修改远程仓库地址

```bash
git remote set-url origin NEW_URL
```

---

## 🔄 建议的工作流程

### 日常开发

```bash
# 1. 修改代码后查看变更
git status

# 2. 添加变更
git add .

# 3. 提交
git commit -m "描述信息"

# 4. 推送到远程
git push
```

### 分支管理

```bash
# 创建开发分支
git checkout -b develop

# 切换分支
git checkout master

# 合并分支
git merge develop

# 推送分支
git push origin develop
```

---

## 🛡️ .gitignore 说明

已配置忽略：
- ✅ Python缓存和虚拟环境
- ✅ Node.js node_modules
- ✅ 音频文件（.wav, .mp3等）
- ✅ 大型模型文件（.pth, .pt等）
- ✅ 环境变量文件（.env）
- ✅ IDE配置
- ✅ 生成的音频文件

---

## 📊 仓库统计

```bash
# 查看仓库大小
du -sh .git

# 查看文件数量
git ls-files | wc -l

# 查看代码统计
git diff --stat $(git rev-list --max-parents=0 HEAD) HEAD
```

---

## ⚠️ 重要提示

### 不要提交的内容
- ❌ 大型模型文件（超过100MB）
- ❌ 生成的音频文件
- ❌ 密钥和密码
- ❌ .env 文件
- ❌ 个人配置

### 如果意外提交了大文件

使用 Git LFS 或从历史中删除：

```bash
# 安装 Git LFS
git lfs install

# 追踪大文件
git lfs track "*.pth"
git lfs track "*.pt"

# 提交 .gitattributes
git add .gitattributes
git commit -m "Add Git LFS tracking"
```

---

## 🚀 快速开始

### 如果你还没有GitHub账号

1. 访问 https://github.com/signup
2. 注册账号
3. 创建新仓库
4. 按照上面的步骤添加远程仓库并推送

### 快速命令（替换YOUR_USERNAME）

```bash
cd /scratch/kcriss/MoshengAI

# 添加远程仓库
git remote add origin https://github.com/YOUR_USERNAME/MoshengAI.git

# 推送
git push -u origin master
```

---

## 📞 需要帮助？

如果推送时遇到问题：

1. **认证失败**: 检查用户名/密码或SSH密钥
2. **权限拒绝**: 确认仓库所有权和访问权限
3. **文件太大**: 使用Git LFS或移除大文件
4. **冲突**: 先pull再push

---

**现在您的代码已经安全地保存在Git中！添加远程仓库后即可推送。**

最后更新: 2025-12-07


