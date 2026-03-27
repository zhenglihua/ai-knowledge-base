import { FullConfig } from '@playwright/test';
import axios from 'axios';

/**
 * 全局设置 - 测试开始前执行
 * 用于准备测试数据、检查服务状态等
 */
async function globalSetup(config: FullConfig) {
  console.log('🚀 开始全局设置...');

  const { apiBaseURL } = config.projects[0].use;
  const baseURL = (apiBaseURL as string) || 'http://localhost:8000';

  // 检查后端服务是否可用
  let retries = 5;
  while (retries > 0) {
    try {
      const response = await axios.get(`${baseURL}/api/v1/health`, {
        timeout: 5000,
      });
      console.log('✅ 后端服务已就绪:', response.status);
      break;
    } catch (error) {
      retries--;
      if (retries === 0) {
        console.warn('⚠️ 后端服务检查失败，测试可能会受到影响');
      } else {
        console.log(`⏳ 等待后端服务... (${retries} 次重试)`);
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }
  }

  // 检查前端服务是否可用
  retries = 5;
  const frontendURL = config.projects[0].use.baseURL as string;
  while (retries > 0) {
    try {
      const response = await axios.get(frontendURL, {
        timeout: 5000,
      });
      console.log('✅ 前端服务已就绪:', response.status);
      break;
    } catch (error) {
      retries--;
      if (retries === 0) {
        console.warn('⚠️ 前端服务检查失败，测试可能会受到影响');
      } else {
        console.log(`⏳ 等待前端服务... (${retries} 次重试)`);
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }
  }

  console.log('✨ 全局设置完成');
}

export default globalSetup;
