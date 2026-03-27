"""
CIM系统集成模块 - 数据库模型
包含MES、EAP、SPC相关数据表
"""
from sqlalchemy import Column, String, Text, DateTime, Integer, Float, Boolean, ForeignKey, JSON, Enum, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

from models.database import Base, engine, SessionLocal

# ============== MES数据模型 ==============

class WorkOrderStatus(enum.Enum):
    """工单状态枚举"""
    PENDING = "pending"           # 待执行
    RUNNING = "running"           # 执行中
    PAUSED = "paused"             # 暂停
    COMPLETED = "completed"       # 已完成
    CANCELLED = "cancelled"       # 已取消
    ERROR = "error"               # 异常

class WorkOrder(Base):
    """MES工单信息表"""
    __tablename__ = 'cim_work_orders'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    wo_number = Column(String(50), nullable=False, unique=True, index=True)  # 工单号
    product_code = Column(String(50), nullable=False, index=True)  # 产品代码
    product_name = Column(String(200))  # 产品名称
    lot_number = Column(String(50), index=True)  # 批次号
    quantity = Column(Integer, default=0)  # 计划数量
    completed_qty = Column(Integer, default=0)  # 已完成数量
    status = Column(String(20), default=WorkOrderStatus.PENDING.value)  # 状态
    priority = Column(Integer, default=5)  # 优先级 1-10
    
    # 工艺路线
    process_flow_id = Column(String(36))  # 工艺路线ID
    current_step = Column(Integer, default=0)  # 当前步骤
    total_steps = Column(Integer, default=0)  # 总步骤数
    
    # 时间信息
    planned_start = Column(DateTime)  # 计划开始时间
    planned_end = Column(DateTime)  # 计划结束时间
    actual_start = Column(DateTime)  # 实际开始时间
    actual_end = Column(DateTime)  # 实际结束时间
    
    # 设备信息
    assigned_equipment = Column(String(50))  # 分配的设备
    assigned_station = Column(String(50))  # 分配的工位
    
    # 元数据
    source_system = Column(String(50), default='MES')  # 来源系统
    external_id = Column(String(100))  # 外部系统ID
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    process_params = relationship("ProcessParameter", back_populates="work_order", cascade="all, delete-orphan")
    production_records = relationship("ProductionRecord", back_populates="work_order", cascade="all, delete-orphan")

class ProcessParameter(Base):
    """工艺参数表 - 存储每个工单的工艺参数设置"""
    __tablename__ = 'cim_process_parameters'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    wo_id = Column(String(36), ForeignKey('cim_work_orders.id'), nullable=False)
    process_step = Column(Integer, default=0)  # 工艺步骤
    step_name = Column(String(100))  # 步骤名称
    
    # 参数定义
    param_code = Column(String(50), nullable=False)  # 参数代码
    param_name = Column(String(100))  # 参数名称
    param_value = Column(String(200))  # 参数值
    param_unit = Column(String(20))  # 单位
    
    # 参数限制
    min_value = Column(Float)  # 最小值
    max_value = Column(Float)  # 最大值
    target_value = Column(Float)  # 目标值
    
    # 元数据
    is_critical = Column(Boolean, default=False)  # 是否关键参数
    source_system = Column(String(50), default='MES')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    work_order = relationship("WorkOrder", back_populates="process_params")

class ProductionRecord(Base):
    """生产记录表 - 记录每个工单的生产详情"""
    __tablename__ = 'cim_production_records'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    wo_id = Column(String(36), ForeignKey('cim_work_orders.id'), nullable=False)
    record_type = Column(String(20), default='normal')  # normal, rework, scrap
    
    # 产量信息
    quantity = Column(Integer, default=0)  # 生产数量
    good_qty = Column(Integer, default=0)  # 良品数量
    scrap_qty = Column(Integer, default=0)  # 报废数量
    
    # 时间信息
    start_time = Column(DateTime)  # 开始时间
    end_time = Column(DateTime)  # 结束时间
    duration_minutes = Column(Integer)  # 持续时间(分钟)
    
    # 操作信息
    operator_id = Column(String(50))  # 操作员工号
    operator_name = Column(String(100))  # 操作员姓名
    station_id = Column(String(50))  # 工位ID
    equipment_id = Column(String(50))  # 设备ID
    
    # 备注
    remarks = Column(Text)
    
    # 元数据
    source_system = Column(String(50), default='MES')
    external_id = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)
    
    work_order = relationship("WorkOrder", back_populates="production_records")


# ============== EAP设备数据模型 ==============

class EquipmentStatus(enum.Enum):
    """设备状态枚举"""
    IDLE = "idle"                 # 空闲
    RUNNING = "running"           # 运行中
    PAUSED = "paused"             # 暂停
    ERROR = "error"               # 故障
    MAINTENANCE = "maintenance"   # 维护中
    OFFLINE = "offline"           # 离线

class Equipment(Base):
    """设备基础信息表"""
    __tablename__ = 'cim_equipments'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    equipment_code = Column(String(50), nullable=False, unique=True, index=True)  # 设备编码
    equipment_name = Column(String(200))  # 设备名称
    equipment_type = Column(String(50))  # 设备类型
    
    # 位置信息
    area_code = Column(String(50))  # 区域代码
    area_name = Column(String(100))  # 区域名称
    line_code = Column(String(50))  # 产线代码
    station_code = Column(String(50))  # 工位代码
    
    # 设备规格
    model = Column(String(100))  # 型号
    manufacturer = Column(String(100))  # 制造商
    serial_number = Column(String(100))  # 序列号
    purchase_date = Column(DateTime)  # 购买日期
    
    # 状态
    status = Column(String(20), default=EquipmentStatus.IDLE.value)  # 当前状态
    is_active = Column(Boolean, default=True)  # 是否启用
    
    # 元数据
    source_system = Column(String(50), default='EAP')
    external_id = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    status_history = relationship("EquipmentStatusHistory", back_populates="equipment", cascade="all, delete-orphan")
    alarms = relationship("EquipmentAlarm", back_populates="equipment", cascade="all, delete-orphan")
    runtime_params = relationship("EquipmentRuntimeParam", back_populates="equipment", cascade="all, delete-orphan")

class EquipmentStatusHistory(Base):
    """设备状态历史记录表"""
    __tablename__ = 'cim_equipment_status_history'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    equipment_id = Column(String(36), ForeignKey('cim_equipments.id'), nullable=False)
    
    # 状态信息
    status = Column(String(20), nullable=False)  # 状态值
    previous_status = Column(String(20))  # 上一状态
    
    # 时间信息
    start_time = Column(DateTime, nullable=False)  # 状态开始时间
    end_time = Column(DateTime)  # 状态结束时间
    duration_minutes = Column(Integer)  # 持续时间
    
    # 原因
    reason_code = Column(String(50))  # 原因代码
    reason_description = Column(String(200))  # 原因描述
    
    # 关联工单
    wo_id = Column(String(36))  # 关联工单ID
    
    # 元数据
    source_system = Column(String(50), default='EAP')
    created_at = Column(DateTime, default=datetime.now)
    
    equipment = relationship("Equipment", back_populates="status_history")

class EquipmentAlarm(Base):
    """设备报警信息表"""
    __tablename__ = 'cim_equipment_alarms'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    equipment_id = Column(String(36), ForeignKey('cim_equipments.id'), nullable=False)
    
    # 报警信息
    alarm_code = Column(String(50), nullable=False)  # 报警代码
    alarm_level = Column(String(20), default='warning')  # 级别: info, warning, error, critical
    alarm_category = Column(String(50))  # 报警类别
    alarm_message = Column(String(500))  # 报警内容
    
    # 时间信息
    occur_time = Column(DateTime, nullable=False)  # 发生时间
    clear_time = Column(DateTime)  # 清除时间
    is_cleared = Column(Boolean, default=False)  # 是否已清除
    
    # 处理信息
    handled_by = Column(String(100))  # 处理人
    handle_time = Column(DateTime)  # 处理时间
    handle_result = Column(Text)  # 处理结果
    
    # 关联工单
    wo_id = Column(String(36))
    
    # 元数据
    source_system = Column(String(50), default='EAP')
    external_id = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)
    
    equipment = relationship("Equipment", back_populates="alarms")

class EquipmentRuntimeParam(Base):
    """设备运行参数表 - 实时或准实时的设备参数"""
    __tablename__ = 'cim_equipment_runtime_params'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    equipment_id = Column(String(36), ForeignKey('cim_equipments.id'), nullable=False)
    
    # 参数信息
    param_code = Column(String(50), nullable=False)  # 参数代码
    param_name = Column(String(100))  # 参数名称
    param_value = Column(Float)  # 数值
    param_unit = Column(String(20))  # 单位
    param_type = Column(String(20))  # 类型: temperature, pressure, speed, etc.
    
    # 限制值
    min_limit = Column(Float)  # 下限
    max_limit = Column(Float)  # 上限
    target_value = Column(Float)  # 目标值
    
    # 时间戳
    timestamp = Column(DateTime, nullable=False)  # 数据采集时间
    
    # 元数据
    source_system = Column(String(50), default='EAP')
    created_at = Column(DateTime, default=datetime.now)
    
    equipment = relationship("Equipment", back_populates="runtime_params")


# ============== SPC质量数据模型 ==============

class SPCControlChart(Base):
    """SPC控制图表定义表"""
    __tablename__ = 'cim_spc_control_charts'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chart_code = Column(String(50), nullable=False, unique=True)  # 控制图代码
    chart_name = Column(String(200))  # 控制图名称
    chart_type = Column(String(20), nullable=False)  # X-R, X-S, X-MR, P, NP, C, U等
    
    # 监控对象
    product_code = Column(String(50))  # 产品代码
    process_code = Column(String(50))  # 工序代码
    param_code = Column(String(50))  # 参数代码
    param_name = Column(String(100))  # 参数名称
    
    # 控制限
    ucl = Column(Float)  # 上控制限
    lcl = Column(Float)  # 下控制限
    usl = Column(Float)  # 上规格限
    lsl = Column(Float)  # 下规格限
    target = Column(Float)  # 目标值
    
    # 采样设置
    sample_size = Column(Integer, default=5)  # 样本容量
    sample_freq = Column(Integer)  # 采样频率(分钟)
    
    # 状态
    is_active = Column(Boolean, default=True)  # 是否启用
    
    # 元数据
    source_system = Column(String(50), default='SPC')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    data_points = relationship("SPCDataPoint", back_populates="chart", cascade="all, delete-orphan")
    anomalies = relationship("SPCAnomaly", back_populates="chart", cascade="all, delete-orphan")

class SPCDataPoint(Base):
    """SPC数据点表 - 控制图数据"""
    __tablename__ = 'cim_spc_data_points'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chart_id = Column(String(36), ForeignKey('cim_spc_control_charts.id'), nullable=False)
    
    # 样本信息
    sample_no = Column(Integer, nullable=False)  # 样本序号
    sample_time = Column(DateTime, nullable=False)  # 采样时间
    lot_number = Column(String(50))  # 批次号
    
    # 统计值
    x_value = Column(Float)  # 均值/单值
    r_value = Column(Float)  # 极差
    s_value = Column(Float)  # 标准差
    
    # 原始数据(JSON存储)
    raw_values = Column(JSON)  # [v1, v2, v3, ...]
    
    # 判定
    is_out_of_control = Column(Boolean, default=False)  # 是否失控
    violation_rules = Column(JSON)  # 违反的规则列表
    
    # 关联工单
    wo_id = Column(String(36))
    
    # 元数据
    source_system = Column(String(50), default='SPC')
    created_at = Column(DateTime, default=datetime.now)
    
    chart = relationship("SPCControlChart", back_populates="data_points")

class SPCAnomaly(Base):
    """SPC异常点记录表"""
    __tablename__ = 'cim_spc_anomalies'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chart_id = Column(String(36), ForeignKey('cim_spc_control_charts.id'), nullable=False)
    data_point_id = Column(String(36), ForeignKey('cim_spc_data_points.id'))
    
    # 异常信息
    anomaly_type = Column(String(50), nullable=False)  # 异常类型
    anomaly_rule = Column(String(20), nullable=False)  # 违反的规则编号
    severity = Column(String(20), default='warning')  # 严重程度
    description = Column(String(500))  # 异常描述
    
    # 数值信息
    measured_value = Column(Float)  # 测量值
    limit_value = Column(Float)  # 界限值
    deviation = Column(Float)  # 偏差
    
    # 时间信息
    occur_time = Column(DateTime, nullable=False)  # 发生时间
    clear_time = Column(DateTime)  # 解除时间
    is_cleared = Column(Boolean, default=False)  # 是否已解除
    
    # 处理信息
    handled_by = Column(String(100))  # 处理人
    handle_time = Column(DateTime)  # 处理时间
    handle_action = Column(Text)  # 处理措施
    root_cause = Column(Text)  # 根本原因
    
    # 关联工单
    wo_id = Column(String(36))
    
    # 元数据
    source_system = Column(String(50), default='SPC')
    created_at = Column(DateTime, default=datetime.now)
    
    chart = relationship("SPCControlChart", back_populates="anomalies")


# ============== 数据连接器配置模型 ==============

class ConnectorType(enum.Enum):
    """连接器类型枚举"""
    DATABASE = "database"  # 数据库连接
    API = "api"            # API连接
    MQTT = "mqtt"          # MQTT消息
    OPCUA = "opcua"        # OPC UA

class ConnectorStatus(enum.Enum):
    """连接器状态枚举"""
    ACTIVE = "active"      # 活跃
    INACTIVE = "inactive"  # 非活跃
    ERROR = "error"        # 错误
    TESTING = "testing"    # 测试中

class DataConnector(Base):
    """数据连接器配置表"""
    __tablename__ = 'cim_data_connectors'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)  # 连接器名称
    connector_type = Column(String(20), nullable=False)  # 类型
    description = Column(Text)  # 描述
    
    # 连接配置(JSON存储)
    config = Column(JSON, default=dict)  # 连接配置
    # 示例: 
    # database: {"host": "...", "port": 3306, "database": "...", "username": "..."}
    # api: {"base_url": "...", "auth_type": "...", "headers": {...}}
    
    # 数据映射配置
    mapping_config = Column(JSON, default=dict)  # 字段映射配置
    
    # 同步配置
    sync_interval = Column(Integer, default=300)  # 同步间隔(秒)
    last_sync_time = Column(DateTime)  # 最后同步时间
    
    # 状态
    status = Column(String(20), default=ConnectorStatus.INACTIVE.value)
    is_enabled = Column(Boolean, default=True)
    
    # 错误信息
    last_error = Column(Text)
    error_count = Column(Integer, default=0)
    
    # 元数据
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    sync_logs = relationship("SyncLog", back_populates="connector", cascade="all, delete-orphan")

class SyncLog(Base):
    """数据同步日志表"""
    __tablename__ = 'cim_sync_logs'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    connector_id = Column(String(36), ForeignKey('cim_data_connectors.id'), nullable=False)
    
    # 同步信息
    sync_type = Column(String(20), default='auto')  # auto, manual
    sync_direction = Column(String(10), default='pull')  # pull, push
    
    # 数据范围
    data_type = Column(String(50))  # 数据类型: work_order, equipment_status, etc.
    start_time = Column(DateTime)  # 数据开始时间
    end_time = Column(DateTime)  # 数据结束时间
    
    # 结果统计
    records_total = Column(Integer, default=0)  # 总记录数
    records_inserted = Column(Integer, default=0)  # 插入数
    records_updated = Column(Integer, default=0)  # 更新数
    records_failed = Column(Integer, default=0)  # 失败数
    
    # 状态
    status = Column(String(20), default='running')  # running, success, failed, partial
    
    # 错误信息
    error_message = Column(Text)
    error_details = Column(JSON)
    
    # 耗时
    started_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)
    
    connector = relationship("DataConnector", back_populates="sync_logs")


# ============== 数据看板配置模型 ==============

class DashboardWidget(Base):
    """看板组件配置表"""
    __tablename__ = 'cim_dashboard_widgets'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)  # 组件名称
    widget_type = Column(String(50), nullable=False)  # 组件类型
    # line_chart, bar_chart, pie_chart, gauge, table, kpi_card, etc.
    
    # 布局配置
    dashboard_id = Column(String(50), default='default')  # 所属看板
    position_x = Column(Integer, default=0)
    position_y = Column(Integer, default=0)
    width = Column(Integer, default=6)
    height = Column(Integer, default=4)
    
    # 数据源配置
    data_source = Column(JSON, default=dict)  # 数据源配置
    # {
    #   "type": "table|api|sql",
    #   "source": "cim_work_orders",
    #   "filter": {...},
    #   "aggregation": "count|sum|avg",
    #   "group_by": ["status"]
    # }
    
    # 显示配置
    display_config = Column(JSON, default=dict)  # 显示配置
    # {
    #   "title": "工单统计",
    #   "colors": ["#1890ff", "#52c41a"],
    #   "show_legend": true,
    #   "refresh_interval": 60
    # }
    
    # 状态
    is_enabled = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    
    # 元数据
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


def init_cim_tables():
    """初始化CIM相关数据表"""
    Base.metadata.create_all(engine, tables=[
        WorkOrder.__table__,
        ProcessParameter.__table__,
        ProductionRecord.__table__,
        Equipment.__table__,
        EquipmentStatusHistory.__table__,
        EquipmentAlarm.__table__,
        EquipmentRuntimeParam.__table__,
        SPCControlChart.__table__,
        SPCDataPoint.__table__,
        SPCAnomaly.__table__,
        DataConnector.__table__,
        SyncLog.__table__,
        DashboardWidget.__table__,
    ])
    print("✅ CIM数据表初始化完成")
