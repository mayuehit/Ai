// 单机离线游戏逻辑
class OfflineGame {
  constructor() {
    this.players = [];
    this.words = this.loadWords();
    this.gameState = 'waiting';
    this.currentRound = 1;
    this.totalRounds = 3;
    this.currentPlayerIndex = 0;
    this.descriptions = [];
    this.votes = {};
    this.myRole = '';
    this.myWord = '';
  }

  // 加载本地词语库
  loadWords() {
    return [
      { civilian: '苹果', undercover: '香蕉', category: '水果', difficulty: 1 },
      { civilian: '电脑', undercover: '手机', category: '电子产品', difficulty: 1 },
      { civilian: '夏天', undercover: '冬天', category: '季节', difficulty: 1 },
      { civilian: '咖啡', undercover: '茶', category: '饮料', difficulty: 1 },
      { civilian: '电影', undercover: '电视剧', category: '娱乐', difficulty: 1 },
      { civilian: '篮球', undercover: '足球', category: '运动', difficulty: 2 },
      { civilian: '微信', undercover: 'QQ', category: '社交软件', difficulty: 2 },
      { civilian: '北京', undercover: '上海', category: '城市', difficulty: 2 },
      { civilian: '钢琴', undercover: '小提琴', category: '乐器', difficulty: 3 },
      { civilian: '孙悟空', undercover: '猪八戒', category: '西游记', difficulty: 3 },
      { civilian: '牛奶', undercover: '豆浆', category: '饮料', difficulty: 1 },
      { civilian: '火车', undercover: '飞机', category: '交通工具', difficulty: 1 },
      { civilian: '猫', undercover: '狗', category: '动物', difficulty: 1 },
      { civilian: '红色', undercover: '蓝色', category: '颜色', difficulty: 1 },
      { civilian: '老师', undercover: '医生', category: '职业', difficulty: 2 }
    ];
  }

  // 添加AI玩家
  addAIPlayer(name) {
    const player = {
      id: `ai_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      name: name || `玩家${this.players.length + 1}`,
      isAI: true,
      avatar: `/images/ai-avatar-${(this.players.length % 5) + 1}.png`
    };
    this.players.push(player);
    return player;
  }

  // 添加人类玩家
  addHumanPlayer(name) {
    const player = {
      id: `human_${Date.now()}`,
      name: name || '我',
      isAI: false,
      avatar: '/images/human-avatar.png'
    };
    this.players.push(player);
    return player;
  }

  // 开始游戏
  startGame(playerCount = 6) {
    // 确保有足够玩家
    while (this.players.length < playerCount) {
      this.addAIPlayer();
    }

    // 分配角色
    this.assignRoles();

    // 分配词语
    this.assignWords();

    this.gameState = 'describing';
    this.currentPlayerIndex = 0;
    this.descriptions = [];
    this.votes = {};

    return {
      players: this.players,
      myRole: this.myRole,
      myWord: this.myWord,
      gameState: this.gameState
    };
  }

  // 分配角色（1个卧底，其余平民）
  assignRoles() {
    const roles = new Array(this.players.length).fill('civilian');
    
    // 随机选择一个卧底
    const undercoverIndex = Math.floor(Math.random() * this.players.length);
    roles[undercoverIndex] = 'undercover';
    
    // 记录玩家角色
    this.players.forEach((player, index) => {
      player.role = roles[index];
    });

    // 设置人类玩家的角色
    const humanPlayer = this.players.find(p => !p.isAI);
    if (humanPlayer) {
      this.myRole = humanPlayer.role;
    }
  }

  // 分配词语
  assignWords() {
    // 随机选择一个词语对
    const wordPair = this.words[Math.floor(Math.random() * this.words.length)];
    
    // 为每个玩家分配词语
    this.players.forEach(player => {
      player.word = player.role === 'civilian' ? wordPair.civilian : wordPair.undercover;
    });

    // 设置人类玩家的词语
    const humanPlayer = this.players.find(p => !p.isAI);
    if (humanPlayer) {
      this.myWord = humanPlayer.word;
    }

    return wordPair;
  }

  // AI玩家描述
  getAIDescription(player) {
    const word = player.word;
    const role = player.role;
    
    // AI根据角色和词语生成描述
    const descriptions = {
      '苹果': ['圆形的', '水果', '红色的', '可以吃', '乔布斯'],
      '香蕉': ['黄色的', '水果', '弯曲的', '猴子爱吃', '需要剥皮'],
      '电脑': ['电子设备', '可以上网', '有屏幕', '工作需要', '玩游戏'],
      '手机': ['随身携带', '可以打电话', '智能的', '有摄像头', '充电'],
      '夏天': ['热的', '季节', '游泳', '冰淇淋', '暑假'],
      '冬天': ['冷的', '季节', '下雪', '羽绒服', '春节'],
      '咖啡': ['饮料', '苦的', '提神', '星巴克', '咖啡因'],
      '茶': ['饮料', '中国的', '养生', '茶叶', '茶馆'],
      '电影': ['娱乐', '在影院看', '有导演', '两个小时', ' popcorn'],
      '电视剧': ['连续剧', '在家看', '很多集', '追剧', '网剧']
    };

    // 如果是卧底，描述要模糊一些
    if (role === 'undercover') {
      const genericDescriptions = [
        '常见的东西', '大家都知道的', '日常生活中', '很普通的', '没什么特别的'
      ];
      return genericDescriptions[Math.floor(Math.random() * genericDescriptions.length)];
    }

    // 平民给出具体描述
    if (descriptions[word]) {
      return descriptions[word][Math.floor(Math.random() * descriptions[word].length)];
    }

    // 默认描述
    return `和${word}相关的东西`;
  }

  // 提交描述
  submitDescription(description, playerId = null) {
    const player = playerId ? 
      this.players.find(p => p.id === playerId) : 
      this.players[this.currentPlayerIndex];
    
    if (!player) return;

    const desc = {
      id: `${player.id}_${Date.now()}`,
      playerId: player.id,
      playerName: player.name,
      description: description || (player.isAI ? this.getAIDescription(player) : ''),
      isAI: player.isAI,
      timestamp: new Date()
    };

    this.descriptions.push(desc);

    // 移动到下一个玩家
    this.currentPlayerIndex++;
    
    // 如果所有玩家都描述完毕，进入投票环节
    if (this.currentPlayerIndex >= this.players.length) {
      this.gameState = 'voting';
      this.currentPlayerIndex = 0;
    }

    return desc;
  }

  // AI投票逻辑
  getAIVote(player) {
    // AI根据描述投票
    // 简单逻辑：随机投给其他玩家
    const otherPlayers = this.players.filter(p => 
      p.id !== player.id && !p.eliminated
    );
    
    if (otherPlayers.length === 0) return null;
    
    const randomPlayer = otherPlayers[Math.floor(Math.random() * otherPlayers.length)];
    return randomPlayer.id;
  }

  // 提交投票
  submitVote(targetPlayerId, voterId = null) {
    const voter = voterId ? 
      this.players.find(p => p.id === voterId) : 
      this.players.find(p => !p.isAI); // 人类玩家
    
    if (!voter) return;

    this.votes[voter.id] = targetPlayerId;

    // 如果是AI，自动投票
    if (voter.isAI && !targetPlayerId) {
      const aiVote = this.getAIVote(voter);
      if (aiVote) {
        this.votes[voter.id] = aiVote;
      }
    }

    // 检查是否所有玩家都投票了
    const votedCount = Object.keys(this.votes).length;
    const alivePlayers = this.players.filter(p => !p.eliminated).length;

    if (votedCount >= alivePlayers) {
      this.calculateVoteResult();
    }

    return {
      voter: voter.id,
      target: targetPlayerId
    };
  }

  // 计算投票结果
  calculateVoteResult() {
    // 统计票数
    const voteCount = {};
    for (const voterId in this.votes) {
      const targetId = this.votes[voterId];
      if (targetId) {
        voteCount[targetId] = (voteCount[targetId] || 0) + 1;
      }
    }

    // 找出得票最多的玩家
    let maxVotes = 0;
    let eliminatedPlayerId = null;

    for (const [playerId, count] of Object.entries(voteCount)) {
      if (count > maxVotes) {
        maxVotes = count;
        eliminatedPlayerId = playerId;
      }
    }

    // 淘汰玩家
    if (eliminatedPlayerId) {
      const player = this.players.find(p => p.id === eliminatedPlayerId);
      if (player) {
        player.eliminated = true;
        
        // 检查游戏是否结束
        const aliveUndercover = this.players.some(p => 
          !p.eliminated && p.role === 'undercover'
        );
        const aliveCivilian = this.players.some(p => 
          !p.eliminated && p.role === 'civilian'
        );

        if (!aliveUndercover) {
          this.gameState = 'ended';
          this.winner = 'civilian';
        } else if (!aliveCivilian) {
          this.gameState = 'ended';
          this.winner = 'undercover';
        } else if (this.currentRound >= this.totalRounds) {
          this.gameState = 'ended';
          this.winner = aliveUndercover ? 'undercover' : 'civilian';
        } else {
          // 进入下一轮
          this.currentRound++;
          this.gameState = 'describing';
          this.currentPlayerIndex = 0;
          this.descriptions = [];
          this.votes = {};
        }

        return {
          eliminatedPlayer: player,
          voteCount,
          winner: this.winner,
          gameState: this.gameState,
          nextRound: this.currentRound
        };
      }
    }

    return null;
  }

  // 获取游戏状态
  getGameState() {
    return {
      gameState: this.gameState,
      currentRound: this.currentRound,
      totalRounds: this.totalRounds,
      players: this.players,
      descriptions: this.descriptions,
      votes: this.votes,
      myRole: this.myRole,
      myWord: this.myWord,
      currentPlayerIndex: this.currentPlayerIndex
    };
  }

  // 重置游戏
  resetGame() {
    this.players = [];
    this.gameState = 'waiting';
    this.currentRound = 1;
    this.currentPlayerIndex = 0;
    this.descriptions = [];
    this.votes = {};
    this.myRole = '';
    this.myWord = '';
  }

  // 保存游戏到本地存储
  saveToStorage() {
    try {
      const gameData = {
        players: this.players,
        gameState: this.gameState,
        currentRound: this.currentRound,
        descriptions: this.descriptions,
        votes: this.votes,
        myRole: this.myRole,
        myWord: this.myWord,
        timestamp: Date.now()
      };
      
      wx.setStorageSync('offline_game_state', gameData);
      return true;
    } catch (error) {
      console.error('保存游戏失败:', error);
      return false;
    }
  }

  // 从本地存储加载游戏
  loadFromStorage() {
    try {
      const gameData = wx.getStorageSync('offline_game_state');
      if (gameData) {
        this.players = gameData.players || [];
        this.gameState = gameData.gameState || 'waiting';
        this.currentRound = gameData.currentRound || 1;
        this.descriptions = gameData.descriptions || [];
        this.votes = gameData.votes || {};
        this.myRole = gameData.myRole || '';
        this.myWord = gameData.myWord || '';
        return true;
      }
    } catch (error) {
      console.error('加载游戏失败:', error);
    }
    return false;
  }

  // 获取游戏统计
  getGameStats() {
    const totalGames = wx.getStorageSync('total_games') || 0;
    const wins = wx.getStorageSync('game_wins') || 0;
    const winRate = totalGames > 0 ? (wins / totalGames * 100).toFixed(1) : 0;
    
    return {
      totalGames,
      wins,
      winRate,
      asCivilian: wx.getStorageSync('as_civilian') || { games: 0, wins: 0 },
      asUndercover: wx.getStorageSync('as_undercover') || { games: 0, wins: 0 }
    };
  }

  // 记录游戏结果
  recordGameResult(isWin, role) {
    try {
      // 总游戏数
      let totalGames = wx.getStorageSync('total_games') || 0;
      totalGames++;
      wx.setStorageSync('total_games', totalGames);

      // 总胜利数
      if (isWin) {
        let wins = wx.getStorageSync('game_wins') || 0;
        wins++;
        wx.setStorageSync('game_wins', wins);
      }

      // 角色统计
      if (role === 'civilian') {
        let stats = wx.getStorageSync('as_civilian') || { games: 0, wins: 0 };
        stats.games++;
        if (isWin) stats.wins++;
        wx.setStorageSync('as_civilian', stats);
      } else if (role === 'undercover') {
        let stats = wx.getStorageSync('as_undercover') || { games: 0, wins: 0 };
        stats.games++;
        if (isWin) stats.wins++;
        wx.setStorageSync('as_undercover', stats);
      }

      return true;
    } catch (error) {
      console.error('记录游戏结果失败:', error);
      return false;
    }
  }
}

// 导出单例
const offlineGame = new OfflineGame();
module.exports = offlineGame;