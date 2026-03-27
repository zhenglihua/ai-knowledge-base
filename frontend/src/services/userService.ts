// 用户管理服务

import { User } from '../types/auth';

// 模拟用户数据
let MOCK_USERS: User[] = [
  {
    id: '1',
    username: 'admin',
    email: 'admin@example.com',
    realName: '系统管理员',
    department: '技术部',
    phone: '13800138000',
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
    lastLoginAt: '2024-01-15 10:30:00',
    createdAt: '2024-01-01 09:00:00',
  },
  {
    id: '2',
    username: 'zhangsan',
    email: 'zhangsan@example.com',
    realName: '张三',
    department: '研发部',
    phone: '13800138001',
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
    lastLoginAt: '2024-01-14 16:45:00',
    createdAt: '2024-01-05 10:00:00',
  },
  {
    id: '3',
    username: 'lisi',
    email: 'lisi@example.com',
    realName: '李四',
    department: '运营部',
    phone: '13800138002',
    roles: [
      {
        id: '3',
        name: '审核员',
        code: 'auditor',
        description: '文档审核权限',
        permissions: [],
        status: 'active',
      }
    ],
    status: 'active',
    lastLoginAt: '2024-01-13 14:20:00',
    createdAt: '2024-01-08 11:30:00',
  },
  {
    id: '4',
    username: 'wangwu',
    email: 'wangwu@example.com',
    realName: '王五',
    department: '市场部',
    phone: '13800138003',
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
    status: 'inactive',
    lastLoginAt: '2024-01-10 09:15:00',
    createdAt: '2024-01-10 09:00:00',
  },
  {
    id: '5',
    username: 'zhaoliu',
    email: 'zhaoliu@example.com',
    realName: '赵六',
    department: '研发部',
    phone: '13800138004',
    roles: [
      {
        id: '4',
        name: '文档管理员',
        code: 'doc_admin',
        description: '文档管理权限',
        permissions: [],
        status: 'active',
      }
    ],
    status: 'active',
    lastLoginAt: '2024-01-12 11:00:00',
    createdAt: '2024-01-12 10:00:00',
  },
];

class UserService {
  // 获取用户列表
  async getUsers(params?: { keyword?: string; status?: string }): Promise<User[]> {
    return new Promise((resolve) => {
      setTimeout(() => {
        let result = [...MOCK_USERS];
        
        if (params?.keyword) {
          const keyword = params.keyword.toLowerCase();
          result = result.filter(user =>
            user.username.toLowerCase().includes(keyword) ||
            user.realName?.toLowerCase().includes(keyword) ||
            user.email.toLowerCase().includes(keyword) ||
            user.department?.toLowerCase().includes(keyword)
          );
        }
        
        if (params?.status) {
          result = result.filter(user => user.status === params.status);
        }
        
        resolve(result);
      }, 300);
    });
  }

  // 获取单个用户
  async getUserById(id: string): Promise<User | null> {
    return new Promise((resolve) => {
      setTimeout(() => {
        const user = MOCK_USERS.find(u => u.id === id);
        resolve(user || null);
      }, 200);
    });
  }

  // 创建用户
  async createUser(userData: Partial<User>): Promise<User> {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        if (MOCK_USERS.some(u => u.username === userData.username)) {
          reject(new Error('用户名已存在'));
          return;
        }
        if (MOCK_USERS.some(u => u.email === userData.email)) {
          reject(new Error('邮箱已被使用'));
          return;
        }
        
        const newUser: User = {
          id: String(Date.now()),
          username: userData.username!,
          email: userData.email!,
          realName: userData.realName,
          department: userData.department,
          phone: userData.phone,
          roles: userData.roles || [],
          status: userData.status || 'active',
          createdAt: new Date().toISOString(),
          ...userData,
        };
        
        MOCK_USERS.push(newUser);
        resolve(newUser);
      }, 300);
    });
  }

  // 更新用户
  async updateUser(id: string, userData: Partial<User>): Promise<User> {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const index = MOCK_USERS.findIndex(u => u.id === id);
        if (index === -1) {
          reject(new Error('用户不存在'));
          return;
        }
        
        MOCK_USERS[index] = { ...MOCK_USERS[index], ...userData };
        resolve(MOCK_USERS[index]);
      }, 300);
    });
  }

  // 删除用户
  async deleteUser(id: string): Promise<void> {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const index = MOCK_USERS.findIndex(u => u.id === id);
        if (index === -1) {
          reject(new Error('用户不存在'));
          return;
        }
        
        MOCK_USERS.splice(index, 1);
        resolve();
      }, 300);
    });
  }

  // 批量删除用户
  async batchDeleteUser(ids: string[]): Promise<void> {
    return new Promise((resolve) => {
      setTimeout(() => {
        MOCK_USERS = MOCK_USERS.filter(u => !ids.includes(u.id));
        resolve();
      }, 300);
    });
  }

  // 更新用户状态
  async updateUserStatus(id: string, status: 'active' | 'inactive'): Promise<void> {
    await this.updateUser(id, { status });
  }

  // 重置密码
  async resetPassword(id: string): Promise<string> {
    return new Promise((resolve) => {
      setTimeout(() => {
        // 生成随机密码
        const newPassword = Math.random().toString(36).slice(-8);
        resolve(newPassword);
      }, 300);
    });
  }

  // 分配角色
  async assignRoles(userId: string, roleIds: string[]): Promise<void> {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const user = MOCK_USERS.find(u => u.id === userId);
        if (!user) {
          reject(new Error('用户不存在'));
          return;
        }
        
        // 这里简化处理，实际应该根据roleIds获取完整的Role对象
        user.roles = roleIds.map(id => ({
          id,
          name: '角色' + id,
          code: 'role_' + id,
          description: '',
          permissions: [],
          status: 'active',
        }));
        
        resolve();
      }, 300);
    });
  }
}

export const userService = new UserService();
export default userService;