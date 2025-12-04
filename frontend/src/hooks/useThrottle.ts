import React, { useRef, useCallback, useEffect, useState } from "react";

/**
 * 节流回调函数 Hook
 * 
 * @param callback - 需要节流的回调函数
 * @param delay - 节流延迟时间（毫秒），默认 300ms
 * @param deps - 依赖数组，当依赖变化时重新创建节流函数
 * @returns 节流后的回调函数
 * 
 * @example
 * const throttledClick = useThrottle((value: string) => {
 *   // 处理点击
 * }, 300, []);
 * 
 * <Button onClick={() => throttledClick('value')} />
 */
export function useThrottle<T extends (...args: any[]) => any>(
  callback: T,
  delay: number = 300,
  deps: React.DependencyList = []
): T {
  const lastRun = useRef<number>(0);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const throttledCallback = useCallback(
    ((...args: Parameters<T>) => {
      const now = Date.now();
      const timeSinceLastRun = now - lastRun.current;

      if (timeSinceLastRun >= delay) {
        // 可以立即执行
        lastRun.current = now;
        callback(...args);
      } else {
        // 需要等待，清除之前的定时器
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }

        // 设置新的定时器，在剩余时间后执行
        const remainingTime = delay - timeSinceLastRun;
        timeoutRef.current = setTimeout(() => {
          lastRun.current = Date.now();
          callback(...args);
          timeoutRef.current = null;
        }, remainingTime);
      }
    }) as T,
    [callback, delay, ...deps]
  );

  // 清理定时器
  const cleanup = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  // 组件卸载时清理
  useEffect(() => {
    return cleanup;
  }, [cleanup]);

  return throttledCallback;
}

/**
 * 节流值 Hook（不常用，主要用于值的变化）
 * 
 * @param value - 需要节流的值
 * @param delay - 节流延迟时间（毫秒），默认 300ms
 * @returns 节流后的值
 */
export function useThrottleValue<T>(value: T, delay: number = 300): T {
  const [throttledValue, setThrottledValue] = useState<T>(value);
  const lastRun = useRef<number>(0);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const now = Date.now();
    const timeSinceLastRun = now - lastRun.current;

    if (timeSinceLastRun >= delay) {
      // 可以立即更新
      lastRun.current = now;
      setThrottledValue(value);
    } else {
      // 需要等待
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      const remainingTime = delay - timeSinceLastRun;
      timeoutRef.current = setTimeout(() => {
        lastRun.current = Date.now();
        setThrottledValue(value);
        timeoutRef.current = null;
      }, remainingTime);
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [value, delay]);

  return throttledValue;
}

