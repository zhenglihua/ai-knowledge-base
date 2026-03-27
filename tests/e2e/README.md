# AI知识库 E2E 测试

基于 Playwright 的端到端自动化测试框架。

## 📦 安装

### 1. 安装依赖

```bash
# 在项目根目录执行
cd /Users/zheng/.openclaw/workspace/ai-knowledge-base/mvp

# 安装 Node.js 依赖
npm install

# 安装 Playwright 浏览器
npx playwright install chromium
```

### 2. 验证安装

```bash
npx playwright --version
```

## 🚀 运行测试

### 运行所有测试

```bash
npm test
# 或
npx playwright test
```

### 运行特定测试文件

```bash
# 仅运行认证测试
npx playwright test tests/e2e/auth.spec.ts

# 仅运行文档上传测试
npx playwright test tests/e2e/upload.spec.ts

# 仅运行AI问答测试
npx playwright test tests/e2e/chat.spec.ts

# 仅运行搜索测试
npx playwright test tests/e2e/search.spec.ts

# 仅运行知识图谱测试
npx playwright test tests/e2e/knowledge-graph.spec.ts
```

### 运行测试并生成报告

```bash
npm run test:report
```

### 以 UI 模式运行（调试）

```bash
npm run test:ui
```

### 带 headed 模式运行（可以看到浏览器）

```bash
npx playwright test --headed
```

## 📊 查看测试报告

### HTML 报告

```bash
npm run report
# 或
npx playwright show-report
```

报告将自动在浏览器中打开。

### JSON 报告

测试结果也会保存为 JSON 格式：
- `test-results/test-results.json`

### 截图和录制

失败的测试会自动截图：
- `test-results/*.png`

首次重试时会录制视频：
- `test-results/*.webm`

## 📁 目录结构

```
/Users/zheng/.openclaw/workspace/ai-knowledge-base/mvp/
├── playwright.config.ts          # Playwright 配置文件
├── tests/
│   └── e2e/
│       ├── fixtures.ts           # 测试 fixture 和辅助方法
│       ├── global-setup.ts       # 全局设置（测试前执行）
│       ├── global-teardown.ts    # 全局清理（测试后执行）
│       ├── auth.spec.ts          # 登录/注册测试
│       ├── upload.spec.ts        # 文档上传测试
│       ├── chat.spec.ts          # AI问答测试
│       ├── search.spec.ts        # 搜索功能测试
│       └── knowledge-graph.spec.ts  # 知识图谱测试
├── test-results/                 # 测试结果、截图、视频
└── playwright-report/            # HTML 测试报告
```

## 🔧 配置

### 环境变量

可以通过环境变量自定义测试行为：

```bash
# 前端 URL
FRONTEND_URL=http://localhost:3000

# 后端 URL
BACKEND_URL=http://localhost:8000

# 运行测试
FRONTEND_URL=http://localhost:3000 BACKEND_URL=http://localhost:8000 npm test
```

### 修改测试用户

编辑 `tests/e2e/fixtures.ts` 中的 `testUser`：

```typescript
testUser: {
  username: 'your_username',
  password: 'your_password',
  email: 'your_email@example.com',
}
```

## 🐛 调试

### 使用 UI 模式

```bash
npx playwright test --ui
```

### 使用断点

在测试代码中添加 `await page.pause()`：

```typescript
test('示例测试', async ({ page }) => {
  await page.goto('/');
  await page.pause(); // 断点
  // ...
});
```

### 慢速模式

```bash
npx playwright test --debug
```

## 📝 测试用例说明

### 认证测试 (auth.spec.ts)
- ✅ 登录页面加载成功
- ✅ 注册表单可以正常填写
- ✅ 登录成功后跳转到首页
- ✅ 登录失败显示错误提示

### 文档上传测试 (upload.spec.ts)
- ✅ 文档管理页面加载成功
- ✅ 可以打开上传对话框
- ✅ 支持多种文件格式上传
- ✅ 上传对话框可以取消
- ✅ 可以拖拽文件到上传区域

### AI问答测试 (chat.spec.ts)
- ✅ AI问答页面加载成功
- ✅ 可以输入问题并发送
- ✅ 显示AI响应加载状态
- ✅ 聊天历史显示正确
- ✅ 清空输入框功能

### 搜索功能测试 (search.spec.ts)
- ✅ 搜索页面加载成功
- ✅ 可以输入搜索关键词
- ✅ 执行搜索并显示结果
- ✅ 支持回车键搜索
- ✅ 搜索结果支持高亮显示
- ✅ 搜索过滤器或分类存在

### 知识图谱测试 (knowledge-graph.spec.ts)
- ✅ 知识图谱页面加载成功
- ✅ 实体搜索功能可用
- ✅ 图谱可视化组件渲染
- ✅ 实体详情可以查看
- ✅ 关系列表或图谱控制存在
- ✅ 图谱管理页面可访问

## ⚠️ 已知问题

1. **服务启动延迟**：如果前后端服务启动较慢，第一次测试可能会超时。可以手动启动服务后再运行测试。

2. **WebSocket Overlay**：开发服务器的 WebSocket 错误覆盖层已自动隐藏，但可能会影响截图。

3. **登录凭证**：测试使用默认凭证，如果系统中没有该用户，认证测试可能会失败。

4. **浏览器权限**：macOS 可能需要授予屏幕录制权限给 Playwright。

## 🔗 相关链接

- [Playwright 文档](https://playwright.dev/)
- [Playwright API 参考](https://playwright.dev/docs/api/class-playwright)

## 🆘 故障排除

### 浏览器安装问题

```bash
# 重新安装浏览器
npx playwright install --force chromium
```

### 权限问题 (macOS)

如果遇到权限错误，尝试：

```bash
# 授予权限
xattr -cr ~/Library/Caches/ms-playwright

# 重新安装
npx playwright install chromium
```

### 测试超时

如果测试超时，可以增加超时时间：

```bash
# 修改 playwright.config.ts 中的 timeout 值
timeout: 120000, // 增加到 120 秒
```

## 👥 贡献

添加新的测试文件时，请遵循命名约定：`*.spec.ts`

测试文件应该放在 `tests/e2e/` 目录下。
