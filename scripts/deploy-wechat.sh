#!/bin/bash

# 微信小程序一键部署脚本
# 使用方法: ./deploy-wechat.sh your-domain.com

set -e

echo "🚀 开始部署微信小程序..."

# 检查参数
if [ $# -eq 0 ]; then
    echo "❌ 请提供域名参数"
    echo "使用方法: $0 your-domain.com"
    exit 1
fi

DOMAIN=$1
BACKEND_URL="https://$DOMAIN"
WS_URL="wss://$DOMAIN"

echo "🌐 域名: $DOMAIN"
echo "🔗 后端地址: $BACKEND_URL"
echo "🔌 WebSocket地址: $WS_URL"

# 1. 更新小程序配置
echo "📝 更新小程序配置..."
sed -i "s|https://api.example.com|$BACKEND_URL|g" miniprogram/app.js
sed -i "s|wss://api.example.com|$WS_URL|g" miniprogram/app.js

echo "✅ 小程序配置更新完成"

# 2. 准备部署目录
echo "📁 准备部署文件..."
DEPLOY_DIR="deploy/$(date +%Y%m%d_%H%M%S)"
mkdir -p $DEPLOY_DIR

# 复制小程序文件
cp -r miniprogram/* $DEPLOY_DIR/

# 3. 生成部署说明
cat > $DEPLOY_DIR/DEPLOY_README.md << EOF
# 微信小程序部署说明

## 部署时间
$(date)

## 配置信息
- 后端域名: $DOMAIN
- API地址: $BACKEND_URL/api
- WebSocket地址: $WS_URL

## 部署步骤

### 1. 后端部署
\`\`\`bash
# 在服务器上执行
cd server
npm install
npm start

# 或使用PM2
pm2 start src/index.js --name "undercover-game"
\`\`\`

### 2. 微信小程序配置
1. 打开微信开发者工具
2. 导入本目录
3. 配置AppID
4. 在微信公众平台配置域名:
   - request合法域名: $BACKEND_URL
   - socket合法域名: $WS_URL
   - uploadFile合法域名: $BACKEND_URL
   - downloadFile合法域名: $BACKEND_URL

### 3. 测试
1. 点击"预览"生成二维码
2. 手机扫描测试
3. 检查所有功能

### 4. 上传发布
1. 点击"上传"
2. 填写版本信息
3. 提交微信审核
EOF

echo "📄 部署说明已生成: $DEPLOY_DIR/DEPLOY_README.md"

# 4. 生成Nginx配置
cat > $DEPLOY_DIR/nginx.conf << EOF
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    # SSL证书（需要手动配置）
    ssl_certificate /etc/nginx/ssl/$DOMAIN.crt;
    ssl_certificate_key /etc/nginx/ssl/$DOMAIN.key;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    location /ws {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host \$host;
    }
}
EOF

echo "🔧 Nginx配置已生成: $DEPLOY_DIR/nginx.conf"

# 5. 生成环境变量模板
cat > $DEPLOY_DIR/.env.example << EOF
# 后端服务配置
NODE_ENV=production
PORT=3000
HOST=0.0.0.0

# 数据库配置
MONGODB_URI=mongodb://localhost:27017/undercover
REDIS_URL=redis://localhost:6379

# 安全配置
JWT_SECRET=your-super-secret-jwt-key-change-this
JWT_EXPIRES_IN=7d

# 微信配置
WECHAT_APPID=你的微信小程序AppID
WECHAT_SECRET=你的微信小程序Secret

# 域名配置
DOMAIN=$DOMAIN
BACKEND_URL=$BACKEND_URL
WS_URL=$WS_URL
EOF

echo "⚙️ 环境变量模板已生成: $DEPLOY_DIR/.env.example"

# 6. 生成微信小程序审核材料
cat > $DEPLOY_DIR/REVIEW_GUIDE.md << EOF
# 微信小程序审核指南

## 基本信息
- 小程序名称: 谁是卧底
- 类目: 游戏 > 休闲游戏
- 版本: 1.0.0

## 功能说明
这是一个社交推理游戏"谁是卧底"的微信小程序版本。
玩家可以创建房间，邀请好友一起游戏，通过描述词语推理出卧底身份。

## 测试账号
（如果需要登录测试，请提供测试账号）

## 审核注意事项
1. 游戏为休闲益智类，无赌博性质
2. 内容健康，无敏感信息
3. 已添加用户协议和隐私政策
4. 所有功能均可正常使用

## 截图要求
请准备以下截图：
1. 首页截图
2. 游戏房间截图
3. 游戏进行中截图
4. 个人中心截图
EOF

echo "📋 审核指南已生成: $DEPLOY_DIR/REVIEW_GUIDE.md"

# 7. 打包部署文件
echo "📦 打包部署文件..."
tar -czf deploy-$DOMAIN-$(date +%Y%m%d).tar.gz $DEPLOY_DIR/

echo "🎉 部署包已创建: deploy-$DOMAIN-$(date +%Y%m%d).tar.gz"

# 8. 显示下一步操作
echo ""
echo "========================================="
echo "✅ 部署准备完成！"
echo ""
echo "📁 部署文件位于: $DEPLOY_DIR"
echo "📦 压缩包: deploy-$DOMAIN-$(date +%Y%m%d).tar.gz"
echo ""
echo "🚀 下一步操作:"
echo "1. 将压缩包上传到服务器"
echo "2. 配置域名和SSL证书"
echo "3. 启动后端服务"
echo "4. 在微信开发者工具中导入小程序"
echo "5. 配置微信公众平台域名"
echo "6. 测试并提交审核"
echo "========================================="