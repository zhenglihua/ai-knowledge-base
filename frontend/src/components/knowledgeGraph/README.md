# 知识图谱前端模块

## 功能概述

知识图谱前端模块提供了以下功能：

### 1. 知识图谱可视化
- 使用 ECharts 实现交互式关系图谱
- 支持节点点击、双击展开
- 支持缩放、拖拽、全屏查看
- 图例显示不同类型的实体
- 节点悬停显示详细信息

### 2. 实体搜索页面
- 关键词搜索实体
- 按实体类型筛选
- 搜索结果列表展示
- 点击实体查看详情抽屉
- 抽屉内展示关系图谱和关联关系

### 3. 关系探索
- 查看实体的入向/出向关系
- 显示关系类型和置信度
- 点击关联实体跳转
- 关系图谱可视化

### 4. 智能推荐组件
- 基于内容的推荐
- 基于共同出现的推荐
- 显示推荐原因
- 推荐置信度评分

### 5. 图谱管理页面
- 图谱统计数据展示
- 实体类型分布
- 操作记录时间线
- 数据导入/导出功能

## 技术栈

- React 18
- TypeScript
- Ant Design 5
- ECharts 5 + echarts-for-react
- React Router 6

## 文件结构

```
src/
├── components/knowledgeGraph/
│   ├── KnowledgeGraphVisualizer.tsx  # 图谱可视化组件
│   ├── EntityDetailCard.tsx          # 实体详情卡片
│   ├── RelationList.tsx              # 关系列表组件
│   ├── RecommendationPanel.tsx       # 推荐面板组件
│   ├── EntitySearch.tsx              # 实体搜索组件
│   └── index.ts                      # 组件导出
├── pages/
│   ├── KnowledgeGraph.tsx            # 知识图谱主页面
│   ├── EntitySearchPage.tsx          # 实体搜索页面
│   └── GraphManagement.tsx           # 图谱管理页面
├── services/
│   └── knowledgeGraphService.ts      # 知识图谱服务
├── types/
│   └── knowledgeGraph.ts             # 类型定义
└── data/
    └── mockKnowledgeGraph.ts         # Mock数据
```

## 实体类型

- **equipment** (蓝色) - 设备
- **process** (绿色) - 工艺
- **material** (黄色) - 材料
- **parameter** (紫色) - 参数
- **document** (粉色) - 文档
- **person** (青色) - 人员
- **organization** (橙色) - 组织
- **location** (深蓝) - 位置

## 关系类型

- **uses** (蓝色) - 使用
- **requires** (黄色) - 需要
- **produces** (绿色) - 产出
- **part_of** (紫色) - 属于
- **located_at** (青色) - 位于
- **operated_by** (粉色) - 操作者
- **related_to** (灰色) - 相关
- **references** (橙色) - 引用

## 使用说明

### 安装依赖

```bash
cd /Users/zheng/.openclaw/workspace/ai-knowledge-base/mvp/frontend
npm install echarts echarts-for-react
```

### 启动开发服务器

```bash
npm start
```

### 访问页面

- 知识图谱可视化: `/knowledge-graph`
- 实体搜索: `/entity-search`
- 图谱管理: `/graph-management`

## API 接口

服务层提供了以下API接口（支持mock数据回退）：

- `getStats()` - 获取图谱统计
- `getGraphData(centerId?, depth?)` - 获取图谱数据
- `searchEntities(params)` - 搜索实体
- `getEntityById(id)` - 获取实体详情
- `getEntityRelations(entityId)` - 获取实体关系
- `getRecommendations(entityId?, limit?)` - 获取推荐
- `getOperations(limit?)` - 获取操作记录

## Mock数据

当后端API不可用时，服务会自动使用mock数据，包括：
- 8个示例实体（设备、工艺、材料、参数、文档）
- 6个示例关系
- 示例统计数据
- 示例操作记录
- 示例推荐数据
