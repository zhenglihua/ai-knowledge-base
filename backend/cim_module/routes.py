"""
CIM系统集成API路由
包含MES、EAP、SPC、数据连接器的RESTful API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import asyncio

from models.database import get_db
from models.cim_models import (
    WorkOrderStatus, EquipmentStatus, ConnectorType, ConnectorStatus
)
from cim_module.services import MESService, EAPService, SPCService
from cim_module.sync_service import SyncService

router = APIRouter(prefix="/api/cim", tags=["CIM集成"])

# ============== Pydantic模型 ==============

class WorkOrderCreate(BaseModel):
    wo_number: str
    product_code: str
    product_name: Optional[str] = None
    lot_number: Optional[str] = None
    quantity: int = 0
    priority: int = 5
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    assigned_equipment: Optional[str] = None
    process_flow_id: Optional[str] = None

class WorkOrderUpdate(BaseModel):
    status: Optional[str] = None
    quantity: Optional[int] = None
    completed_qty: Optional[int] = None
    priority: Optional[int] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None

class EquipmentCreate(BaseModel):
    equipment_code: str
    equipment_name: str
    equipment_type: Optional[str] = None
    area_code: Optional[str] = None
    area_name: Optional[str] = None
    line_code: Optional[str] = None
    model: Optional[str] = None
    manufacturer: Optional[str] = None

class AlarmCreate(BaseModel):
    equipment_id: str
    alarm_code: str
    alarm_level: str = "warning"
    alarm_category: Optional[str] = None
    alarm_message: str

class AlarmClear(BaseModel):
    handled_by: str
    handle_result: str

class DataPointCreate(BaseModel):
    chart_id: str
    sample_no: int
    sample_time: datetime
    x_value: float
    r_value: Optional[float] = None
    raw_values: Optional[List[float]] = None
    lot_number: Optional[str] = None

class AnomalyClear(BaseModel):
    handled_by: str
    handle_action: str
    root_cause: str

class ConnectorCreate(BaseModel):
    name: str
    connector_type: str
    description: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    mapping_config: Dict[str, Any] = Field(default_factory=dict)
    sync_interval: int = 300

class ConnectorUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    mapping_config: Optional[Dict[str, Any]] = None
    sync_interval: Optional[int] = None
    is_enabled: Optional[bool] = None

class SyncRequest(BaseModel):
    data_type: str  # work_order, equipment_status, equipment_alarm, spc_data_point
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

# ============== MES API ==============

@router.get("/mes/work-orders")
def list_work_orders(
    status: Optional[str] = None,
    product_code: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """获取工单列表"""
    service = MESService(db)
    items, total = service.get_work_orders(
        status=status,
        product_code=product_code,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": item.id,
                "wo_number": item.wo_number,
                "product_code": item.product_code,
                "product_name": item.product_name,
                "lot_number": item.lot_number,
                "quantity": item.quantity,
                "completed_qty": item.completed_qty,
                "status": item.status,
                "priority": item.priority,
                "planned_start": item.planned_start.isoformat() if item.planned_start else None,
                "planned_end": item.planned_end.isoformat() if item.planned_end else None,
                "actual_start": item.actual_start.isoformat() if item.actual_start else None,
                "actual_end": item.actual_end.isoformat() if item.actual_end else None,
                "assigned_equipment": item.assigned_equipment,
                "source_system": item.source_system,
                "created_at": item.created_at.isoformat()
            }
            for item in items
        ]
    }

@router.get("/mes/work-orders/{wo_id}")
def get_work_order(wo_id: str, db: Session = Depends(get_db)):
    """获取工单详情"""
    service = MESService(db)
    wo = service.get_work_order_by_id(wo_id)
    
    if not wo:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    return {
        "id": wo.id,
        "wo_number": wo.wo_number,
        "product_code": wo.product_code,
        "product_name": wo.product_name,
        "lot_number": wo.lot_number,
        "quantity": wo.quantity,
        "completed_qty": wo.completed_qty,
        "status": wo.status,
        "priority": wo.priority,
        "process_flow_id": wo.process_flow_id,
        "current_step": wo.current_step,
        "total_steps": wo.total_steps,
        "planned_start": wo.planned_start.isoformat() if wo.planned_start else None,
        "planned_end": wo.planned_end.isoformat() if wo.planned_end else None,
        "actual_start": wo.actual_start.isoformat() if wo.actual_start else None,
        "actual_end": wo.actual_end.isoformat() if wo.actual_end else None,
        "assigned_equipment": wo.assigned_equipment,
        "assigned_station": wo.assigned_station,
        "source_system": wo.source_system,
        "created_at": wo.created_at.isoformat(),
        "updated_at": wo.updated_at.isoformat()
    }

@router.post("/mes/work-orders")
def create_work_order(data: WorkOrderCreate, db: Session = Depends(get_db)):
    """创建工单"""
    service = MESService(db)
    wo = service.create_work_order(data.dict())
    return {"id": wo.id, "message": "工单创建成功"}

@router.put("/mes/work-orders/{wo_id}")
def update_work_order(wo_id: str, data: WorkOrderUpdate, db: Session = Depends(get_db)):
    """更新工单"""
    service = MESService(db)
    wo = service.update_work_order(wo_id, data.dict(exclude_unset=True))
    
    if not wo:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    return {"id": wo.id, "message": "工单更新成功"}

@router.get("/mes/work-orders/{wo_id}/production-summary")
def get_production_summary(wo_id: str, db: Session = Depends(get_db)):
    """获取工单生产汇总"""
    service = MESService(db)
    wo = service.get_work_order_by_id(wo_id)
    
    if not wo:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    summary = service.get_production_summary(wo_id)
    return summary

@router.get("/mes/statistics")
def get_mes_statistics(db: Session = Depends(get_db)):
    """获取MES统计信息"""
    service = MESService(db)
    stats = service.get_wo_statistics()
    return stats

# ============== EAP API ==============

@router.get("/eap/equipments")
def list_equipments(
    status: Optional[str] = None,
    area_code: Optional[str] = None,
    equipment_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取设备列表"""
    service = EAPService(db)
    items = service.get_equipments(
        status=status,
        area_code=area_code,
        equipment_type=equipment_type
    )
    
    return {
        "total": len(items),
        "items": [
            {
                "id": item.id,
                "equipment_code": item.equipment_code,
                "equipment_name": item.equipment_name,
                "equipment_type": item.equipment_type,
                "area_code": item.area_code,
                "area_name": item.area_name,
                "line_code": item.line_code,
                "model": item.model,
                "manufacturer": item.manufacturer,
                "status": item.status,
                "is_active": item.is_active,
                "created_at": item.created_at.isoformat()
            }
            for item in items
        ]
    }

@router.get("/eap/equipments/{equipment_id}")
def get_equipment(equipment_id: str, db: Session = Depends(get_db)):
    """获取设备详情"""
    service = EAPService(db)
    equipment = service.get_equipment_by_id(equipment_id)
    
    if not equipment:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    return {
        "id": equipment.id,
        "equipment_code": equipment.equipment_code,
        "equipment_name": equipment.equipment_name,
        "equipment_type": equipment.equipment_type,
        "area_code": equipment.area_code,
        "area_name": equipment.area_name,
        "line_code": equipment.line_code,
        "station_code": equipment.station_code,
        "model": equipment.model,
        "manufacturer": equipment.manufacturer,
        "serial_number": equipment.serial_number,
        "status": equipment.status,
        "is_active": equipment.is_active,
        "created_at": equipment.created_at.isoformat()
    }

@router.post("/eap/equipments")
def create_equipment(data: EquipmentCreate, db: Session = Depends(get_db)):
    """创建设备"""
    service = EAPService(db)
    equipment = service.create_equipment(data.dict())
    return {"id": equipment.id, "message": "设备创建成功"}

@router.put("/eap/equipments/{equipment_id}/status")
def update_equipment_status(
    equipment_id: str,
    status: str,
    reason: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """更新设备状态"""
    service = EAPService(db)
    equipment = service.update_equipment_status(equipment_id, status, reason)
    
    if not equipment:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    return {"id": equipment.id, "status": equipment.status, "message": "状态更新成功"}

@router.get("/eap/alarms")
def list_alarms(
    equipment_id: Optional[str] = None,
    alarm_level: Optional[str] = None,
    is_cleared: Optional[bool] = None,
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """获取报警列表"""
    service = EAPService(db)
    start_time = datetime.now() - timedelta(hours=hours)
    
    items = service.get_alarms(
        equipment_id=equipment_id,
        alarm_level=alarm_level,
        is_cleared=is_cleared,
        start_date=start_time,
        limit=limit
    )
    
    return {
        "total": len(items),
        "time_range_hours": hours,
        "items": [
            {
                "id": item.id,
                "equipment_id": item.equipment_id,
                "equipment_code": item.equipment.equipment_code if item.equipment else None,
                "alarm_code": item.alarm_code,
                "alarm_level": item.alarm_level,
                "alarm_category": item.alarm_category,
                "alarm_message": item.alarm_message,
                "occur_time": item.occur_time.isoformat(),
                "clear_time": item.clear_time.isoformat() if item.clear_time else None,
                "is_cleared": item.is_cleared,
                "handled_by": item.handled_by,
                "handle_result": item.handle_result
            }
            for item in items
        ]
    }

@router.post("/eap/alarms")
def create_alarm(data: AlarmCreate, db: Session = Depends(get_db)):
    """创建报警"""
    service = EAPService(db)
    data_dict = data.dict()
    data_dict['occur_time'] = datetime.now()
    alarm = service.create_alarm(data_dict)
    return {"id": alarm.id, "message": "报警创建成功"}

@router.put("/eap/alarms/{alarm_id}/clear")
def clear_alarm(alarm_id: str, data: AlarmClear, db: Session = Depends(get_db)):
    """清除报警"""
    service = EAPService(db)
    alarm = service.clear_alarm(alarm_id, data.handled_by, data.handle_result)
    
    if not alarm:
        raise HTTPException(status_code=404, detail="报警不存在")
    
    return {"id": alarm.id, "message": "报警已清除"}

@router.get("/eap/equipments/{equipment_id}/runtime-params")
def get_runtime_params(
    equipment_id: str,
    param_code: Optional[str] = None,
    hours: int = Query(1, ge=1, le=24),
    db: Session = Depends(get_db)
):
    """获取设备运行参数"""
    service = EAPService(db)
    start_time = datetime.now() - timedelta(hours=hours)
    
    items = service.get_runtime_params(
        equipment_id=equipment_id,
        param_code=param_code,
        start_time=start_time
    )
    
    return {
        "total": len(items),
        "time_range_hours": hours,
        "items": [
            {
                "id": item.id,
                "param_code": item.param_code,
                "param_name": item.param_name,
                "param_value": item.param_value,
                "param_unit": item.param_unit,
                "param_type": item.param_type,
                "min_limit": item.min_limit,
                "max_limit": item.max_limit,
                "timestamp": item.timestamp.isoformat()
            }
            for item in items
        ]
    }

@router.get("/eap/statistics")
def get_eap_statistics(db: Session = Depends(get_db)):
    """获取EAP统计信息"""
    service = EAPService(db)
    stats = service.get_equipment_statistics()
    alarm_stats = service.get_alarm_statistics(hours=24)
    
    return {
        "equipment": stats,
        "alarms": alarm_stats
    }

# ============== SPC API ==============

@router.get("/spc/control-charts")
def list_control_charts(
    chart_type: Optional[str] = None,
    product_code: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取控制图列表"""
    service = SPCService(db)
    items = service.get_control_charts(
        chart_type=chart_type,
        product_code=product_code
    )
    
    return {
        "total": len(items),
        "items": [
            {
                "id": item.id,
                "chart_code": item.chart_code,
                "chart_name": item.chart_name,
                "chart_type": item.chart_type,
                "product_code": item.product_code,
                "process_code": item.process_code,
                "param_code": item.param_code,
                "param_name": item.param_name,
                "ucl": item.ucl,
                "lcl": item.lcl,
                "target": item.target,
                "sample_size": item.sample_size,
                "is_active": item.is_active
            }
            for item in items
        ]
    }

@router.get("/spc/control-charts/{chart_id}")
def get_control_chart(chart_id: str, db: Session = Depends(get_db)):
    """获取控制图详情"""
    service = SPCService(db)
    chart = service.get_control_chart_by_id(chart_id)
    
    if not chart:
        raise HTTPException(status_code=404, detail="控制图不存在")
    
    return {
        "id": chart.id,
        "chart_code": chart.chart_code,
        "chart_name": chart.chart_name,
        "chart_type": chart.chart_type,
        "product_code": chart.product_code,
        "process_code": chart.process_code,
        "param_code": chart.param_code,
        "param_name": chart.param_name,
        "ucl": chart.ucl,
        "lcl": chart.lcl,
        "usl": chart.usl,
        "lsl": chart.lsl,
        "target": chart.target,
        "sample_size": chart.sample_size,
        "sample_freq": chart.sample_freq,
        "is_active": chart.is_active
    }

@router.get("/spc/control-charts/{chart_id}/data-points")
def get_data_points(
    chart_id: str,
    hours: int = Query(24, ge=1, le=168),
    is_out_of_control: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """获取控制图数据点"""
    service = SPCService(db)
    start_time = datetime.now() - timedelta(hours=hours)
    
    items = service.get_data_points(
        chart_id=chart_id,
        start_time=start_time,
        is_out_of_control=is_out_of_control
    )
    
    return {
        "total": len(items),
        "chart_id": chart_id,
        "time_range_hours": hours,
        "items": [
            {
                "id": item.id,
                "sample_no": item.sample_no,
                "sample_time": item.sample_time.isoformat(),
                "lot_number": item.lot_number,
                "x_value": item.x_value,
                "r_value": item.r_value,
                "s_value": item.s_value,
                "raw_values": item.raw_values,
                "is_out_of_control": item.is_out_of_control,
                "violation_rules": item.violation_rules
            }
            for item in items
        ]
    }

@router.post("/spc/control-charts/{chart_id}/data-points")
def add_data_point(chart_id: str, data: DataPointCreate, db: Session = Depends(get_db)):
    """添加控制图数据点"""
    service = SPCService(db)
    data_dict = data.dict()
    data_dict['chart_id'] = chart_id
    
    point = service.add_data_point(data_dict)
    return {"id": point.id, "message": "数据点添加成功"}

@router.get("/spc/control-charts/{chart_id}/control-limits")
def get_control_limits(chart_id: str, db: Session = Depends(get_db)):
    """计算控制限"""
    service = SPCService(db)
    limits = service.calculate_control_limits(chart_id)
    return limits

@router.get("/spc/anomalies")
def list_anomalies(
    chart_id: Optional[str] = None,
    is_cleared: Optional[bool] = None,
    severity: Optional[str] = None,
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """获取异常点列表"""
    service = SPCService(db)
    start_time = datetime.now() - timedelta(hours=hours)
    
    items = service.get_anomalies(
        chart_id=chart_id,
        is_cleared=is_cleared,
        severity=severity,
        start_time=start_time
    )
    
    return {
        "total": len(items),
        "time_range_hours": hours,
        "items": [
            {
                "id": item.id,
                "chart_id": item.chart_id,
                "chart_code": item.chart.chart_code if item.chart else None,
                "anomaly_type": item.anomaly_type,
                "anomaly_rule": item.anomaly_rule,
                "severity": item.severity,
                "description": item.description,
                "measured_value": item.measured_value,
                "limit_value": item.limit_value,
                "occur_time": item.occur_time.isoformat(),
                "is_cleared": item.is_cleared,
                "handled_by": item.handled_by,
                "handle_action": item.handle_action,
                "root_cause": item.root_cause
            }
            for item in items
        ]
    }

@router.put("/spc/anomalies/{anomaly_id}/clear")
def clear_anomaly(anomaly_id: str, data: AnomalyClear, db: Session = Depends(get_db)):
    """清除异常点"""
    service = SPCService(db)
    anomaly = service.clear_anomaly(
        anomaly_id,
        data.handled_by,
        data.handle_action,
        data.root_cause
    )
    
    if not anomaly:
        raise HTTPException(status_code=404, detail="异常点不存在")
    
    return {"id": anomaly.id, "message": "异常点已清除"}

@router.get("/spc/statistics")
def get_spc_statistics(db: Session = Depends(get_db)):
    """获取SPC统计信息"""
    service = SPCService(db)
    stats = service.get_spc_summary()
    return stats

# ============== 数据连接器 API ==============

@router.get("/connectors")
def list_connectors(
    connector_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取连接器列表"""
    service = SyncService(db)
    items = service.get_connectors(
        connector_type=connector_type,
        status=status
    )
    
    return {
        "total": len(items),
        "items": [
            {
                "id": item.id,
                "name": item.name,
                "connector_type": item.connector_type,
                "description": item.description,
                "sync_interval": item.sync_interval,
                "last_sync_time": item.last_sync_time.isoformat() if item.last_sync_time else None,
                "status": item.status,
                "is_enabled": item.is_enabled,
                "error_count": item.error_count,
                "created_at": item.created_at.isoformat()
            }
            for item in items
        ]
    }

@router.get("/connectors/{connector_id}")
def get_connector(connector_id: str, db: Session = Depends(get_db)):
    """获取连接器详情"""
    service = SyncService(db)
    connector = service.get_connector_by_id(connector_id)
    
    if not connector:
        raise HTTPException(status_code=404, detail="连接器不存在")
    
    return {
        "id": connector.id,
        "name": connector.name,
        "connector_type": connector.connector_type,
        "description": connector.description,
        "config": connector.config,
        "mapping_config": connector.mapping_config,
        "sync_interval": connector.sync_interval,
        "last_sync_time": connector.last_sync_time.isoformat() if connector.last_sync_time else None,
        "status": connector.status,
        "is_enabled": connector.is_enabled,
        "last_error": connector.last_error,
        "error_count": connector.error_count,
        "created_at": connector.created_at.isoformat(),
        "updated_at": connector.updated_at.isoformat()
    }

@router.post("/connectors")
def create_connector(data: ConnectorCreate, db: Session = Depends(get_db)):
    """创建连接器"""
    service = SyncService(db)
    connector = service.create_connector(data.dict())
    return {"id": connector.id, "message": "连接器创建成功"}

@router.put("/connectors/{connector_id}")
def update_connector(connector_id: str, data: ConnectorUpdate, db: Session = Depends(get_db)):
    """更新连接器"""
    service = SyncService(db)
    connector = service.update_connector(connector_id, data.dict(exclude_unset=True))
    
    if not connector:
        raise HTTPException(status_code=404, detail="连接器不存在")
    
    return {"id": connector.id, "message": "连接器更新成功"}

@router.delete("/connectors/{connector_id}")
def delete_connector(connector_id: str, db: Session = Depends(get_db)):
    """删除连接器"""
    service = SyncService(db)
    success = service.delete_connector(connector_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="连接器不存在")
    
    return {"message": "连接器删除成功"}

@router.post("/connectors/{connector_id}/test")
async def test_connector(connector_id: str, db: Session = Depends(get_db)):
    """测试连接器"""
    service = SyncService(db)
    result = await service.test_connector(connector_id)
    return result

@router.post("/connectors/{connector_id}/sync")
async def sync_data(
    connector_id: str,
    data: SyncRequest,
    db: Session = Depends(get_db)
):
    """执行数据同步"""
    service = SyncService(db)
    result = await service.sync_data(
        connector_id=connector_id,
        data_type=data.data_type,
        start_time=data.start_time,
        end_time=data.end_time,
        sync_type='manual'
    )
    return result

@router.get("/connectors/{connector_id}/sync-logs")
def get_sync_logs(
    connector_id: str,
    data_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取同步日志"""
    service = SyncService(db)
    items = service.get_sync_logs(
        connector_id=connector_id,
        data_type=data_type,
        status=status,
        limit=limit
    )
    
    return {
        "total": len(items),
        "items": [
            {
                "id": item.id,
                "sync_type": item.sync_type,
                "data_type": item.data_type,
                "start_time": item.start_time.isoformat() if item.start_time else None,
                "end_time": item.end_time.isoformat() if item.end_time else None,
                "records_total": item.records_total,
                "records_inserted": item.records_inserted,
                "records_updated": item.records_updated,
                "records_failed": item.records_failed,
                "status": item.status,
                "started_at": item.started_at.isoformat(),
                "completed_at": item.completed_at.isoformat() if item.completed_at else None,
                "duration_seconds": item.duration_seconds
            }
            for item in items
        ]
    }