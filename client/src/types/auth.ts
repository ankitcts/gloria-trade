export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  account_status: string;
  group_ids: string[];
  extra_permissions: string[];
  email_verified: boolean;
  phone_verified: boolean;
  last_login_at: string | null;
  login_count: number;
  created_at: string;
  updated_at: string;
}

export interface AdminUserDetail extends User {
  phone: string | null;
  display_name: string | null;
  timezone: string;
  preferred_locale: string;
}

export interface UserGroup {
  id: string;
  name: string;
  description: string | null;
  permissions: string[];
  member_ids: string[];
  member_count: number;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  first_name: string;
  last_name: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
}
