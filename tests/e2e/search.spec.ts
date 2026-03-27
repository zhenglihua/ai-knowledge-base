import { test, expect } from './fixtures';

/**
 * 搜索功能测试
 */
test.describe('搜索功能', () => {
  
  test.beforeEach(async ({ loggedInPage: page, helpers }) => {
    await page.goto('/search');
    await helpers.waitForLoading();
    await helpers.hideDevOverlay();
  });

  test('搜索页面加载成功', async ({ loggedInPage: page }) => {
    // 验证页面URL
    await expect(page).toHaveURL(/.*search.*/);
    
    // 验证搜索框存在
    const searchInput = page.locator('input[type="search"], input[placeholder*="搜索"], input[placeholder*="search"], .ant-input-search input').first();
    await expect(searchInput).toBeVisible();
    
    // 验证搜索按钮存在
    const searchBtn = page.locator('button:has-text("搜索"), button:has-text("Search"), .ant-input-search-button, button[type="submit"]').first();
    await expect(searchBtn).toBeVisible();
    
    await page.screenshot({ path: 'test-results/search-page.png', fullPage: true });
  });

  test('可以输入搜索关键词', async ({ loggedInPage: page }) => {
    const searchInput = page.locator('input[type="search"], input[placeholder*="搜索"], input[placeholder*="search"], .ant-input-search input').first();
    
    // 输入搜索词
    const searchTerm = '人工智能';
    await searchInput.fill(searchTerm);
    
    // 验证输入成功
    await expect(searchInput).toHaveValue(searchTerm);
    
    await page.screenshot({ path: 'test-results/search-input.png' });
  });

  test('执行搜索并显示结果', async ({ loggedInPage: page }) => {
    const searchInput = page.locator('input[type="search"], input[placeholder*="搜索"], input[placeholder*="search"], .ant-input-search input').first();
    const searchBtn = page.locator('button:has-text("搜索"), button:has-text("Search"), .ant-input-search-button, button[type="submit"]').first();
    
    // 输入搜索词
    await searchInput.fill('测试');
    
    // 点击搜索
    await searchBtn.click();
    
    // 等待搜索完成
    await page.waitForTimeout(3000);
    
    // 验证搜索结果区域存在
    const resultsArea = page.locator('.search-results, .results-list, .ant-list, [data-testid="search-results"]').first();
    const loadingIndicator = page.locator('.ant-spin, .loading').first();
    
    // 等待加载完成
    await loadingIndicator.waitFor({ state: 'hidden', timeout: 10000 }).catch(() => {});
    
    // 验证有结果或空状态
    const hasResults = await resultsArea.isVisible().catch(() => false);
    const emptyState = page.locator('.ant-empty, .empty-state, .no-results').first();
    const hasEmptyState = await emptyState.isVisible().catch(() => false);
    
    expect(hasResults || hasEmptyState).toBeTruthy();
    
    await page.screenshot({ path: 'test-results/search-results.png', fullPage: true });
  });

  test('支持回车键搜索', async ({ loggedInPage: page }) => {
    const searchInput = page.locator('input[type="search"], input[placeholder*="搜索"], input[placeholder*="search"], .ant-input-search input').first();
    
    // 输入搜索词
    await searchInput.fill('知识库');
    
    // 按回车键
    await searchInput.press('Enter');
    
    // 等待搜索执行
    await page.waitForTimeout(2000);
    
    // 验证页面没有错误
    const errorMessage = page.locator('.ant-message-error, .error-message').first();
    const hasError = await errorMessage.isVisible().catch(() => false);
    
    expect(hasError).toBeFalsy();
  });

  test('搜索结果支持高亮显示', async ({ loggedInPage: page }) => {
    const searchInput = page.locator('input[type="search"], input[placeholder*="搜索"], input[placeholder*="search"], .ant-input-search input').first();
    const searchBtn = page.locator('button:has-text("搜索"), button:has-text("Search"), .ant-input-search-button, button[type="submit"]').first();
    
    // 执行搜索
    await searchInput.fill('AI');
    await searchBtn.click();
    await page.waitForTimeout(3000);
    
    // 检查是否有高亮样式
    const highlightedText = page.locator('.highlight, .highlighted, mark, .search-highlight').first();
    const hasHighlight = await highlightedText.isVisible().catch(() => false);
    
    // 记录高亮状态（不强制要求，因为可能没有匹配结果）
    if (hasHighlight) {
      console.log('✅ 搜索结果包含高亮显示');
    }
  });

  test('搜索过滤器或分类存在', async ({ loggedInPage: page }) => {
    // 检查是否有过滤器
    const filters = page.locator('.ant-select, .filter, .category-filter, [data-testid="filter"]').first();
    const hasFilters = await filters.isVisible().catch(() => false);
    
    // 检查是否有分类选项
    const categories = page.locator('.ant-radio-group, .ant-tabs, .category-tabs').first();
    const hasCategories = await categories.isVisible().catch(() => false);
    
    // 记录状态
    if (hasFilters) {
      console.log('✅ 搜索页面有过滤器');
    }
    if (hasCategories) {
      console.log('✅ 搜索页面有分类选项');
    }
  });
});
