# 用户权限管理模块

## 功能概览

用户权限管理模块提供完整的认证、授权、角色管理和审计日志功能。

### 核心功能

1. **用户认证**
   - 登录 / 注册 / 登出
   - JWT Token认证（Access Token + Refresh Token）
   - 密码加密存储（bcrypt）

2. **角色管理**
   - 超级管理员 (super_admin)
   - 部门管理员 (dept_admin)
   - 工程师 (engineer)
   - 访客 (visitor)

3. **权限控制**
   - 基于角色的访问控制（RBAC）
   - 细粒度权限定义（文档操作、用户管理、系统配置）

4. **数据分级**
   - 公开 (1) - 所有用户可见
   - 内部 (2) - 内部用户可见
   - 机密 (3) - 部门管理员及以上
   - 绝密 (4) - 仅超级管理员

5. **操作审计日志**
   - 记录所有访问、下载、编辑操作
   - 支持按用户、时间、操作类型查询
   - 文档访问单独记录

## API端点列表

### 认证API

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/auth/login` | 用户登录 |
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/logout` | 用户登出 |
| POST | `/api/auth/refresh` | 刷新Access Token |
| GET  | `/api/auth/me` | 获取当前用户信息 |
| POST | `/api/auth/change-password` | 修改密码 |

### 用户管理API

| 方法 | 端点 | 描述 | 所需权限 |
|------|------|------|----------|
| GET  | `/api/users` | 获取用户列表 | user:view |
| POST | `/api/users` | 创建用户 | user:create |
| GET  | `/api/users/{id}` | 获取用户详情 | user:view |
| PUT  | `/api/users/{id}` | 更新用户信息 | user:edit |
| DELETE | `/api/users/{id}` | 删除用户 | user:delete |
| POST | `/api/users/{id}/reset-password` | 重置用户密码 | user:edit |

### 审计日志API

| 方法 | 端点 | 描述 | 所需权限 |
|------|------|------|----------|
| GET  | `/api/audit/logs` | 查询操作日志 | sys:audit |
| GET  | `/api/audit/document-logs` | 查询文档访问日志 | sys:audit |
| GET  | `/api/audit/statistics` | 获取审计统计 | sys:audit |

## 数据库模型

### User (用户表)
- id: 用户唯一标识
- username: 用户名
- email: 邮箱
- hashed_password: 加密密码
- full_name: 姓名
- department: 部门
- role: 角色
- is_active: 是否激活
- last_login: 最后登录时间

### Role (角色表)
- id: 角色标识
- name: 角色名称
- description: 描述
- is_system: 是否系统预设

### Permission (权限表)
- id: 权限标识
- code: 权限代码（如 doc:view）
- name: 权限名称
- module: 所属模块

### AuditLog (审计日志表)
- id: 日志ID
- user_id/username: 用户信息
- action: 操作类型
- module/resource_type/resource_id: 操作对象
- ip_address/user_agent: 访问信息
- created_at: 操作时间

### DocumentAccessLog (文档访问日志表)
- user_id: 用户ID
- document_id/title/classification: 文档信息
- action: 操作类型（view/download/edit/delete/upload）
- created_at: 访问时间

## 角色权限映射

### 超级管理员 (super_admin)
- 所有文档操作权限
- 用户管理权限
- 角色管理权限
- 系统配置权限
- 最高密级访问权限（绝密）

### 部门管理员 (dept_admin)
- 文档查看、上传、编辑、下载
- 部门用户管理
- 统计数据查看
- 密级访问权限（机密）

### 工程师 (engineer)
- 文档查看、上传、下载
- 密级访问权限（内部）

### 访客 (visitor)
- 仅文档查看
- 密级访问权限（公开）

## 使用方法

### 1. 安装依赖

```bash
pip install -r requirements.txt
pip install -r requirements.auth.txt
```

### 2. 初始化数据库

```bash
cd /Users/zheng/.openclaw/workspace/ai-knowledge-base/mvp/backend
python init_auth.py
```

这将创建：
- 认证相关数据库表
- 默认管理员账号 (admin/admin123)

### 3. 启动服务

```bash
python main.py
```

### 4. 测试API

```bash
# 注册用户
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"test123"}'

# 登录
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"test123"}'

# 使用Token访问受保护资源
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 测试用例

运行测试：

```bash
pytest test_auth.py -v
```

测试覆盖：
- 密码加密与验证
- JWT Token创建与解码
- 用户注册/登录
- 权限控制
- 审计日志

## 安全注意事项

1. **生产环境请修改默认密码**
2. **更换 JWT_SECRET_KEY 环境变量**
3. **使用 HTTPS 传输**
4. **定期清理过期Token**
5. **审计日志定期归档**
