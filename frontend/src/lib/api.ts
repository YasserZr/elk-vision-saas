import axios, { AxiosProgressEvent } from 'axios';
import {
  User,
  UserProfile,
  AuthTokens,
  LoginCredentials,
  RegisterData,
  LogMetadata,
  LogUploadResponse,
  LogSearchParams,
  LogSearchResult,
  Dashboard,
  AlertRule,
  ApiResponse,
  PaginatedResponse,
} from '@/types';

// =============================================================================
// API Client Configuration
// =============================================================================

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = typeof window !== 'undefined' 
          ? localStorage.getItem('refresh_token') 
          : null;
        
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        const response = await axios.post(
          `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/auth/refresh/`,
          { refresh: refreshToken }
        );
        
        const { access } = response.data;
        if (typeof window !== 'undefined') {
          localStorage.setItem('access_token', access);
        }
        
        originalRequest.headers.Authorization = `Bearer ${access}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Clear tokens and redirect to login
        if (typeof window !== 'undefined') {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user');
          window.location.href = '/login';
        }
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

// =============================================================================
// Authentication API
// =============================================================================

export const authApi = {
  /**
   * Login with email and password
   */
  login: async (credentials: LoginCredentials): Promise<ApiResponse<AuthTokens & { user: User }>> => {
    const response = await apiClient.post('/auth/login/', credentials);
    return response.data;
  },

  /**
   * Register a new user
   */
  register: async (data: RegisterData): Promise<ApiResponse<{ user: User; message: string }>> => {
    console.log('Sending registration data:', data);
    const response = await apiClient.post('/v1/users/register/', data);
    return response.data;
  },

  /**
   * Refresh access token
   */
  refreshToken: async (refreshToken: string): Promise<ApiResponse<{ access: string }>> => {
    const response = await apiClient.post('/v1/auth/refresh/', { refresh: refreshToken });
    return response.data;
  },

  /**
   * Logout and invalidate tokens
   */
  logout: async (): Promise<ApiResponse<{ message: string }>> => {
    const refreshToken = typeof window !== 'undefined' 
      ? localStorage.getItem('refresh_token') 
      : null;
    const response = await apiClient.post('/v1/auth/logout/', { refresh: refreshToken });
    return response.data;
  },

  /**
   * Request password reset
   */
  requestPasswordReset: async (email: string): Promise<ApiResponse<{ message: string }>> => {
    const response = await apiClient.post('/v1/auth/password-reset/', { email });
    return response.data;
  },

  /**
   * Confirm password reset
   */
  confirmPasswordReset: async (token: string, password: string): Promise<ApiResponse<{ message: string }>> => {
    const response = await apiClient.post('/v1/auth/password-reset/confirm/', { token, password });
    return response.data;
  },

  /**
   * Change password for authenticated user
   */
  changePassword: async (oldPassword: string, newPassword: string): Promise<ApiResponse<{ message: string }>> => {
    const response = await apiClient.post('/v1/auth/change-password/', {
      old_password: oldPassword,
      new_password: newPassword,
    });
    return response.data;
  },
};

// =============================================================================
// User Profile API
// =============================================================================

export const profileApi = {
  /**
   * Get current user's profile
   */
  getProfile: async (): Promise<ApiResponse<UserProfile>> => {
    const response = await apiClient.get('/v1/users/profile/');
    return response.data;
  },

  /**
   * Update current user's profile
   */
  updateProfile: async (data: Partial<UserProfile>): Promise<ApiResponse<UserProfile>> => {
    const response = await apiClient.patch('/v1/users/profile/', data);
    return response.data;
  },

  /**
   * Get user's API quota information
   */
  getQuota: async (): Promise<ApiResponse<{
    used: number;
    limit: number;
    reset_at: string;
    percentage_used: number;
  }>> => {
    const response = await apiClient.get('/v1/profile/quota/');
    return response.data;
  },

  /**
   * Update user preferences
   */
  updatePreferences: async (preferences: UserProfile['preferences']): Promise<ApiResponse<UserProfile>> => {
    const response = await apiClient.patch('/v1/profile/preferences/', { preferences });
    return response.data;
  },

  /**
   * Get API keys
   */
  getApiKeys: async (): Promise<ApiResponse<Array<{
    id: string;
    name: string;
    created_at: string;
    last_used_at: string | null;
    is_active: boolean;
  }>>> => {
    const response = await apiClient.get('/v1/profile/api-keys/');
    return response.data;
  },

  /**
   * Create new API key
   */
  createApiKey: async (name: string): Promise<ApiResponse<{
    id: string;
    name: string;
    key: string;
    created_at: string;
  }>> => {
    const response = await apiClient.post('/v1/profile/api-keys/', { name });
    return response.data;
  },

  /**
   * Delete API key
   */
  deleteApiKey: async (keyId: string): Promise<ApiResponse<{ message: string }>> => {
    const response = await apiClient.delete(`/v1/profile/api-keys/${keyId}/`);
    return response.data;
  },
};

// =============================================================================
// Log Upload API
// =============================================================================

export const logsApi = {
  /**
   * Upload log file(s)
   */
  upload: async (
    files: File[],
    metadata: {
      source?: string;
      environment?: string;
      service_name?: string;
      tags?: string[];
    } = {},
    onProgress?: (progress: number) => void
  ): Promise<ApiResponse<LogUploadResponse>> => {
    const formData = new FormData();
    
    files.forEach((file, index) => {
      formData.append(`file${index > 0 ? index : ''}`, file);
    });

    if (metadata.source) formData.append('source', metadata.source);
    if (metadata.environment) formData.append('environment', metadata.environment);
    if (metadata.service_name) formData.append('service_name', metadata.service_name);
    if (metadata.tags) formData.append('tags', JSON.stringify(metadata.tags));

    const response = await apiClient.post('/v1/logs/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent: AxiosProgressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });
    
    return response.data;
  },

  /**
   * Get upload status by task ID
   */
  getUploadStatus: async (taskId: string): Promise<ApiResponse<{
    task_id: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    progress: number;
    message?: string;
    result?: LogUploadResponse;
  }>> => {
    const response = await apiClient.get(`/v1/logs/upload/status/${taskId}/`);
    return response.data;
  },

  /**
   * Search logs with filters
   */
  search: async (params: LogSearchParams): Promise<ApiResponse<LogSearchResult>> => {
    const response = await apiClient.post('/v1/logs/search/', params);
    return response.data;
  },

  /**
   * Get log metadata by upload ID
   */
  getMetadata: async (uploadId: string): Promise<ApiResponse<LogMetadata>> => {
    const response = await apiClient.get(`/v1/logs/metadata/${uploadId}/`);
    return response.data;
  },

  /**
   * List log metadata with pagination
   */
  listMetadata: async (params: {
    page?: number;
    page_size?: number;
    source?: string;
    environment?: string;
    status?: string;
  } = {}): Promise<PaginatedResponse<LogMetadata>> => {
    const response = await apiClient.get('/v1/logs/metadata/', { params });
    return response.data;
  },

  /**
   * Get log statistics
   */
  getStats: async (params: {
    start_date?: string;
    end_date?: string;
    group_by?: 'day' | 'hour' | 'source' | 'environment';
  } = {}): Promise<ApiResponse<{
    total_logs: number;
    total_uploads: number;
    by_source: Record<string, number>;
    by_environment: Record<string, number>;
    by_level: Record<string, number>;
    timeline: Array<{ date: string; count: number }>;
  }>> => {
    const response = await apiClient.get('/v1/logs/metadata/stats/', { params });
    return response.data;
  },

  /**
   * Delete logs by upload ID
   */
  deleteByUploadId: async (uploadId: string): Promise<ApiResponse<{ message: string; deleted_count: number }>> => {
    const response = await apiClient.delete(`/v1/logs/${uploadId}/`);
    return response.data;
  },

  /**
   * Get search history
   */
  getSearchHistory: async (limit: number = 10): Promise<ApiResponse<{
    history: Array<{
      search_id: string;
      query: string;
      filters: Record<string, unknown>;
      results_count: number;
      created_at: string;
    }>;
    count: number;
  }>> => {
    const response = await apiClient.get('/v1/logs/search/history/', { params: { limit } });
    return response.data;
  },

  /**
   * Save search to history
   */
  saveSearchHistory: async (data: {
    query: string;
    filters?: Record<string, unknown>;
    results_count?: number;
  }): Promise<ApiResponse<{
    search_id: string;
    query: string;
    filters: Record<string, unknown>;
    results_count: number;
    created_at: string;
  }>> => {
    const response = await apiClient.post('/v1/logs/search/history/', data);
    return response.data;
  },

  /**
   * Delete search history entry
   */
  deleteSearchHistory: async (searchId: string): Promise<ApiResponse<{ message: string }>> => {
    const response = await apiClient.delete(`/v1/logs/search/history/${searchId}/`);
    return response.data;
  },

  /**
   * Clear all search history
   */
  clearSearchHistory: async (): Promise<ApiResponse<{ message: string }>> => {
    const response = await apiClient.delete('/v1/logs/search/history/');
    return response.data;
  },
};

// =============================================================================
// Dashboard API
// =============================================================================

export const dashboardApi = {
  /**
   * Get all dashboards
   */
  list: async (): Promise<ApiResponse<Dashboard[]>> => {
    const response = await apiClient.get('/v1/dashboards/');
    return response.data;
  },

  /**
   * Get dashboard by ID
   */
  get: async (dashboardId: string): Promise<ApiResponse<Dashboard>> => {
    const response = await apiClient.get(`/v1/dashboards/${dashboardId}/`);
    return response.data;
  },

  /**
   * Create new dashboard
   */
  create: async (data: Omit<Dashboard, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse<Dashboard>> => {
    const response = await apiClient.post('/v1/dashboards/', data);
    return response.data;
  },

  /**
   * Update dashboard
   */
  update: async (dashboardId: string, data: Partial<Dashboard>): Promise<ApiResponse<Dashboard>> => {
    const response = await apiClient.patch(`/v1/dashboards/${dashboardId}/`, data);
    return response.data;
  },

  /**
   * Delete dashboard
   */
  delete: async (dashboardId: string): Promise<ApiResponse<{ message: string }>> => {
    const response = await apiClient.delete(`/v1/dashboards/${dashboardId}/`);
    return response.data;
  },

  /**
   * Duplicate dashboard
   */
  duplicate: async (dashboardId: string, name: string): Promise<ApiResponse<Dashboard>> => {
    const response = await apiClient.post(`/v1/dashboards/${dashboardId}/duplicate/`, { name });
    return response.data;
  },
};

// =============================================================================
// Alerts API
// =============================================================================

export const alertsApi = {
  /**
   * Get all alert rules
   */
  list: async (): Promise<ApiResponse<AlertRule[]>> => {
    const response = await apiClient.get('/v1/alerts/');
    return response.data;
  },

  /**
   * Get alert rule by ID
   */
  get: async (alertId: string): Promise<ApiResponse<AlertRule>> => {
    const response = await apiClient.get(`/v1/alerts/${alertId}/`);
    return response.data;
  },

  /**
   * Create new alert rule
   */
  create: async (data: Omit<AlertRule, 'id' | 'created_at' | 'updated_at' | 'last_triggered'>): Promise<ApiResponse<AlertRule>> => {
    const response = await apiClient.post('/v1/alerts/', data);
    return response.data;
  },

  /**
   * Update alert rule
   */
  update: async (alertId: string, data: Partial<AlertRule>): Promise<ApiResponse<AlertRule>> => {
    const response = await apiClient.patch(`/v1/alerts/${alertId}/`, data);
    return response.data;
  },

  /**
   * Delete alert rule
   */
  delete: async (alertId: string): Promise<ApiResponse<{ message: string }>> => {
    const response = await apiClient.delete(`/v1/alerts/${alertId}/`);
    return response.data;
  },

  /**
   * Toggle alert rule status
   */
  toggle: async (alertId: string): Promise<ApiResponse<AlertRule>> => {
    const response = await apiClient.post(`/v1/alerts/${alertId}/toggle/`);
    return response.data;
  },

  /**
   * Test alert rule
   */
  test: async (alertId: string): Promise<ApiResponse<{ triggered: boolean; message: string }>> => {
    const response = await apiClient.post(`/v1/alerts/${alertId}/test/`);
    return response.data;
  },

  /**
   * Get alert history
   */
  getHistory: async (params: {
    alert_id?: string;
    start_date?: string;
    end_date?: string;
    page?: number;
    page_size?: number;
  } = {}): Promise<PaginatedResponse<{
    id: string;
    alert_id: string;
    alert_name: string;
    triggered_at: string;
    value: number;
    message: string;
  }>> => {
    const response = await apiClient.get('/v1/alerts/history/', { params });
    return response.data;
  },
};

// =============================================================================
// Health API
// =============================================================================

export const healthApi = {
  /**
   * Get system health status
   */
  check: async (): Promise<ApiResponse<{
    status: 'healthy' | 'degraded' | 'unhealthy';
    services: {
      api: { status: string; latency_ms: number };
      elasticsearch: { status: string; latency_ms: number };
      mongodb: { status: string; latency_ms: number };
      redis: { status: string; latency_ms: number };
      logstash: { status: string; latency_ms: number };
    };
    timestamp: string;
  }>> => {
    const response = await apiClient.get('/health/');
    return response.data;
  },

  /**
   * Get detailed system metrics
   */
  metrics: async (): Promise<ApiResponse<{
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
    active_connections: number;
    request_rate: number;
    error_rate: number;
  }>> => {
    const response = await apiClient.get('/health/metrics/');
    return response.data;
  },
};

// =============================================================================
// Export Default Client
// =============================================================================

export default apiClient;
