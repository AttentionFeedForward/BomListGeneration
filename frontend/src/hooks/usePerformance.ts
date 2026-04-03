import { useState, useEffect, useCallback, useRef, useMemo } from 'react';

// 防抖Hook
export const useDebounce = <T>(value: T, delay: number): T => {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};

// 节流Hook
export const useThrottle = <T>(value: T, limit: number): T => {
  const [throttledValue, setThrottledValue] = useState<T>(value);
  const lastRan = useRef<number>(Date.now());

  useEffect(() => {
    const handler = setTimeout(() => {
      if (Date.now() - lastRan.current >= limit) {
        setThrottledValue(value);
        lastRan.current = Date.now();
      }
    }, limit - (Date.now() - lastRan.current));

    return () => {
      clearTimeout(handler);
    };
  }, [value, limit]);

  return throttledValue;
};

// 懒加载Hook
export const useLazyLoad = (threshold: number = 0.1) => {
  const [isVisible, setIsVisible] = useState(false);
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { threshold }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => observer.disconnect();
  }, [threshold]);

  return { ref, isVisible };
};

// 虚拟滚动Hook
export interface VirtualScrollOptions {
  itemHeight: number;
  containerHeight: number;
  overscan?: number;
}

export const useVirtualScroll = <T>(
  items: T[],
  options: VirtualScrollOptions
) => {
  const [scrollTop, setScrollTop] = useState(0);
  const { itemHeight, containerHeight, overscan = 5 } = options;

  const visibleRange = useMemo(() => {
    const visibleCount = Math.ceil(containerHeight / itemHeight);
    const start = Math.floor(scrollTop / itemHeight);
    const end = Math.min(start + visibleCount + overscan, items.length);
    
    return {
      start: Math.max(0, start - overscan),
      end,
      visibleCount
    };
  }, [scrollTop, itemHeight, containerHeight, overscan, items.length]);

  const visibleItems = useMemo(() => {
    return items.slice(visibleRange.start, visibleRange.end).map((item, index) => ({
      item,
      index: visibleRange.start + index,
      style: {
        position: 'absolute' as const,
        top: (visibleRange.start + index) * itemHeight,
        height: itemHeight,
        width: '100%'
      }
    }));
  }, [items, visibleRange, itemHeight]);

  const totalHeight = items.length * itemHeight;

  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  }, []);

  return {
    visibleItems,
    totalHeight,
    handleScroll,
    containerProps: {
      style: {
        height: containerHeight,
        overflow: 'auto' as const,
        position: 'relative' as const
      },
      onScroll: handleScroll
    }
  };
};

// 内存使用监控Hook
export const useMemoryMonitor = () => {
  const [memoryInfo, setMemoryInfo] = useState<{
    usedJSHeapSize?: number;
    totalJSHeapSize?: number;
    jsHeapSizeLimit?: number;
    usage?: number;
  }>({});

  useEffect(() => {
    const updateMemoryInfo = () => {
      if ('memory' in performance) {
        const memory = (performance as any).memory;
        const usage = memory.usedJSHeapSize / memory.jsHeapSizeLimit;
        
        setMemoryInfo({
          usedJSHeapSize: memory.usedJSHeapSize,
          totalJSHeapSize: memory.totalJSHeapSize,
          jsHeapSizeLimit: memory.jsHeapSizeLimit,
          usage: Math.round(usage * 100) / 100
        });
      }
    };

    updateMemoryInfo();
    const interval = setInterval(updateMemoryInfo, 5000);

    return () => clearInterval(interval);
  }, []);

  return memoryInfo;
};

// 图片懒加载Hook
export const useImageLazyLoad = (src: string, placeholder?: string) => {
  const [imageSrc, setImageSrc] = useState(placeholder || '');
  const [isLoaded, setIsLoaded] = useState(false);
  const [isError, setIsError] = useState(false);
  const { ref, isVisible } = useLazyLoad();

  useEffect(() => {
    if (isVisible && src) {
      const img = new Image();
      
      img.onload = () => {
        setImageSrc(src);
        setIsLoaded(true);
      };
      
      img.onerror = () => {
        setIsError(true);
      };
      
      img.src = src;
    }
  }, [isVisible, src]);

  return {
    ref,
    src: imageSrc,
    isLoaded,
    isError,
    isVisible
  };
};

// 性能监控Hook
export const usePerformanceMonitor = () => {
  const [metrics, setMetrics] = useState<{
    renderTime?: number;
    componentCount?: number;
    reRenderCount?: number;
  }>({});

  const renderCount = useRef(0);
  const startTime = useRef(performance.now());
  const lastUpdateTime = useRef(0);

  // 使用 useCallback 来避免无限循环
  const updateMetrics = useCallback(() => {
    const now = performance.now();
    // 限制更新频率，避免过于频繁的状态更新
    if (now - lastUpdateTime.current > 1000) { // 每秒最多更新一次
      renderCount.current += 1;
      const renderTime = now - startTime.current;

      setMetrics(prev => ({
        ...prev,
        renderTime: Math.round(renderTime * 100) / 100,
        reRenderCount: renderCount.current
      }));

      lastUpdateTime.current = now;
      startTime.current = now;
    }
  }, []);

  // 只在组件挂载时设置初始值
  useEffect(() => {
    startTime.current = performance.now();
    setMetrics({
      renderTime: 0,
      componentCount: 1,
      reRenderCount: 1
    });
  }, []);

  return { metrics, updateMetrics };
};

// 缓存Hook
export const useCache = <T>(key: string, fetcher: () => Promise<T>, ttl: number = 300000) => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const cache = useRef(new Map<string, { data: T; timestamp: number }>());

  const fetchData = useCallback(async () => {
    const cached = cache.current.get(key);
    const now = Date.now();

    if (cached && (now - cached.timestamp) < ttl) {
      setData(cached.data);
      return cached.data;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await fetcher();
      cache.current.set(key, { data: result, timestamp: now });
      setData(result);
      return result;
    } catch (err) {
      setError(err as Error);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [key, fetcher, ttl]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const invalidate = useCallback(() => {
    cache.current.delete(key);
  }, [key]);

  return { data, loading, error, refetch: fetchData, invalidate };
};