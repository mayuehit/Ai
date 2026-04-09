# 部署指南

## 项目概述
"谁是卧底"微信小程序是一个完整的社交推理游戏，包含前端微信小程序和后端Node.js服务。

## 系统要求

### 服务器要求
- **操作系统**: Ubuntu 20.04+ / CentOS 7+ / macOS
- **Node.js**: 18.x 或更高版本
- **MongoDB**: 4.4+ (用于主数据库)
- **Redis**: 6.0+ (可选，用于缓存和会话)
- **内存**: 至少2GB RAM
- **存储**: 至少10GB可用空间

### 微信小程序要求
- 微信开发者账号
- 已注册的小程序AppID
- 小程序开发工具

## 快速开始

### 1. 克隆项目
```bash
git clone https://github.com/mayuehit/Ai.git
cd Ai
```

### 2. 安装依赖
```bash
# 安装后端依赖
cd server
npm install

# 安装前端依赖（如果需要构建）
cd ../miniprogram
# 微信小程序不需要npm install，直接使用微信开发者工具
```

### 3. 环境配置
创建 `.env` 文件：
```bash
cd server
cp .env.example .env
```

编辑 `.env` 文件：
```env
# 服务器配置
NODE_ENV=production
PORT=3000
HOST=0.0.0.0

# 数据库配置
MONGODB_URI=mongodb://localhost:27017/undercover
REDIS_URL=redis://localhost:6379

# JWT配置
JWT_SECRET=your-super-secret-jwt-key-change-this
JWT_EXPIRES_IN=7d

# 微信小程序配置
WECHAT_APPID=your-wechat-appid
WECHAT_SECRET=your-wechat-secret

# 文件上传配置
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=5242880 # 5MB

# 邮件配置（可选）
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-email-password
```

### 4. 初始化数据库
```bash
# 启动MongoDB服务
sudo systemctl start mongod

# 创建数据库和集合
mongo undercover --eval "db.createCollection('users')"
mongo undercover --eval "db.createCollection('words')"
mongo undercover --eval "db.createCollection('games')"

# 导入初始词语数据
mongoimport --db undercover --collection words --file server/data/initial-words.json --jsonArray
```

### 5. 启动服务
```bash
# 开发模式
npm run dev

# 生产模式
npm start

# 使用PM2管理（推荐）
npm install -g pm2
pm2 start server/src/index.js --name "undercover-game"
pm2 save
pm2 startup
```

## 微信小程序配置

### 1. 微信开发者工具设置
1. 打开微信开发者工具
2. 导入项目：选择 `miniprogram` 目录
3. 填写AppID（需要注册微信小程序）
4. 配置服务器域名：
   - request合法域名: `https://your-domain.com`
   - socket合法域名: `wss://your-domain.com`
   - uploadFile合法域名: `https://your-domain.com`
   - downloadFile合法域名: `https://your-domain.com`

### 2. 小程序配置修改
编辑 `miniprogram/app.js`：
```javascript
// 修改API地址
const API_BASE = 'https://your-domain.com/api';
const WS_URL = 'wss://your-domain.com';
```

## 生产环境部署

### 使用Docker部署（推荐）

#### 1. 构建Docker镜像
```bash
# 构建后端镜像
docker build -t undercover-game:latest -f Dockerfile.backend .

# 构建前端镜像（如果需要）
docker build -t undercover-game-frontend:latest -f Dockerfile.frontend .
```

#### 2. 使用Docker Compose
创建 `docker-compose.yml`：
```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:6
    container_name: undercover-mongodb
    restart: always
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: your-mongodb-password
    volumes:
      - mongodb_data:/data/db
      - ./server/data/initial-words.json:/docker-entrypoint-initdb.d/initial-words.json

  redis:
    image: redis:7-alpine
    container_name: undercover-redis
    restart: always
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  backend:
    image: undercover-game:latest
    container_name: undercover-backend
    restart: always
    ports:
      - "3000:3000"
    environment:
      NODE_ENV: production
      MONGODB_URI: mongodb://admin:your-mongodb-password@mongodb:27017/undercover?authSource=admin
      REDIS_URL: redis://redis:6379
      JWT_SECRET: your-jwt-secret
    depends_on:
      - mongodb
      - redis
    volumes:
      - uploads_data:/app/uploads

  nginx:
    image: nginx:alpine
    container_name: undercover-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend

volumes:
  mongodb_data:
  redis_data:
  uploads_data:
```

#### 3. 启动服务
```bash
docker-compose up -d
```

### 使用Nginx反向代理
创建 `nginx.conf`：
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL证书
    ssl_certificate /etc/nginx/ssl/your-domain.com.crt;
    ssl_certificate_key /etc/nginx/ssl/your-domain.com.key;
    
    # SSL配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # 静态文件
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }
    
    # API代理
    location /api {
        proxy_pass http://backend:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket代理
    location /ws {
        proxy_pass http://backend:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 监控和维护

### 日志管理
```bash
# 查看实时日志
pm2 logs undercover-game

# 查看特定日期的日志
tail -f /var/log/undercover/access.log
tail -f /var/log/undercover/error.log

# 日志轮转配置（logrotate）
sudo nano /etc/logrotate.d/undercover-game
```

### 性能监控
```bash
# 使用PM2监控
pm2 monit

# 查看系统资源
htop
free -h
df -h

# 监控网络连接
netstat -tulpn | grep :3000
```

### 备份和恢复
```bash
# 备份MongoDB
mongodump --db undercover --out /backup/undercover-$(date +%Y%m%d)

# 恢复MongoDB
mongorestore --db undercover /backup/undercover-20240101

# 备份上传文件
tar -czf /backup/uploads-$(date +%Y%m%d).tar.gz /app/uploads
```

## 安全配置

### 1. 防火墙配置
```bash
# 只开放必要端口
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 3000/tcp  # 开发端口（可选）
sudo ufw enable
```

### 2. SSL证书
```bash
# 使用Let's Encrypt获取免费证书
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

### 3. 数据库安全
```bash
# 启用MongoDB认证
use admin
db.createUser({
  user: "admin",
  pwd: "strong-password",
  roles: ["root"]
})

# 限制MongoDB只监听本地
sudo nano /etc/mongod.conf
# 添加: bindIp: 127.0.0.1
```

## 故障排除

### 常见问题

#### 1. 服务无法启动
```bash
# 检查端口占用
sudo lsof -i :3000

# 检查日志
pm2 logs undercover-game --lines 100

# 检查依赖
npm list --depth=0
```

#### 2. 数据库连接失败
```bash
# 检查MongoDB服务
sudo systemctl status mongod

# 测试连接
mongo --host localhost --port 27017

# 检查连接字符串
echo $MONGODB_URI
```

#### 3. WebSocket连接失败
```bash
# 检查防火墙
sudo ufw status

# 测试WebSocket
wscat -c wss://your-domain.com/ws

# 检查Nginx配置
sudo nginx -t
```

#### 4. 微信小程序无法连接
```bash
# 检查域名备案
# 检查SSL证书
# 检查微信小程序后台配置
```

### 性能优化建议

1. **数据库索引优化**
```javascript
// 为常用查询添加索引
db.users.createIndex({ openid: 1 }, { unique: true });
db.words.createIndex({ category: 1, difficulty: 1 });
db.games.createIndex({ roomCode: 1 }, { unique: true });
```

2. **启用Gzip压缩**
```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
```

3. **配置缓存**
```nginx
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## 更新部署

### 手动更新
```bash
# 拉取最新代码
git pull origin main

# 安装新依赖
npm install

# 重启服务
pm2 restart undercover-game

# 运行数据库迁移（如果有）
npm run migrate
```

### 自动化更新（使用CI/CD）
配置GitHub Actions或Jenkins实现自动部署。

## 支持与联系

- **项目文档**: [https://github.com/mayuehit/Ai](https://github.com/mayuehit/Ai)
- **问题反馈**: [GitHub Issues](https://github.com/mayuehit/Ai/issues)
- **社区讨论**: [Discord/Slack链接]

## 许可证
MIT License - 详见 LICENSE 文件