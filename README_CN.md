# 国内版配置说明

## 快速启动（国内优化版）

```bash
# 使用国内镜像安装依赖
cd backend && pip install -r requirements.cn.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 下载中文Embedding模型（国内镜像）
python scripts/download_models.py

# 启动服务
bash start.cn.sh
```

## 国内优化内容

### 1. PyPI镜像
- 使用清华镜像源
- 阿里云镜像备选

### 2. HuggingFace模型
- 使用魔搭社区ModelScope镜像
- 预下载脚本避免运行时下载

### 3. 中文Embedding模型
- 默认使用BGE中文模型
- 支持GTE、Piccolo等国产模型

### 4. npm镜像
- 使用淘宝镜像
- 或腾讯云镜像

## 支持的模型

| 模型 | 来源 | 维度 | 特点 |
|-----|-----|-----|-----|
| BAAI/bge-large-zh-v1.5 | 智源 | 1024 | 中文最优 |
| BAAI/bge-base-zh-v1.5 | 智源 | 768 | 轻量快速 |
| GanymedeNil/text2vec-large-chinese | 社区 | 1024 | 长文本好 |
| shibing624/text2vec-base-chinese | 社区 | 768 | 通用场景 |
