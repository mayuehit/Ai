# 微信小程序快速开始指南

## 🚀 5分钟快速部署

### 第一步：准备环境
```bash
# 1. 克隆项目
git clone https://github.com/mayuehit/Ai.git
cd Ai

# 2. 运行一键部署脚本
./scripts/deploy-wechat.sh your-domain.com
```

### 第二步：部署后端
```bash
# 1. 上传部署包到服务器
scp deploy-your-domain.com-*.tar.gz user@your-server:/tmp/

# 2. 在服务器上解压和配置
ssh user@your-server
tar -xzf /tmp/deploy-*.tar.gz
cd deploy-*

# 3. 配置环境变量
cp .env.example .env
nano .env  # 编辑配置

# 4. 启动服务（使用Docker）
docker-compose up -d

# 或使用Node.js直接运行
cd server
npm install
npm start
```

### 第三步：配置微信小程序
1. **注册微信小程序**（获取AppID）
2. **下载微信开发者工具**
3. **导入项目**：选择 `miniprogram` 目录
4. **修改配置**：
   - 在 `app.js` 中更新域名
   - 在 `project.config.json` 中填入AppID

### 第四步：微信后台配置
1. 登录[微信公众平台](https://mp.weixin.qq.com/)
2. 进入"开发" → "开发设置"
3. 配置服务器域名：
   - request合法域名: `https://your-domain.com`
   - socket合法域名: `wss://your-domain.com`
   - uploadFile合法域名: `https://your-domain.com`
   - downloadFile合法域名: `https://your-domain.com`

### 第五步：测试和发布
1. **本地测试**：在开发者工具点击"预览"
2. **真机调试**：点击"真机调试"
3. **上传代码**：点击"上传"到微信平台
4. **提交审核**：在微信后台提交版本审核
5. **发布上线**：审核通过后发布

## 📱 功能验证清单

### 基础功能测试
- [ ] 微信登录正常
- [ ] 创建游戏房间
- [ ] 加入房间（房间号/二维码）
- [ ] 房间内实时聊天
- [ ] 开始游戏流程
- [ ] 角色和词语分配
- [ ] 描述环节
- [ ] 投票环节
- [ ] 游戏结果展示
- [ ] 返回房间/再来一局

### 性能测试
- [ ] 页面加载速度 < 2秒
- [ ] 实时消息延迟 < 500ms
- [ ] 同时支持10个房间
- [ ] 内存使用正常
- [ ] 无崩溃和卡顿

### 兼容性测试
- [ ] iOS微信客户端
- [ ] Android微信客户端
- [ ] 不同屏幕尺寸
- [ ] 微信不同版本

## 🔧 故障排除

### 常见问题

#### 1. 微信登录失败
```javascript
// 检查项：
// 1. AppID配置是否正确
// 2. 微信后台域名配置
// 3. 后端服务是否运行
// 4. 网络连接是否正常
```

#### 2. WebSocket连接失败
```bash
# 检查项：
# 1. SSL证书配置
# 2. 防火墙端口开放
# 3. Nginx WebSocket代理配置
# 4. 后端WebSocket服务状态
```

#### 3. 实时消息延迟高
```javascript
// 优化建议：
// 1. 使用消息压缩
// 2. 优化数据库查询
// 3. 增加服务器带宽
// 4. 使用CDN加速
```

#### 4. 审核被拒
```
常见原因：
1. 功能不完整或有bug
2. 内容不符合规范
3. 缺少用户协议
4. 涉及敏感内容

解决方案：
1. 修复所有bug
2. 添加用户协议和隐私政策
3. 确保内容健康
4. 提供详细的功能说明
```

## 📊 监控和维护

### 日常监控
```bash
# 查看服务状态
docker-compose ps
pm2 list

# 查看日志
docker-compose logs -f backend
pm2 logs undercover-game

# 监控性能
htop  # CPU/内存
iftop # 网络流量
```

### 数据备份
```bash
# 备份MongoDB
docker exec undercover-mongodb mongodump --out /backup/

# 备份上传文件
tar -czf /backup/uploads-$(date +%Y%m%d).tar.gz /app/uploads
```

### 版本更新
```bash
# 更新后端
git pull origin main
docker-compose build --no-cache backend
docker-compose up -d backend

# 更新小程序
# 1. 修改代码
# 2. 在开发者工具上传新版本
# 3. 提交审核
```

## 🎯 成功指标

### 技术指标
- ✅ 服务可用性 > 99.9%
- ✅ 平均响应时间 < 100ms
- ✅ 错误率 < 0.1%
- ✅ 同时在线用户 > 1000

### 业务指标
- 📈 日活跃用户(DAU) > 1000
- 📈 用户留存率(7日) > 30%
- 📈 平均游戏时长 > 15分钟
- 📈 用户评分 > 4.5/5

## 📞 支持与帮助

### 文档资源
- [项目GitHub](https://github.com/mayuehit/Ai)
- [微信官方文档](https://developers.weixin.qq.com/miniprogram/dev/framework/)
- [部署指南](./DEPLOYMENT.md)

### 问题反馈
1. GitHub Issues: 提交技术问题
2. 微信客服: 处理用户反馈
3. 监控告警: 自动通知系统异常

### 社区支持
- 微信开发者社区
- GitHub Discussions
- 技术博客和教程

## 🎉 恭喜！
你的"谁是卧底"微信小程序已经准备就绪！

**下一步行动：**
1. 立即运行部署脚本
2. 配置你的域名和SSL
3. 在微信开发者工具中测试
4. 提交审核并发布

祝你的小程序上线成功！🎮✨