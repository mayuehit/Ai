// 小程序应用测试用例

describe('微信小程序应用测试', () => {
  let app;

  beforeEach(() => {
    // 模拟微信小程序环境
    global.wx = {
      login: jest.fn(),
      request: jest.fn(),
      connectSocket: jest.fn(),
      showToast: jest.fn(),
      showLoading: jest.fn(),
      hideLoading: jest.fn(),
      getStorageSync: jest.fn(),
      setStorageSync: jest.fn()
    };

    // 创建应用实例
    const AppClass = require('../miniprogram/app.js');
    app = new AppClass();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('应用初始化', () => {
    test('应用启动时应检查登录状态', () => {
      wx.getStorageSync.mockReturnValue('mock-token');
      app.onLaunch();
      
      expect(wx.getStorageSync).toHaveBeenCalledWith('token');
      expect(app.globalData.token).toBe('mock-token');
    });

    test('应用启动时应连接WebSocket', () => {
      wx.getStorageSync.mockReturnValue('mock-token');
      app.onLaunch();
      
      expect(wx.connectSocket).toHaveBeenCalled();
    });
  });

  describe('微信登录功能', () => {
    test('登录成功应存储token并连接WebSocket', async () => {
      wx.login.mockImplementation(({ success }) => {
        success({ code: 'mock-code' });
      });

      wx.request.mockImplementation(({ success }) => {
        success({
          data: {
            success: true,
            token: 'new-token'
          }
        });
      });

      await app.wxLogin();

      expect(wx.login).toHaveBeenCalled();
      expect(wx.request).toHaveBeenCalledWith(
        expect.objectContaining({
          url: 'https://api.example.com/auth/login',
          method: 'POST',
          data: { code: 'mock-code' }
        })
      );
      expect(wx.setStorageSync).toHaveBeenCalledWith('token', 'new-token');
      expect(app.globalData.token).toBe('new-token');
    });

    test('登录失败应抛出错误', async () => {
      wx.login.mockImplementation(({ fail }) => {
        fail({ errMsg: '登录失败' });
      });

      await expect(app.wxLogin()).rejects.toThrow('获取code失败');
    });
  });

  describe('WebSocket功能', () => {
    test('应正确处理房间更新消息', () => {
      const mockSocket = {
        send: jest.fn()
      };
      app.globalData.socket = mockSocket;

      const message = {
        type: 'room_updated',
        payload: { roomId: '123', players: [] }
      };

      app.handleSocketMessage(message);
      // 这里可以添加对handleRoomUpdate的验证
    });

    test('发送消息时WebSocket未连接应报错', () => {
      app.globalData.socket = null;
      console.error = jest.fn();

      app.sendSocketMessage('test', {});

      expect(console.error).toHaveBeenCalledWith('WebSocket未连接');
    });
  });

  describe('工具函数', () => {
    test('showToast应调用wx.showToast', () => {
      app.showToast('测试提示');
      
      expect(wx.showToast).toHaveBeenCalledWith({
        title: '测试提示',
        icon: 'none',
        duration: 2000
      });
    });

    test('showLoading应调用wx.showLoading', () => {
      app.showLoading('加载中...');
      
      expect(wx.showLoading).toHaveBeenCalledWith({
        title: '加载中...'
      });
    });

    test('hideLoading应调用wx.hideLoading', () => {
      app.hideLoading();
      
      expect(wx.hideLoading).toHaveBeenCalled();
    });
  });

  describe('全局数据', () => {
    test('全局数据应包含必要字段', () => {
      expect(app.globalData).toEqual({
        userInfo: null,
        token: null,
        socket: null,
        currentRoom: null
      });
    });
  });
});