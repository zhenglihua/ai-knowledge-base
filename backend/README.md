# AI知识库MVP - 后端服务

AI知识库后端服务，提供文档管理、智能检索和AI问答功能。

## 🏗️ 项目结构

```
backend/
├── main.py                    # 主应用入口 (FastAPI)
├── requirements.txt           # 依赖列表
├── requirements.cn.txt        # 国内镜像依赖
├── batch_upload_api.py        # 批量上传API (已合并到main.py)
├── models/
│   └── database.py            # 数据库模型 (SQLite)
├── services/
│   ├── document_parser.py     # 基础文档解析器
│   ├── document_parser_v2.py  # 增强版文档解析器 ⭐新增
│   ├── vector_store.py        # 基础向量存储
│   ├── ai_service.py          # AI服务
│   └── rag_service.py         # 增强版RAG服务 ⭐新增
├── scripts/
│   └── download_models.py     # 模型下载脚本
└── data/                      # 数据存储目录
    ├── vector_store.json      # 向量数据
    └── vector_store_enhanced.json  # 增强版向量数据
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 使用默认源
pip install -r requirements.txt

# 或使用国内镜像（推荐）
pip install -r requirements.cn.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. 启动服务

```bash
cd backend
python main.py
```

服务将启动在: http://localhost:8000

API文档: http://localhost:8000/docs

### 3. 运行测试

```bash
python test_api.py
```

## 📚 API端点

### 文档管理

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/documents/upload` | 单文件上传 |
| POST | `/api/documents/batch-upload` | 批量上传 |
| GET | `/api/documents` | 获取文档列表 |
| GET | `/api/documents/{doc_id}` | 获取文档详情 |
| DELETE | `/api/documents/{doc_id}` | 删除文档 |

### 搜索与问答

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/search` | 语义搜索 |
| POST | `/api/chat` | AI问答 |

### 系统

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/docs` | API文档 (Swagger UI) |

## 🔧 核心功能

### 1. 文档解析服务 (document_parser_v2.py)

**支持的文件类型:**
- PDF (.pdf)
- Word (.docx, .doc)
- 文本 (.txt, .md)
- JSON (.json)
- CSV (.csv)
- Excel (.xlsx, .xls)

**特性:**
- 智能文本分块（支持重叠）
- 按段落/句子分块
- 详细的解析元数据

### 2. 向量存储服务 (rag_service.py)

**特性:**
- 基于 sentence-transformers 的语义向量化
- 智能文档分块存储
- 支持重排序的搜索结果
- 文档过滤功能
- 持久化存储

### 3. RAG问答服务 (rag_service.py)

**特性:**
- 上下文检索优化
- 支持对话历史
- 引用来源追踪
- 本地/云端AI模式切换

## 🔌 数据模型

### Document (文档)

```python
{
    "id": "uuid",
    "filename": "原始文件名",
    "title": "文档标题",
    "content": "文档内容",
    "category": "分类",
    "tags": "标签",
    "file_path": "存储路径",
    "file_size": "文件大小",
    "file_type": "文件类型",
    "status": "active/processing/error",
    "created_at": "创建时间",
    "updated_at": "更新时间"
}
```

## 🔐 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENAI_API_KEY` | OpenAI API密钥 | 无（使用本地模式） |

## 📊 使用示例

### 上传文档

```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@process.pdf" \
  -F "category=工艺文档"
```

### AI问答

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "什么是光刻工艺？"}'
```

### 搜索

```bash
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{"keyword": "刻蚀", "limit": 5}'
```

## 📝 开发计划

- [x] 基础文档上传和解析
- [x] 批量上传API
- [x] 向量存储和语义搜索
- [x] AI问答RAG流程
- [x] 增强版文档解析器
- [x] 增强版RAG服务
- [ ] 对话历史持久化
- [ ] 用户权限管理
- [ ] 文档版本控制

## 🐛 故障排除

### 模型下载失败

```bash
python scripts/download_models.py
```

### 依赖安装问题

如果使用国内镜像仍有问题，尝试：
```bash
pip install torch transformers -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 内存不足

如果加载模型时内存不足，可以：
1. 使用更小的模型
2. 修改 `rag_service.py` 中的模型名称
3. 使用简单向量化模式（自动降级）
