# 多阶段构建：后端服务

# 第一阶段：构建依赖
FROM node:18-alpine AS builder

WORKDIR /app

# 复制package文件
COPY server/package*.json ./

# 安装依赖（包括开发依赖）
RUN npm ci --only=production

# 第二阶段：运行环境
FROM node:18-alpine

WORKDIR /app

# 创建非root用户
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001 && \
    mkdir -p /app/uploads && \
    chown -R nodejs:nodejs /app

# 从构建阶段复制依赖
COPY --from=builder /app/node_modules ./node_modules

# 复制应用代码
COPY server/ ./

# 复制环境变量文件
COPY .env.example .env

# 设置权限
RUN chown -R nodejs:nodejs /app

# 切换到非root用户
USER nodejs

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "const http = require('http'); const options = { host: 'localhost', port: 3000, path: '/health', timeout: 2000 }; const req = http.request(options, (res) => { if (res.statusCode === 200) process.exit(0); else process.exit(1); }); req.on('error', () => process.exit(1)); req.end();"

# 暴露端口
EXPOSE 3000

# 启动命令
CMD ["node", "src/index.js"]