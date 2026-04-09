const mongoose = require('mongoose');

const userSchema = new mongoose.Schema({
  // 微信相关字段
  openid: {
    type: String,
    required: true,
    unique: true,
    index: true
  },
  unionid: {
    type: String,
    sparse: true
  },
  
  // 用户信息
  nickname: {
    type: String,
    required: true,
    default: '神秘玩家'
  },
  avatar: {
    type: String,
    default: 'https://example.com/default-avatar.png'
  },
  gender: {
    type: Number,
    enum: [0, 1, 2], // 0: 未知, 1: 男, 2: 女
    default: 0
  },
  
  // 游戏数据
  games_played: {
    type: Number,
    default: 0
  },
  games_won: {
    type: Number,
    default: 0
  },
  win_rate: {
    type: Number,
    default: 0,
    min: 0,
    max: 100
  },
  total_score: {
    type: Number,
    default: 0
  },
  average_score: {
    type: Number,
    default: 0
  },
  
  // 角色表现
  as_civilian: {
    games: { type: Number, default: 0 },
    wins: { type: Number, default: 0 },
    win_rate: { type: Number, default: 0 }
  },
  as_undercover: {
    games: { type: Number, default: 0 },
    wins: { type: Number, default: 0 },
    win_rate: { type: Number, default: 0 }
  },
  
  // 社交数据
  friends: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  }],
  friend_requests: [{
    from: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
    status: { type: String, enum: ['pending', 'accepted', 'rejected'], default: 'pending' },
    sent_at: { type: Date, default: Date.now }
  }],
  
  // 成就系统
  achievements: [{
    id: String,
    name: String,
    description: String,
    unlocked_at: Date,
    progress: Number
  }],
  
  // 设置
  settings: {
    notifications: {
      game_invites: { type: Boolean, default: true },
      friend_requests: { type: Boolean, default: true },
      game_results: { type: Boolean, default: true }
    },
    privacy: {
      show_profile: { type: Boolean, default: true },
      show_game_history: { type: Boolean, default: true }
    },
    game_preferences: {
      default_room_size: { type: Number, default: 8, min: 4, max: 12 },
      default_rounds: { type: Number, default: 3, min: 1, max: 10 },
      language: { type: String, default: 'zh-CN' }
    }
  },
  
  // 统计信息
  last_login: {
    type: Date,
    default: Date.now
  },
  login_count: {
    type: Number,
    default: 0
  },
  online_status: {
    type: String,
    enum: ['online', 'offline', 'in_game'],
    default: 'offline'
  },
  
  // 时间戳
  created_at: {
    type: Date,
    default: Date.now
  },
  updated_at: {
    type: Date,
    default: Date.now
  }
}, {
  timestamps: { createdAt: 'created_at', updatedAt: 'updated_at' }
});

// 更新统计信息的中间件
userSchema.pre('save', function(next) {
  // 计算胜率
  if (this.games_played > 0) {
    this.win_rate = Math.round((this.games_won / this.games_played) * 100);
  }
  
  // 计算平均分
  if (this.games_played > 0) {
    this.average_score = Math.round(this.total_score / this.games_played);
  }
  
  // 计算角色胜率
  if (this.as_civilian.games > 0) {
    this.as_civilian.win_rate = Math.round((this.as_civilian.wins / this.as_civilian.games) * 100);
  }
  
  if (this.as_undercover.games > 0) {
    this.as_undercover.win_rate = Math.round((this.as_undercover.wins / this.as_undercover.games) * 100);
  }
  
  this.updated_at = new Date();
  next();
});

// 静态方法：根据openid查找或创建用户
userSchema.statics.findOrCreate = async function(openid, userData = {}) {
  let user = await this.findOne({ openid });
  
  if (!user) {
    user = new this({
      openid,
      nickname: userData.nickname || `用户_${openid.substr(-6)}`,
      avatar: userData.avatar || 'https://example.com/default-avatar.png',
      gender: userData.gender || 0
    });
    await user.save();
  }
  
  return user;
};

// 实例方法：更新游戏数据
userSchema.methods.updateGameStats = function(isWin, role, score) {
  this.games_played += 1;
  this.total_score += score;
  
  if (isWin) {
    this.games_won += 1;
  }
  
  if (role === 'civilian') {
    this.as_civilian.games += 1;
    if (isWin) this.as_civilian.wins += 1;
  } else if (role === 'undercover') {
    this.as_undercover.games += 1;
    if (isWin) this.as_undercover.wins += 1;
  }
  
  return this.save();
};

// 实例方法：添加好友
userSchema.methods.addFriend = async function(friendId) {
  if (!this.friends.includes(friendId)) {
    this.friends.push(friendId);
    await this.save();
  }
};

// 索引
userSchema.index({ openid: 1 });
userSchema.index({ nickname: 1 });
userSchema.index({ total_score: -1 });
userSchema.index({ win_rate: -1 });
userSchema.index({ 'settings.game_preferences.default_room_size': 1 });
userSchema.index({ online_status: 1, last_login: -1 });

const User = mongoose.model('User', userSchema);

module.exports = User;