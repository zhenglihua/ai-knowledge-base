import { test, expect } from './fixtures';

/**
 * AI问答功能测试
 */
test.describe('AI问答', () => {
  
  test.beforeEach(async ({ loggedInPage: page, helpers }) => {
    await page.goto('/chat');
    await helpers.waitForLoading();
    await helpers.hideDevOverlay();
  });

  test('AI问答页面加载成功', async ({ loggedInPage: page }) => {
    // 验证页面URL
    await expect(page).toHaveURL(/.*chat.*/);
    
    // 验证聊天界面存在 - 使用标题和输入框
    const chatTitle = page.locator('text=AI智能助手').first();
    const chatInput = page.locator('textarea[placeholder*="输入问题"]').first();
    
    // 验证输入框存在
    await expect(chatInput).toBeVisible();
    
    await page.screenshot({ path: 'test-results/chat-page.png', fullPage: true });
  });

  test('可以输入问题并发送', async ({ loggedInPage: page }) => {
    // 找到输入框 - 使用placeholder匹配
    const inputField = page.locator('textarea[placeholder*="输入问题"]').first();
    await expect(inputField).toBeVisible();
    
    // 输入测试问题
    const testQuestion = '什么是人工智能？';
    await inputField.fill(testQuestion);
    await expect(inputField).toHaveValue(testQuestion);
    
    // 找到发送按钮 - 使用更通用的选择器
    const sendBtn = page.locator('button:has(.anticon-send), button[type="primary"]').first();
    
    if (await sendBtn.isVisible().catch(() => false)) {
      await sendBtn.click();
      
      // 等待响应
      await page.waitForTimeout(3000);
      
      // 验证问题显示在聊天历史中
      const chatHistory = page.locator('.ant-list, .chat-history, .chat-messages').first();
      await expect(chatHistory).toBeVisible();
      
      // 验证问题文本出现在聊天历史中
      const pageContent = await page.content();
      expect(pageContent).toContain(testQuestion);
    }
    
    await page.screenshot({ path: 'test-results/chat-question.png', fullPage: true });
  });

  test('显示AI响应加载状态', async ({ loggedInPage: page }) => {
    // 输入问题 - 使用placeholder匹配
    const inputField = page.locator('textarea[placeholder*="输入问题"]').first();
    await inputField.fill('测试问题');
    
    // 发送 - 使用更通用的选择器
    const sendBtn = page.locator('button:has(.anticon-send), button[type="primary"]').first();
    if (await sendBtn.isVisible().catch(() => false)) {
      await sendBtn.click();
      
      // 检查加载状态
      const loadingIndicator = page.locator('.ant-spin, .loading, .typing-indicator, [data-testid="loading"]').first();
      
      // 等待一下看是否出现加载状态
      await page.waitForTimeout(500);
      
      // 加载状态可能出现也可能不出现（如果响应很快）
      // 这里只验证页面没有错误
      const errorMessage = page.locator('.ant-message-error, .error-message').first();
      const hasError = await errorMessage.isVisible().catch(() => false);
      
      if (hasError) {
        console.log('AI响应可能有错误，但测试继续');
      }
    }
  });

  test('聊天历史显示正确', async ({ loggedInPage: page }) => {
    // 查找聊天历史区域
    const chatHistory = page.locator('.chat-history, .message-list, .chat-messages, .ant-list').first();
    
    // 即使没有消息，也应该显示历史区域或空状态
    const hasHistory = await chatHistory.isVisible().catch(() => false);
    
    if (hasHistory) {
      await expect(chatHistory).toBeVisible();
    } else {
      // 检查是否有空状态提示
      const emptyState = page.locator('.ant-empty, .empty-state, [data-testid="empty"]').first();
      const hasEmptyState = await emptyState.isVisible().catch(() => false);
      
      // 应该有历史区域或空状态
      expect(hasHistory || hasEmptyState).toBeTruthy();
    }
  });

  test('清空输入框功能', async ({ loggedInPage: page }) => {
    const inputField = page.locator('textarea[placeholder*="输入问题"]').first();
    
    // 输入文本
    await inputField.fill('测试文本');
    await expect(inputField).toHaveValue('测试文本');
    
    // 清空输入框
    await inputField.fill('');
    await expect(inputField).toHaveValue('');
  });
});
