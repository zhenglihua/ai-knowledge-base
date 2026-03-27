"""
数据看板API - 提供综合数据看板接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

from models.database import get_db
from models.cim_models import (
    WorkOrder, WorkOrderStatus,
    Equipment, EquipmentStatus,
    EquipmentAlarm, SPCAnomaly, SPCDataPoint,
    DashboardWidget
)
from cim_module.services import MESService, EAPService, SPCService

router = APIRouter(prefix="/api/dashboard", tags=["数据看板"])

# ============== Pydantic模型 ==============

class WidgetCreate(BaseModel):
    name: str
    widget_type: str
    dashboard_id: str = "default"
    position_x: int = 0
    position_y: int = 0
    width: int = 6
    height: int = 4
    data_source: Dict[str, Any] = {}
    display_config: Dict[str, Any] = {}

class WidgetUpdate(BaseModel):
    name: Optional[str] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    data_source: Optional[Dict[str, Any]] = None
    display_config: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None

# ============== 综合看板API ==============

@router.get("/overview")
def get_dashboard_overview(db: Session = Depends(get_db)):
    """获取看板总览数据"""
    mes_service = MESService(db)
    eap_service = EAPService(db)
    spc_service = SPCService(db)
    
    # MES统计
    wo_stats = mes_service.get_wo_statistics()
    
    # EAP统计
    equip_stats = eap_service.get_equipment_statistics()
    alarm_stats = eap_service.get_alarm_statistics(hours=24)
    
    # SPC统计
    spc_stats = spc_service.get_spc_summary()
    
    # 今日数据
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    today_wo = db.query(WorkOrder).filter(WorkOrder.created_at >= today).count()
    today_alarms = db.query(EquipmentAlarm).filter(EquipmentAlarm.occur_time >= today).count()
    today_anomalies = db.query(SPCAnomaly).filter(SPCAnomaly.occur_time >= today).count()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "mes": {
            "total_work_orders": wo_stats.get("total", 0),
            "running_orders": wo_stats.get("running_count", 0),
            "today_orders": today_wo,
            "completion_rate": wo_stats.get("completion_rate", 0)
        },
        "eap": {
            "total_equipments": equip_stats.get("total", 0),
            "running_equipments": equip_stats.get("running_count", 0),
            "error_equipments": equip_stats.get("error_count", 0),
            "availability_rate": equip_stats.get("availability_rate", 0),
            "today_alarms": today_alarms,
            "uncleared_alarms": alarm_stats.get("uncleared", 0)
        },
        "spc": {
            "total_charts": spc_stats.get("total_charts", 0),
            "today_anomalies": today_anomalies,
            "uncleared_anomalies": spc_stats.get("uncleared_anomalies", 0),
            "control_rate": spc_stats.get("control_rate", 0)
        }
    }

@router.get("/production")
def get_production_dashboard(
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """获取生产看板数据"""
    start_time = datetime.now() - timedelta(hours=hours)
    
    # 工单趋势（按小时）
    from sqlalchemy import func
    
    wo_trend = db.query(
        func.strftime('%Y-%m-%d %H:00', WorkOrder.created_at).label('hour'),
        func.count(WorkOrder.id).label('count')
    ).filter(
        WorkOrder.created_at >= start_time
    ).group_by('hour').order_by('hour').all()
    
    # 工单状态分布
    status_dist = db.query(
        WorkOrder.status,
        func.count(WorkOrder.id).label('count')
    ).group_by(WorkOrder.status).all()
    
    # 优先级分布
    priority_dist = db.query(
        WorkOrder.priority,
        func.count(WorkOrder.id).label('count')
    ).group_by(WorkOrder.priority).all()
    
    # 产品产量TOP10
    product_yield = db.query(
        WorkOrder.product_code,
        WorkOrder.product_name,
        func.sum(WorkOrder.completed_qty).label('total_qty')
    ).filter(
        WorkOrder.status == WorkOrderStatus.COMPLETED.value
    ).group_by(
        WorkOrder.product_code,
        WorkOrder.product_name
    ).order_by(desc('total_qty')).limit(10).all()
    
    return {
        "time_range_hours": hours,
        "work_order_trend": [
            {"hour": item.hour, "count": item.count}
            for item in wo_trend
        ],
        "status_distribution": [
            {"status": item.status, "count": item.count}
            for item in status_dist
        ],
        "priority_distribution": [
            {"priority": item.priority, "count": item.count}
            for item in priority_dist
        ],
        "top_products": [
            {
                "product_code": item.product_code,
                "product_name": item.product_name,
                "total_qty": item.total_qty or 0
            }
            for item in product_yield
        ]
    }

@router.get("/equipment")
def get_equipment_dashboard(
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """获取设备看板数据"""
    start_time = datetime.now() - timedelta(hours=hours)
    
    # 设备状态分布
    status_dist = db.query(
        Equipment.status,
        func.count(Equipment.id).label('count')
    ).filter(Equipment.is_active == True).group_by(Equipment.status).all()
    
    # 区域设备分布
    area_dist = db.query(
        Equipment.area_name,
        func.count(Equipment.id).label('count')
    ).filter(Equipment.is_active == True).group_by(Equipment.area_name).all()
    
    # 报警趋势
    alarm_trend = db.query(
        func.strftime('%Y-%m-%d %H:00', EquipmentAlarm.occur_time).label('hour'),
        func.count(EquipmentAlarm.id).label('count')
    ).filter(
        EquipmentAlarm.occur_time >= start_time
    ).group_by('hour').order_by('hour').all()
    
    # 报警级别分布
    alarm_level_dist = db.query(
        EquipmentAlarm.alarm_level,
        func.count(EquipmentAlarm.id).label('count')
    ).filter(
        EquipmentAlarm.occur_time >= start_time
    ).group_by(EquipmentAlarm.alarm_level).all()
    
    # 最近报警
    recent_alarms = db.query(EquipmentAlarm).filter(
        EquipmentAlarm.occur_time >= start_time
    ).order_by(desc(EquipmentAlarm.occur_time)).limit(10).all()
    
    return {
        "time_range_hours": hours,
        "status_distribution": [
            {"status": item.status, "count": item.count}
            for item in status_dist
        ],
        "area_distribution": [
            {"area": item.area_name or "未分类", "count": item.count}
            for item in area_dist
        ],
        "alarm_trend": [
            {"hour": item.hour, "count": item.count}
            for item in alarm_trend
        ],
        "alarm_level_distribution": [
            {"level": item.alarm_level, "count": item.count}
            for item in alarm_level_dist
        ],
        "recent_alarms": [
            {
                "id": alarm.id,
                "equipment_code": alarm.equipment.equipment_code if alarm.equipment else None,
                "alarm_code": alarm.alarm_code,
                "alarm_level": alarm.alarm_level,
                "alarm_message": alarm.alarm_message,
                "occur_time": alarm.occur_time.isoformat(),
                "is_cleared": alarm.is_cleared
            }
            for alarm in recent_alarms
        ]
    }

@router.get("/quality")
def get_quality_dashboard(
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """获取质量看板数据"""
    start_time = datetime.now() - timedelta(hours=hours)
    
    # 异常趋势
    anomaly_trend = db.query(
        func.strftime('%Y-%m-%d %H:00', SPCAnomaly.occur_time).label('hour'),
        func.count(SPCAnomaly.id).label('count')
    ).filter(
        SPCAnomaly.occur_time >= start_time
    ).group_by('hour').order_by('hour').all()
    
    # 异常级别分布
    severity_dist = db.query(
        SPCAnomaly.severity,
        func.count(SPCAnomaly.id).label('count')
    ).filter(
        SPCAnomaly.occur_time >= start_time
    ).group_by(SPCAnomaly.severity).all()
    
    # 异常类型分布
    type_dist = db.query(
        SPCAnomaly.anomaly_type,
        func.count(SPCAnomaly.id).label('count')
    ).filter(
        SPCAnomaly.occur_time >= start_time
    ).group_by(SPCAnomaly.anomaly_type).all()
    
    # 失控点统计
    ooc_stats = db.query(
        func.strftime('%Y-%m-%d %H:00', SPCDataPoint.sample_time).label('hour'),
        func.count(SPCDataPoint.id).label('count')
    ).filter(
        SPCDataPoint.sample_time >= start_time,
        SPCDataPoint.is_out_of_control == True
    ).group_by('hour').order_by('hour').all()
    
    # 最近异常
    recent_anomalies = db.query(SPCAnomaly).filter(
        SPCAnomaly.occur_time >= start_time
    ).order_by(desc(SPCAnomaly.occur_time)).limit(10).all()
    
    return {
        "time_range_hours": hours,
        "anomaly_trend": [
            {"hour": item.hour, "count": item.count}
            for item in anomaly_trend
        ],
        "severity_distribution": [
            {"severity": item.severity, "count": item.count}
            for item in severity_dist
        ],
        "type_distribution": [
            {"type": item.anomaly_type, "count": item.count}
            for item in type_dist
        ],
        "out_of_control_trend": [
            {"hour": item.hour, "count": item.count}
            for item in ooc_stats
        ],
        "recent_anomalies": [
            {
                "id": anomaly.id,
                "chart_code": anomaly.chart.chart_code if anomaly.chart else None,
                "anomaly_type": anomaly.anomaly_type,
                "severity": anomaly.severity,
                "description": anomaly.description,
                "occur_time": anomaly.occur_time.isoformat(),
                "is_cleared": anomaly.is_cleared
            }
            for anomaly in recent_anomalies
        ]
    }

@router.get("/kpi")
def get_kpi_dashboard(
    db: Session = Depends(get_db)
):
    """获取KPI指标看板"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    
    # 订单完成率
    def calc_completion_rate(start_time):
        total = db.query(WorkOrder).filter(WorkOrder.created_at >= start_time).count()
        completed = db.query(WorkOrder).filter(
            WorkOrder.created_at >= start_time,
            WorkOrder.status == WorkOrderStatus.COMPLETED.value
        ).count()
        return round(completed / total * 100, 2) if total > 0 else 0
    
    # 设备稼动率
    def calc_availability_rate():
        total = db.query(Equipment).filter(Equipment.is_active == True).count()
        running = db.query(Equipment).filter(
            Equipment.is_active == True,
            Equipment.status == EquipmentStatus.RUNNING.value
        ).count()
        return round(running / total * 100, 2) if total > 0 else 0
    
    # 良品率
    from models.cim_models import ProductionRecord
    def calc_yield_rate(start_time):
        records = db.query(ProductionRecord).filter(
            ProductionRecord.start_time >= start_time
        ).all()
        
        total_qty = sum(r.quantity for r in records)
        good_qty = sum(r.good_qty for r in records)
        
        return round(good_qty / total_qty * 100, 2) if total_qty > 0 else 0
    
    # 报警响应时间
    from sqlalchemy import func
    avg_response_time = db.query(
        func.avg(
            func.julianday(EquipmentAlarm.handle_time) - func.julianday(EquipmentAlarm.occur_time)
        ) * 24 * 60  # 转换为分钟
    ).filter(
        EquipmentAlarm.handle_time.isnot(None)
    ).scalar()
    
    return {
        "production": {
            "today_completion_rate": calc_completion_rate(today),
            "yesterday_completion_rate": calc_completion_rate(yesterday),
            "week_completion_rate": calc_completion_rate(week_start),
            "month_completion_rate": calc_completion_rate(month_start)
        },
        "equipment": {
            "current_availability_rate": calc_availability_rate(),
            "avg_response_time_minutes": round(avg_response_time, 2) if avg_response_time else None
        },
        "quality": {
            "today_yield_rate": calc_yield_rate(today),
            "yesterday_yield_rate": calc_yield_rate(yesterday),
            "week_yield_rate": calc_yield_rate(week_start),
            "month_yield_rate": calc_yield_rate(month_start)
        }
    }

# ============== 自定义组件管理API ==============

@router.get("/widgets")
def list_widgets(
    dashboard_id: str = "default",
    db: Session = Depends(get_db)
):
    """获取看板组件列表"""
    widgets = db.query(DashboardWidget).filter(
        DashboardWidget.dashboard_id == dashboard_id,
        DashboardWidget.is_enabled == True
    ).order_by(DashboardWidget.sort_order).all()
    
    return {
        "dashboard_id": dashboard_id,
        "total": len(widgets),
        "widgets": [
            {
                "id": w.id,
                "name": w.name,
                "widget_type": w.widget_type,
                "position": {"x": w.position_x, "y": w.position_y},
                "size": {"width": w.width, "height": w.height},
                "data_source": w.data_source,
                "display_config": w.display_config,
                "sort_order": w.sort_order
            }
            for w in widgets
        ]
    }

@router.post("/widgets")
def create_widget(data: WidgetCreate, db: Session = Depends(get_db)):
    """创建看板组件"""
    widget = DashboardWidget(**data.dict())
    db.add(widget)
    db.commit()
    db.refresh(widget)
    
    return {"id": widget.id, "message": "组件创建成功"}

@router.put("/widgets/{widget_id}")
def update_widget(widget_id: str, data: WidgetUpdate, db: Session = Depends(get_db)):
    """更新看板组件"""
    widget = db.query(DashboardWidget).filter(DashboardWidget.id == widget_id).first()
    
    if not widget:
        raise HTTPException(status_code=404, detail="组件不存在")
    
    for key, value in data.dict(exclude_unset=True).items():
        setattr(widget, key, value)
    
    widget.updated_at = datetime.now()
    db.commit()
    
    return {"id": widget.id, "message": "组件更新成功"}

@router.delete("/widgets/{widget_id}")
def delete_widget(widget_id: str, db: Session = Depends(get_db)):
    """删除看板组件"""
    widget = db.query(DashboardWidget).filter(DashboardWidget.id == widget_id).first()
    
    if not widget:
        raise HTTPException(status_code=404, detail="组件不存在")
    
    db.delete(widget)
    db.commit()
    
    return {"message": "组件删除成功"}

@router.get("/widgets/{widget_id}/data")
def get_widget_data(widget_id: str, db: Session = Depends(get_db)):
    """获取组件数据"""
    widget = db.query(DashboardWidget).filter(DashboardWidget.id == widget_id).first()
    
    if not widget:
        raise HTTPException(status_code=404, detail="组件不存在")
    
    data_source = widget.data_source or {}
    source_type = data_source.get('type')
    
    # 根据数据源类型获取数据
    if source_type == 'table':
        table_name = data_source.get('source')
        # 这里可以根据表名动态查询数据
        # 实际实现需要根据具体需求完善
        data = {"message": f"从表 {table_name} 获取数据", "count": 0}
    elif source_type == 'api':
        endpoint = data_source.get('endpoint')
        data = {"message": f"从API {endpoint} 获取数据", "count": 0}
    else:
        data = {"message": "未配置数据源"}
    
    return {
        "widget_id": widget_id,
        "widget_name": widget.name,
        "widget_type": widget.widget_type,
        "data": data
    }