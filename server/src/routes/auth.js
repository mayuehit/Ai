const express = require('express');
const router = express.Router();
const jwt = require('jsonwebtoken');
const User = require('../models/User');

// 微信登录
router.post('/login', async (req, res) => {
  try {
    const { code } = req.body;
    
    if (!code) {
      return res.status(400).json({ error: '缺少code参数' });
    }

    // 这里应该调用微信API获取openid
    // 为了演示，我们模拟一个openid
    const mockOpenid = `wx_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // 查找或创建用户
    let user = await User.findOne({ openid: mockOpenid });
    
    if (!user) {
      user = new User({
        openid: mockOpenid,
        nickname: `用户_${mockOpenid.substr(-6)}`,
        avatar: 'https://example.com/default-avatar.png'
      });
      await user.save();
    }

    // 生成JWT token
    const token = jwt.sign(
      { userId: user._id, openid: user.openid },
      process.env.JWT_SECRET || 'your-secret-key',
      { expiresIn: '7d' }
    );

    res.json({
      success: true,
      token,
      user: {
        id: user._id,
        nickname: user.nickname,
        avatar: user.avatar,
        gamesPlayed: user.games_played || 0,
        winRate: user.win_rate || 0
      }
    });
  } catch (error) {
    console.error('登录错误:', error);
    res.status(500).json({ error: '登录失败' });
  }
});

// 获取用户信息
router.get('/profile', async (req, res) => {
  try {
    const token = req.headers.authorization?.replace('Bearer ', '');
    
    if (!token) {
      return res.status(401).json({ error: '未提供token' });
    }

    const decoded = jwt.verify(token, process.env.JWT_SECRET || 'your-secret-key');
    const user = await User.findById(decoded.userId);
    
    if (!user) {
      return res.status(404).json({ error: '用户不存在' });
    }

    res.json({
      success: true,
      user: {
        id: user._id,
        openid: user.openid,
        nickname: user.nickname,
        avatar: user.avatar,
        gamesPlayed: user.games_played || 0,
        winRate: user.win_rate || 0,
        createdAt: user.created_at
      }
    });
  } catch (error) {
    console.error('获取用户信息错误:', error);
    
    if (error.name === 'JsonWebTokenError') {
      return res.status(401).json({ error: '无效的token' });
    }
    
    res.status(500).json({ error: '获取用户信息失败' });
  }
});

// 更新用户信息
router.put('/profile', async (req, res) => {
  try {
    const token = req.headers.authorization?.replace('Bearer ', '');
    
    if (!token) {
      return res.status(401).json({ error: '未提供token' });
    }

    const decoded = jwt.verify(token, process.env.JWT_SECRET || 'your-secret-key');
    const { nickname, avatar } = req.body;
    
    const updateData = {};
    if (nickname) updateData.nickname = nickname;
    if (avatar) updateData.avatar = avatar;
    
    const user = await User.findByIdAndUpdate(
      decoded.userId,
      updateData,
      { new: true }
    );
    
    if (!user) {
      return res.status(404).json({ error: '用户不存在' });
    }

    res.json({
      success: true,
      user: {
        id: user._id,
        nickname: user.nickname,
        avatar: user.avatar
      }
    });
  } catch (error) {
    console.error('更新用户信息错误:', error);
    res.status(500).json({ error: '更新用户信息失败' });
  }
});

// 登出（客户端清除token即可）
router.post('/logout', (req, res) => {
  res.json({ success: true, message: '登出成功' });
});

module.exports = router;