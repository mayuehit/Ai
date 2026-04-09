// 游戏逻辑服务
const Word = require('../models/Word');

class GameLogic {
  constructor() {
    this.wordPairs = [];
    this.loadWordPairs();
  }

  // 加载词语对
  async loadWordPairs() {
    try {
      // 从数据库加载词语
      const words = await Word.find().limit(100);
      this.wordPairs = words.map(word => ({
        civilian: word.civilian,
        undercover: word.undercover,
        category: word.category,
        difficulty: word.difficulty || 1
      }));
      
      // 如果没有数据，使用默认词语
      if (this.wordPairs.length === 0) {
        this.wordPairs = this.getDefaultWordPairs();
      }
      
      console.log(`✅ 加载了 ${this.wordPairs.length} 个词语对`);
    } catch (error) {
      console.error('❌ 加载词语对失败:', error);
      this.wordPairs = this.getDefaultWordPairs();
    }
  }

  // 获取默认词语对
  getDefaultWordPairs() {
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
      { civilian: '孙悟空', undercover: '猪八戒', category: '西游记', difficulty: 3 }
    ];
  }

  // 分配角色
  assignRoles(playerCount) {
    if (playerCount < 4) {
      throw new Error('至少需要4名玩家');
    }

    const roles = new Array(playerCount).fill('civilian');
    
    // 计算卧底数量（通常1个卧底，玩家多时可增加）
    let undercoverCount = 1;
    if (playerCount >= 8) {
      undercoverCount = 2;
    }
    if (playerCount >= 12) {
      undercoverCount = 3;
    }

    // 随机选择卧底位置
    const undercoverIndices = new Set();
    while (undercoverIndices.size < undercoverCount) {
      const index = Math.floor(Math.random() * playerCount);
      undercoverIndices.add(index);
    }

    // 分配卧底角色
    for (const index of undercoverIndices) {
      roles[index] = 'undercover';
    }

    return roles;
  }

  // 分配词语
  assignWords(roles) {
    if (this.wordPairs.length === 0) {
      this.wordPairs = this.getDefaultWordPairs();
    }

    // 随机选择一个词语对
    const wordPair = this.wordPairs[Math.floor(Math.random() * this.wordPairs.length)];
    
    // 为每个玩家分配词语
    const playerWords = roles.map(role => ({
      word: role === 'civilian' ? wordPair.civilian : wordPair.undercover,
      role,
      originalPair: wordPair
    }));

    return {
      playerWords,
      wordPair,
      civilianWord: wordPair.civilian,
      undercoverWord: wordPair.undercover
    };
  }

  // 处理描述
  processDescription(description, playerId, round) {
    // 清洗描述文本
    const cleaned = this.cleanDescription(description);
    
    // 检查是否违规（直接说出词语）
    const isViolation = this.checkViolation(cleaned);
    
    return {
      id: `${playerId}_${Date.now()}`,
      playerId,
      description: cleaned,
      round,
      timestamp: new Date(),
      isViolation,
      score: this.calculateDescriptionScore(cleaned)
    };
  }

  // 清洗描述
  cleanDescription(text) {
    if (!text) return '';
    
    // 移除多余空格和换行
    let cleaned = text.trim().replace(/\s+/g, ' ');
    
    // 限制长度
    if (cleaned.length > 50) {
      cleaned = cleaned.substring(0, 47) + '...';
    }
    
    return cleaned;
  }

  // 检查违规
  checkViolation(description) {
    if (!description) return false;
    
    // 这里可以添加更复杂的违规检测逻辑
    // 例如：检查是否直接说出了常见词语
    
    const commonViolations = [
      '就是', '肯定是', '一定是', '我的是', '词语是'
    ];
    
    return commonViolations.some(violation => 
      description.toLowerCase().includes(violation)
    );
  }

  // 计算描述分数
  calculateDescriptionScore(description) {
    if (!description || description.length === 0) return 0;
    
    let score = 10; // 基础分
    
    // 根据描述长度加分
    if (description.length >= 5 && description.length <= 20) {
      score += 5;
    }
    
    // 根据词汇丰富度加分（简单实现）
    const words = description.split(' ');
    const uniqueWords = new Set(words);
    if (uniqueWords.size >= 3) {
      score += 3;
    }
    
    return Math.min(score, 20); // 最高20分
  }

  // 处理投票
  processVotes(votes, players, roles) {
    // 统计票数
    const voteCount = {};
    const voterMap = {};
    
    for (const [voterId, targetId] of Object.entries(votes)) {
      if (targetId) {
        voteCount[targetId] = (voteCount[targetId] || 0) + 1;
        voterMap[voterId] = targetId;
      }
    }
    
    // 找出得票最多的玩家
    let maxVotes = 0;
    let eliminatedPlayers = [];
    
    for (const [playerId, count] of Object.entries(voteCount)) {
      if (count > maxVotes) {
        maxVotes = count;
        eliminatedPlayers = [playerId];
      } else if (count === maxVotes) {
        eliminatedPlayers.push(playerId);
      }
    }
    
    // 处理平票情况
    let eliminatedPlayerId = null;
    if (eliminatedPlayers.length === 1) {
      eliminatedPlayerId = eliminatedPlayers[0];
    } else if (eliminatedPlayers.length > 1) {
      // 平票时随机淘汰一个
      eliminatedPlayerId = eliminatedPlayers[Math.floor(Math.random() * eliminatedPlayers.length)];
    }
    
    // 获取淘汰玩家信息
    const eliminatedPlayer = players.find(p => p.id === eliminatedPlayerId);
    const eliminatedRole = eliminatedPlayer ? roles[players.indexOf(eliminatedPlayer)] : null;
    
    // 判断胜负
    let winner = '';
    if (eliminatedRole === 'undercover') {
      winner = 'civilian'; // 平民找出卧底
    } else if (eliminatedRole === 'civilian') {
      // 检查是否还有卧底存活
      const aliveUndercover = players.some((player, index) => 
        player.id !== eliminatedPlayerId && roles[index] === 'undercover'
      );
      winner = aliveUndercover ? 'undercover' : 'civilian';
    }
    
    return {
      voteCount,
      voterMap,
      eliminatedPlayer: eliminatedPlayer || null,
      eliminatedRole,
      winner,
      isTie: eliminatedPlayers.length > 1
    };
  }

  // 计算游戏得分
  calculateScores(gameResult, players, roles, descriptions) {
    const scores = {};
    
    players.forEach((player, index) => {
      const role = roles[index];
      let score = 0;
      
      // 基础参与分
      score += 10;
      
      // 胜利奖励
      if (gameResult.winner === role) {
        score += 30;
      }
      
      // 描述质量分
      const playerDescriptions = descriptions.filter(d => d.playerId === player.id);
      playerDescriptions.forEach(desc => {
        score += desc.score || 0;
      });
      
      // 投票正确加分（如果投中了卧底）
      if (gameResult.voterMap && gameResult.voterMap[player.id]) {
        const votedPlayerId = gameResult.voterMap[player.id];
        const votedPlayerIndex = players.findIndex(p => p.id === votedPlayerId);
        if (votedPlayerIndex !== -1 && roles[votedPlayerIndex] === 'undercover') {
          score += 20;
        }
      }
      
      // 卧底隐藏奖励
      if (role === 'undercover' && player.id !== gameResult.eliminatedPlayer?.id) {
        score += 25;
      }
      
      scores[player.id] = score;
    });
    
    return scores;
  }

  // 生成游戏报告
  generateGameReport(gameData) {
    const {
      players,
      roles,
      wordPair,
      descriptions,
      votes,
      result,
      scores
    } = gameData;
    
    const report = {
      gameId: `game_${Date.now()}`,
      timestamp: new Date(),
      players: players.map((player, index) => ({
        id: player.id,
        nickname: player.nickname,
        role: roles[index],
        score: scores[player.id] || 0,
        description: descriptions.find(d => d.playerId === player.id)?.description || '',
        votedFor: votes[player.id] || null
      })),
      wordPair,
      result: {
        winner: result.winner,
        eliminatedPlayer: result.eliminatedPlayer,
        voteDetails: result.voteCount
      },
      statistics: {
        totalPlayers: players.length,
        undercoverCount: roles.filter(r => r === 'undercover').length,
        averageScore: Object.values(scores).reduce((a, b) => a + b, 0) / players.length,
        bestPlayer: players.reduce((best, player) => 
          (scores[player.id] || 0) > (scores[best.id] || 0) ? player : best
        )
      }
    };
    
    return report;
  }

  // 验证游戏操作
  validateGameAction(action, playerId, gameState) {
    const validations = {
      submitDescription: () => {
        if (gameState !== 'describing') {
          return { valid: false, error: '当前不是描述阶段' };
        }
        if (gameState.currentPlayer !== playerId) {
          return { valid: false, error: '不是你的回合' };
        }
        return { valid: true };
      },
      
      submitVote: () => {
        if (gameState !== 'voting') {
          return { valid: false, error: '当前不是投票阶段' };
        }
        if (gameState.hasVoted && gameState.hasVoted.includes(playerId)) {
          return { valid: false, error: '你已经投过票了' };
        }
        return { valid: true };
      },
      
      startGame: () => {
        if (gameState !== 'waiting') {
          return { valid: false, error: '游戏已经开始' };
        }
        if (gameState.host !== playerId) {
          return { valid: false, error: '只有房主可以开始游戏' };
        }
        return { valid: true };
      }
    };
    
    return validations[action] ? validations[action]() : { valid: false, error: '未知操作' };
  }
}

module.exports = new GameLogic();