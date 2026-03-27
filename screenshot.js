const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  
  // 截图API文档
  await page.goto('http://localhost:8000/docs');
  await page.waitForTimeout(2000);
  await page.screenshot({ path: 'screenshot_api.png', fullPage: true });
  
  console.log('API文档截图已保存: screenshot_api.png');
  await browser.close();
})();
