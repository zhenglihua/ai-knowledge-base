# 半导体工厂AI知识库 - MVP

快速启动命令：
```bash
# 1. 安装依赖
cd backend && pip install -r requirements.txt

# 2. 启动后端
uvicorn main:app --reload --port 8000

# 3. 启动前端（新终端）
cd frontend && npm install && npm start
```

## 功能特性
- 📄 文档上传（PDF/Word/TXT）
- 🔍 智能搜索（关键词+语义）
- 🤖 AI问答（RAG模式）
- 📊 文档管理

## 技术栈
- 后端：FastAPI + SQLite + Sentence Transformers
- 前端：React + TypeScript + Ant Design
- AI：本地Embedding + OpenAI API（可选）

## 国内用户使用
```bash
# 使用国内镜像一键启动
chmod +x start.cn.sh && ./start.cn.sh
```

国内优化：
- PyPI清华镜像源
- npm淘宝镜像
- HuggingFace魔搭社区镜像
- 预置中文Embedding模型

## 自动化测试
```bash
# 运行全部测试
chmod +x test.sh && ./test.sh

# 或手动测试
cd e2e && npm install && npx playwright test
```

测试覆盖：
- API接口测试
- 前端功能E2E测试
- 集成测试
