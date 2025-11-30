/**
 * 剪贴板工具函数
 * 提供复制到剪贴板的功能，包含错误处理和降级方案
 */

/**
 * 复制文本到剪贴板
 * @param text 要复制的文本
 * @returns Promise<boolean> 是否复制成功
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  if (!text) {
    return false;
  }

  // 优先使用现代 Clipboard API
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (err) {
      console.warn('Clipboard API failed, falling back to legacy method:', err);
      // 降级到传统方法
      return fallbackCopyToClipboard(text);
    }
  } else {
    // 使用降级方案
    return fallbackCopyToClipboard(text);
  }
}

/**
 * 降级方案：使用传统方法复制到剪贴板
 * @param text 要复制的文本
 * @returns boolean 是否复制成功
 */
function fallbackCopyToClipboard(text: string): boolean {
  try {
    // 创建临时 textarea 元素
    const textArea = document.createElement('textarea');
    textArea.value = text;
    
    // 设置样式使其不可见但可选中
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    textArea.style.opacity = '0';
    textArea.style.pointerEvents = 'none';
    
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    // 对于移动设备，使用 setSelectionRange
    if (navigator.userAgent.match(/ipad|iphone/i)) {
      const range = document.createRange();
      range.selectNodeContents(textArea);
      const selection = window.getSelection();
      if (selection) {
        selection.removeAllRanges();
        selection.addRange(range);
      }
      textArea.setSelectionRange(0, 999999);
    }
    
    // 执行复制
    const successful = document.execCommand('copy');
    
    // 清理
    document.body.removeChild(textArea);
    
    return successful;
  } catch (err) {
    console.error('Fallback copy method failed:', err);
    return false;
  }
}
