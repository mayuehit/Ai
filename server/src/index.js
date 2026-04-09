// 后端服务入口文件
const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const mongoose = require('mongoose');
const cors = require('cors');
require('dotenv').config();

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: '*',
    methods: ['GET', 'POST']
  }
});

// 中间件
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// 数据库连接
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/undercover', {
  useNewUrlParser: true,
  useUnifiedTopology: true
}).then(() => {
  console.log('✅ MongoDB连接成功');
}).catch(err => {
  console.error('❌ MongoDB连接失败:', err);
});

// 导入路由
const authRoutes = require('./routes/auth');
const roomRoutes = require('./routes/room');
const gameRoutes = require('./routes/game');

// 使用路由
app.use('/api/auth', authRoutes);
app.use('/api/rooms', roomRoutes);
app.use('/api/games', gameRoutes);

// WebSocket连接处理
io.on('connection', (socket) => {
  console.log('🔌 新客户端连接:', socket.id);

  // 加入房间
  socket.on('join-room', (roomCode) => {
    socket.join(roomCode);
    console.log(`用户 ${socket.id} 加入房间 ${roomCode}`);
    
    // 通知房间内其他用户
    socket.to(roomCode).emit('player-joined', {
      playerId: socket.id,
      timestamp: new Date()
    });
  });

  // 发送消息
  socket.on('send-message', ({ roomCode, content, type = 'text' }) => {
    const message = {
      id: Date.now().toString(),
      sender: socket.id,
      content,
      type,
      timestamp: new Date()
    };
    
    io.to(roomCode).emit('new-message', message);
  });

  // 开始游戏
  socket.on('start-game', (roomCode) => {
    // 游戏逻辑：分配角色和词语
    const gameData = {
      roomCode,
      status: 'playing',
      startTime: new Date(),
      players: [], // 这里需要从数据库获取玩家列表
      words: generateWords()
    };
    
    io.to(roomCode).emit('game-started', gameData);
  });

  // 投票
  socket.on('vote', ({ roomCode, targetPlayerId }) => {
    // 记录投票
    const voteData = {
      voter: socket.id,
      target: targetPlayerId,
      timestamp: new Date()
    };
    
    // 这里需要处理投票逻辑和结果判断
    io.to(roomCode).emit('vote-received', voteData);
  });

  // 断开连接
  socket.on('disconnect', () => {
    console.log('🔌 客户端断开连接:', socket.id);
  });
});

// 生成游戏词语
function generateWords() {
  const wordPairs = [
    { civilian: '苹果', undercover: '香蕉' },
    { civilian: '电脑', undercover: '手机' },
    { civilian: '夏天', undercover: '冬天' },
    { civilian: '咖啡', undercover: '茶' },
    { civilian: '电影', undercover: '电视剧' }
  ];
  
  const randomPair = wordPairs[Math.floor(Math.random() * wordPairs.length)];
  return randomPair;
}

// 健康检查端点
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date(),
    uptime: process.uptime(),
    database: mongoose.connection.readyState === 1 ? 'connected' : 'disconnected'
  });
});

// 错误处理中间件
app.use((err, req, res, next) => {
  console.error('❌ 服务器错误:', err);
  res.status(500).json({
    error: '服务器内部错误',
    message: process.env.NODE_ENV === 'development' ? err.message : undefined
  });
});

// 404处理
app.use('*', (req, res) => {
  res.status(404).json({ error: '接口不存在' });
});

// 启动服务器
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`🚀 服务器运行在端口 ${PORT}`);
  console.log(`📡 WebSocket服务已启动`);
  console.log(`🌐 健康检查: http://localhost:${PORT}/health`);
});

module.exports = { app, server, io };