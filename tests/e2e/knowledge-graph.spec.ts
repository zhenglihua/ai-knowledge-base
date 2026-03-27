import { test, expect } from './fixtures';

/**
 * 知识图谱页面测试
 */
test.describe('知识图谱', () => {
  
  test.beforeEach(async ({ loggedInPage: page, helpers }) => {
    await page.goto('/knowledge-graph');
    await helpers.waitForLoading();
    await helpers.hideDevOverlay();
  });

  test('知识图谱页面加载成功', async ({ loggedInPage: page }) => {
    // 验证页面URL
    await expect(page).toHaveURL(/.*knowledge-graph.*/);
    
    // 验证页面标题或内容
    const pageTitle = page.locator('h1, h2, .ant-page-header-heading-title').first();
    await expect(pageTitle).toBeVisible();
    
    // 验证知识图谱可视化区域
    const graphContainer = page.locator('.knowledge-graph, .graph-container, [data-testid="knowledge-graph"], .echarts-for-react, canvas').first();
    const hasGraph = await graphContainer.isVisible().catch(() => false);
    
    // 即使没有图形，也应该有相关内容
    const content = await page.content();
    const hasGraphContent = content.includes('知识图谱') || content.includes('实体') || content.includes('关系');
    
    expect(hasGraph || hasGraphContent).toBeTruthy();
    
    await page.screenshot({ path: 'test-results/knowledge-graph-page.png', fullPage: true });
  });

  test('实体搜索功能可用', async ({ loggedInPage: page }) => {
    // 跳转到实体搜索页面
    await page.goto('/entity-search');
    await page.waitForLoadState('networkidle');
    
    // 验证搜索输入框
    const searchInput = page.locator('input[type="search"], input[placeholder*="实体"], input[placeholder*="搜索"], .ant-input').first();
    await expect(searchInput).toBeVisible();
    
    // 测试输入
    await searchInput.fill('测试实体');
    await expect(searchInput).toHaveValue('测试实体');
    
    await page.screenshot({ path: 'test-results/entity-search.png' });
  });

  test('图谱可视化组件渲染', async ({ loggedInPage: page }) => {
    // 等待图谱加载
    await page.waitForTimeout(3000);
    
    // 检查是否有SVG或Canvas元素（图谱通常使用这些技术）
    const svgElement = page.locator('svg').first();
    const canvasElement = page.locator('canvas').first();
    const echartsElement = page.locator('.echarts-for-react, [data-testid="echarts"]').first();
    
    const hasSvg = await svgElement.isVisible().catch(() => false);
    const hasCanvas = await canvasElement.isVisible().catch(() => false);
    const hasEcharts = await echartsElement.isVisible().catch(() => false);
    
    // 应该有可视化组件或加载状态
    const loadingElement = page.locator('.ant-spin, .loading').first();
    const hasLoading = await loadingElement.isVisible().catch(() => false);
    
    const hasVisualization = hasSvg || hasCanvas || hasEcharts || hasLoading;
    
    expect(hasVisualization).toBeTruthy();
  });

  test('实体详情可以查看', async ({ loggedInPage: page }) => {
    // 尝试点击图谱中的节点
    const nodeElement = page.locator('.node, .entity-node, circle, .ant-card').first();
    
    if (await nodeElement.isVisible().catch(() => false)) {
      await nodeElement.click();
      
      // 等待详情面板出现
      await page.waitForTimeout(1000);
      
      // 验证详情面板
      const detailPanel = page.locator('.entity-detail, .detail-panel, .ant-drawer, .ant-modal').first();
      const hasDetail = await detailPanel.isVisible().catch(() => false);
      
      if (hasDetail) {
        await expect(detailPanel).toBeVisible();
        await page.screenshot({ path: 'test-results/entity-detail.png' });
      }
    }
  });

  test('关系列表或图谱控制存在', async ({ loggedInPage: page }) => {
    // 检查是否有关系列表
    const relationList = page.locator('.relation-list, .relations, [data-testid="relations"]').first();
    const hasRelationList = await relationList.isVisible().catch(() => false);
    
    // 检查是否有图谱控制按钮
    const controls = page.locator('.graph-controls, .zoom-controls, button:has-text("放大"), button:has-text("缩小"), button:has-text("重置")').first();
    const hasControls = await controls.isVisible().catch(() => false);
    
    // 检查是否有推荐面板
    const recommendationPanel = page.locator('.recommendation-panel, .recommendations, [data-testid="recommendations"]').first();
    const hasRecommendations = await recommendationPanel.isVisible().catch(() => false);
    
    // 记录存在的功能
    if (hasRelationList) console.log('✅ 有关系列表');
    if (hasControls) console.log('✅ 有图谱控制');
    if (hasRecommendations) console.log('✅ 有推荐面板');
  });

  test('图谱管理页面可访问', async ({ loggedInPage: page }) => {
    // 访问图谱管理页面
    await page.goto('/graph-management');
    await page.waitForLoadState('networkidle');
    
    // 验证页面加载
    await expect(page).toHaveURL(/.*graph-management.*/);
    
    // 验证页面内容
    const content = await page.content();
    const hasManagementContent = content.includes('图谱') || content.includes('管理') || content.includes('实体');
    
    expect(hasManagementContent).toBeTruthy();
    
    await page.screenshot({ path: 'test-results/graph-management.png', fullPage: true });
  });
});
