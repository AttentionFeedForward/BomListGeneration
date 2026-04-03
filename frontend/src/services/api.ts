// API服务层 - 基础HTTP客户端
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';

// API响应类型
export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  message?: string;
  code?: number;
  timestamp?: string;
}

// API错误类型
export interface ApiError {
  message: string;
  code?: number;
  details?: any;
}

// 请求配置类型
export interface RequestConfig extends AxiosRequestConfig {
  skipAuth?: boolean;
  skipErrorHandler?: boolean;
}

// 扩展Axios配置类型
declare module 'axios' {
  interface InternalAxiosRequestConfig {
    skipAuth?: boolean;
    skipErrorHandler?: boolean;
  }
}

class ApiClient {
  private instance: AxiosInstance;
  private baseURL: string;
  private fallbackBaseURL?: string;
  private hasSwitchedToFallback: boolean = false;
  private envBaseURLProvided: boolean = false;

  constructor(
    baseURL?: string
  ) {
    // 是否由环境变量显式提供
    const envBaseURL = process.env.REACT_APP_API_BASE_URL;
    this.envBaseURLProvided = !!envBaseURL;

    // 浏览器环境下的协议与主机名
    const isBrowser = typeof window !== 'undefined';
    const protocol = isBrowser ? window.location.protocol : 'http:';
    const pageHost = isBrowser ? window.location.hostname : 'localhost';

    // 当页面以 localhost 访问时，优先映射到 127.0.0.1，避免 IPv6 localhost 差异
    const preferredHost = (pageHost === 'localhost') ? '127.0.0.1' : pageHost;
    const defaultBaseURL = `${protocol}//${preferredHost}:5000/api`;

    // 本机回退基址（仅在需要时使用）
    this.fallbackBaseURL = `${protocol}//127.0.0.1:5000/api`;

    // 最终选用的基址：优先环境变量，其次根据当前页面主机名推导
    this.baseURL = (baseURL || envBaseURL || defaultBaseURL);
    this.instance = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // 请求拦截器
    this.instance.interceptors.request.use(
      (config) => {
        // 添加认证token
        const token = localStorage.getItem('auth_token');
        if (token && !config.skipAuth) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // 添加请求时间戳
        config.headers['X-Request-Time'] = new Date().toISOString();

        console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, {
          params: config.params,
          data: config.data,
        });

        return config;
      },
      (error) => {
        console.error('[API Request Error]', error);
        return Promise.reject(error);
      }
    );

    // 响应拦截器
    this.instance.interceptors.response.use(
      (response: AxiosResponse<ApiResponse>) => {
        console.log(`[API Response] ${response.config.method?.toUpperCase()} ${response.config.url}`, {
          status: response.status,
          data: response.data,
        });

        return response;
      },
      (error: AxiosError<ApiResponse>) => {
        console.error('[API Response Error]', {
          url: error.config?.url,
          status: error.response?.status,
          message: error.response?.data?.message || error.message,
          data: error.response?.data,
        });

        // 当以本机的局域网 IP 打开页面但该 IP 访问后端失败时，自动回退到 127.0.0.1
        // 仅在未显式配置 REACT_APP_API_BASE_URL 时生效，且只重试一次
        const isNetworkError = !error.response; // 没有响应，一般为网络/连接错误
        if (
          isNetworkError &&
          !this.envBaseURLProvided &&
          !this.hasSwitchedToFallback &&
          typeof window !== 'undefined'
        ) {
          const host = window.location.hostname;
          const isLocalHost = (host === 'localhost' || host === '127.0.0.1');
          const isPrivateIP = /^(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[0-1])\.)/.test(host);

          // 仅当页面是用私网 IP 打开、且不是 localhost 时，才触发回退
          if (isPrivateIP && !isLocalHost && this.fallbackBaseURL) {
            this.hasSwitchedToFallback = true;
            this.baseURL = this.fallbackBaseURL;
            this.instance.defaults.baseURL = this.fallbackBaseURL;

            const retryConfig = { ...error.config, baseURL: this.fallbackBaseURL } as AxiosRequestConfig;
            console.warn('[API Fallback] 网络错误，切换到本机环回地址重试:', this.fallbackBaseURL);
            return this.instance.request(retryConfig);
          }
        }

        // 处理特定错误状态
        if (error.response?.status === 401) {
          // 未授权，清除token并重定向到登录页
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
        }

        return Promise.reject(this.transformError(error));
      }
    );
  }

  private transformError(error: AxiosError<ApiResponse>): ApiError {
    if (error.response?.data) {
      return {
        message: error.response.data.message || '请求失败',
        code: error.response.data.code || error.response.status,
        details: error.response.data,
      };
    }

    if (error.code === 'ECONNABORTED') {
      return {
        message: '请求超时，请稍后重试',
        code: 408,
      };
    }

    if (error.code === 'ERR_NETWORK') {
      return {
        message: '网络连接失败，请检查网络设置',
        code: 0,
      };
    }

    return {
      message: error.message || '未知错误',
      code: 500,
    };
  }

  // GET请求
  async get<T = any>(url: string, config?: RequestConfig): Promise<ApiResponse<T>> {
    const response = await this.instance.get<ApiResponse<T>>(url, config);
    return response.data;
  }

  // POST请求
  async post<T = any>(url: string, data?: any, config?: RequestConfig): Promise<ApiResponse<T>> {
    const response = await this.instance.post<ApiResponse<T>>(url, data, config);
    return response.data;
  }

  // PUT请求
  async put<T = any>(url: string, data?: any, config?: RequestConfig): Promise<ApiResponse<T>> {
    const response = await this.instance.put<ApiResponse<T>>(url, data, config);
    return response.data;
  }

  // DELETE请求
  async delete<T = any>(url: string, config?: RequestConfig): Promise<ApiResponse<T>> {
    const response = await this.instance.delete<ApiResponse<T>>(url, config);
    return response.data;
  }

  // PATCH请求
  async patch<T = any>(url: string, data?: any, config?: RequestConfig): Promise<ApiResponse<T>> {
    const response = await this.instance.patch<ApiResponse<T>>(url, data, config);
    return response.data;
  }

  // 文件上传
  async upload<T = any>(url: string, file: File, onProgress?: (progress: number) => void): Promise<ApiResponse<T>> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.instance.post<ApiResponse<T>>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });

    return response.data;
  }

  // 下载文件
  async download(url: string, filename?: string): Promise<void> {
    const response = await this.instance.get(url, {
      responseType: 'blob',
    });

    const blob = new Blob([response.data]);
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename || 'download';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  }

  // 设置认证token
  setAuthToken(token: string) {
    localStorage.setItem('auth_token', token);
  }

  // 清除认证token
  clearAuthToken() {
    localStorage.removeItem('auth_token');
  }

  // 获取基础URL
  getBaseURL(): string {
    return this.baseURL;
  }
}

// 创建默认API客户端实例
export const apiClient = new ApiClient();

// 导出类型和实例
export default apiClient;