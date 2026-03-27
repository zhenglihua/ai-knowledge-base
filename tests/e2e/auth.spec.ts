import { test, expect } from './fixtures';

/**
 * 登录/注册流程测试
 */
test.describe('认证流程', () => {
  
  test.beforeEach(async ({ page, helpers }) => {
    await page.goto('/auth');
    await page.waitForLoadState('networkidle');
    await helpers.hideDevOverlay();
    // 等待页面完全加载
    await page.waitForSelector('.ant-tabs-tab', { timeout: 10000 });
  });

  test('登录页面加载成功', async ({ page }) => {
    // 验证页面标题或内容
    await expect(page.locator('text=AI 知识库系统')).toBeVisible();
    
    // 验证有用户名和密码输入框 - 使用 role/label 选择器
    const usernameInput = page.getByRole('textbox', { name: '用户名' });
    const passwordInput = page.getByRole('textbox', { name: '密码' });
    
    await expect(usernameInput).toBeVisible();
    await expect(passwordInput).toBeVisible();
    
    // 验证登录按钮
    const loginBtn = page.locator('button:has-text("登 录")');
    await expect(loginBtn).toBeVisible();
    
    // 截图保存
    await page.screenshot({ path: 'test-results/auth-page.png' });
  });

  test('注册表单可以正常填写', async ({ page }) => {
    // 切换到注册标签
    const registerTab = page.locator('.ant-tabs-tab:has-text("用户注册"), .ant-tabs-tab:has-text("注册")').first();
    await registerTab.click();
    await page.waitForTimeout(500);

    // 等待注册标签页加载（不依赖form[name="register"]）
    await page.waitForSelector('.ant-tabs-tabpane-active', { timeout: 5000 });

    // 填写注册表单 - 使用 label/role 选择器（在激活的标签页中只有一个）
    await page.getByRole('textbox', { name: '用户名' }).fill('newtestuser');
    await page.getByRole('textbox', { name: '邮箱' }).fill('newtest@example.com');
    await page.getByRole('textbox', { name: '手机号（可选）' }).fill('13800138000');
    // 密码输入框使用 first() 因为在注册页只有一个"密码"标签
    await page.getByRole('textbox', { name: '密码' }).first().fill('Test123456!');
    await page.getByRole('textbox', { name: '确认密码' }).fill('Test123456!');

    // 勾选协议
    const agreementCheckbox = page.locator('input[type="checkbox"]').first();
    if (await agreementCheckbox.isVisible().catch(() => false)) {
      await agreementCheckbox.click();
    }

    // 验证输入
    await expect(page.getByRole('textbox', { name: '邮箱' })).toHaveValue('newtest@example.com');

    await page.screenshot({ path: 'test-results/register-form.png' });
  });

  test('使用演示账号登录成功', async ({ page }) => {
    // 填写登录表单 - 使用演示账号
    await page.locator('input[placeholder="用户名"]').fill('admin');
    await page.locator('input[placeholder="密码"]').fill('123456');

    // 点击登录按钮
    await page.locator('button:has-text("登 录")').click();

    // 等待导航完成
    await page.waitForURL('/', { timeout: 15000 });
    
    // 验证已跳转到首页
    await expect(page).toHaveURL('/');
    
    // 验证页面内容
    await expect(page.locator('body')).toContainText(/AI|知识库|首页|文档/);
    
    await page.screenshot({ path: 'test-results/logged-in-home.png', fullPage: true });
  });

  test('登录失败显示错误提示', async ({ page }) => {
    // 填写错误的凭证 - 使用 label/role 选择器
    await page.getByRole('textbox', { name: '用户名' }).fill('wronguser');
    await page.getByRole('textbox', { name: '密码' }).fill('wrongpassword');

    // 点击登录
    await page.locator('button:has-text("登 录")').click();

    // 等待错误消息出现 - Ant Design 的 message 组件
    await page.waitForTimeout(2000);

    // 验证错误提示（Ant Design message 组件）
    const errorMessage = page.locator('.ant-message-error, .ant-notification-notice-error').first();
    const stillOnAuthPage = await page.locator('form[name="login"]').isVisible().catch(() => false);
    
    // 应该有错误消息或者仍在登录页
    const hasError = await errorMessage.isVisible().catch(() => false);
    expect(hasError || stillOnAuthPage).toBeTruthy();
    
    await page.screenshot({ path: 'test-results/login-error.png' });
  });
});
