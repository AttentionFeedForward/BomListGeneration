// 数据获取相关hooks
import { useState, useEffect, useCallback, useRef } from 'react';
import { ApiResponse, ApiError } from '../services/api';

// 基础状态类型
export interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: ApiError | null;
  lastUpdated: Date | null;
}

// 查询选项
export interface QueryOptions {
  enabled?: boolean;
  refetchOnMount?: boolean;
  refetchOnWindowFocus?: boolean;
  staleTime?: number;
  cacheTime?: number;
  retry?: number;
  retryDelay?: number;
  onSuccess?: (data: any) => void;
  onError?: (error: ApiError) => void;
}

// 变更选项
export interface MutationOptions<TData, TVariables> {
  onSuccess?: (data: TData, variables: TVariables) => void;
  onError?: (error: ApiError, variables: TVariables) => void;
  onSettled?: (data: TData | undefined, error: ApiError | null, variables: TVariables) => void;
}

// 基础API hook
export function useApi<T>(
  apiCall: () => Promise<ApiResponse<T>>,
  options: QueryOptions = {}
) {
  const {
    enabled = true,
    refetchOnMount = true,
    refetchOnWindowFocus = false,
    staleTime = 5 * 60 * 1000, // 5分钟
    cacheTime = 10 * 60 * 1000, // 10分钟
    retry = 3,
    retryDelay = 1000,
    onSuccess,
    onError,
  } = options;

  const [state, setState] = useState<ApiState<T>>({
    data: null,
    loading: false,
    error: null,
    lastUpdated: null,
  });

  const retryCountRef = useRef(0);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const abortControllerRef = useRef<AbortController | undefined>(undefined);

  const fetchData = useCallback(async (isRetry = false) => {
    if (!enabled) return;

    // 取消之前的请求
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();

    if (!isRetry) {
      setState(prev => ({ ...prev, loading: true, error: null }));
      retryCountRef.current = 0;
    }

    try {
      const response = await apiCall();
      
      setState({
        data: response.data,
        loading: false,
        error: null,
        lastUpdated: new Date(),
      });

      retryCountRef.current = 0;
      onSuccess?.(response.data);
    } catch (error) {
      const apiError = error as ApiError;
      
      if (retryCountRef.current < retry) {
        retryCountRef.current++;
        timeoutRef.current = setTimeout(() => {
          fetchData(true);
        }, retryDelay * retryCountRef.current);
      } else {
        setState(prev => ({
          ...prev,
          loading: false,
          error: apiError,
        }));
        onError?.(apiError);
      }
    }
  }, [apiCall, enabled, retry, retryDelay, onSuccess, onError]);

  const refetch = useCallback(() => {
    retryCountRef.current = 0;
    return fetchData();
  }, [fetchData]);

  const invalidate = useCallback(() => {
    setState(prev => ({ ...prev, lastUpdated: null }));
  }, []);

  // 初始加载
  useEffect(() => {
    if (enabled && refetchOnMount) {
      fetchData();
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [fetchData, enabled, refetchOnMount]);

  // 窗口焦点重新获取
  useEffect(() => {
    if (!refetchOnWindowFocus) return;

    const handleFocus = () => {
      if (state.lastUpdated && Date.now() - state.lastUpdated.getTime() > staleTime) {
        refetch();
      }
    };

    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [refetchOnWindowFocus, staleTime, state.lastUpdated, refetch]);

  return {
    ...state,
    refetch,
    invalidate,
    isStale: state.lastUpdated ? Date.now() - state.lastUpdated.getTime() > staleTime : true,
  };
}

// 查询hook
export function useQuery<T>(
  key: string | string[],
  apiCall: () => Promise<ApiResponse<T>>,
  options?: QueryOptions
) {
  const queryKey = Array.isArray(key) ? key.join(':') : key;
  
  return useApi(apiCall, {
    ...options,
    onSuccess: (data) => {
      // 可以在这里添加缓存逻辑
      options?.onSuccess?.(data);
    },
  });
}

// 变更hook
export function useMutation<TData, TVariables = void>(
  mutationFn: (variables: TVariables) => Promise<ApiResponse<TData>>,
  options: MutationOptions<TData, TVariables> = {}
) {
  const [state, setState] = useState<{
    data: TData | undefined;
    loading: boolean;
    error: ApiError | null;
  }>({
    data: undefined,
    loading: false,
    error: null,
  });

  const mutate = useCallback(async (variables: TVariables) => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const response = await mutationFn(variables);
      const data = response.data;

      setState({
        data,
        loading: false,
        error: null,
      });

      options.onSuccess?.(data, variables);
      options.onSettled?.(data, null, variables);

      return data;
    } catch (error) {
      const apiError = error as ApiError;
      
      setState(prev => ({
        ...prev,
        loading: false,
        error: apiError,
      }));

      options.onError?.(apiError, variables);
      options.onSettled?.(undefined, apiError, variables);

      throw apiError;
    }
  }, [mutationFn, options]);

  const reset = useCallback(() => {
    setState({
      data: undefined,
      loading: false,
      error: null,
    });
  }, []);

  return {
    ...state,
    mutate,
    mutateAsync: mutate,
    reset,
  };
}

// 无限查询hook（用于分页数据）
export function useInfiniteQuery<T>(
  key: string | string[],
  apiCall: (pageParam: number) => Promise<ApiResponse<{ items: T[]; total: number; page: number; hasMore: boolean }>>,
  options: QueryOptions = {}
) {
  const [state, setState] = useState<{
    data: T[];
    loading: boolean;
    error: ApiError | null;
    hasNextPage: boolean;
    isFetchingNextPage: boolean;
    lastUpdated: Date | null;
  }>({
    data: [],
    loading: false,
    error: null,
    hasNextPage: true,
    isFetchingNextPage: false,
    lastUpdated: null,
  });

  const pageRef = useRef(1);

  const fetchPage = useCallback(async (page: number, isNextPage = false) => {
    if (!options.enabled && options.enabled !== undefined) return;

    setState(prev => ({
      ...prev,
      loading: !isNextPage,
      isFetchingNextPage: isNextPage,
      error: null,
    }));

    try {
      const response = await apiCall(page);
      const { items, hasMore } = response.data;

      setState(prev => ({
        data: page === 1 ? items : [...prev.data, ...items],
        loading: false,
        isFetchingNextPage: false,
        error: null,
        hasNextPage: hasMore,
        lastUpdated: new Date(),
      }));

      pageRef.current = page;
      options.onSuccess?.(response.data);
    } catch (error) {
      const apiError = error as ApiError;
      
      setState(prev => ({
        ...prev,
        loading: false,
        isFetchingNextPage: false,
        error: apiError,
      }));

      options.onError?.(apiError);
    }
  }, [apiCall, options]);

  const fetchNextPage = useCallback(() => {
    if (state.hasNextPage && !state.isFetchingNextPage) {
      return fetchPage(pageRef.current + 1, true);
    }
  }, [fetchPage, state.hasNextPage, state.isFetchingNextPage]);

  const refetch = useCallback(() => {
    pageRef.current = 1;
    return fetchPage(1);
  }, [fetchPage]);

  useEffect(() => {
    if (options.enabled !== false && options.refetchOnMount !== false) {
      fetchPage(1);
    }
  }, [fetchPage, options.enabled, options.refetchOnMount]);

  return {
    ...state,
    fetchNextPage,
    refetch,
  };
}

// 实时数据hook
export function useRealTimeData<T>(
  apiCall: () => Promise<ApiResponse<T>>,
  interval: number = 5000,
  options: QueryOptions = {}
) {
  const intervalRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);
  const result = useApi(apiCall, options);

  useEffect(() => {
    if (!options.enabled && options.enabled !== undefined) return;

    intervalRef.current = setInterval(() => {
      result.refetch();
    }, interval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [interval, options.enabled, result.refetch]);

  return result;
}

// 导出所有hooks
export default {
  useApi,
  useQuery,
  useMutation,
  useInfiniteQuery,
  useRealTimeData,
};