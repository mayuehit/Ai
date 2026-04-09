// pages/room/room.js - 游戏房间页面
const app = getApp();

Page({
  data: {
    roomCode: '',
    roomInfo: null,
    players: [],
    messages: [],
    newMessage: '',
    isHost: false,
    gameStatus: 'waiting', // waiting, playing, ended
    showCreateModal: false,
    showJoinModal: false,
    roomSettings: {
      maxPlayers: 8,
      rounds: 3,
      timeLimit: 60
    }
  },

  onLoad(options) {
    const { roomCode } = options;
    if (roomCode) {
      this.setData({ roomCode });
      this.joinRoom(roomCode);
    }
  },

  onShow() {
    // 页面显示时连接WebSocket
    if (app.globalData.token && !app.globalData.socket) {
      app.connectSocket();
    }
  },

  onUnload() {
    // 页面卸载时离开房间
    if (this.data.roomCode) {
      this.leaveRoom();
    }
  },

  // 创建房间
  createRoom() {
    const settings = this.data.roomSettings;
    
    wx.showLoading({ title: '创建房间中...' });
    
    wx.request({
      url: 'https://api.example.com/api/rooms',
      method: 'POST',
      header: {
        'Authorization': `Bearer ${app.globalData.token}`
      },
      data: settings,
      success: (res) => {
        wx.hideLoading();
        
        if (res.data.success) {
          const roomCode = res.data.roomCode;
          this.setData({ 
            roomCode,
            roomInfo: res.data.room,
            isHost: true 
          });
          
          this.joinRoom(roomCode);
          app.showToast('房间创建成功');
        } else {
          app.showToast(res.data.error || '创建房间失败');
        }
      },
      fail: (err) => {
        wx.hideLoading();
        app.showToast('网络错误，请重试');
      }
    });
  },

  // 加入房间
  joinRoom(roomCode) {
    if (!roomCode) {
      app.showToast('请输入房间号');
      return;
    }

    wx.showLoading({ title: '加入房间中...' });
    
    wx.request({
      url: `https://api.example.com/api/rooms/${roomCode}/join`,
      method: 'POST',
      header: {
        'Authorization': `Bearer ${app.globalData.token}`
      },
      success: (res) => {
        wx.hideLoading();
        
        if (res.data.success) {
          this.setData({
            roomCode,
            roomInfo: res.data.room,
            players: res.data.players || [],
            isHost: res.data.isHost || false
          });
          
          // 通过WebSocket加入房间
          if (app.globalData.socket) {
            app.sendSocketMessage('join-room', { roomCode });
          }
          
          app.showToast('加入房间成功');
        } else {
          app.showToast(res.data.error || '加入房间失败');
        }
      },
      fail: (err) => {
        wx.hideLoading();
        app.showToast('网络错误，请重试');
      }
    });
  },

  // 离开房间
  leaveRoom() {
    if (app.globalData.socket && this.data.roomCode) {
      app.sendSocketMessage('leave-room', { roomCode: this.data.roomCode });
    }
    
    this.setData({
      roomCode: '',
      roomInfo: null,
      players: [],
      messages: []
    });
  },

  // 开始游戏
  startGame() {
    if (!this.data.isHost) {
      app.showToast('只有房主可以开始游戏');
      return;
    }

    if (this.data.players.length < 4) {
      app.showToast('至少需要4名玩家才能开始游戏');
      return;
    }

    wx.showModal({
      title: '开始游戏',
      content: '确定要开始游戏吗？',
      success: (res) => {
        if (res.confirm) {
          if (app.globalData.socket) {
            app.sendSocketMessage('start-game', { roomCode: this.data.roomCode });
          }
        }
      }
    });
  },

  // 发送消息
  sendMessage() {
    const message = this.data.newMessage.trim();
    if (!message) {
      return;
    }

    if (app.globalData.socket && this.data.roomCode) {
      app.sendSocketMessage('send-message', {
        roomCode: this.data.roomCode,
        content: message,
        type: 'text'
      });
      
      this.setData({ newMessage: '' });
    }
  },

  // 输入消息
  onMessageInput(e) {
    this.setData({ newMessage: e.detail.value });
  },

  // 复制房间号
  copyRoomCode() {
    wx.setClipboardData({
      data: this.data.roomCode,
      success: () => {
        app.showToast('房间号已复制');
      }
    });
  },

  // 分享房间
  shareRoom() {
    wx.showShareMenu({
      withShareTicket: true
    });
  },

  // 显示创建房间弹窗
  showCreateRoomModal() {
    this.setData({ showCreateModal: true });
  },

  // 隐藏创建房间弹窗
  hideCreateRoomModal() {
    this.setData({ showCreateModal: false });
  },

  // 显示加入房间弹窗
  showJoinRoomModal() {
    this.setData({ showJoinModal: true });
  },

  // 隐藏加入房间弹窗
  hideJoinRoomModal() {
    this.setData({ showJoinModal: false });
  },

  // 更新房间设置
  updateRoomSetting(e) {
    const { key } = e.currentTarget.dataset;
    const value = e.detail.value;
    
    const settings = { ...this.data.roomSettings };
    settings[key] = parseInt(value) || value;
    
    this.setData({ roomSettings: settings });
  },

  // 处理WebSocket消息
  handleSocketMessage(data) {
    const { type, payload } = data;
    
    switch (type) {
      case 'player-joined':
        this.handlePlayerJoined(payload);
        break;
      case 'player-left':
        this.handlePlayerLeft(payload);
        break;
      case 'new-message':
        this.handleNewMessage(payload);
        break;
      case 'game-started':
        this.handleGameStarted(payload);
        break;
      default:
        console.warn('未知的消息类型:', type);
    }
  },

  // 处理玩家加入
  handlePlayerJoined(player) {
    const players = [...this.data.players, player];
    this.setData({ players });
    
    app.showToast(`${player.nickname || '新玩家'} 加入了房间`);
  },

  // 处理玩家离开
  handlePlayerLeft(player) {
    const players = this.data.players.filter(p => p.id !== player.id);
    this.setData({ players });
    
    app.showToast(`${player.nickname || '玩家'} 离开了房间`);
  },

  // 处理新消息
  handleNewMessage(message) {
    const messages = [...this.data.messages, message];
    this.setData({ messages });
    
    // 滚动到底部
    setTimeout(() => {
      wx.pageScrollTo({
        scrollTop: 9999,
        duration: 300
      });
    }, 100);
  },

  // 处理游戏开始
  handleGameStarted(gameData) {
    this.setData({ gameStatus: 'playing' });
    
    // 跳转到游戏页面
    wx.navigateTo({
      url: `/pages/game/game?roomCode=${this.data.roomCode}`
    });
  }
});