import { useState, useEffect } from "react";

/**
 * 防抖 Hook
 * 
 * @param value - 需要防抖的值
 * @param delay - 防抖延迟时间（毫秒），默认 500ms
 * @returns 防抖后的值和取消函数
 * 
 * @example
 * const [searchTerm, setSearchTerm] = useState('');
 * const debouncedSearch = useDebounce(searchTerm, 500);
 * 
 * useEffect(() => {
 *   if (debouncedSearch) {
 *     // 执行搜索
 *   }
 * }, [debouncedSearch]);
 */
export function useDebounce<T>(value: T, delay: number = 500): [T, () => void] {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);
  const [timeoutId, setTimeoutId] = useState<NodeJS.Timeout | null>(null);

  const cancel = () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
      setTimeoutId(null);
    }
  };

  useEffect(() => {
    // 清除之前的定时器
    if (timeoutId) {
      clearTimeout(timeoutId);
    }

    // 设置新的定时器
    const id = setTimeout(() => {
      setDebouncedValue(value);
      setTimeoutId(null);
    }, delay);

    setTimeoutId(id);

    // 清理函数
    return () => {
      if (id) {
        clearTimeout(id);
      }
    };
  }, [value, delay]);

  return [debouncedValue, cancel];
}

/**
 * 防抖回调函数 Hook
 * 
 * @param callback - 需要防抖的回调函数
 * @param delay - 防抖延迟时间（毫秒），默认 500ms
 * @param deps - 依赖数组，当依赖变化时重新创建防抖函数
 * @returns 防抖后的回调函数和取消函数
 * 
 * @example
 * const debouncedSearch = useDebounceCallback((value: string) => {
 *   // 执行搜索
 * }, 500, []);
 * 
 * <Input onChange={(e) => debouncedSearch(e.target.value)} />
 */
export function useDebounceCallback<T extends (...args: any[]) => any>(
  callback: T,
  delay: number = 500,
  deps: React.DependencyList = []
): [T, () => void] {
  const [timeoutId, setTimeoutId] = useState<NodeJS.Timeout | null>(null);

  const cancel = () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
      setTimeoutId(null);
    }
  };

  const debouncedCallback = ((...args: Parameters<T>) => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }

    const id = setTimeout(() => {
      callback(...args);
      setTimeoutId(null);
    }, delay);

    setTimeoutId(id);
  }) as T;

  // 当依赖变化时，取消当前的防抖
  useEffect(() => {
    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, deps);

  return [debouncedCallback, cancel];
}

