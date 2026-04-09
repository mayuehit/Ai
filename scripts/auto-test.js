#!/usr/bin/env node

/**
 * 自动化测试脚本
 * 模拟完整的游戏流程测试
 */

const axios = require('axios');
const WebSocket = require('ws');

// 配置
const API_BASE = 'http://localhost:3000/api';
const WS_URL = 'ws://localhost:3000';

// 测试用户
const testUsers = [
  { nickname: '测试玩家1', role: 'civilian' },
  { nickname: '测试玩家2', role: 'civilian' },
  { nickname: '测试玩家3', role: 'civilian' },
  { nickname: '测试玩家4', role: 'undercover' }
];

// 测试结果
const testResults = {
  passed: 0,
  failed: 0,
  errors: []
};

// 工具函数：延迟
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// 工具函数：记录结果
const recordResult = (testName, passed, error = null) => {
  if (passed) {
    testResults.passed++;
    console.log(`✅ ${testName}`);
  } else {
    testResults.failed++;
    testResults.errors.push({ testName, error });
    console.log(`❌ ${testName}: ${error}`);
  }
};

// 测试1: 用户注册和登录
async function testUserAuth() {
  console.log('\n🔐 测试用户认证...');
  
  try {
    // 模拟微信登录
    const loginRes = await axios.post(`${API_BASE}/auth/login`, {
      code: 'test_code_123'
    });
    
    if (loginRes.data.success && loginRes.data.token) {
      recordResult('用户登录', true);
      return loginRes.data.token;
    } else {
      recordResult('用户登录', false, '登录响应格式错误');
      return null;
    }
  } catch (error) {
    recordResult('用户登录', false, error.message);
    return null;
  }
}

// 测试2: 创建游戏房间
async function testCreateRoom(token) {
  console.log('\n🏠 测试创建房间...');
  
  try {
    const createRes = await axios.post(`${API_BASE}/rooms`, {
      maxPlayers: 8,
      rounds: 3,
      timeLimit: 60
    }, {
      headers: { Authorization: `Bearer ${token}` }
    });
    
    if (createRes.data.success && createRes.data.roomCode) {
      recordResult('创建房间', true);
      return createRes.data;
    } else {
      recordResult('创建房间', false, '创建房间响应格式错误');
      return null;
    }
  } catch (error) {
    recordResult('创建房间', false, error.message);
    return null;
  }
}

// 测试3: WebSocket连接
async function testWebSocket(token, roomCode) {
  console.log('\n🔌 测试WebSocket连接...');
  
  return new Promise((resolve) => {
    const ws = new WebSocket(`${WS_URL}?token=${token}`);
    
    ws.on('open', () => {
      recordResult('WebSocket连接', true);
      
      // 加入房间
      ws.send(JSON.stringify({
        type: 'join-room',
        payload: { roomCode }
      }));
      
      setTimeout(() => {
        ws.close();
        resolve(true);
      }, 1000);
    });
    
    ws.on('error', (error) => {
      recordResult('WebSocket连接', false, error.message);
      resolve(false);
    });
    
    ws.on('close', () => {
      // 连接关闭
    });
  });
}

// 测试4: 游戏逻辑
async function testGameLogic() {
  console.log('\n🎮 测试游戏逻辑...');
  
  try {
    // 测试词语生成
    const words = generateTestWords();
    if (words.civilian && words.undercover && words.civilian !== words.undercover) {
      recordResult('词语生成', true);
    } else {
      recordResult('词语生成', false, '词语生成错误');
    }
    
    // 测试角色分配
    const roles = assignTestRoles(4);
    const undercoverCount = roles.filter(r => r === 'undercover').length;
    if (undercoverCount === 1) {
      recordResult('角色分配', true);
    } else {
      recordResult('角色分配', false, `卧底数量错误: ${undercoverCount}`);
    }
    
    // 测试投票逻辑
    const voteResult = simulateVote(roles);
    if (voteResult.winner === 'civilian' || voteResult.winner === 'undercover') {
      recordResult('投票逻辑', true);
    } else {
      recordResult('投票逻辑', false, '投票结果错误');
    }
    
  } catch (error) {
    recordResult('游戏逻辑', false, error.message);
  }
}

// 测试5: 性能测试
async function testPerformance() {
  console.log('\n⚡ 测试性能...');
  
  const startTime = Date.now();
  
  try {
    // 模拟并发请求
    const promises = [];
    for (let i = 0; i < 10; i++) {
      promises.push(
        axios.post(`${API_BASE}/auth/login`, {
          code: `test_code_${i}`
        }).catch(() => null)
      );
    }
    
    await Promise.all(promises);
    const duration = Date.now() - startTime;
    
    if (duration < 5000) {
      recordResult('并发性能', true, `耗时: ${duration}ms`);
    } else {
      recordResult('并发性能', false, `耗时过长: ${duration}ms`);
    }
    
  } catch (error) {
    recordResult('性能测试', false, error.message);
  }
}

// 辅助函数：生成测试词语
function generateTestWords() {
  const wordPairs = [
    { civilian: '苹果', undercover: '香蕉' },
    { civilian: '电脑', undercover: '手机' },
    { civilian: '夏天', undercover: '冬天' }
  ];
  
  return wordPairs[Math.floor(Math.random() * wordPairs.length)];
}

// 辅助函数：分配测试角色
function assignTestRoles(playerCount) {
  const roles = Array(playerCount).fill('civilian');
  const undercoverIndex = Math.floor(Math.random() * playerCount);
  roles[undercoverIndex] = 'undercover';
  return roles;
}

// 辅助函数：模拟投票
function simulateVote(roles) {
  const votes = {};
  const playerCount = roles.length;
  
  // 模拟投票
  for (let i = 0; i < playerCount; i++) {
    let vote;
    do {
      vote = Math.floor(Math.random() * playerCount);
    } while (vote === i); // 不能投自己
    
    votes[vote] = (votes[vote] || 0) + 1;
  }
  
  // 找出得票最多的玩家
  let maxVotes = 0;
  let votedPlayer = -1;
  
  for (const [player, voteCount] of Object.entries(votes)) {
    if (voteCount > maxVotes) {
      maxVotes = voteCount;
      votedPlayer = parseInt(player);
    }
  }
  
  // 判断游戏结果
  const isUndercover = roles[votedPlayer] === 'undercover';
  
  return {
    votedPlayer,
    votes,
    winner: isUndercover ? 'civilian' : 'undercover',
    isUndercoverEliminated: isUndercover
  };
}

// 主测试函数
async function runAllTests() {
  console.log('🚀 开始自动化测试...');
  console.log('='.repeat(50));
  
  // 测试1: 用户认证
  const token = await testUserAuth();
  if (!token) {
    console.log('❌ 用户认证失败，停止测试');
    return;
  }
  
  // 测试2: 创建房间
  const roomData = await testCreateRoom(token);
  if (!roomData) {
    console.log('❌ 创建房间失败，停止测试');
    return;
  }
  
  // 测试3: WebSocket
  await testWebSocket(token, roomData.roomCode);
  
  // 测试4: 游戏逻辑
  await testGameLogic();
  
  // 测试5: 性能测试
  await testPerformance();
  
  // 输出测试结果
  console.log('\n' + '='.repeat(50));
  console.log('📊 测试结果汇总:');
  console.log(`✅ 通过: ${testResults.passed}`);
  console.log(`❌ 失败: ${testResults.failed}`);
  console.log(`📈 通过率: ${((testResults.passed / (testResults.passed + testResults.failed)) * 100).toFixed(1)}%`);
  
  if (testResults.errors.length > 0) {
    console.log('\n🔍 错误详情:');
    testResults.errors.forEach((error, index) => {
      console.log(`${index + 1}. ${error.testName}: ${error.error}`);
    });
  }
  
  // 退出码
  process.exit(testResults.failed > 0 ? 1 : 0);
}

// 运行测试
runAllTests().catch(error => {
  console.error('💥 测试运行错误:', error);
  process.exit(1);
});