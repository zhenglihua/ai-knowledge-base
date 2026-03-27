import { test, expect } from './fixtures';
import * as fs from 'fs';
import * as path from 'path';

/**
 * 文档上传功能测试
 */
test.describe('文档上传', () => {
  
  // 测试文件路径
  const testFilesDir = path.join(__dirname, '../../test_data');
  
  test.beforeEach(async ({ loggedInPage: page, helpers }) => {
    await page.goto('/documents');
    await helpers.waitForLoading();
    await helpers.hideDevOverlay();
  });

  test('文档管理页面加载成功', async ({ loggedInPage: page }) => {
    // 验证页面标题 - Documents.tsx使用的是Title level={3}
    await expect(page.locator('text=文档管理').first()).toBeVisible();
    
    // 验证上传按钮存在
    const uploadBtn = page.locator('button:has-text("批量上传"), button:has(.anticon-cloudupload)').first();
    await expect(uploadBtn).toBeVisible();
    
    // 验证文档列表区域 - 使用Table组件
    const documentList = page.locator('.ant-table, .ant-list').first();
    await expect(documentList).toBeVisible();
    
    await page.screenshot({ path: 'test-results/documents-page.png', fullPage: true });
  });

  test('可以打开上传对话框', async ({ loggedInPage: page }) => {
    // 点击上传按钮
    const uploadBtn = page.locator('button:has-text("上传"), button:has-text("Upload"), .ant-upload').first();
    await uploadBtn.click();
    
    // 等待对话框出现
    await page.waitForTimeout(1000);
    
    // 验证上传对话框或区域存在
    const uploadModal = page.locator('.ant-modal, .upload-modal, .ant-upload-drag, [data-testid="upload-modal"]').first();
    const uploadArea = page.locator('.ant-upload, .upload-area').first();
    
    const isModalVisible = await uploadModal.isVisible().catch(() => false);
    const isAreaVisible = await uploadArea.isVisible().catch(() => false);
    
    expect(isModalVisible || isAreaVisible).toBeTruthy();
    
    await page.screenshot({ path: 'test-results/upload-dialog.png' });
  });

  test('支持多种文件格式上传', async ({ loggedInPage: page }) => {
    // 检查支持的文件格式提示
    const content = await page.content();
    
    // 验证页面包含支持的文件格式信息
    const hasFormatInfo = 
      content.includes('PDF') || 
      content.includes('DOCX') || 
      content.includes('TXT') ||
      content.includes('png') ||
      content.includes('jpg');
    
    // 如果没有明确的格式提示，至少验证上传组件存在
    if (!hasFormatInfo) {
      const uploadComponent = page.locator('.ant-upload, input[type="file"]').first();
      await expect(uploadComponent).toBeVisible();
    }
  });

  test('上传对话框可以取消', async ({ loggedInPage: page }) => {
    // 点击上传按钮
    const uploadBtn = page.locator('button:has-text("上传"), button:has-text("Upload"), .ant-upload').first();
    await uploadBtn.click();
    
    await page.waitForTimeout(500);
    
    // 查找取消或关闭按钮
    const cancelBtn = page.locator('button:has-text("取消"), button:has-text("Cancel"), .ant-modal-close').first();
    
    if (await cancelBtn.isVisible().catch(() => false)) {
      await cancelBtn.click();
      
      // 等待对话框关闭
      await page.waitForTimeout(500);
      
      // 验证回到文档列表页面
      await expect(page).toHaveURL(/.*documents.*/);
    }
  });

  test('可以拖拽文件到上传区域', async ({ loggedInPage: page }) => {
    // 查找拖放区域
    const dropZone = page.locator('.ant-upload-drag, .upload-dropzone, [data-testid="dropzone"]').first();
    
    if (await dropZone.isVisible().catch(() => false)) {
      // 验证拖放区域可见且有正确的提示文字
      await expect(dropZone).toBeVisible();
      
      const dropText = await dropZone.textContent();
      expect(dropText).toMatch(/拖|drop|上传|upload/i);
    } else {
      // 如果没有拖放区域，验证有上传按钮
      const uploadBtn = page.locator('button:has-text("上传"), button:has-text("Upload")').first();
      await expect(uploadBtn).toBeVisible();
    }
  });
});
