// 角色权限管理服务

import { Role, Permission } from '../types/auth';

// 模拟权限数据
const ALL_PERMISSIONS: Permission[] = [
  // 系统管理
  { id: '1', name: '用户管理', code: 'user:manage', description: '管理用户账户', module: 'system' },
  { id: '2', name: '角色管理', code: 'role:manage', description: '管理角色权限', module: 'system' },
  { id: '3', name: '系统设置', code: 'system:config', description: '系统配置', module: 'system' },
  { id: '4', name: '日志查看', code: 'log:view', description: '查看系统日志', module: 'system' },
  
  // 文档管理
  { id: '5', name: '文档查看', code: 'doc:view', description: '查看文档', module: 'document' },
  { id: '6', name: '文档创建', code: 'doc:create', description: '创建新文档', module: 'document' },
  { id: '7', name: '文档编辑', code: 'doc:edit', description: '编辑文档', module: 'document' },
  { id: '8', name: '文档删除', code: 'doc:delete', description: '删除文档', module: 'document' },
  { id: '9', name: '文档审核', code: 'doc:audit', description: '审核文档', module: 'document' },
  { id: '10', name: '批量上传', code: 'doc:batch', description: '批量上传文档', module: 'document' },
  
  // AI功能
  { id: '11', name: '智能搜索', code: 'ai:search', description: '使用AI搜索', module: 'ai' },
  { id: '12', name: 'AI问答', code: 'ai:chat', description: 'AI对话功能', module: 'ai' },
  { id: '13', name: '数据分析', code: 'ai:analytics', description: '数据分析功能', module: 'ai' },
  
  // 数据统计
  { id: '14', name: '查看统计', code: 'stats:view', description: '查看统计数据', module: 'stats' },
  { id: '15', name: '导出报表', code: 'stats:export', description: '导出统计报表', module: 'stats' },
];

// 模拟角色数据
let MOCK_ROLES: Role[] = [
  {
    id: '1',
    name: '超级管理员',
    code: 'super_admin',
    description: '拥有系统所有权限',
    permissions: ALL_PERMISSIONS,
    status: 'active',
    createdAt: '2024-01-01 09:00:00',
  },
  {
    id: '2',
    name: '普通用户',
    code: 'user',
    description: '基础的文档查看和AI功能使用权限',
    permissions: ALL_PERMISSIONS.filter(p => 
      ['doc:view', 'ai:search', 'ai:chat', 'stats:view'].includes(p.code)
    ),
    status: 'active',
    createdAt: '2024-01-01 09:00:00',
  },
  {
    id: '3',
    name: '审核员',
    code: 'auditor',
    description: '负责文档审核工作',
    permissions: ALL_PERMISSIONS.filter(p => 
      ['doc:view', 'doc:audit', 'doc:edit', 'ai:search', 'ai:chat'].includes(p.code)
    ),
    status: 'active',
    createdAt: '2024-01-05 10:00:00',
  },
  {
    id: '4',
    name: '文档管理员',
    code: 'doc_admin',
    description: '管理文档内容和分类',
    permissions: ALL_PERMISSIONS.filter(p => 
      ['doc:view', 'doc:create', 'doc:edit', 'doc:delete', 'doc:batch', 'ai:search'].includes(p.code)
    ),
    status: 'active',
    createdAt: '2024-01-10 11:00:00',
  },
  {
    id: '5',
    name: '访客',
    code: 'visitor',
    description: '仅查看权限',
    permissions: ALL_PERMISSIONS.filter(p => p.code === 'doc:view'),
    status: 'active',
    createdAt: '2024-01-12 14:00:00',
  },
];

class RoleService {
  // 获取所有角色
  async getRoles(): Promise<Role[]> {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve([...MOCK_ROLES]);
      }, 300);
    });
  }

  // 获取单个角色
  async getRoleById(id: string): Promise<Role | null> {
    return new Promise((resolve) => {
      setTimeout(() => {
        const role = MOCK_ROLES.find(r => r.id === id);
        resolve(role ? { ...role } : null);
      }, 200);
    });
  }

  // 创建角色
  async createRole(roleData: Partial<Role>): Promise<Role> {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        if (MOCK_ROLES.some(r => r.code === roleData.code)) {
          reject(new Error('角色代码已存在'));
          return;
        }
        
        const newRole: Role = {
          id: String(Date.now()),
          name: roleData.name!,
          code: roleData.code!,
          description: roleData.description || '',
          permissions: roleData.permissions || [],
          status: roleData.status || 'active',
          createdAt: new Date().toISOString(),
        };
        
        MOCK_ROLES.push(newRole);
        resolve(newRole);
      }, 300);
    });
  }

  // 更新角色
  async updateRole(id: string, roleData: Partial<Role>): Promise<Role> {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const index = MOCK_ROLES.findIndex(r => r.id === id);
        if (index === -1) {
          reject(new Error('角色不存在'));
          return;
        }
        
        MOCK_ROLES[index] = { ...MOCK_ROLES[index], ...roleData };
        resolve(MOCK_ROLES[index]);
      }, 300);
    });
  }

  // 删除角色
  async deleteRole(id: string): Promise<void> {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const index = MOCK_ROLES.findIndex(r => r.id === id);
        if (index === -1) {
          reject(new Error('角色不存在'));
          return;
        }
        
        MOCK_ROLES.splice(index, 1);
        resolve();
      }, 300);
    });
  }

  // 获取所有权限
  async getAllPermissions(): Promise<Permission[]> {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve([...ALL_PERMISSIONS]);
      }, 200);
    });
  }

  // 更新角色权限
  async updateRolePermissions(roleId: string, permissionIds: string[]): Promise<void> {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const role = MOCK_ROLES.find(r => r.id === roleId);
        if (!role) {
          reject(new Error('角色不存在'));
          return;
        }
        
        role.permissions = ALL_PERMISSIONS.filter(p => permissionIds.includes(p.id));
        resolve();
      }, 300);
    });
  }

  // 获取按模块分组的权限
  async getPermissionsByModule(): Promise<Record<string, Permission[]>> {
    return new Promise((resolve) => {
      setTimeout(() => {
        const grouped: Record<string, Permission[]> = {};
        ALL_PERMISSIONS.forEach(p => {
          const module = p.module!;
          if (!grouped[module]) {
            grouped[module] = [];
          }
          grouped[module].push(p);
        });
        resolve(grouped);
      }, 200);
    });
  }
}

export const roleService = new RoleService();
export default roleService;