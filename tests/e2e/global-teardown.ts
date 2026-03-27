import { FullConfig } from '@playwright/test';

/**
 * 全局清理 - 测试结束后执行
 * 用于清理测试数据、关闭资源等
 */
async function globalTeardown(config: FullConfig) {
  console.log('🧹 开始全局清理...');

  // 这里可以添加清理逻辑
  // 例如：删除测试用户、清理上传的测试文件等

  console.log('✨ 全局清理完成');
}

export default globalTeardown;
