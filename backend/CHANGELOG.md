# AI知识库后端 - 更新日志

## v2.0.0 - 新功能发布

### 1. 对话历史API ✅

新增完整的对话管理功能：

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/conversations` | POST | 创建新对话 |
| `/api/conversations` | GET | 获取对话列表（支持分页） |
| `/api/conversations/{id}` | GET | 获取对话详情和消息 |
| `/api/conversations/{id}` | DELETE | 删除对话 |
| `/api/conversations/{id}` | PATCH | 更新对话标题 |
| `/api/conversations/{id}/messages` | POST | 添加消息 |

**特性：**
- 支持多用户（user_id）
- 自动保存对话标题（从第一轮问题生成）
- 消息包含角色、内容、来源、延迟等信息
- 级联删除对话及其消息

### 2. 流式响应支持 ✅

新增SSE流式响应端点：

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/chat/stream` | POST | 流式AI问答 |

**特性：**
- 使用Server-Sent Events (SSE) 协议
- 实时返回生成的文本片段
- 包含开始/内容/结束事件类型
- 自动保存完整对话记录

**示例请求：**
```json
{
  "query": "什么是半导体制造？",
  "conversation_id": "可选的对话ID"
}
```

**响应格式：**
```
data: {"type": "start", "message_id": "xxx"}
data: {"type": "content", "text": "半导体制造..."}
data: {"type": "end", "sources": [...], "latency_ms": 1500}
```

### 3. 数据统计API ✅

新增完整的统计功能：

| 端点 | 描述 |
|------|------|
| `/api/stats/dashboard` | 仪表盘综合统计 |
| `/api/stats/documents` | 文档统计详情 |
| `/api/stats/chats` | 问答统计详情 |
| `/api/stats/users` | 用户活跃度统计 |
| `/api/stats/search-trends` | 搜索趋势分析 |
| `/api/stats/daily-update` | 手动更新每日统计 |

**统计维度：**
- 📊 文档：总数、今日上传、分类分布、文件类型、大小统计
- 💬 问答：总问题数、今日问答、延迟分布、热门话题
- 👤 用户：活跃用户、活动分布、每日活跃趋势
- 🔍 搜索：关键词频率、搜索趋势

### 4. 后端性能优化 ✅

#### 4.1 数据库优化
- 添加数据库连接池配置
- 使用 `check_same_thread=False` 支持多线程
- 添加会话上下文管理器

#### 4.2 缓存机制
- 新增内存缓存模块 (`services/cache.py`)
- 支持缓存装饰器
- 缓存过期策略

#### 4.3 压缩传输
- 添加GZip中间件
- 最小压缩阈值：1000字节

#### 4.4 应用生命周期管理
- 使用 `lifespan` 管理启动和关闭
- 全局服务状态管理

### 5. 其他改进

- **健康检查增强**：包含数据库状态、统计数据
- **用户活动追踪**：自动记录上传、搜索、问答活动
- **延迟统计**：记录每个AI回答的响应时间
- **API版本升级**：v1.0.0 → v2.0.0

## 数据库变更

新增表：
- `conversations` - 对话会话
- `chat_messages` - 聊天消息
- `user_activities` - 用户活动日志
- `daily_stats` - 每日统计

## API测试

使用测试脚本验证所有功能：
```bash
python test_new_api.py
```

## 启动服务

```bash
python main.py
```

服务将自动初始化数据库和向量库。