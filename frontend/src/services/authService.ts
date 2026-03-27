// 认证服务 - 处理登录、注册、Token管理等

import { LoginRequest, RegisterRequest, AuthResponse, User, CurrentUser } from '../types/auth';

const AUTH_TOKEN_KEY = 'auth_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const USER_INFO_KEY = 'user_info';

// 模拟用户数据
const MOCK_USERS: User[] = [
  {
    id: '1',
    username: 'admin',
    email: 'admin@example.com',
    realName: '系统管理员',
    department: '技术部',
    roles: [
      {
        id: '1',
        name: '超级管理员',
        code: 'super_admin',
        description: '拥有所有权限',
        permissions: [],
        status: 'active',
      }
    ],
    status: 'active',
    lastLoginAt: new Date().toISOString(),
    createdAt: new Date().toISOString(),
  },
  {
    id: '2',
    username: 'user',
    email: 'user@example.com',
    realName: '普通用户',
    department: '运营部',
    roles: [
      {
        id: '2',
        name: '普通用户',
        code: 'user',
        description: '基础权限',
        permissions: [],
        status: 'active',
      }
    ],
    status: 'active',
    lastLoginAt: new Date().toISOString(),
    createdAt: new Date().toISOString(),
  }
];

class AuthService {
  // 登录
  async login(data: LoginRequest): Promise<AuthResponse> {
    // 模拟API调用
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const user = MOCK_USERS.find(u => u.username === data.username);
        if (user && data.password === '123456') {
          const response: AuthResponse = {
            token: 'mock_token_' + Date.now(),
            refreshToken: 'mock_refresh_token_' + Date.now(),
            expiresIn: 7200,
            user: user,
          };
          this.setAuth(response);
          resolve(response);
        } else {
          reject(new Error('用户名或密码错误'));
        }
      }, 500);
    });
  }

  // 注册
  async register(data: RegisterRequest): Promise<AuthResponse> {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        if (MOCK_USERS.some(u => u.username === data.username)) {
          reject(new Error('用户名已存在'));
          return;
        }
        if (MOCK_USERS.some(u => u.email === data.email)) {
          reject(new Error('邮箱已被注册'));
          return;
        }
        
        const newUser: User = {
          id: String(MOCK_USERS.length + 1),
          username: data.username,
          email: data.email,
          phone: data.phone,
          roles: [
            {
              id: '2',
              name: '普通用户',
              code: 'user',
              description: '基础权限',
              permissions: [],
              status: 'active',
            }
          ],
          status: 'active',
          createdAt: new Date().toISOString(),
        };
        MOCK_USERS.push(newUser);
        
        const response: AuthResponse = {
          token: 'mock_token_' + Date.now(),
          refreshToken: 'mock_refresh_token_' + Date.now(),
          expiresIn: 7200,
          user: newUser,
        };
        this.setAuth(response);
        resolve(response);
      }, 500);
    });
  }

  // 登出
  async logout(): Promise<void> {
    this.clearAuth();
    return Promise.resolve();
  }

  // 获取当前用户信息
  async getCurrentUser(): Promise<CurrentUser | null> {
    const userStr = localStorage.getItem(USER_INFO_KEY);
    if (userStr) {
      return JSON.parse(userStr);
    }
    return null;
  }

  // 更新用户信息
  async updateUserInfo(data: Partial<User>): Promise<User> {
    return new Promise((resolve) => {
      setTimeout(() => {
        const currentUser = this.getUserFromStorage();
        if (currentUser) {
          const updatedUser = { ...currentUser, ...data };
          localStorage.setItem(USER_INFO_KEY, JSON.stringify(updatedUser));
          resolve(updatedUser);
        } else {
          throw new Error('用户未登录');
        }
      }, 300);
    });
  }

  // 修改密码
  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        if (oldPassword === '123456') {
          resolve();
        } else {
          reject(new Error('原密码错误'));
        }
      }, 300);
    });
  }

  // 存储认证信息
  setAuth(response: AuthResponse): void {
    localStorage.setItem(AUTH_TOKEN_KEY, response.token);
    localStorage.setItem(REFRESH_TOKEN_KEY, response.refreshToken);
    localStorage.setItem(USER_INFO_KEY, JSON.stringify(response.user));
  }

  // 清除认证信息
  clearAuth(): void {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_INFO_KEY);
  }

  // 获取Token
  getToken(): string | null {
    return localStorage.getItem(AUTH_TOKEN_KEY);
  }

  // 判断是否已登录
  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  // 从存储获取用户信息
  private getUserFromStorage(): User | null {
    const userStr = localStorage.getItem(USER_INFO_KEY);
    if (userStr) {
      return JSON.parse(userStr);
    }
    return null;
  }
}

export const authService = new AuthService();
export default authService;
