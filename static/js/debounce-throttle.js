// 防抖和节流统一事件绑定工具
// 依赖于 utils.js 中的 debounce 和 throttle 函数

/**
 * 为输入框应用防抖
 * @param {string} inputId - 输入框的 ID
 * @param {Function} handler - 处理函数
 * @param {number} wait - 防抖延迟时间（毫秒），默认 500ms
 */
function applyDebounceToInput(inputId, handler, wait = 500) {
  const input = document.getElementById(inputId);
  if (!input) {
    console.warn(`[防抖] 未找到 ID 为 "${inputId}" 的输入框`);
    return;
  }

  const debouncedHandler = debounce(handler, wait);
  input.addEventListener('input', (e) => {
    debouncedHandler(e.target.value, e);
  });

  console.log(`[防抖] 已为输入框 "${inputId}" 应用防抖（延迟: ${wait}ms）`);
}

/**
 * 为按钮应用节流
 * @param {string} buttonId - 按钮的 ID
 * @param {Function} handler - 处理函数
 * @param {number} wait - 节流延迟时间（毫秒），默认 300ms
 */
function applyThrottleToButton(buttonId, handler, wait = 300) {
  const button = document.getElementById(buttonId);
  if (!button) {
    console.warn(`[节流] 未找到 ID 为 "${buttonId}" 的按钮`);
    return;
  }

  // 检查按钮类型，如果是 submit 类型，不应用节流
  if (button.type === 'submit') {
    console.warn(`[节流] 按钮 "${buttonId}" 是提交类型，跳过节流以避免阻止表单提交`);
    return;
  }

  const throttledHandler = throttle(handler, wait);
  button.addEventListener('click', (e) => {
    // 如果按钮被禁用，跳过节流
    if (button.disabled) {
      return;
    }
    throttledHandler(e);
  });

  console.log(`[节流] 已为按钮 "${buttonId}" 应用节流（延迟: ${wait}ms）`);
}

/**
 * 自动为搜索输入框应用防抖
 * 会查找所有包含 "search" 或 "filter" 类名或特定 ID 的输入框
 */
function autoApplyDebounceToSearchInputs() {
  // 通过 ID 匹配
  const searchInputIds = [
    'emailSearch',
    'tagSearch',
    'tableSearch',
    'searchInput',
    'emailSearchInput',
  ];

  searchInputIds.forEach((id) => {
    const input = document.getElementById(id);
    if (input && !input.dataset.debounceApplied) {
      const originalHandler = input.oninput || (() => {});
      const debouncedHandler = debounce((e) => {
        if (originalHandler) {
          originalHandler(e);
        }
      }, 500);
      
      input.addEventListener('input', debouncedHandler);
      input.dataset.debounceApplied = 'true';
      console.log(`[自动防抖] 已为搜索输入框 "${id}" 应用防抖`);
    }
  });

  // 通过类名匹配
  const searchInputs = document.querySelectorAll(
    'input[class*="search"], input[class*="filter"], input[placeholder*="搜索"], input[placeholder*="search"]'
  );
  
  searchInputs.forEach((input) => {
    if (!input.dataset.debounceApplied && input.id) {
      const originalHandler = input.oninput || (() => {});
      const debouncedHandler = debounce((e) => {
        if (originalHandler) {
          originalHandler(e);
        }
      }, 500);
      
      input.addEventListener('input', debouncedHandler);
      input.dataset.debounceApplied = 'true';
      console.log(`[自动防抖] 已为搜索输入框 "${input.id || input.className}" 应用防抖`);
    }
  });
}

/**
 * 自动为操作按钮应用节流
 * 会查找所有包含特定类名或 ID 的按钮
 */
function autoApplyThrottleToButtons() {
  // 通过类名匹配操作按钮
  const actionButtons = document.querySelectorAll(
    'button.btn:not([type="submit"]), button[class*="action"]:not([type="submit"])'
  );
  
  actionButtons.forEach((button) => {
    if (!button.dataset.throttleApplied && button.onclick) {
      const originalHandler = button.onclick;
      const throttledHandler = throttle((e) => {
        if (button.disabled) {
          return;
        }
        if (originalHandler) {
          originalHandler(e);
        }
      }, 300);
      
      button.addEventListener('click', throttledHandler);
      button.onclick = null; // 移除内联 onclick，使用 addEventListener
      button.dataset.throttleApplied = 'true';
      console.log(`[自动节流] 已为按钮 "${button.id || button.className}" 应用节流`);
    }
  });
}

// DOM 加载完成后自动应用
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
      autoApplyDebounceToSearchInputs();
      autoApplyThrottleToButtons();
    }, 100);
  });
} else {
  // DOM 已经加载完成
  setTimeout(() => {
    autoApplyDebounceToSearchInputs();
    autoApplyThrottleToButtons();
  }, 100);
}

