#!/bin/bash
# RAGFlow 集成后端启动脚本
# 使用虚拟环境确保ragflow-sdk可用

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PATH="/Users/zheng/.openclaw/workspace/ragflow_env"
PORT=8000

echo "🚀 启动AI知识库后端服务 (RAGFlow集成版)..."

# 检查虚拟环境
if [ ! -d "$VENV_PATH" ]; then
    echo "📦 创建虚拟环境..."
    python3.14 -m venv "$VENV_PATH"
fi

# 安装依赖
echo "📦 安装依赖..."
"$VENV_PATH/bin/pip" install -q ragflow-sdk sqlalchemy pymysql fastapi uvicorn python-multipart aiofiles pydantic-settings

# 激活虚拟环境并启动
echo "🌐 启动服务 on port $PORT..."
cd "$SCRIPT_DIR"
"$VENV_PATH/bin/python3.14" main.py > server.log 2>&1 &

echo "✅ 服务已启动 (PID: $!)"
echo "   API: http://localhost:$PORT"
echo "   文档: http://localhost:$PORT/docs"
