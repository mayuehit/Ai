// 单机版首页
const offlineGame = require('../../utils/offlineGame');

Page({
  data: {
    // 游戏设置
    playerCount: 6,
    totalRounds: 3,
    difficulty: 2,
    
    // 玩家列表
    players: [],
    humanPlayerName: '我',
    
    // 游戏状态
    gameStarted: false,
    gameState: 'waiting', // waiting, describing, voting, result, ended
    
    // 统计信息
    stats: {
      totalGames: 0,
      wins: 0,
      winRate: 0
    }
  },

  onLoad() {
    // 加载游戏统计
    this.loadGameStats();
    
    // 尝试加载保存的游戏
    this.loadSavedGame();
  },

  onShow() {
    // 每次显示页面时更新统计
    this.loadGameStats();
  },

  // 加载游戏统计
  loadGameStats() {
    const stats = offlineGame.getGameStats();
    this.setData({ stats });
  },

  // 加载保存的游戏
  loadSavedGame() {
    const loaded = offlineGame.loadFromStorage();
    if (loaded) {
      const gameState = offlineGame.getGameState();
      this.setData({
        gameStarted: gameState.gameState !== 'waiting',
        gameState: gameState.gameState,
        players: gameState.players,
        playerCount: gameState.players.length
      });
    }
  },

  // 更新玩家数量
  updatePlayerCount(e) {
    const playerCount = parseInt(e.detail.value);
    this.setData({ playerCount });
  },

  // 更新游戏轮数
  updateTotalRounds(e) {
    const totalRounds = parseInt(e.detail.value);
    this.setData({ totalRounds });
  },

  // 更新难度
  updateDifficulty(e) {
    const difficulty = parseInt(e.detail.value);
    this.setData({ difficulty });
  },

  // 获取难度文本
  getDifficultyText(level) {
    const levels = ['简单', '普通', '困难'];
    return levels[level - 1] || '普通';
  },

  // 显示/隐藏规则弹窗
  showRulesModal() {
    this.setData({ showRulesModal: true });
  },

  hideRulesModal() {
    this.setData({ showRulesModal: false });
  },

  // 更新玩家名称
  updatePlayerName(e) {
    this.setData({ humanPlayerName: e.detail.value });
  },

  // 添加AI玩家
  addAIPlayer() {
    if (this.data.players.length >= 12) {
      wx.showToast({
        title: '最多12名玩家',
        icon: 'none'
      });
      return;
    }

    const player = offlineGame.addAIPlayer();
    this.setData({
      players: offlineGame.players
    });
  },

  // 移除玩家
  removePlayer(e) {
    const index = e.currentTarget.dataset.index;
    if (index >= 0 && index < this.data.players.length) {
      // 不能移除人类玩家
      if (!this.data.players[index].isAI) {
        wx.showToast({
          title: '不能移除自己',
          icon: 'none'
        });
        return;
      }

      offlineGame.players.splice(index, 1);
      this.setData({
        players: offlineGame.players,
        playerCount: offlineGame.players.length
      });
    }
  },

  // 开始游戏
  startGame() {
    if (this.data.players.length < 4) {
      wx.showToast({
        title: '至少需要4名玩家',
        icon: 'none'
      });
      return;
    }

    // 确保有人类玩家
    const hasHuman = this.data.players.some(p => !p.isAI);
    if (!hasHuman) {
      // 添加人类玩家
      offlineGame.addHumanPlayer(this.data.humanPlayerName);
    }

    // 开始游戏
    const gameData = offlineGame.startGame(this.data.playerCount);
    
    // 保存游戏状态
    offlineGame.saveToStorage();

    this.setData({
      gameStarted: true,
      gameState: gameData.gameState,
      players: gameData.players
    });

    // 跳转到游戏页面
    wx.navigateTo({
      url: '/pages/offlineGame/offlineGame'
    });
  },

  // 继续游戏
  continueGame() {
    if (offlineGame.gameState === 'waiting') {
      wx.showToast({
        title: '没有进行中的游戏',
        icon: 'none'
      });
      return;
    }

    wx.navigateTo({
      url: '/pages/offlineGame/offlineGame'
    });
  },

  // 新游戏
  newGame() {
    wx.showModal({
      title: '新游戏',
      content: '开始新游戏将丢失当前进度，确定吗？',
      success: (res) => {
        if (res.confirm) {
          offlineGame.resetGame();
          this.setData({
            gameStarted: false,
            gameState: 'waiting',
            players: []
          });
          
          // 清除保存的游戏
          wx.removeStorageSync('offline_game_state');
          
          wx.showToast({
            title: '已重置游戏',
            icon: 'success'
          });
        }
      }
    });
  },

  // 查看游戏规则
  showRules() {
    wx.showModal({
      title: '游戏规则',
      content: `谁是卧底 - 单机版

游戏规则：
1. 游戏中有平民和卧底两种角色
2. 平民获得相同的词语，卧底获得相似的词语
3. 玩家轮流描述自己的词语（不能直接说出）
4. 每轮描述后投票选出怀疑的卧底
5. 被投票淘汰的玩家出局
6. 平民目标：找出所有卧底
7. 卧底目标：隐藏身份存活到最后

胜利条件：
- 平民胜利：所有卧底被淘汰
- 卧底胜利：平民全部被淘汰或游戏轮数结束

提示：
- 仔细听其他人的描述
- 卧底的描述通常比较模糊
- 平民要尽量给出具体但不暴露的描述`,
      showCancel: false,
      confirmText: '明白了'
    });
  },

  // 查看统计详情
  showStatsDetail() {
    const stats = this.data.stats;
    const civilianStats = stats.asCivilian || { games: 0, wins: 0 };
    const undercoverStats = stats.asUndercover || { games: 0, wins: 0 };
    
    const civilianRate = civilianStats.games > 0 ? 
      (civilianStats.wins / civilianStats.games * 100).toFixed(1) : 0;
    const undercoverRate = undercoverStats.games > 0 ? 
      (undercoverStats.wins / undercoverStats.games * 100).toFixed(1) : 0;
    
    wx.showModal({
      title: '游戏统计',
      content: `总游戏数: ${stats.totalGames}
总胜利数: ${stats.wins}
胜率: ${stats.winRate}%

平民身份:
  游戏次数: ${civilianStats.games}
  胜利次数: ${civilianStats.wins}
  胜率: ${civilianRate}%

卧底身份:
  游戏次数: ${undercoverStats.games}
  胜利次数: ${undercoverStats.wins}
  胜率: ${undercoverRate}%`,
      showCancel: false,
      confirmText: '关闭'
    });
  },

  // 清空统计
  clearStats() {
    wx.showModal({
      title: '清空统计',
      content: '确定要清空所有游戏统计吗？此操作不可恢复。',
      success: (res) => {
        if (res.confirm) {
          wx.removeStorageSync('total_games');
          wx.removeStorageSync('game_wins');
          wx.removeStorageSync('as_civilian');
          wx.removeStorageSync('as_undercover');
          
          this.loadGameStats();
          
          wx.showToast({
            title: '统计已清空',
            icon: 'success'
          });
        }
      }
    });
  },

  // 分享游戏
  onShareAppMessage() {
    return {
      title: '谁是卧底 - 单机版',
      path: '/pages/offline/offline',
      imageUrl: '/images/share-cover.png'
    };
  },

  // 分享到朋友圈
  onShareTimeline() {
    return {
      title: '谁是卧底 - 单机版',
      query: '',
      imageUrl: '/images/share-cover.png'
    };
  }
});