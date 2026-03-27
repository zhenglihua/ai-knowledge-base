// 认证相关类型定义

export interface User {
  id: string;
  username: string;
  email: string;
  phone?: string;
  realName?: string;
  department?: string;
  avatar?: string;
  roles: Role[];
  status?: 'active' | 'inactive' | 'locked';
  createdAt?: string;
  updatedAt?: string;
  lastLoginAt?: string;
}

export interface Role {
  id: string;
  name: string;
  code: string;
  description?: string;
  permissions: Permission[];
  status: 'active' | 'inactive';
  createdAt?: string;
  updatedAt?: string;
}

export interface Permission {
  id: string;
  name: string;
  code: string;
  type?: 'menu' | 'button' | 'api';
  parentId?: string;
  path?: string;
  icon?: string;
  sort?: number;
  status?: 'active' | 'inactive';
  description?: string;
  module?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
  captcha?: string;
  remember?: boolean;
}

export interface RegisterRequest {
  username: string;
  password: string;
  email: string;
  phone?: string;
  realName?: string;
  department?: string;
}

export interface AuthResponse {
  token: string;
  refreshToken: string;
  expiresIn: number;
  user: User;
}

export interface CurrentUser {
  id: string;
  username: string;
  email: string;
  realName?: string;
  avatar?: string;
  roles: Role[];
  permissions: string[];
}

export interface PasswordChangeRequest {
  oldPassword: string;
  newPassword: string;
  confirmPassword: string;
}