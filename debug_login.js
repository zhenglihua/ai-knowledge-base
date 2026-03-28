const { chromium } = require('playwright');

async function debug() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  // 监听控制台消息
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('Console Error:', msg.text());
    }
  });

  // 监听页面错误
  page.on('pageerror', error => {
    console.log('Page Error:', error.message);
  });

  await page.goto('http://localhost:3000/auth', { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(5000); // 等待更长时间让React渲染

  // 获取页面HTML
  const html = await page.content();
  console.log('HTML length:', html.length);
  console.log('Root div content:', html.includes('ant-tabs'), 'has ant-tabs');

  // 获取body内容
  const bodyContent = await page.$eval('body', el => el.innerHTML.substring(0, 500));
  console.log('Body content:', bodyContent);

  // 获取所有input元素
  const inputs = await page.$$eval('input', els => els.map(el => ({
    type: el.type,
    name: el.name,
    id: el.id,
    className: el.className,
    placeholder: el.placeholder
  })));

  console.log('Input elements:', JSON.stringify(inputs, null, 2));

  // 截图
  await page.screenshot({ path: '/Users/zheng/.openclaw/workspace/screenshots/knowledge-base/debug_login.png', fullPage: true });

  await browser.close();
}

debug().catch(console.error);
