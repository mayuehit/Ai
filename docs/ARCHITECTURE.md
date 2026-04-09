# 系统架构设计文档

## 1. 整体架构

### 1.1 架构图
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  微信小程序前端  │────│   后端API服务    │────│     数据库       │
│                 │    │                 │    │                 │
│ • WXML/WXSS/JS  │    │ • Express.js    │    │ • MongoDB       │
│ • 小程序组件     │    │ • Socket.io     │    │ • Redis缓存     │
│ • 云函数        │    │ • REST API      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                         ┌─────────────────┐
                         │   实时通信服务   │
                         │                 │
                         │ • WebSocket     │
                         │ • 房间管理      │
                         │ • 消息广播      │
                         └─────────────────┘
```

### 1.2 技术选型
- **前端**: 微信小程序原生开发
- **后端**: Node.js + Express + Socket.io
- **数据库**: MongoDB (主数据) + Redis (缓存/会话)
- **部署**: Docker + Nginx + PM2
- **监控**: Sentry + 微信小程序监控

## 2. 模块设计

### 2.1 前端模块
```
miniprogram/
├── pages/           # 页面文件
│   ├── index/      # 首页
│   ├── room/       # 游戏房间
│   ├── game/       # 游戏主界面
│   └── profile/    # 个人中心
├── components/     # 自定义组件
│   ├── player-card # 玩家卡片
│   ├── chat-box    # 聊天框
│   └── vote-modal  # 投票弹窗
├── utils/          # 工具函数
│   ├── api.js      # API封装
│   ├── socket.js   # WebSocket封装
│   └── game-logic.js # 游戏逻辑
└── app.js          # 小程序入口
```

### 2.2 后端模块
```
server/
├── src/
│   ├── index.js           # 服务入口
│   ├── routes/           # 路由层
│   │   ├── auth.js       # 认证相关
│   │   ├── room.js       # 房间管理
│   │   └── game.js       # 游戏逻辑
│   ├── controllers/      # 控制器层
│   ├── services/         # 业务逻辑层
│   ├── models/          # 数据模型
│   │   ├── User.js      # 用户模型
│   │   ├── Room.js      # 房间模型
│   │   └── Game.js      # 游戏模型
│   └── middleware/       # 中间件
├── config/              # 配置文件
└── tests/               # 测试文件
```

## 3. 数据库设计

### 3.1 MongoDB集合设计
```javascript
// 用户集合
{
  _id: ObjectId,
  openid: String,      // 微信openid
  nickname: String,    // 昵称
  avatar: String,      // 头像
  games_played: Number, // 游戏次数
  win_rate: Number,    // 胜率
  created_at: Date
}

// 房间集合
{
  _id: ObjectId,
  room_code: String,   // 房间号
  creator: ObjectId,   // 创建者ID
  players: [ObjectId], // 玩家列表
  status: String,      // 状态: waiting/playing/ended
  settings: {
    max_players: Number,
    rounds: Number,
    time_limit: Number
  },
  created_at: Date
}

// 游戏记录集合
{
  _id: ObjectId,
  room_id: ObjectId,
  players: [{
    user_id: ObjectId,
    role: String,      // civilian/undercover
    score: Number
  }],
  words: {
    civilian: String,
    undercover: String
  },
  result: {
    winner: String,    // civilian/undercover
    undercover_id: ObjectId
  },
  created_at: Date
}
```

### 3.2 Redis使用场景
- 用户会话管理
- 游戏房间实时状态
- WebSocket连接映射
- 高频查询缓存

## 4. API设计

### 4.1 RESTful API
```
GET    /api/users/:id        # 获取用户信息
POST   /api/rooms           # 创建房间
GET    /api/rooms/:code     # 获取房间信息
POST   /api/rooms/:code/join # 加入房间
POST   /api/games           # 开始游戏
POST   /api/games/:id/vote  # 投票
```

### 4.2 WebSocket事件
```javascript
// 客户端发送
socket.emit('join-room', { roomCode })
socket.emit('send-message', { content })
socket.emit('vote', { targetPlayerId })

// 服务端广播
socket.on('player-joined', (player) => {})
socket.on('new-message', (message) => {})
socket.on('game-started', (gameInfo) => {})
socket.on('vote-result', (result) => {})
```

## 5. 安全设计

### 5.1 认证授权
- 微信登录获取openid
- JWT token认证
- 接口权限控制

### 5.2 数据安全
- 敏感数据加密存储
- SQL/NoSQL注入防护
- XSS攻击防护

### 5.3 游戏公平性
- 服务器端游戏逻辑验证
- 防作弊检测
- 操作时间戳验证

## 6. 性能优化

### 6.1 前端优化
- 图片懒加载
- 数据分页加载
- 本地缓存策略

### 6.2 后端优化
- 数据库索引优化
- 查询结果缓存
- 连接池管理

### 6.3 实时通信优化
- 消息压缩
- 心跳检测
- 断线重连

## 7. 部署架构

### 7.1 开发环境
- 本地开发服务器
- 热重载支持
- 模拟数据

### 7.2 测试环境
- 独立测试服务器
- 自动化测试
- 性能测试

### 7.3 生产环境
- 负载均衡
- 数据库主从复制
- 监控告警系统