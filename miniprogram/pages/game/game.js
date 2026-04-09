// pages/game/game.js - 游戏主页面
const app = getApp();

Page({
  data: {
    // 游戏状态
    gameState: 'waiting', // waiting, describing, voting, result, ended
    currentRound: 1,
    totalRounds: 3,
    timeLeft: 60,
    timer: null,
    
    // 玩家信息
    myRole: '', // civilian, undercover
    myWord: '',
    players: [],
    currentPlayerIndex: 0,
    
    // 描述和投票
    descriptions: [],
    myDescription: '',
    votes: {},
    myVote: null,
    
    // UI状态
    showWordModal: false,
    showVoteModal: false,
    showResultModal: false,
    isMyTurn: false,
    
    // 游戏结果
    gameResult: null,
    winner: '',
    eliminatedPlayer: null
  },

  onLoad(options) {
    const { roomCode } = options;
    this.setData({ roomCode });
    
    // 监听WebSocket消息
    this.setupSocketListeners();
    
    // 请求游戏数据
    this.fetchGameData();
  },

  onUnload() {
    // 清理定时器
    if (this.data.timer) {
      clearInterval(this.data.timer);
    }
  },

  // 设置WebSocket监听
  setupSocketListeners() {
    if (app.globalData.socket) {
      // 监听游戏状态更新
      app.globalData.socket.onMessage((res) => {
        const data = JSON.parse(res.data);
        this.handleGameMessage(data);
      });
    }
  },

  // 处理游戏消息
  handleGameMessage(data) {
    const { type, payload } = data;
    
    switch (type) {
      case 'game_state_update':
        this.updateGameState(payload);
        break;
      case 'player_turn':
        this.handlePlayerTurn(payload);
        break;
      case 'description_received':
        this.handleDescription(payload);
        break;
      case 'vote_received':
        this.handleVote(payload);
        break;
      case 'game_result':
        this.handleGameResult(payload);
        break;
      case 'time_update':
        this.updateTime(payload);
        break;
    }
  },

  // 获取游戏数据
  fetchGameData() {
    wx.showLoading({ title: '加载游戏中...' });
    
    wx.request({
      url: `https://api.example.com/api/games/${this.data.roomCode}`,
      header: {
        'Authorization': `Bearer ${app.globalData.token}`
      },
      success: (res) => {
        wx.hideLoading();
        
        if (res.data.success) {
          const game = res.data.game;
          this.setData({
            gameState: game.status,
            myRole: game.myRole,
            myWord: game.myWord,
            players: game.players,
            totalRounds: game.totalRounds || 3,
            currentRound: game.currentRound || 1
          });
          
          // 如果是描述阶段，开始计时
          if (game.status === 'describing') {
            this.startTimer();
          }
          
          // 显示词语弹窗
          if (game.myWord) {
            this.showWordModal();
          }
        }
      },
      fail: () => {
        wx.hideLoading();
        app.showToast('加载游戏失败');
      }
    });
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
    if (this.data.gameState === 'describing') {
      // 自动提交空描述
      this.submitDescription('');
    } else if (this.data.gameState === 'voting') {
      // 自动随机投票
      this.submitRandomVote();
    }
  },

  // 更新游戏状态
  updateGameState(state) {
    this.setData({
      gameState: state.status,
      currentRound: state.currentRound,
      players: state.players,
      descriptions: state.descriptions || [],
      votes: state.votes || {}
    });
    
    // 根据状态执行相应操作
    switch (state.status) {
      case 'describing':
        this.startTimer();
        this.setData({ timeLeft: state.timeLimit || 60 });
        break;
      case 'voting':
        this.startTimer();
        this.setData({ timeLeft: state.voteTime || 30 });
        this.showVoteModal();
        break;
      case 'result':
        this.showResultModal();
        break;
    }
  },

  // 处理玩家回合
  handlePlayerTurn(player) {
    const isMyTurn = player.id === app.globalData.userInfo?.id;
    this.setData({ 
      currentPlayerIndex: player.index,
      isMyTurn 
    });
    
    if (isMyTurn) {
      app.showToast('轮到你了，请描述你的词语');
    }
  },

  // 提交描述
  submitDescription(description = '') {
    if (!description.trim() && this.data.myDescription.trim()) {
      description = this.data.myDescription;
    }
    
    if (app.globalData.socket) {
      app.sendSocketMessage('submit-description', {
        roomCode: this.data.roomCode,
        description: description.trim(),
        round: this.data.currentRound
      });
    }
    
    this.setData({ myDescription: '' });
  },

  // 处理收到的描述
  handleDescription(description) {
    const descriptions = [...this.data.descriptions, description];
    this.setData({ descriptions });
  },

  // 提交投票
  submitVote(playerId) {
    if (!playerId) return;
    
    this.setData({ myVote: playerId });
    
    if (app.globalData.socket) {
      app.sendSocketMessage('submit-vote', {
        roomCode: this.data.roomCode,
        targetPlayerId: playerId,
        round: this.data.currentRound
      });
    }
    
    this.hideVoteModal();
  },

  // 处理投票
  handleVote(vote) {
    const votes = { ...this.data.votes };
    votes[vote.voter] = vote.target;
    this.setData({ votes });
  },

  // 处理游戏结果
  handleGameResult(result) {
    this.setData({
      gameState: 'ended',
      gameResult: result,
      winner: result.winner,
      eliminatedPlayer: result.eliminatedPlayer
    });
    
    this.showFinalResultModal();
    
    // 清理定时器
    if (this.data.timer) {
      clearInterval(this.data.timer);
    }
  },

  // 更新时间
  updateTime(time) {
    this.setData({ timeLeft: time.remaining });
  },

  // 输入描述
  onDescriptionInput(e) {
    this.setData({ myDescription: e.detail.value });
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

  // 显示回合结果弹窗
  showResultModal() {
    this.setData({ showResultModal: true });
    
    // 5秒后自动进入下一轮或结束
    setTimeout(() => {
      this.hideResultModal();
      this.nextRoundOrEnd();
    }, 5000);
  },

  // 隐藏回合结果弹窗
  hideResultModal() {
    this.setData({ showResultModal: false });
  },

  // 显示最终结果弹窗
  showFinalResultModal() {
    wx.showModal({
      title: '游戏结束',
      content: this.getResultMessage(),
      showCancel: false,
      confirmText: '返回房间',
      success: (res) => {
        if (res.confirm) {
          wx.navigateBack();
        }
      }
    });
  },

  // 获取结果消息
  getResultMessage() {
    const { winner, eliminatedPlayer } = this.data;
    
    if (winner === 'civilian') {
      return `平民胜利！\n卧底 ${eliminatedPlayer?.nickname || '玩家'} 被找出。`;
    } else {
      return `卧底胜利！\n卧底 ${eliminatedPlayer?.nickname || '玩家'} 成功隐藏。`;
    }
  },

  // 下一轮或结束游戏
  nextRoundOrEnd() {
    if (this.data.currentRound >= this.data.totalRounds) {
      // 游戏结束，请求最终结果
      if (app.globalData.socket) {
        app.sendSocketMessage('request-final-result', {
          roomCode: this.data.roomCode
        });
      }
    } else {
      // 进入下一轮
      if (app.globalData.socket) {
        app.sendSocketMessage('next-round', {
          roomCode: this.data.roomCode
        });
      }
    }
  },

  // 自动随机投票（超时用）
  submitRandomVote() {
    const otherPlayers = this.data.players.filter(
      player => player.id !== app.globalData.userInfo?.id
    );
    
    if (otherPlayers.length > 0) {
      const randomPlayer = otherPlayers[Math.floor(Math.random() * otherPlayers.length)];
      this.submitVote(randomPlayer.id);
    }
  },

  // 获取玩家角色文本
  getRoleText(role) {
    return role === 'civilian' ? '平民' : '卧底';
  },

  // 获取玩家状态颜色
  getPlayerStatusColor(player) {
    if (player.eliminated) return 'eliminated';
    if (player.id === this.data.currentPlayerIndex) return 'current';
    return 'normal';
  },

  // 返回房间
  backToRoom() {
    wx.navigateBack();
  },

  // 分享游戏结果
  shareResult() {
    wx.showShareMenu({
      withShareTicket: true
    });
  }
});