const { chromium } = require('playwright');

async function screenshotFeatures() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 }
  });
  const page = await context.newPage();

  const baseUrl = 'http://localhost:3000';
  const screenshotsDir = '/Users/zheng/.openclaw/workspace/screenshots/knowledge-base/';

  // 确保截图目录存在
  const fs = require('fs');
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir, { recursive: true });
  }

  try {
    // 1. 截图登录页
    console.log('📸 截图1: 登录页面');
    await page.goto(`${baseUrl}/auth`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);
    // 隐藏webpack覆盖层
    await page.evaluate(() => {
      const iframe = document.getElementById('webpack-dev-server-client-overlay');
      if (iframe) iframe.remove();
    });
    await page.screenshot({ path: `${screenshotsDir}01_login.png` });
    console.log('✅ 登录页已保存');

    // 2. 执行登录 - 使用正确的ID选择器
    console.log('🔐 执行登录...');
    await page.fill('#login_username', 'admin');
    await page.fill('#login_password', '123456');
    // 隐藏覆盖层后点击
    await page.evaluate(() => {
      const iframe = document.getElementById('webpack-dev-server-client-overlay');
      if (iframe) iframe.remove();
    });
    await page.click('button[type="submit"]');
    await page.waitForTimeout(3000);
    console.log('✅ 登录成功');

    // 3. 首页
    console.log('📸 截图2: 首页');
    await page.goto(`${baseUrl}/`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);
    await page.evaluate(() => {
      const iframe = document.getElementById('webpack-dev-server-client-overlay');
      if (iframe) iframe.remove();
    });
    await page.screenshot({ path: `${screenshotsDir}02_home.png` });
    console.log('✅ 首页已保存');

    // 4. 文档管理
    console.log('📸 截图3: 文档管理');
    await page.goto(`${baseUrl}/documents`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);
    await page.evaluate(() => {
      const iframe = document.getElementById('webpack-dev-server-client-overlay');
      if (iframe) iframe.remove();
    });
    await page.screenshot({ path: `${screenshotsDir}03_documents.png` });
    console.log('✅ 文档管理已保存');

    // 5. 智能搜索
    console.log('📸 截图4: 智能搜索');
    await page.goto(`${baseUrl}/search`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);
    await page.evaluate(() => {
      const iframe = document.getElementById('webpack-dev-server-client-overlay');
      if (iframe) iframe.remove();
    });
    await page.screenshot({ path: `${screenshotsDir}04_search.png` });
    console.log('✅ 智能搜索已保存');

    // 6. AI问答
    console.log('📸 截图5: AI问答');
    await page.goto(`${baseUrl}/chat`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);
    await page.evaluate(() => {
      const iframe = document.getElementById('webpack-dev-server-client-overlay');
      if (iframe) iframe.remove();
    });
    await page.screenshot({ path: `${screenshotsDir}05_chat.png` });
    console.log('✅ AI问答已保存');

    // 7. 知识图谱
    console.log('📸 截图6: 知识图谱');
    await page.goto(`${baseUrl}/knowledge-graph`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);
    await page.evaluate(() => {
      const iframe = document.getElementById('webpack-dev-server-client-overlay');
      if (iframe) iframe.remove();
    });
    await page.screenshot({ path: `${screenshotsDir}06_knowledge_graph.png` });
    console.log('✅ 知识图谱已保存');

    // 8. 实体搜索
    console.log('📸 截图7: 实体搜索');
    await page.goto(`${baseUrl}/entity-search`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);
    await page.evaluate(() => {
      const iframe = document.getElementById('webpack-dev-server-client-overlay');
      if (iframe) iframe.remove();
    });
    await page.screenshot({ path: `${screenshotsDir}07_entity_search.png` });
    console.log('✅ 实体搜索已保存');

    // 9. 图谱管理
    console.log('📸 截图8: 图谱管理');
    await page.goto(`${baseUrl}/graph-management`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);
    await page.evaluate(() => {
      const iframe = document.getElementById('webpack-dev-server-client-overlay');
      if (iframe) iframe.remove();
    });
    await page.screenshot({ path: `${screenshotsDir}08_graph_management.png` });
    console.log('✅ 图谱管理已保存');

    // 10. 用户管理
    console.log('📸 截图9: 用户管理');
    await page.goto(`${baseUrl}/users`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);
    await page.evaluate(() => {
      const iframe = document.getElementById('webpack-dev-server-client-overlay');
      if (iframe) iframe.remove();
    });
    await page.screenshot({ path: `${screenshotsDir}09_user_management.png` });
    console.log('✅ 用户管理已保存');

    console.log('\n🎉 全部截图完成!');
    console.log(`📁 保存位置: ${screenshotsDir}`);

  } catch (err) {
    console.error('❌ 截图过程出错:', err.message);
  } finally {
    await browser.close();
  }
}

screenshotFeatures().catch(console.error);
