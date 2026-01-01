// User types
export interface User {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  is_active: boolean;
}

export interface UserProfile {
  _id: string;
  user_id: number;
  tenant_id: string;
  organization: string;
  role: "viewer" | "admin" | "superadmin";
  preferences: UserPreferences;
  api_quota: ApiQuota;
  created_at: string;
  updated_at: string;
  last_login: string | null;
}

export interface UserPreferences {
  theme: "light" | "dark";
  timezone: string;
  notifications: {
    email: boolean;
    browser: boolean;
    slack: boolean;
  };
  default_dashboard: string | null;
}

export interface ApiQuota {
  logs_per_day: number;
  api_calls_per_hour: number;
  retention_days: number;
  usage?: {
    logs_uploaded?: number;
    api_calls?: number;
  };
}

// Auth types
export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  password2: string;
  first_name?: string;
  last_name?: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface AuthState {
  user: User | null;
  profile: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// Log types
export interface LogMetadata {
  _id: string;
  upload_id: string;
  task_id: string;
  tenant_id: string;
  user_id: number;
  source: string;
  environment: string;
  service_name: string;
  file_name: string;
  file_size: number;
  format_type: "json" | "csv" | "text";
  log_count: number;
  status: "pending" | "processing" | "success" | "failed";
  processing_time: number | null;
  ingestion_method: string;
  tags: string[];
  created_at: string;
  updated_at: string;
  indexed_at: string | null;
  errors: string[];
}

export interface LogUploadResponse {
  task_id: string;
  message: string;
  file_name: string;
  file_size: number;
  format: string;
  estimated_entries: number;
  status: string;
}

export interface LogSearchParams {
  query?: string;
  q?: string;
  from?: string;
  to?: string;
  start_time?: string;
  end_time?: string;
  level?: string;
  source?: string;
  environment?: string;
  service?: string;
  size?: number;
  page?: number;
  page_size?: number;
}

export interface LogSearchResult {
  query: string;
  results: LogEntry[];
  total: number;
  page: number;
  size: number;
  took: number;
}

export interface LogEntry {
  "@timestamp": string;
  message: string;
  level?: string;
  service_name?: string;
  tenant_id: string;
  [key: string]: unknown;
}

// Statistics types
export interface LogStatistics {
  period_days: number;
  total_uploads: number;
  total_logs: number;
  total_size_bytes: number;
  by_status: {
    [status: string]: {
      count: number;
      total_logs: number;
      avg_processing_time: number | null;
    };
  };
}

// Dashboard types
export interface Dashboard {
  _id: string;
  name: string;
  description: string;
  tenant_id: string;
  user_id: number;
  widgets: DashboardWidget[];
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface DashboardWidget {
  id: string;
  type: "line" | "bar" | "pie" | "metric" | "table" | "logs";
  title: string;
  query: string;
  position: { x: number; y: number; w: number; h: number };
  config: Record<string, unknown>;
}

// Alert types
export interface Alert {
  _id: string;
  name: string;
  description: string;
  tenant_id: string;
  user_id: number;
  condition: AlertCondition;
  actions: AlertAction[];
  enabled: boolean;
  last_triggered: string | null;
  created_at: string;
  updated_at: string;
}

export interface AlertRule {
  id: string;
  name: string;
  description: string;
  condition: {
    field: string;
    operator: string;
    value: string;
    time_window: string;
  };
  actions: Array<{
    type: string;
    config: Record<string, string>;
  }>;
  severity: 'low' | 'medium' | 'high' | 'critical';
  is_active: boolean;
  last_triggered?: string;
  created_at: string;
  updated_at: string;
}

export interface AlertCondition {
  field: string;
  operator: "gt" | "lt" | "eq" | "contains" | "regex";
  value: string | number;
  time_window: number;
  threshold: number;
}

export interface AlertAction {
  type: "email" | "slack" | "webhook";
  config: Record<string, unknown>;
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  results: T[];
  count: number;
  page: number;
  size: number;
  total_pages: number;
}

// Health types
export interface HealthStatus {
  status: "healthy" | "unhealthy";
  version: string;
  checks: {
    database: { status: string; type?: string; error?: string };
    mongodb: { status: string; connected: boolean; error?: string };
    redis: {
      status: string;
      connected: boolean;
      used_memory_human?: string;
      error?: string;
    };
    elasticsearch: {
      status: string;
      cluster_status?: string;
      error?: string;
    };
  };
}
