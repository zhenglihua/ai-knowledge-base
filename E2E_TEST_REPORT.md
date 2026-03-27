# Playwright E2E 测试报告

## 测试执行时间
- 时间: 2026-03-26 23:09
- 项目: /Users/zheng/.openclaw/workspace/ai-knowledge-base/mvp

## 测试结果汇总

| 指标 | 数值 |
|------|------|
| 总测试数 | 29 |
| 通过 | 0 |
| 失败 | 29 |
| 通过率 | 0% |

## 失败的测试详情

### 1. Auth 认证测试 (auth-simple.spec.ts)
- ❌ 登录页面可以访问
- ❌ 首页可以访问  
- ❌ 可以填写登录表单

### 2. Auth 认证测试 (auth.spec.ts)
- ❌ 登录页面加载成功
- ❌ 注册表单可以正常填写
- ❌ 使用演示账号登录成功
- ❌ 登录失败显示错误提示

### 3. Chat AI问答测试 (chat.spec.ts)
- ❌ AI问答页面加载成功
- ❌ 可以输入问题并发送
- ❌ 显示AI响应加载状态
- ❌ 聊天历史显示正确
- ❌ 清空输入框功能

### 4. Knowledge Graph 知识图谱测试 (knowledge-graph.spec.ts)
- ❌ 知识图谱页面加载成功
- ❌ 实体搜索功能可用
- ❌ 图谱可视化组件渲染
- ❌ 实体详情可以查看
- ❌ 关系列表或图谱控制存在
- ❌ 图谱管理页面可访问

### 5. Search 搜索测试 (search.spec.ts)
- ❌ 搜索页面加载成功
- ❌ 可以输入搜索关键词
- ❌ 执行搜索并显示结果
- ❌ 支持回车键搜索
- ❌ 搜索结果支持高亮显示
- ❌ 搜索过滤器或分类存在

### 6. Upload 上传测试 (upload.spec.ts)
- ❌ 文档管理页面加载成功
- (更多测试...)

## 失败原因

**所有测试失败的共同原因：服务未启动**

错误信息: `net::ERR_CONNECTION_REFUSED at http://localhost:3000/auth`

- 前端服务 (localhost:3000) 未运行
- 后端服务 (localhost:8000) 未运行

## 报告位置

- HTML报告: `/Users/zheng/.openclaw/workspace/ai-knowledge-base/mvp/playwright-report/index.html`
- JSON结果: `/Users/zheng/.openclaw/workspace/ai-knowledge-base/mvp/test-results/test-results.json`
- 截图: `/Users/zheng/.openclaw/workspace/ai-knowledge-base/mvp/test-results/`

## 建议

1. 启动后端服务: `cd backend && python3 main.py`
2. 启动前端服务: `cd frontend && npm start`
3. 确保服务完全启动后再运行测试
4. 或者启用 playwright.config.ts 中的 webServer 配置自动启动服务

---
报告生成时间: 2026-03-26 23:10
