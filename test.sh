#!/bin/bash
# 自动化测试脚本

cd "$(dirname "$0")"

echo "🧪 AI知识库MVP自动化测试"
echo "========================================"

# 检查服务是否运行
echo "📡 检查服务状态..."

# 检查后端口
if ! curl -s http://localhost:8000/api/health > /dev/null; then
    echo "❌ 后端服务未启动，请先运行 ./start.sh"
    exit 1
fi

if ! curl -s http://localhost:3000 > /dev/null; then
    echo "❌ 前端服务未启动，请先运行 ./start.sh"
    exit 1
fi

echo "✅ 服务运行正常"
echo ""

# API测试
echo "🔌 API接口测试..."

# 1. 健康检查
echo "  - 健康检查..."
curl -s http://localhost:8000/api/health | grep -q "ok" && echo "    ✅ 通过" || echo "    ❌ 失败"

# 2. 获取文档列表
echo "  - 文档列表接口..."
curl -s http://localhost:8000/api/documents | grep -q "documents" && echo "    ✅ 通过" || echo "    ❌ 失败"

# 3. 搜索接口
echo "  - 搜索接口..."
curl -s -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"keyword":"测试"}' | grep -q "results" && echo "    ✅ 通过" || echo "    ❌ 失败"

# 4. 聊天接口
echo "  - AI问答接口..."
curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"你好"}' | grep -q "answer" && echo "    ✅ 通过" || echo "    ❌ 失败"

echo ""

# E2E测试
echo "🎭 Playwright E2E测试..."
cd e2e

# 检查playwright是否安装
if ! command -v npx &> /dev/null; then
    echo "⚠️ 未安装npx，跳过E2E测试"
else
    # 安装playwright依赖
    if [ ! -d "node_modules" ]; then
        echo "  安装测试依赖..."
        npm install -D @playwright/test
        npx playwright install chromium
    fi
    
    # 运行测试
    echo "  运行E2E测试..."
    npx playwright test mvp.spec.js --reporter=line
fi

echo ""
echo "========================================"
echo "✅ 自动化测试完成"
echo "========================================"
