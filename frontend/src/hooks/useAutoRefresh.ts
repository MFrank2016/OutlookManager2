import { useState, useEffect, useRef } from 'react';

interface UseAutoRefreshOptions {
  enabled: boolean;
  intervalSeconds: number;
  onRefresh: () => void | Promise<void>;
  isLoading?: boolean;
  isRefetching?: boolean;
}

/**
 * 自动刷新 Hook
 * 使用单例模式确保同一时间只有一个 interval 在运行
 */
export function useAutoRefresh({
  enabled,
  intervalSeconds,
  onRefresh,
  isLoading = false,
  isRefetching = false,
}: UseAutoRefreshOptions) {
  // 使用 state 存储倒计时，确保 UI 响应式更新
  const [countdown, setCountdown] = useState(intervalSeconds);
  // 使用 ref 存储 interval，确保跨渲染保持同一个实例
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const onRefreshRef = useRef(onRefresh);
  const isRefreshingRef = useRef(false);

  // 更新 onRefresh ref
  useEffect(() => {
    onRefreshRef.current = onRefresh;
  }, [onRefresh]);

  // 主逻辑
  useEffect(() => {
    // 先清理旧的 interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    // 如果不满足启动条件，直接返回
    if (!enabled || isLoading || isRefetching) {
      // 如果之前在刷新中，现在刷新完成了，重置标志
      if (isRefreshingRef.current && !isRefetching) {
        isRefreshingRef.current = false;
      }
      
      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      };
    }

    // 创建新的 interval
    // 使用函数式更新来初始化倒计时，避免在 effect 中同步调用 setState
    let isFirstTick = true;
    const interval = setInterval(() => {
      setCountdown((prevCountdown) => {
        // 第一次执行时，重置为初始值
        if (isFirstTick) {
          isFirstTick = false;
          return intervalSeconds;
        }
        
        const newCountdown = prevCountdown - 1;

        if (newCountdown <= 0) {
          // 倒计时结束，触发刷新
          if (!isRefreshingRef.current) {
            isRefreshingRef.current = true;

            // 调用刷新函数
            const result = onRefreshRef.current();
            
            // 如果返回 Promise，等待完成后重置标志
            if (result instanceof Promise) {
              result.finally(() => {
                isRefreshingRef.current = false;
              });
            } else {
              isRefreshingRef.current = false;
            }
          }

          // 重置倒计时
          return intervalSeconds;
        }

        return newCountdown;
      });
    }, 1000);

    intervalRef.current = interval;

    // 返回清理函数
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [enabled, isLoading, isRefetching, intervalSeconds]);

  return {
    countdown,
  };
}

