import { useState, useEffect, useRef, useCallback } from "react";

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
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const cancel = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  useEffect(() => {
    cancel();

    // 设置新的定时器
    timeoutRef.current = setTimeout(() => {
      setDebouncedValue(value);
      timeoutRef.current = null;
    }, delay);

    // 清理函数
    return cancel;
  }, [value, delay, cancel]);

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
export function useDebounceCallback<T extends (...args: unknown[]) => void>(
  callback: T,
  delay: number = 500
): [T, () => void] {
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const callbackRef = useRef(callback);

  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  const cancel = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  const debouncedCallback = useCallback((...args: Parameters<T>) => {
    cancel();

    timeoutRef.current = setTimeout(() => {
      callbackRef.current(...args);
      timeoutRef.current = null;
    }, delay);
  }, [cancel, delay]) as T;

  // 当依赖变化时，取消当前的防抖
  useEffect(() => {
    return cancel;
  }, [cancel]);

  return [debouncedCallback, cancel];
}
