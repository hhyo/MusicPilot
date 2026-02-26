# MusicPilot 部署指南

本文档介绍如何部署 MusicPilot 到生产环境。

---

## 📋 系统要求

- **操作系统**：Linux / macOS / Windows (WSL2)
- **Python**：3.12+
- **Node.js**：20.12.1+
- **数据库**：SQLite (默认) 或 PostgreSQL 14+
- **Redis**：6.0+ (可选，用于分布式缓存)
- **下载器**：qBittorrent 4.3+ 或 Transmission 3.0+ (可选)

---

## 🐳 Docker 部署（推荐）

### 快速启动

```bash
git clone https://github.com/hhyo/MusicPilot.git
cd MusicPilot
docker-compose up -d
```

### 配置

编辑 `docker-compose.yml` 配置环境变量：

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./config:/app/config
      - ./data:/app/data
      - ./downloads:/app/downloads
      - ./media:/app/media
    environment:
      - DATABASE_URL=sqlite:///./data/musicpilot.db
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=your-secret-key-here
      - TZ=Asia/Shanghai

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

volumes:
  redis-data:
```

### 目录结构

```
MusicPilot/
├── config/          # 配置文件
│   └── .env        # 环境变量
├── data/           # 数据库和缓存
├── downloads/      # 下载目录
└── media/          # 媒体库目录
```

---

## 💻 手动部署

### 1. 安装依赖

#### 后端

```bash
cd backend
pip install -r requirements.txt
```

#### 前端

```bash
cd frontend
npm install
```

### 2. 配置环境变量

创建 `backend/.env` 文件：

```env
# 数据库
DATABASE_URL=sqlite:///./data/musicpilot.db
# 或 PostgreSQL
# DATABASE_URL=postgresql+psycopg2://user:password@localhost/musicpilot

# Redis
REDIS_URL=redis://localhost:6379/0

# 安全
SECRET_KEY=your-secret-key-here

# 时区
TZ=Asia/Shanghai

# 下载器（可选）
QBITTORRENT_URL=http://localhost:8080
QBITTORRENT_USERNAME=admin
QBITTORRENT_PASSWORD=password

# 资源站点（可选）
# 在 Web 界面中配置
```

### 3. 初始化数据库

```bash
cd backend
alembic upgrade head
```

### 4. 构建前端

```bash
cd frontend
npm run build
```

### 5. 启动后端

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 6. 启动前端（开发模式）

```bash
cd frontend
npm run dev
```

### 7. 使用 Nginx 部署前端（生产环境）

创建 `/etc/nginx/sites-available/musicpilot`：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    root /path/to/MusicPilot/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/MusicPilot/frontend/dist/assets;
    }
}
```

启用站点：

```bash
sudo ln -s /etc/nginx/sites-available/musicpilot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔧 配置下载器

### qBittorrent

1. 安装 qBittorrent：
   ```bash
   sudo apt install qbittorrent-nox  # Ubuntu/Debian
   ```

2. 启动 qBittorrent：
   ```bash
   qbittorrent-nox
   ```

3. 访问 http://localhost:8080，登录并配置：
   - 默认用户名：admin
   - 默认密码：adminadmin

4. 在 MusicPilot 中配置 qBittorrent：
   - 地址：http://localhost:8080
   - 用户名和密码

### Transmission

1. 安装 Transmission：
   ```bash
   sudo apt install transmission-daemon  # Ubuntu/Debian
   ```

2. 配置 `/etc/transmission-daemon/settings.json`：
   ```json
   {
     "rpc-enabled": true,
     "rpc-bind-address": "0.0.0.0",
     "rpc-port": 9091,
     "rpc-username": "transmission",
     "rpc-password": "password",
     "download-dir": "/path/to/downloads"
   }
   ```

3. 重启 Transmission：
   ```bash
   sudo systemctl restart transmission-daemon
   ```

4. 在 MusicPilot 中配置 Transmission：
   - 地址：http://localhost:9091
   - 用户名和密码

---

## 🔍 配置资源站点

在 MusicPilot Web 界面中配置资源站点：

1. 访问 http://localhost:8080/sites
2. 点击"添加站点"
3. 填写站点信息：
   - 站点名称
   - 站点地址
   - Cookie 或 Passkey
   - User-Agent
   - 下载器选择

4. 测试连接

---

## 📊 监控和日志

### 查看后端日志

```bash
docker-compose logs -f backend
```

### 查看前端日志

```bash
docker-compose logs -f frontend
```

### 查看 Redis 日志

```bash
docker-compose logs -f redis
```

---

## 🔄 更新

### Docker 更新

```bash
git pull origin main
docker-compose down
docker-compose pull
docker-compose up -d
```

### 手动更新

```bash
git pull origin main
cd backend
pip install -r requirements.txt
alembic upgrade head
cd ../frontend
npm install
npm run build
```

---

## 🐛 故障排查

### 后端无法启动

1. 检查数据库连接：
   ```bash
   cat backend/.env | grep DATABASE_URL
   ```

2. 检查 Redis 连接：
   ```bash
   cat backend/.env | grep REDIS_URL
   redis-cli ping
   ```

3. 查看日志：
   ```bash
   docker-compose logs backend
   ```

### 前端无法访问

1. 检查 Nginx 配置：
   ```bash
   sudo nginx -t
   ```

2. 检查后端 API：
   ```bash
   curl http://localhost:8000/health
   ```

### 下载器无法连接

1. 检查下载器是否运行：
   ```bash
   sudo systemctl status qbittorrent-nox
   ```

2. 检查防火墙：
   ```bash
   sudo ufw status
   ```

3. 测试连接：
   ```bash
   curl http://localhost:8080/api/v2/app/version  # qBittorrent
   curl http://localhost:9091/transmission/rpc    # Transmission
   ```

---

## 📞 支持

- 问题反馈：[GitHub Issues](https://github.com/hhyo/MusicPilot/issues)
- 文档：[README.md](README.md)

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)