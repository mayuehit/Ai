// 单机版游戏页面
const offlineGame = require('../../utils/offlineGame');

Page({
  data: {
    // 游戏状态
    gameState: 'waiting',
    currentRound: 1,
    totalRounds: 3,
    timeLeft: 60,
    timer: null,
    
    // 玩家信息
    players: [],
    currentPlayerIndex: 0,
    myRole: '',
    myWord: '',
    
    // 描述和投票
    descriptions: [],
    myDescription: '',
    votes: {},
    myVote: null,
    
    // UI状态
    showWordModal: true,
    showVoteModal: false,
    showResultModal: false,
    isMyTurn: false,
    
    // 游戏结果
    gameResult: null,
    winner: '',
    eliminatedPlayer: null
  },

  onLoad() {
    // 加载游戏状态
    this.loadGameState();
    
    // 设置定时器
    this.setupTimer();
  },

  onUnload() {
    // 清理定时器
    if (this.data.timer) {
      clearInterval(this.data.timer);
    }
    
    // 保存游戏状态
    offlineGame.saveToStorage();
  },

  onHide() {
    // 保存游戏状态
    offlineGame.saveToStorage();
  },

  // 加载游戏状态
  loadGameState() {
    const gameState = offlineGame.getGameState();
    
    this.setData({
      gameState: gameState.gameState,
      currentRound: gameState.currentRound,
      totalRounds: gameState.totalRounds,
      players: gameState.players,
      currentPlayerIndex: gameState.currentPlayerIndex,
      descriptions: gameState.descriptions,
      votes: gameState.votes,
      myRole: gameState.myRole,
      myWord: gameState.myWord
    });

    // 检查是否是我的回合
    this.checkMyTurn();
    
    // 如果是描述阶段且是我的回合，开始计时
    if (gameState.gameState === 'describing' && this.data.isMyTurn) {
      this.startTimer();
    }
  },

  // 设置定时器
  setupTimer() {
    // 每5秒检查一次游戏状态（用于AI自动操作）
    const timer = setInterval(() => {
      this.checkAIActions();
    }, 5000);
    
    this.setData({ timer });
  },

  // 检查AI行动
  checkAIActions() {
    const gameState = offlineGame.getGameState();
    
    if (gameState.gameState === 'describing') {
      const currentPlayer = gameState.players[gameState.currentPlayerIndex];
      
      // 如果是AI的回合，自动描述
      if (currentPlayer && currentPlayer.isAI) {
        this.autoAIDescription(currentPlayer);
      }
    } else if (gameState.gameState === 'voting') {
      // AI自动投票
      this.autoAIVote();
    }
    
    // 更新UI
    this.loadGameState();
  },

  // AI自动描述
  autoAIDescription(player) {
    if (!player || !player.isAI) return;
    
    // AI提交描述
    offlineGame.submitDescription(null, player.id);
    
    // 更新UI
    this.loadGameState();
  },

  // AI自动投票
  autoAIVote() {
    const gameState = offlineGame.getGameState();
    
    // 检查哪些AI还没有投票
    gameState.players.forEach(player => {
      if (player.isAI && !player.eliminated && !gameState.votes[player.id]) {
        // AI投票
        offlineGame.submitVote(null, player.id);
      }
    });
    
    // 更新UI
    this.loadGameState();
  },

  // 开始计时器
  startTimer() {
    if (this.data.timer) {
      clearInterval(this.data.timer);
    }
    
    const timer = setInterval(() => {
      let timeLeft = this.data.timeLeft - 1;
      
      if (timeLeft <= 0) {
        clearInterval(timer);
        timeLeft = 0;
        this.timeUp();
      }
      
      this.setData({ timeLeft });
    }, 1000);
    
    this.setData({ timer });
  },

  // 时间到
  timeUp() {
    if (this.data.gameState === 'describing' && this.data.isMyTurn) {
      // 自动提交空描述
      this.submitDescription('');
    } else if (this.data.gameState === 'voting' && !this.data.myVote) {
      // 自动随机投票
      this.submitRandomVote();
    }
  },

  // 检查是否是我的回合
  checkMyTurn() {
    const gameState = offlineGame.getGameState();
    const currentPlayer = gameState.players[gameState.currentPlayerIndex];
    const humanPlayer = gameState.players.find(p => !p.isAI);
    
    const isMyTurn = currentPlayer && humanPlayer && 
                    currentPlayer.id === humanPlayer.id;
    
    this.setData({ isMyTurn });
  },

  // 提交描述
  submitDescription(description = '') {
    if (!description.trim() && this.data.myDescription.trim()) {
      description = this.data.myDescription;
    }
    
    // 提交描述
    offlineGame.submitDescription(description.trim());
    
    // 保存游戏状态
    offlineGame.saveToStorage();
    
    // 更新UI
    this.loadGameState();
    this.setData({ myDescription: '' });
    
    // 如果是我的回合结束，停止计时
    if (this.data.isMyTurn) {
      if (this.data.timer) {
        clearInterval(this.data.timer);
      }
    }
  },

  // 输入描述
  onDescriptionInput(e) {
    this.setData({ myDescription: e.detail.value });
  },

  // 提交投票
  submitVote(playerId) {
    if (!playerId) return;
    
    this.setData({ myVote: playerId });
    
    // 提交投票
    offlineGame.submitVote(playerId);
    
    // 保存游戏状态
    offlineGame.saveToStorage();
    
    // 更新UI
    this.loadGameState();
    
    this.hideVoteModal();
  },

  // 自动随机投票
  submitRandomVote() {
    const otherPlayers = this.data.players.filter(
      player => !player.isAI && !player.eliminated
    );
    
    if (otherPlayers.length > 0) {
      const randomPlayer = otherPlayers[Math.floor(Math.random() * otherPlayers.length)];
      this.submitVote(randomPlayer.id);
    }
  },

  // 显示词语弹窗
  showWordModal() {
    this.setData({ showWordModal: true });
    
    // 3秒后自动关闭
    setTimeout(() => {
      this.hideWordModal();
    }, 3000);
  },

  // 隐藏词语弹窗
  hideWordModal() {
    this.setData({ showWordModal: false });
  },

  // 显示投票弹窗
  showVoteModal() {
    this.setData({ showVoteModal: true });
  },

  // 隐藏投票弹窗
  hideVoteModal() {
    this.setData({ showVoteModal: false });
  },

  // 玩家点击（投票时）
  onPlayerTap(e) {
    if (this.data.gameState !== 'voting') return;
    
    const player = e.currentTarget.dataset.player;
    if (player && !player.eliminated && player.isAI) {
      this.setData({ myVote: player.id });
      this.showVoteModal();
    }
  },

  // 获取玩家角色文本
  getRoleText(role) {
    return role === 'civilian' ? '平民' : '卧底';
  },

  // 获取玩家状态颜色
  getPlayerStatusColor(player) {
    if (player.eliminated) return 'eliminated';
    
    const gameState = offlineGame.getGameState();
    if (player.id === gameState.players[gameState.currentPlayerIndex]?.id) {
      return 'current';
    }
    
    return 'normal';
  },

  // 获取投票数量
  getVoteCount(playerId) {
    const votes = offlineGame.getGameState().votes;
    let count = 0;
    
    for (const voterId in votes) {
      if (votes[voterId] === playerId) {
        count++;
      }
    }
    
    return count;
  },

  // 获取当前玩家
  getCurrentPlayer() {
    const gameState = offlineGame.getGameState();
    return gameState.players[gameState.currentPlayerIndex];
  },

  // 获取玩家描述
  getPlayerDescription(playerId) {
    const descriptions = offlineGame.getGameState().descriptions;
    const lastRoundDesc = descriptions.filter(d => d.playerId === playerId);
    return lastRoundDesc.length > 0 ? lastRoundDesc[lastRoundDesc.length - 1].description : '';
  },

  // 返回首页
  backToHome() {
    // 如果游戏结束，记录结果
    if (this.data.gameState === 'ended') {
      const humanPlayer = this.data.players.find(p => !p.isAI);
      if (humanPlayer) {
        const isWin = this.data.winner === humanPlayer.role;
        offlineGame.recordGameResult(isWin, humanPlayer.role);
      }
      
      // 清除保存的游戏
      wx.removeStorageSync('offline_game_state');
    }
    
    wx.navigateBack();
  },

  // 再来一局
  playAgain() {
    // 记录上一局结果
    const humanPlayer = this.data.players.find(p => !p.isAI);
    if (humanPlayer) {
      const isWin = this.data.winner === humanPlayer.role;
      offlineGame.recordGameResult(isWin, humanPlayer.role);
    }
    
    // 重置游戏但保留玩家
    offlineGame.resetGame();
    
    // 重新添加玩家（保持相同的AI玩家）
    this.data.players.forEach(player => {
      if (player.isAI) {
        offlineGame.addAIPlayer(player.name);
      } else {
        offlineGame.addHumanPlayer(player.name);
      }
    });
    
    // 开始新游戏
    offlineGame.startGame(this.data.players.length);
    
    // 保存状态
    offlineGame.saveToStorage();
    
    // 重新加载页面
    this.loadGameState();
    this.showWordModal();
  },

  // 分享结果
  shareResult() {
    const resultText = this.data.winner === 'civilian' ? 
      '平民胜利！我成功找出了卧底。' : 
      '卧底胜利！我成功隐藏了身份。';
    
    wx.showShareMenu({
      withShareTicket: true
    });
  },

  // 辅助函数
  getGameStateText(state) {
    const states = {
      waiting: '等待开始',
      describing: '描述环节',
      voting: '投票环节',
      result: '结果揭晓',
      ended: '游戏结束'
    };
    return states[state] || state;
  },

  getStateHint(state) {
    const hints = {
      describing: '玩家轮流描述词语',
      voting: '投票选出怀疑的卧底',
      result: '查看本轮结果',
      ended: '游戏已结束'
    };
    return hints[state] || '';
  },

  getPlayerStatus(player) {
    if (player.eliminated) return 'eliminated';
    if (this.isPlayerTurn(player)) return 'current';
    return 'normal';
  },

  isPlayerTurn(player) {
    const gameState = offlineGame.getGameState();
    const currentPlayer = gameState.players[gameState.currentPlayerIndex];
    return currentPlayer && player.id === currentPlayer.id;
  },

  getAliveCount() {
    return this.data.players.filter(p => !p.eliminated).length;
  },

  getPlayerAvatar(playerId) {
    const player = this.data.players.find(p => p.id === playerId);
    return player ? player.avatar : '/images/default-avatar.png';
  },

  getPlayerName(playerId) {
    const player = this.data.players.find(p => p.id === playerId);
    return player ? player.name : '玩家';
  },

  isPlayerAI(playerId) {
    const player = this.data.players.find(p => p.id === playerId);
    return player ? player.isAI : false;
  },

  getVotedCount() {
    return Object.keys(this.data.votes).length;
  },

  getResultSubtitle() {
    if (this.data.winner === 'civilian') {
      return '成功找出所有卧底';
    } else {
      return '卧底成功隐藏身份';
    }
  },

  getVotedPlayerName(playerId) {
    const targetId = this.data.votes[playerId];
    if (!targetId) return '';
    const player = this.data.players.find(p => p.id === targetId);
    return player ? player.name : '';
  },

  getPlayerById(playerId) {
    return this.data.players.find(p => p.id === playerId);
  },

  formatTime(timestamp) {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
  },

  saveGame() {
    const saved = offlineGame.saveToStorage();
    wx.showToast({
      title: saved ? '游戏已保存' : '保存失败',
      icon: saved ? 'success' : 'none'
    });
  },

  onShareAppMessage() {
    const resultText = this.data.winner === 'civilian' ? 
      '平民胜利' : '卧底胜利';
    
    return {
      title: `谁是卧底 - ${resultText}`,
      path: '/pages/offline/offline',
      imageUrl: '/images/game-result-share.png'
    };
  }
});