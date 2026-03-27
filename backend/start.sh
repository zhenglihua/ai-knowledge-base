#!/bin/bash
# AI知识库MVP - 快速启动脚本

echo "🚀 启动AI知识库后端服务..."

# 检查Python
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "❌ 未找到Python，请先安装Python 3.8+"
    exit 1
fi

echo "✅ 使用Python: $PYTHON"

# 检查依赖
echo "📦 检查依赖..."
$PYTHON -c "import fastapi" 2>/dev/null || {
    echo "⚠️ 依赖未安装，正在安装..."
    pip install -r requirements.txt
}

# 创建必要目录
mkdir -p uploads data

# 启动服务
echo "🌐 启动服务..."
echo "   API地址: http://localhost:8000"
echo "   文档地址: http://localhost:8000/docs"
echo "   按 Ctrl+C 停止服务"
echo ""

$PYTHON main.py
