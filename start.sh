# 快速启动脚本

cd "$(dirname "$0")"

echo "🚀 启动AI知识库MVP..."

# 启动后端
echo "📦 启动后端服务..."
cd backend
pip install -q -r requirements.txt
python -c "from models.database import init_db; init_db()"
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
echo $! > backend.pid
echo "✅ 后端已启动 (PID: $(cat backend.pid))"

# 启动前端
echo "🎨 启动前端服务..."
cd ../frontend
npm install
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
