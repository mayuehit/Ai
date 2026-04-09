// 词语管理API
const express = require('express');
const router = express.Router();
const Word = require('../models/Word');
const jwt = require('jsonwebtoken');

// 中间件：验证管理员权限
const requireAdmin = async (req, res, next) => {
  try {
    const token = req.headers.authorization?.replace('Bearer ', '');
    
    if (!token) {
      return res.status(401).json({ error: '需要登录' });
    }
    
    const decoded = jwt.verify(token, process.env.JWT_SECRET || 'your-secret-key');
    
    // 这里应该检查用户是否是管理员
    // 为了演示，我们假设所有登录用户都可以管理词语
    req.userId = decoded.userId;
    next();
  } catch (error) {
    res.status(401).json({ error: '无效的token' });
  }
};

// 获取随机词语
router.get('/random', async (req, res) => {
  try {
    const {
      category,
      difficulty,
      minDifficulty = 1,
      maxDifficulty = 5,
      language = 'zh-CN'
    } = req.query;
    
    const word = await Word.getRandomWord({
      category,
      difficulty: difficulty ? parseInt(difficulty) : undefined,
      minDifficulty: parseInt(minDifficulty),
      maxDifficulty: parseInt(maxDifficulty),
      language
    });
    
    if (!word) {
      return res.status(404).json({ error: '没有找到符合条件的词语' });
    }
    
    res.json({
      success: true,
      word: {
        id: word._id,
        civilian: word.civilian,
        undercover: word.undercover,
        category: word.category,
        difficulty: word.difficulty,
        similarity: word.similarity,
        description: word.description,
        tags: word.tags
      }
    });
  } catch (error) {
    console.error('获取随机词语错误:', error);
    res.status(500).json({ error: '获取词语失败' });
  }
});

// 批量获取词语
router.get('/batch', async (req, res) => {
  try {
    const count = parseInt(req.query.count) || 10;
    const { category, difficulty, language = 'zh-CN' } = req.query;
    
    const words = await Word.getWordsBatch(count, {
      category,
      difficulty: difficulty ? parseInt(difficulty) : undefined,
      language
    });
    
    res.json({
      success: true,
      words: words.map(word => ({
        id: word._id,
        civilian: word.civilian,
        undercover: word.undercover,
        category: word.category,
        difficulty: word.difficulty,
        similarity: word.similarity
      })),
      count: words.length
    });
  } catch (error) {
    console.error('批量获取词语错误:', error);
    res.status(500).json({ error: '获取词语失败' });
  }
});

// 搜索词语
router.get('/search', async (req, res) => {
  try {
    const {
      q: searchTerm,
      page = 1,
      limit = 20,
      category,
      difficulty,
      language = 'zh-CN'
    } = req.query;
    
    const result = await Word.searchWords(searchTerm, {
      page: parseInt(page),
      limit: parseInt(limit),
      category,
      difficulty: difficulty ? parseInt(difficulty) : undefined,
      language
    });
    
    res.json({
      success: true,
      ...result,
      words: result.words.map(word => ({
        id: word._id,
        civilian: word.civilian,
        undercover: word.undercover,
        category: word.category,
        difficulty: word.difficulty,
        similarity: word.similarity,
        usageCount: word.usageCount,
        averageRating: word.averageRating,
        tags: word.tags,
        description: word.description
      }))
    });
  } catch (error) {
    console.error('搜索词语错误:', error);
    res.status(500).json({ error: '搜索失败' });
  }
});

// 获取词语分类
router.get('/categories', async (req, res) => {
  try {
    const categories = await Word.distinct('category', { status: 'approved' });
    
    // 获取每个分类的词语数量
    const categoryStats = await Promise.all(
      categories.map(async category => {
        const count = await Word.countDocuments({ 
          category, 
          status: 'approved' 
        });
        return { category, count };
      })
    );
    
    res.json({
      success: true,
      categories: categoryStats.sort((a, b) => b.count - a.count)
    });
  } catch (error) {
    console.error('获取分类错误:', error);
    res.status(500).json({ error: '获取分类失败' });
  }
});

// 获取热门词语
router.get('/popular', async (req, res) => {
  try {
    const limit = parseInt(req.query.limit) || 10;
    
    const words = await Word.find({ status: 'approved' })
      .sort({ usageCount: -1, averageRating: -1 })
      .limit(limit);
    
    res.json({
      success: true,
      words: words.map(word => ({
        id: word._id,
        civilian: word.civilian,
        undercover: word.undercover,
        category: word.category,
        difficulty: word.difficulty,
        usageCount: word.usageCount,
        successRate: word.successRate,
        averageRating: word.averageRating
      }))
    });
  } catch (error) {
    console.error('获取热门词语错误:', error);
    res.status(500).json({ error: '获取热门词语失败' });
  }
});

// 用户贡献词语（需要登录）
router.post('/contribute', requireAdmin, async (req, res) => {
  try {
    const {
      civilian,
      undercover,
      category = '物品',
      difficulty = 3,
      similarity = 5,
      description = '',
      tags = [],
      language = 'zh-CN'
    } = req.body;
    
    // 验证输入
    if (!civilian || !undercover) {
      return res.status(400).json({ error: '需要提供平民词语和卧底词语' });
    }
    
    if (civilian === undercover) {
      return res.status(400).json({ error: '平民词语和卧底词语不能相同' });
    }
    
    // 检查是否已存在
    const existing = await Word.findOne({ 
      civilian, 
      undercover,
      language 
    });
    
    if (existing) {
      return res.status(400).json({ error: '该词语对已存在' });
    }
    
    // 创建新词语
    const word = new Word({
      civilian,
      undercover,
      category,
      difficulty,
      similarity,
      description,
      tags,
      language,
      contributedBy: req.userId,
      status: 'pending' // 等待审核
    });
    
    await word.save();
    
    res.json({
      success: true,
      message: '词语提交成功，等待审核',
      wordId: word._id
    });
  } catch (error) {
    console.error('贡献词语错误:', error);
    res.status(500).json({ error: '提交词语失败' });
  }
});

// 评分词语（需要登录）
router.post('/:id/rate', requireAdmin, async (req, res) => {
  try {
    const { id } = req.params;
    const { rating, comment = '' } = req.body;
    
    if (!rating || rating < 1 || rating > 5) {
      return res.status(400).json({ error: '评分必须在1-5之间' });
    }
    
    const word = await Word.findById(id);
    if (!word) {
      return res.status(404).json({ error: '词语不存在' });
    }
    
    await word.addRating(req.userId, rating, comment);
    
    res.json({
      success: true,
      message: '评分成功',
      averageRating: word.averageRating,
      totalRatings: word.ratings.length
    });
  } catch (error) {
    console.error('评分词语错误:', error);
    res.status(500).json({ error: '评分失败' });
  }
});

// 管理员：获取待审核词语
router.get('/pending', requireAdmin, async (req, res) => {
  try {
    const { page = 1, limit = 20 } = req.query;
    const skip = (parseInt(page) - 1) * parseInt(limit);
    
    const [words, total] = await Promise.all([
      Word.find({ status: 'pending' })
        .sort({ createdAt: -1 })
        .skip(skip)
        .limit(parseInt(limit))
        .populate('contributedBy', 'nickname avatar'),
      Word.countDocuments({ status: 'pending' })
    ]);
    
    res.json({
      success: true,
      words: words.map(word => ({
        id: word._id,
        civilian: word.civilian,
        undercover: word.undercover,
        category: word.category,
        difficulty: word.difficulty,
        description: word.description,
        contributedBy: word.contributedBy,
        createdAt: word.createdAt
      })),
      total,
      page: parseInt(page),
      totalPages: Math.ceil(total / parseInt(limit))
    });
  } catch (error) {
    console.error('获取待审核词语错误:', error);
    res.status(500).json({ error: '获取失败' });
  }
});

// 管理员：审核词语
router.post('/:id/review', requireAdmin, async (req, res) => {
  try {
    const { id } = req.params;
    const { status, notes = '' } = req.body;
    
    if (!['approved', 'rejected'].includes(status)) {
      return res.status(400).json({ error: '无效的审核状态' });
    }
    
    const word = await Word.findById(id);
    if (!word) {
      return res.status(404).json({ error: '词语不存在' });
    }
    
    if (word.status !== 'pending') {
      return res.status(400).json({ error: '该词语已审核' });
    }
    
    word.status = status;
    word.reviewedBy = req.userId;
    word.reviewNotes = notes;
    
    await word.save();
    
    res.json({
      success: true,
      message: `词语已${status === 'approved' ? '通过' : '拒绝'}`,
      word: {
        id: word._id,
        civilian: word.civilian,
        undercover: word.undercover,
        status: word.status
      }
    });
  } catch (error) {
    console.error('审核词语错误:', error);
    res.status(500).json({ error: '审核失败' });
  }
});

// 获取词语详情
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
    const word = await Word.findById(id)
      .populate('contributedBy', 'nickname avatar')
      .populate('reviewedBy', 'nickname');
    
    if (!word) {
      return res.status(404).json({ error: '词语不存在' });
    }
    
    // 只有审核通过的词语或管理员可以查看详情
    if (word.status !== 'approved') {
      // 检查是否是管理员或贡献者
      const token = req.headers.authorization?.replace('Bearer ', '');
      if (!token) {
        return res.status(403).json({ error: '无权限查看' });
      }
      
      try {
        const decoded = jwt.verify(token, process.env.JWT_SECRET || 'your-secret-key');
        const isOwner = word.contributedBy && word.contributedBy._id.toString() === decoded.userId;
        
        if (!isOwner) {
          return res.status(403).json({ error: '无权限查看' });
        }
      } catch (authError) {
        return res.status(403).json({ error: '无权限查看' });
      }
    }
    
    res.json({
      success: true,
      word: {
        id: word._id,
        civilian: word.civilian,
        undercover: word.undercover,
        category: word.category,
        difficulty: word.difficulty,
        similarity: word.similarity,
        description: word.description,
        exampleUsage: word.exampleUsage,
        tags: word.tags,
        language: word.language,
        usageCount: word.usageCount,
        successRate: word.successRate,
        averageRating: word.averageRating,
        ratings: word.ratings.length,
        status: word.status,
        contributedBy: word.contributedBy,
        reviewedBy: word.reviewedBy,
        reviewNotes: word.reviewNotes,
        createdAt: word.createdAt,
        updatedAt: word.updatedAt
      }
    });
  } catch (error) {
    console.error('获取词语详情错误:', error);
    res.status(500).json({ error: '获取详情失败' });
  }
});

module.exports = router;