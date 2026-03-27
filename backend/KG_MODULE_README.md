# 知识图谱模块 (Knowledge Graph Module)

基于 FastAPI + NetworkX 的知识图谱后端模块，提供实体抽取、关系抽取、图谱存储和智能推荐功能。

## 功能特性

### 1. 实体抽取服务 (Entity Extraction)
从文档中自动提取以下类型的实体：
- **设备** (equipment): 光刻机、刻蚀机、沉积设备等半导体设备型号
- **工艺** (process): 光刻、刻蚀、沉积、清洗等工艺流程
- **材料** (material): Si, SiO2, 光刻胶、化学品等
- **参数** (parameter): 温度、压力、流量、功率等工艺参数
- **质量指标** (quality): 缺陷密度、良率、CD均匀性等
- **产品** (product): 芯片类型、技术节点等
- **部门/位置**: 生产相关的部门和设施

### 2. 关系抽取服务 (Relation Extraction)
识别实体间的语义关系：
- **使用** (uses): 设备使用材料/工艺
- **包含** (has_part): 设备包含部件
- **需要** (requires): 工艺需要参数/材料
- **产生** (produces): 工艺产生产品/材料
- **影响** (influences): 参数影响质量
- **测量** (measures): 设备测量参数/质量
- **描述** (describes): 文档描述实体
- **相关** (related_to): 一般关联

### 3. 知识图谱存储 (Graph Storage)
基于 NetworkX 的轻量级图谱存储：
- 实体和关系的CRUD操作
- 名称索引和模糊搜索
- 邻居节点查询
- 路径查找
- 连通分量分析
- 图谱统计
- 数据持久化（pickle格式）

### 4. 智能推荐 (Recommendation)
基于图谱的文档推荐系统：
- **内容推荐**: 基于共同实体的文档推荐
- **协同过滤**: 基于实体共现的推荐
- **混合推荐**: 结合内容和协同过滤
- **关键词推荐**: 基于关键词的文档推荐
- **实体推荐**: 推荐相关实体
- **热门实体**: 获取被最多文档提及的实体

## API 接口

### 实体抽取
```http
POST /api/kg/extract/entities
Content-Type: application/json

{
  "text": "ASML光刻机使用ArF激光...",
  "min_confidence": 0.5
}
```

### 关系抽取
```http
POST /api/kg/extract/relations
Content-Type: application/json

{
  "text": "ASML光刻机使用ArF激光...",
  "entities": [...],
  "min_confidence": 0.3
}
```

### 处理文档构建图谱
```http
POST /api/kg/documents/{doc_id}/process
```

### 搜索实体
```http
GET /api/kg/entities/search?keyword=ASML&entity_type=equipment&limit=20
```

### 获取实体详情
```http
GET /api/kg/entities/{entity_id}
```

### 获取实体邻居
```http
POST /api/kg/entities/{entity_id}/neighbors
Content-Type: application/json

{
  "relation_type": "uses",
  "depth": 2
}
```

### 查找路径
```http
POST /api/kg/path/find
Content-Type: application/json

{
  "source_id": "entity_1",
  "target_id": "entity_2",
  "max_depth": 5
}
```

### 文档推荐
```http
POST /api/kg/recommend/documents
Content-Type: application/json

{
  "doc_id": "doc_001",
  "keywords": ["光刻机", "刻蚀"],
  "limit": 5,
  "method": "hybrid"
}
```

### 图谱统计
```http
GET /api/kg/statistics
```

## 使用示例

### 基本使用
```python
from kg_module.services.entity_extraction import extract_entities
from kg_module.services.relation_extraction import extract_relations
from kg_module.services.kg_builder import get_kg_builder

# 抽取实体
text = "ASML TWINSCAN光刻机使用ArF激光，温度设置为120°C。"
result = extract_entities(text)

for entity in result.entities:
    print(f"{entity.type.value}: {entity.text}")

# 抽取关系
relations = extract_relations(text, result.entities)
for rel in relations:
    print(f"{rel.head_text} -{rel.type.value}-> {rel.tail_text}")

# 构建文档知识图谱
builder = get_kg_builder()
result = builder.process_document(
    doc_id="doc_001",
    text=text,
    title="光刻工艺说明"
)
print(f"添加了{result['added_entities']}个实体，{result['added_relations']}个关系")
```

### 图谱查询
```python
from kg_module.models.graph_store import get_graph_store

store = get_graph_store()

# 搜索实体
entities = store.search_entities("ASML", limit=10)

# 获取实体邻居
neighbors = store.get_neighbors(entity_id, depth=2)

# 查找路径
path = store.find_path(entity_a_id, entity_b_id)

# 获取统计
stats = store.get_statistics()
```

### 智能推荐
```python
from kg_module.services.recommendation import get_recommender

recommender = get_recommender()

# 文档推荐
recommendations = recommender.recommend_documents("doc_001", limit=5)

# 关键词推荐
recommendations = recommender.recommend_by_keywords(["光刻机", "刻蚀"])

# 获取热门实体
trending = recommender.get_trending_entities(limit=10)
```

## 目录结构
```
kg_module/
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── entity.py          # 实体、关系、抽取结果模型
│   └── graph_store.py     # NetworkX图谱存储
├── services/
│   ├── __init__.py
│   ├── entity_extraction.py    # 实体抽取服务
│   ├── relation_extraction.py  # 关系抽取服务
│   ├── kg_builder.py           # 知识图谱构建
│   └── recommendation.py       # 智能推荐
└── api/
    ├── __init__.py
    └── routes.py          # FastAPI路由
```

## 配置说明

### 环境变量
```bash
# 图谱存储路径（可选，默认data/knowledge_graph.pkl）
KG_STORAGE_PATH=data/knowledge_graph.pkl
```

### 实体类型
- `equipment`: 设备
- `process`: 工艺
- `material`: 材料
- `parameter`: 参数
- `quality`: 质量指标
- `product`: 产品
- `person`: 人员
- `department`: 部门
- `document`: 文档
- `location`: 位置
- `other`: 其他

### 关系类型
- `uses`: 使用
- `has_part`: 包含部件
- `part_of`: 属于
- `requires`: 需要
- `produces`: 产生
- `influences`: 影响
- `measures`: 测量
- `describes`: 描述
- `related_to`: 相关

## 依赖
- networkx>=2.8
- fastapi>=0.104
- sqlalchemy>=2.0

## 安装
```bash
pip install networkx
```

## 测试
```bash
python test_kg_module.py
```