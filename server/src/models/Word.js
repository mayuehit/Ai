// 词语数据模型
const mongoose = require('mongoose');

const wordSchema = new mongoose.Schema({
  // 词语对
  civilian: {
    type: String,
    required: true,
    trim: true,
    minlength: 1,
    maxlength: 20
  },
  undercover: {
    type: String,
    required: true,
    trim: true,
    minlength: 1,
    maxlength: 20
  },
  
  // 分类信息
  category: {
    type: String,
    required: true,
    enum: [
      '水果', '蔬菜', '动物', '职业', '地点', 
      '物品', '动作', '颜色', '数字', '形状',
      '食物', '饮料', '交通工具', '电子产品',
      '服装', '节日', '国家', '城市', '名人',
      '电影', '音乐', '书籍', '游戏', '运动'
    ],
    default: '物品'
  },
  
  // 难度等级
  difficulty: {
    type: Number,
    required: true,
    min: 1,
    max: 5,
    default: 3
  },
  
  // 相似度评分（由管理员设置）
  similarity: {
    type: Number,
    min: 1,
    max: 10,
    default: 5
  },
  
  // 使用统计
  usageCount: {
    type: Number,
    default: 0
  },
  successRate: {
    type: Number,
    min: 0,
    max: 100,
    default: 50
  },
  lastUsed: {
    type: Date
  },
  
  // 用户贡献信息
  contributedBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  },
  contributorName: {
    type: String
  },
  
  // 审核状态
  status: {
    type: String,
    enum: ['pending', 'approved', 'rejected', 'archived'],
    default: 'pending'
  },
  reviewedBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  },
  reviewNotes: {
    type: String,
    maxlength: 500
  },
  
  // 标签系统
  tags: [{
    type: String,
    maxlength: 20
  }],
  
  // 多语言支持
  language: {
    type: String,
    default: 'zh-CN',
    enum: ['zh-CN', 'zh-TW', 'en-US', 'ja-JP', 'ko-KR']
  },
  
  // 扩展信息
  description: {
    type: String,
    maxlength: 200
  },
  exampleUsage: {
    type: String,
    maxlength: 100
  },
  relatedWords: [{
    word: String,
    relation: String // synonym, antonym, related
  }],
  
  // 评分系统
  ratings: [{
    userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
    rating: { type: Number, min: 1, max: 5 },
    comment: { type: String, maxlength: 200 },
    createdAt: { type: Date, default: Date.now }
  }],
  averageRating: {
    type: Number,
    min: 0,
    max: 5,
    default: 0
  },
  
  // 时间戳
  createdAt: {
    type: Date,
    default: Date.now
  },
  updatedAt: {
    type: Date,
    default: Date.now
  }
}, {
  timestamps: { createdAt: 'createdAt', updatedAt: 'updatedAt' }
});

// 索引
wordSchema.index({ civilian: 1, undercover: 1 }, { unique: true });
wordSchema.index({ category: 1, difficulty: 1 });
wordSchema.index({ status: 1, createdAt: -1 });
wordSchema.index({ usageCount: -1 });
wordSchema.index({ averageRating: -1 });
wordSchema.index({ tags: 1 });
wordSchema.index({ language: 1 });

// 中间件：更新使用统计
wordSchema.pre('save', function(next) {
  // 计算平均评分
  if (this.ratings && this.ratings.length > 0) {
    const total = this.ratings.reduce((sum, rating) => sum + rating.rating, 0);
    this.averageRating = total / this.ratings.length;
  }
  
  this.updatedAt = new Date();
  next();
});

// 静态方法：获取随机词语对
wordSchema.statics.getRandomWord = async function(options = {}) {
  const {
    category,
    difficulty,
    minDifficulty = 1,
    maxDifficulty = 5,
    language = 'zh-CN',
    excludeUsed = true
  } = options;
  
  const query = { 
    status: 'approved',
    language 
  };
  
  // 添加筛选条件
  if (category) {
    query.category = category;
  }
  
  if (difficulty) {
    query.difficulty = difficulty;
  } else {
    query.difficulty = { $gte: minDifficulty, $lte: maxDifficulty };
  }
  
  // 排除最近使用过的词语
  if (excludeUsed) {
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
    query.$or = [
      { lastUsed: { $lt: oneHourAgo } },
      { lastUsed: { $exists: false } }
    ];
  }
  
  // 随机获取一个词语
  const count = await this.countDocuments(query);
  if (count === 0) {
    // 如果没有符合条件的词语，放宽条件
    delete query.$or;
    const newCount = await this.countDocuments(query);
    if (newCount === 0) {
      throw new Error('没有可用的词语');
    }
    
    const random = Math.floor(Math.random() * newCount);
    const word = await this.findOne(query).skip(random);
    return word;
  }
  
  const random = Math.floor(Math.random() * count);
  const word = await this.findOne(query).skip(random);
  return word;
};

// 静态方法：批量获取词语
wordSchema.statics.getWordsBatch = async function(count = 10, options = {}) {
  const words = [];
  const usedIds = new Set();
  
  for (let i = 0; i < count; i++) {
    try {
      const word = await this.getRandomWord({
        ...options,
        excludeUsed: false // 在批量获取中允许重复
      });
      
      if (word && !usedIds.has(word._id.toString())) {
        words.push(word);
        usedIds.add(word._id.toString());
      }
    } catch (error) {
      // 如果获取失败，继续尝试
      console.warn('获取词语失败:', error.message);
    }
  }
  
  return words;
};

// 静态方法：更新使用统计
wordSchema.statics.recordUsage = async function(wordId, gameResult) {
  const word = await this.findById(wordId);
  if (!word) return;
  
  word.usageCount += 1;
  word.lastUsed = new Date();
  
  // 更新成功率
  if (gameResult) {
    const isSuccessful = gameResult.winner === 'civilian'; // 平民胜利表示词语设计合理
    const currentRate = word.successRate || 50;
    const newRate = currentRate * 0.9 + (isSuccessful ? 10 : 0);
    word.successRate = Math.min(Math.max(newRate, 0), 100);
  }
  
  await word.save();
};

// 静态方法：搜索词语
wordSchema.statics.searchWords = async function(searchTerm, options = {}) {
  const {
    page = 1,
    limit = 20,
    category,
    difficulty,
    language = 'zh-CN',
    status = 'approved'
  } = options;
  
  const query = { status, language };
  
  // 搜索词匹配
  if (searchTerm) {
    query.$or = [
      { civilian: { $regex: searchTerm, $options: 'i' } },
      { undercover: { $regex: searchTerm, $options: 'i' } },
      { category: { $regex: searchTerm, $options: 'i' } },
      { tags: { $regex: searchTerm, $options: 'i' } }
    ];
  }
  
  // 其他筛选条件
  if (category) query.category = category;
  if (difficulty) query.difficulty = difficulty;
  
  const skip = (page - 1) * limit;
  
  const [words, total] = await Promise.all([
    this.find(query)
      .sort({ usageCount: -1, averageRating: -1 })
      .skip(skip)
      .limit(limit),
    this.countDocuments(query)
  ]);
  
  return {
    words,
    total,
    page,
    totalPages: Math.ceil(total / limit),
    hasMore: page * limit < total
  };
};

// 实例方法：添加评分
wordSchema.methods.addRating = async function(userId, rating, comment = '') {
  // 检查是否已经评分
  const existingIndex = this.ratings.findIndex(r => r.userId.toString() === userId.toString());
  
  if (existingIndex >= 0) {
    // 更新现有评分
    this.ratings[existingIndex].rating = rating;
    this.ratings[existingIndex].comment = comment;
    this.ratings[existingIndex].createdAt = new Date();
  } else {
    // 添加新评分
    this.ratings.push({
      userId,
      rating,
      comment,
      createdAt: new Date()
    });
  }
  
  await this.save();
};

// 实例方法：获取相似词语建议
wordSchema.methods.getSimilarWords = async function(limit = 5) {
  return this.model('Word').find({
    _id: { $ne: this._id },
    category: this.category,
    difficulty: this.difficulty,
    status: 'approved'
  })
  .limit(limit)
  .sort({ similarity: -1, averageRating: -1 });
};

const Word = mongoose.model('Word', wordSchema);

module.exports = Word;