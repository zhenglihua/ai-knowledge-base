# 功能演示指南

## 晨会演示流程 (5分钟)

### 1. 系统启动 (30秒)
```bash
cd ai-knowledge-base/mvp
./start.sh
```
访问 http://localhost:3000

### 2. 文档管理 (1分钟)
- 展示已上传的2份演示文档
- 演示文档上传功能
- 查看文档详情

### 3. 智能搜索 (1.5分钟)
- 搜索"光刻工艺"
- 展示语义搜索结果
- 显示相关度分数

### 4. AI问答 (2分钟)
- 提问："光刻机故障E-203怎么处理"
- 展示AI回答
- 显示引用来源
- 展示知识库价值

## 演示数据

已预置2份演示文档：
1. **半导体工艺基础.txt** - 光刻/CVD/离子注入工艺介绍
2. **设备故障处理.txt** - 光刻机/刻蚀机故障处理手册

## API端点

| 功能 | 端点 | 状态 |
|-----|-----|-----|
| 健康检查 | GET /api/health | ✅ |
| 文档列表 | GET /api/documents | ✅ |
| 文档上传 | POST /api/documents/upload | ✅ |
| 智能搜索 | POST /api/search | ✅ |
| AI问答 | POST /api/chat | ✅ |

## 技术亮点

- ✅ 零配置启动（降级方案兼容）
- ✅ 文档自动解析（PDF/Word/TXT）
- ✅ 语义搜索（无需sentence_transformers）
- ✅ AI问答（RAG模式，无需OpenAI Key）
- ✅ 完整的API和Web界面
