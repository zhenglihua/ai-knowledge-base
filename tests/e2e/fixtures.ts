import { test as base, expect, Page } from '@playwright/test';

/**
 * 扩展的测试 fixture
 * 提供常用的测试工具和辅助方法
 */
export type TestFixtures = {
  /** 已登录的页面 */
  loggedInPage: Page;
  /** 测试用户凭证 */
  testUser: {
    username: string;
    password: string;
    email: string;
  };
  /** 辅助方法 */
  helpers: {
    login: (username: string, password: string) => Promise<void>;
    logout: () => Promise<void>;
    waitForLoading: () => Promise<void>;
    hideDevOverlay: () => Promise<void>;
  };
};

/**
 * 扩展的测试对象
 */
export const test = base.extend<TestFixtures>({
  // 测试用户配置 - 使用演示账号
  testUser: {
    username: 'admin',
    password: '123456',
    email: 'admin@example.com',
  },

  // 辅助方法
  helpers: async ({ page }, use) => {
    const helpers = {
      /**
       * 登录操作
       */
      login: async (username: string, password: string) => {
        await page.goto('/auth');
        await page.waitForLoadState('networkidle');
        await page.waitForSelector('input[placeholder="用户名"]', { timeout: 10000 });
        
        // 填写登录表单 - 使用 placeholder 选择器
        await page.locator('input[placeholder="用户名"]').fill(username);
        await page.locator('input[placeholder="密码"]').fill(password);
        
        // 点击登录按钮
        await page.locator('button:has-text("登 录")').click();
        
        // 等待登录完成
        await page.waitForURL('/', { timeout: 15000 });
        await page.waitForLoadState('networkidle');
      },

      /**
       * 登出操作
       */
      logout: async () => {
        // 尝试找到用户菜单并登出
        const userMenu = page.locator('.user-menu, [data-testid="user-menu"], .ant-dropdown-trigger').first();
        if (await userMenu.isVisible().catch(() => false)) {
          await userMenu.click();
          const logoutBtn = page.locator('text=退出登录, text=Logout, text=退出').first();
          if (await logoutBtn.isVisible().catch(() => false)) {
            await logoutBtn.click();
            await page.waitForURL('/auth');
          }
        }
      },

      /**
       * 等待加载完成
       */
      waitForLoading: async () => {
        // 等待加载指示器消失
        const loading = page.locator('.ant-spin, .loading, [data-testid="loading"]').first();
        await loading.waitFor({ state: 'hidden', timeout: 10000 }).catch(() => {});
        await page.waitForLoadState('networkidle');
      },

      /**
       * 隐藏开发覆盖层
       */
      hideDevOverlay: async () => {
        await page.addStyleTag({
          content: '#webpack-dev-server-client-overlay { display: none !important; }',
        });
      },
    };

    await use(helpers);
  },

  // 已登录的页面 - 使用演示账号登录
  loggedInPage: async ({ page, helpers, testUser }, use) => {
    await helpers.login(testUser.username, testUser.password);
    await use(page);
  },
});

export { expect };
