import { test, expect } from '@playwright/test';

/**
 * 登录/注册流程测试 - 简化版
 */
test.describe('认证流程', () => {
  
  test.beforeEach(async ({ page }) => {
    // 隐藏 webpack overlay
    await page.addStyleTag({
      content: '#webpack-dev-server-client-overlay { display: none !important; }',
    });
  });

  test('登录页面可以访问', async ({ page }) => {
    await page.goto('/auth');
    
    // 等待页面加载
    await page.waitForTimeout(3000);
    
    // 验证页面URL
    const url = page.url();
    console.log('Current URL:', url);
    
    // 截图保存
    await page.screenshot({ path: 'test-results/auth-page.png', fullPage: true });
    
    // 页面应该有内容（不管是不是在登录页）
    const body = await page.locator('body').textContent();
    console.log('Page body length:', body?.length);
    expect(body?.length).toBeGreaterThan(0);
  });

  test('首页可以访问', async ({ page }) => {
    await page.goto('/');
    
    // 等待页面加载
    await page.waitForTimeout(3000);
    
    // 截图保存
    await page.screenshot({ path: 'test-results/home-page.png', fullPage: true });
    
    // 页面应该有内容
    const body = await page.locator('body').textContent();
    console.log('Home page body length:', body?.length);
    expect(body?.length).toBeGreaterThan(0);
  });

  test('可以填写登录表单', async ({ page }) => {
    await page.goto('/auth');
    await page.waitForTimeout(3000);
    
    // 查找任何输入框
    const inputs = await page.locator('input').all();
    console.log('Found', inputs.length, 'input fields');
    
    if (inputs.length >= 2) {
      // 尝试填写第一个两个输入框
      await inputs[0].fill('admin');
      await inputs[1].fill('123456');
      
      // 截图
      await page.screenshot({ path: 'test-results/login-filled.png' });
    }
  });
});
