// app.js - 微信小程序入口文件

App({
  onLaunch() {
    // 小程序初始化时执行
    console.log('小程序初始化');
    
    // 单机版：不需要微信登录
    // this.checkLoginStatus();
  },

  onShow() {
    // 小程序显示时执行
    console.log('小程序显示');
  },

  onHide() {
    // 小程序隐藏时执行
    console.log('小程序隐藏');
  },

  globalData: {
    userInfo: null,
    token: null,
    socket: null,
    currentRoom: null
  },

  // 检查登录状态
  checkLoginStatus() {
    const token = wx.getStorageSync('token');
    if (token) {
      this.globalData.token = token;
      this.connectSocket();
    }
  },

  // 微信登录
  wxLogin() {
    return new Promise((resolve, reject) => {
      wx.login({
        success: (res) => {
          if (res.code) {
            // 发送code到后端获取token
            wx.request({
              url: 'https://api.example.com/auth/login',
              method: 'POST',
              data: { code: res.code },
              success: (res) => {
                if (res.data.success) {
                  const token = res.data.token;
                  wx.setStorageSync('token', token);
                  this.globalData.token = token;
                  this.connectSocket();
                  resolve(token);
                } else {
                  reject(new Error('登录失败'));
                }
              },
              fail: reject
            });
          } else {
            reject(new Error('获取code失败'));
          }
        },
        fail: reject
      });
    });
  },

  // 连接WebSocket
  connectSocket() {
    if (this.globalData.socket) {
      return;
    }

    const socket = wx.connectSocket({
      url: 'wss://api.example.com/ws',
      header: {
        'Authorization': `Bearer ${this.globalData.token}`
      }
    });

    socket.onOpen(() => {
      console.log('WebSocket连接已打开');
      this.globalData.socket = socket;
    });

    socket.onClose(() => {
      console.log('WebSocket连接已关闭');
      this.globalData.socket = null;
    });

    socket.onError((error) => {
      console.error('WebSocket连接错误:', error);
    });

    // 监听服务器消息
    socket.onMessage((res) => {
      const data = JSON.parse(res.data);
      this.handleSocketMessage(data);
    });
  },

  // 处理WebSocket消息
  handleSocketMessage(data) {
    const { type, payload } = data;
    
    switch (type) {
      case 'room_updated':
        this.handleRoomUpdate(payload);
        break;
      case 'game_started':
        this.handleGameStarted(payload);
        break;
      case 'new_message':
        this.handleNewMessage(payload);
        break;
      case 'vote_result':
        this.handleVoteResult(payload);
        break;
      default:
        console.warn('未知的消息类型:', type);
    }
  },

  // 发送WebSocket消息
  sendSocketMessage(type, payload) {
    if (!this.globalData.socket) {
      console.error('WebSocket未连接');
      return;
    }

    this.globalData.socket.send({
      data: JSON.stringify({ type, payload })
    });
  },

  // 工具函数：显示提示
  showToast(title, icon = 'none') {
    wx.showToast({
      title,
      icon,
      duration: 2000
    });
  },

  // 工具函数：显示加载中
  showLoading(title = '加载中') {
    wx.showLoading({ title });
  },

  // 工具函数：隐藏加载
  hideLoading() {
    wx.hideLoading();
  }
});