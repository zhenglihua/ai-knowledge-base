# CIM系统集成模块

## 模块概述

CIM（Computer Integrated Manufacturing）系统集成模块，用于连接和同步制造执行系统（MES）、设备自动化系统（EAP）和统计过程控制（SPC）数据。

## 功能模块

### 1. MES数据同步
- **工单管理** (`/api/cim/mes/work-orders`)
  - 工单创建、查询、更新
  - 工单状态跟踪（待执行、执行中、暂停、已完成、已取消、异常）
  - 生产记录追踪
  
- **工艺参数** (`/api/cim/mes/process-params`)
  - 工艺参数配置
  - 参数限制管理（最小值、最大值、目标值）

- **生产记录** (`/api/cim/mes/production-records`)
  - 产量记录
  - 良品/报废统计
  - 生产时间追踪

### 2. EAP设备数据
- **设备管理** (`/api/cim/eap/equipments`)
  - 设备基础信息
  - 设备状态监控（空闲、运行中、暂停、故障、维护中、离线）
  - 状态历史记录

- **报警管理** (`/api/cim/eap/alarms`)
  - 报警记录
  - 报警级别（info、warning、error、critical）
  - 报警处理追踪

- **运行参数** (`/api/cim/eap/equipments/{id}/runtime-params`)
  - 实时参数采集
  - 参数限制监控

### 3. SPC质量数据
- **控制图管理** (`/api/cim/spc/control-charts`)
  - 控制图定义（X-R、X-S、X-MR、P、NP、C、U等）
  - 控制限设置

- **数据点** (`/api/cim/spc/control-charts/{id}/data-points`)
  - 数据采集
  - 失控点标记

- **异常点** (`/api/cim/spc/anomalies`)
  - 异常检测
  - 异常处理追踪

### 4. 数据连接器
- **连接器管理** (`/api/cim/connectors`)
  - 支持数据库直连（MySQL、PostgreSQL、SQL Server、SQLite）
  - 支持API接入（RESTful API）
  - 字段映射配置

- **数据同步** (`/api/cim/connectors/{id}/sync`)
  - 手动同步
  - 同步日志查询

### 5. 数据看板
- **综合看板** (`/api/dashboard/overview`)
  - MES/EAP/SPC综合统计
  
- **生产看板** (`/api/dashboard/production`)
  - 工单趋势
  - 产量统计

- **设备看板** (`/api/dashboard/equipment`)
  - 设备状态分布
  - 报警趋势

- **质量看板** (`/api/dashboard/quality`)
  - 异常趋势
  - 控制图数据

- **KPI看板** (`/api/dashboard/kpi`)
  - 订单完成率
  - 设备稼动率
  - 良品率

## API端点汇总

### MES端点
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/cim/mes/work-orders` | 获取工单列表 |
| GET | `/api/cim/mes/work-orders/{id}` | 获取工单详情 |
| POST | `/api/cim/mes/work-orders` | 创建工单 |
| PUT | `/api/cim/mes/work-orders/{id}` | 更新工单 |
| GET | `/api/cim/mes/work-orders/{id}/production-summary` | 生产汇总 |
| GET | `/api/cim/mes/statistics` | MES统计 |

### EAP端点
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/cim/eap/equipments` | 获取设备列表 |
| GET | `/api/cim/eap/equipments/{id}` | 获取设备详情 |
| POST | `/api/cim/eap/equipments` | 创建设备 |
| PUT | `/api/cim/eap/equipments/{id}/status` | 更新设备状态 |
| GET | `/api/cim/eap/alarms` | 获取报警列表 |
| POST | `/api/cim/eap/alarms` | 创建报警 |
| PUT | `/api/cim/eap/alarms/{id}/clear` | 清除报警 |
| GET | `/api/cim/eap/equipments/{id}/runtime-params` | 获取运行参数 |
| GET | `/api/cim/eap/statistics` | EAP统计 |

### SPC端点
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/cim/spc/control-charts` | 获取控制图列表 |
| GET | `/api/cim/spc/control-charts/{id}` | 获取控制图详情 |
| GET | `/api/cim/spc/control-charts/{id}/data-points` | 获取数据点 |
| POST | `/api/cim/spc/control-charts/{id}/data-points` | 添加数据点 |
| GET | `/api/cim/spc/control-charts/{id}/control-limits` | 计算控制限 |
| GET | `/api/cim/spc/anomalies` | 获取异常点 |
| PUT | `/api/cim/spc/anomalies/{id}/clear` | 清除异常点 |
| GET | `/api/cim/spc/statistics` | SPC统计 |

### 连接器端点
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/cim/connectors` | 获取连接器列表 |
| GET | `/api/cim/connectors/{id}` | 获取连接器详情 |
| POST | `/api/cim/connectors` | 创建连接器 |
| PUT | `/api/cim/connectors/{id}` | 更新连接器 |
| DELETE | `/api/cim/connectors/{id}` | 删除连接器 |
| POST | `/api/cim/connectors/{id}/test` | 测试连接器 |
| POST | `/api/cim/connectors/{id}/sync` | 执行数据同步 |
| GET | `/api/cim/connectors/{id}/sync-logs` | 获取同步日志 |

### 看板端点
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/dashboard/overview` | 看板总览 |
| GET | `/api/dashboard/production` | 生产看板 |
| GET | `/api/dashboard/equipment` | 设备看板 |
| GET | `/api/dashboard/quality` | 质量看板 |
| GET | `/api/dashboard/kpi` | KPI看板 |
| GET | `/api/dashboard/widgets` | 获取组件列表 |
| POST | `/api/dashboard/widgets` | 创建组件 |
| PUT | `/api/dashboard/widgets/{id}` | 更新组件 |
| DELETE | `/api/dashboard/widgets/{id}` | 删除组件 |
| GET | `/api/dashboard/widgets/{id}/data` | 获取组件数据 |

## 数据库模型

### MES表
- `cim_work_orders` - 工单表
- `cim_process_parameters` - 工艺参数表
- `cim_production_records` - 生产记录表

### EAP表
- `cim_equipments` - 设备表
- `cim_equipment_status_history` - 设备状态历史表
- `cim_equipment_alarms` - 设备报警表
- `cim_equipment_runtime_params` - 设备运行参数表

### SPC表
- `cim_spc_control_charts` - 控制图表定义表
- `cim_spc_data_points` - 控制图数据点表
- `cim_spc_anomalies` - SPC异常点记录表

### 连接器表
- `cim_data_connectors` - 数据连接器配置表
- `cim_sync_logs` - 数据同步日志表

### 看板表
- `cim_dashboard_widgets` - 看板组件配置表

## 使用示例

### 创建工单
```bash
curl -X POST http://localhost:8000/api/cim/mes/work-orders \
  -H "Content-Type: application/json" \
  -d '{
    "wo_number": "WO20240326001",
    "product_code": "P001",
    "product_name": "测试产品",
    "quantity": 100,
    "priority": 5
  }'
```

### 创建设备
```bash
curl -X POST http://localhost:8000/api/cim/eap/equipments \
  -H "Content-Type: application/json" \
  -d '{
    "equipment_code": "EQ001",
    "equipment_name": "测试设备",
    "equipment_type": "印刷机",
    "area_code": "A01"
  }'
```

### 创建数据连接器
```bash
curl -X POST http://localhost:8000/api/cim/connectors \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MES数据库连接",
    "connector_type": "database",
    "config": {
      "db_type": "mysql",
      "host": "localhost",
      "port": 3306,
      "database": "mes_db",
      "username": "user",
      "password": "password"
    },
    "mapping_config": {
      "work_order_query": {
        "table": "work_orders",
        "where": "1=1"
      },
      "work_order_fields": {
        "wo_number": "wo_no",
        "product_code": "product_id",
        "quantity": "plan_qty"
      }
    }
  }'
```

### 执行数据同步
```bash
curl -X POST http://localhost:8000/api/cim/connectors/{id}/sync \
  -H "Content-Type: application/json" \
  -d '{
    "data_type": "work_order",
    "start_time": "2024-03-01T00:00:00",
    "end_time": "2024-03-26T23:59:59"
  }'
```

## 目录结构

```
cim_module/
├── __init__.py           # 模块导出
├── routes.py             # CIM API路由
├── dashboard_routes.py   # 看板API路由
├── services.py           # MES/EAP/SPC服务
├── sync_service.py       # 数据同步服务
└── connectors/
    ├── __init__.py       # 连接器导出
    ├── base.py           # 连接器基类
    ├── database.py       # 数据库连接器
    └── api.py            # API连接器
```

## 依赖

- FastAPI - Web框架
- SQLAlchemy - ORM
- aiohttp - 异步HTTP客户端（可选）
- pymysql - MySQL驱动
- psycopg2-binary - PostgreSQL驱动
- pymssql - SQL Server驱动
