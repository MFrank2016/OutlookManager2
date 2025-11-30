import { useState, useEffect } from "react";

/**
 * 响应式操作按钮 Hook
 * 动态检测可用空间，决定是否显示所有操作按钮
 */
export function useResponsiveActions(threshold: number = 1200) {
  const [showAllActions, setShowAllActions] = useState(false);

  useEffect(() => {
    const checkWidth = () => {
      setShowAllActions(window.innerWidth >= threshold);
    };

    // 初始检查
    checkWidth();

    // 监听窗口大小变化
    window.addEventListener("resize", checkWidth);

    // 使用 ResizeObserver 监听表格容器（如果存在）
    const tableContainer = document.querySelector('[data-table-container]');
    if (tableContainer) {
      const resizeObserver = new ResizeObserver((entries) => {
        for (const entry of entries) {
          const width = entry.contentRect.width;
          setShowAllActions(width >= threshold);
        }
      });
      resizeObserver.observe(tableContainer);
      return () => {
        resizeObserver.disconnect();
        window.removeEventListener("resize", checkWidth);
      };
    }

    return () => {
      window.removeEventListener("resize", checkWidth);
    };
  }, [threshold]);

  return showAllActions;
}
