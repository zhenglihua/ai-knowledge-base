# CIMBrain 私有化部署指南

## 概述

CIMBrain 支持两种私有化部署方式：

| 部署方式 | 适用场景 | 并发用户 | 复杂度 |
|---------|---------|---------|--------|
| **Docker Compose** | 单机部署 | ≤50 | 低 |
| **Kubernetes Helm** | 集群部署 | ≥50 | 中高 |

## 快速开始

### 方式一: Docker Compose (单机部署)

#### 前置条件
- Docker 20.10+
- Docker Compose 2.0+

#### 安装步骤

```bash
# 1. 进入部署目录
cd deploy/docker

# 2. 复制配置模板
cp .env.example .env
# 编辑 .env 配置密码

# 3. 启动服务
docker-compose up -d

# 4. 检查状态
docker-compose ps
```

#### 访问地址
- 前端界面: http://localhost:3000
- API 文档: http://localhost:8000/docs
- MinIO 控制台: http://localhost:9001

---

### 方式二: Kubernetes Helm (集群部署)

#### 前置条件
- Kubernetes 1.20+
- Helm 3.0+
- PV/PVC 存储供应

#### 安装步骤

```bash
# 1. 添加 Helm 仓库 (或使用本地 Chart)
helm repo add cimbrain https://charts.cimbrain.example.com

# 2. 创建命名空间
kubectl create namespace cimbrain

# 3. 安装 Chart
helm install cimbrain ./deploy/k8s/helm/cimbrain \
  -n cimbrain \
  -f deploy/k8s/helm/cimbrain/values.yaml

# 4. 检查状态
kubectl get pods -n cimbrain
```

#### 配置自定义

```bash
# 创建配置覆盖文件
cat > my-values.yaml << EOF
frontend:
  ingress:
    hosts:
      - host: cimbrain.yourcompany.com

backend:
  env:
    LLM_PROVIDER: "qwen"
    QWEN_API_KEY: "your-api-key"
EOF

# 使用自定义配置安装
helm upgrade --install cimbrain ./deploy/k8s/helm/cimbrain \
  -n cimbrain \
  -f my-values.yaml
```

---

## 离线安装 (Air-Gapped)

### Docker 镜像导出/导入

```bash
# 在有网络的机器上导出
docker save $(docker images -q cimbrain/*) | gzip > cimbrain-images.tar.gz

# 在离线环境中导入
docker load < cimbrain-images.tar.gz
```

### 使用离线脚本

```bash
chmod +x deploy/docker/install-offline.sh
./deploy/docker/install-offline.sh
```

---

## 配置参考

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `POSTGRES_PASSWORD` | 数据库密码 | (必填) |
| `MINIO_ACCESS_KEY` | MinIO 用户名 | (必填) |
| `MINIO_SECRET_KEY` | MinIO 密码 | (必填) |
| `LLM_PROVIDER` | LLM 提供商 | `ollama` |
| `OLLAMA_HOST` | Ollama 地址 | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama 模型 | `qwen2.5:7b` |

### 端口配置

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端 | 3000 | React 应用 |
| 后端 API | 8000 | FastAPI |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6379 | 缓存 |
| MinIO API | 9000 | S3 兼容 |
| MinIO Console | 9001 | Web 控制台 |

---

## 运维命令

### Docker Compose

```bash
# 查看日志
docker-compose logs -f backend

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 重建服务
docker-compose up -d --force-recreate
```

### Kubernetes

```bash
# 查看 Pods
kubectl get pods -n cimbrain

# 查看日志
kubectl logs -f deployment/cimbrain-backend -n cimbrain

# 进入容器
kubectl exec -it deployment/cimbrain-backend -n cimbrain -- /bin/sh

# 扩缩容
kubectl scale deployment cimbrain-backend -n cimbrain --replicas=3

# 升级版本
helm upgrade cimbrain ./deploy/k8s/helm/cimbrain -n cimbrain
```

---

## 数据备份

### Docker 环境

```bash
# 备份数据库
docker exec cimbrain-postgres pg_dump -U cimbrain cimbrain > backup.sql

# 备份文件存储
tar -czf uploads-backup.tar.gz uploads/
```

### Kubernetes 环境

```bash
# 使用 Velero 备份
velero backup create cimbrain-backup --include-namespaces cimbrain
```

---

## 卸载

### Docker Compose

```bash
docker-compose down -v  # -v 会删除数据卷
rm -rf uploads/ data/
```

### Kubernetes

```bash
helm uninstall cimbrain -n cimbrain
kubectl delete namespace cimbrain
```

---

## 国产化适配

### 支持的配置

| 类别 | 支持选项 |
|------|---------|
| CPU | x86 (Intel/AMD), ARM (鲲鹏, 飞腾) |
| 操作系统 | Ubuntu 20.04+, 银河麒麟 V10, 统信 UOS |
| 数据库 | PostgreSQL, 人大金仓, 达梦 |
| 容器平台 | Docker, Kubernetes, 麒麟容器云 |

### 注意事项

1. **ARM 架构**: 使用 `values-arm64.yaml` 配置
2. **国产数据库**: 修改 `database.url` 连接字符串
3. **离线模式**: 需提前导入 Docker 镜像

---

## 技术支持

- 文档: https://docs.cimbrain.example.com
- 问题反馈: support@cimbrain.example.com
