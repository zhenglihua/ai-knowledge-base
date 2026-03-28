#!/bin/bash
# CIMBrain 离线安装脚本
# 适用于物理隔离网络环境 (Air-Gapped)
#
# 使用方式:
#   chmod +x install-offline.sh
#   ./install-offline.sh
#
# 前置条件:
#   1. Docker 已安装并启动
#   2. Docker 镜像已导入: docker load < cimbrain-images.tar.gz

set -e

echo "=========================================="
echo "  CIMBrain 离线安装脚本"
echo "=========================================="

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker 未启动"
    exit 1
fi

echo "✅ Docker 检查通过"

# 检查镜像文件
if [ -f "cimbrain-images.tar.gz" ]; then
    echo "📦 导入 Docker 镜像..."
    docker load < cimbrain-images.tar.gz
    echo "✅ 镜像导入完成"
else
    echo "⚠️ 未找到镜像文件 cimbrain-images.tar.gz"
    echo "   如需离线安装，请先导出镜像:"
    echo "   docker save \$(docker images -q) | gzip > cimbrain-images.tar.gz"
fi

# 复制配置模板
if [ ! -f ".env" ]; then
    echo "📝 创建配置文件..."
    cp deploy/docker/.env.example .env
    echo "✅ 配置文件已创建: .env"
    echo "   请编辑 .env 文件配置参数"
else
    echo "✅ 配置文件已存在"
fi

# 创建数据目录
echo "📁 创建数据目录..."
mkdir -p uploads
mkdir -p data/postgres
mkdir -p data/redis
mkdir -p data/minio
chmod -R 777 uploads data

echo "✅ 数据目录创建完成"

# 启动服务
echo "🚀 启动服务..."
docker-compose up -d

echo ""
echo "=========================================="
echo "  安装完成!"
echo "=========================================="
echo ""
echo "服务状态:"
docker-compose ps
echo ""
echo "访问地址:"
echo "  前端界面: http://localhost:3000"
echo "  API 文档: http://localhost:8000/docs"
echo "  MinIO 控制台: http://localhost:9001"
echo ""
echo "管理命令:"
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo ""
