import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright Configuration
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  // 测试目录
  testDir: './tests/e2e',

  // 每个测试的超时时间
  timeout: 60000,

  // 预期断言的超时时间
  expect: {
    timeout: 10000,
  },

  // 是否并行运行测试
  fullyParallel: true,

  // CI环境中禁止.only测试
  forbidOnly: !!process.env.CI,

  // 失败重试次数
  retries: process.env.CI ? 2 : 1,

  // 工作进程数
  workers: process.env.CI ? 1 : undefined,

  // 报告器配置
  reporter: [
    ['html', { open: 'never', outputFolder: 'playwright-report' }],
    ['list'],
    ['json', { outputFile: 'test-results/test-results.json' }],
  ],

  // 全局设置
  globalSetup: require.resolve('./tests/e2e/global-setup'),
  globalTeardown: require.resolve('./tests/e2e/global-teardown'),

  // 共享配置
  use: {
    // 基础URL
    baseURL: process.env.FRONTEND_URL || 'http://localhost:3000',

    // API基础URL
    apiBaseURL: process.env.BACKEND_URL || 'http://localhost:8001',

    // 操作超时
    actionTimeout: 10000,

    // 导航超时
    navigationTimeout: 30000,

    // 跟踪配置
    trace: 'on-first-retry',

    // 截图配置
    screenshot: 'only-on-failure',

    // 视频配置
    video: 'on-first-retry',

    // 视口大小
    viewport: { width: 1280, height: 720 },

    // 浏览器上下文选项
    contextOptions: {
      reducedMotion: 'reduce',
    },
  },

  // 项目配置（不同浏览器）
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        launchOptions: {
          args: ['--disable-web-security', '--disable-features=IsolateOrigins,site-per-process'],
        },
      },
    },
    // 可以添加更多浏览器配置
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },
  ],

  // 本地开发服务器配置（默认禁用，服务需要手动启动）
  // webServer: [
  //   // 前端服务
  //   {
  //     command: 'cd frontend && npm start',
  //     url: 'http://localhost:3000',
  //     reuseExistingServer: true,
  //     timeout: 120000,
  //     env: {
  //       BROWSER: 'none',
  //       PORT: '3000',
  //     },
  //   },
  //   // 后端服务
  //   {
  //     command: 'cd backend && python3 main.py',
  //     url: 'http://localhost:8000/api/v1/health',
  //     reuseExistingServer: true,
  //     timeout: 120000,
  //   },
  // ],
});
