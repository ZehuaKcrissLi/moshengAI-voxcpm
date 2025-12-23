# v0.1 端口与环境变量口径

## 端口（统一口径）
- **前端 (Next.js)**：`33000`
- **后端 (FastAPI)**：`38000`
- **监控 (monitor_web)**：`33001`
- **PostgreSQL (docker)**：`5432`

## 环境变量（后端/监控共用）
后端与 `monitor_web.py` 都通过 `backend/app/core/config.py` 读取环境变量（pydantic-settings）。

### 必需变量
- `DATABASE_URL`
- `SECRET_KEY`
- `ALLOWED_ORIGINS`

### 示例文件
由于本 workspace 的全局规则会过滤 dotfiles（例如 `.env.example`），仓库提供：
- 根目录 `env.example`

你可以手工复制为 `.env`：
```bash
cp env.example .env
```

## 开发 vs 上线（暴露策略）
### 开发（便于联调）
- 前端、后端、监控监听 `0.0.0.0`，便于局域网/SSH 转发访问。

### v0.1 上线建议（最小安全）
- **对公网只暴露一个入口**（推荐 Nginx/Cloudflare Tunnel），内部服务只监听 `127.0.0.1`。
- `ALLOWED_ORIGINS` 只放你的真实域名（或固定的前端地址），不要用 `*`。
- `SECRET_KEY` 必须替换为长随机字符串（生产不可复用开发值）。

