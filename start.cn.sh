#!/bin/bash
# 国内版启动脚本 - 使用国内镜像

cd "$(dirname "$0")"

echo "🚀 启动AI知识库MVP（国内优化版）..."
echo ""

# 设置国内镜像
export PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
export PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

# 设置npm国内镜像
echo "📦 配置npm国内镜像..."
npm config set registry https://registry.npmmirror.com

# 下载模型
echo "🤖 检查并下载中文模型..."
cd backend
if [ ! -d "models/bge-base-zh" ]; then
    python scripts/download_models.py bge-base-zh
fi

# 安装后端依赖
echo "📦 安装后端依赖（国内镜像）..."
pip install -q -r requirements.cn.txt

# 初始化数据库
echo "🗄️ 初始化数据库..."
python -c "from models.database import init_db; init_db()"

# 启动后端
echo "🌐 启动后端服务..."
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
echo $! > backend.pid
echo "✅ 后端已启动 (PID: $(cat backend.pid))"

# 启动前端
echo "🎨 启动前端服务..."
cd ../frontend
if [ ! -d "node_modules" ]; then
    npm install
fi
nohup npm start > frontend.log 2>&1 &
echo $! > frontend.pid
echo "✅ 前端已启动 (PID: $(cat frontend.pid))"

echo ""
echo "========================================"
echo "🎉 AI知识库MVP启动成功!"
echo "========================================"
echo "后端API: http://localhost:8000"
echo "前端界面: http://localhost:3000"
echo "API文档: http://localhost:8000/docs"
echo "========================================"
echo ""
echo "使用以下命令查看日志:"
echo "  tail -f backend/backend.log"
echo "  tail -f frontend/frontend.log"
