"""
CIM服务层 - 业务逻辑处理
包含MES、EAP、SPC数据服务和数据同步服务
"""
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, and_, or_
import json
import logging

from models.cim_models import (
    WorkOrder, WorkOrderStatus, ProcessParameter, ProductionRecord,
    Equipment, EquipmentStatus, EquipmentStatusHistory, EquipmentAlarm, EquipmentRuntimeParam,
    SPCControlChart, SPCDataPoint, SPCAnomaly,
    DataConnector, ConnectorStatus, SyncLog
)
from cim_module.connectors import DatabaseConnector, APIConnector

logger = logging.getLogger(__name__)

# ============== MES服务 ==============

class MESService:
    """MES数据服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # --- 工单管理 ---
    
    def get_work_orders(
        self,
        status: Optional[str] = None,
        product_code: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[WorkOrder], int]:
        """获取工单列表"""
        query = self.db.query(WorkOrder)
        
        if status:
            query = query.filter(WorkOrder.status == status)
        if product_code:
            query = query.filter(WorkOrder.product_code == product_code)
        if start_date:
            query = query.filter(WorkOrder.created_at >= start_date)
        if end_date:
            query = query.filter(WorkOrder.created_at <= end_date)
        
        total = query.count()
        items = query.order_by(desc(WorkOrder.created_at)).offset(offset).limit(limit).all()
        
        return items, total
    
    def get_work_order_by_id(self, wo_id: str) -> Optional[WorkOrder]:
        """根据ID获取工单"""
        return self.db.query(WorkOrder).filter(WorkOrder.id == wo_id).first()
    
    def get_work_order_by_number(self, wo_number: str) -> Optional[WorkOrder]:
        """根据工单号获取工单"""
        return self.db.query(WorkOrder).filter(WorkOrder.wo_number == wo_number).first()
    
    def create_work_order(self, data: Dict[str, Any]) -> WorkOrder:
        """创建工单"""
        wo = WorkOrder(**data)
        self.db.add(wo)
        self.db.commit()
        self.db.refresh(wo)
        return wo
    
    def update_work_order(self, wo_id: str, data: Dict[str, Any]) -> Optional[WorkOrder]:
        """更新工单"""
        wo = self.get_work_order_by_id(wo_id)
        if not wo:
            return None
        
        for key, value in data.items():
            setattr(wo, key, value)
        
        wo.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(wo)
        return wo
    
    def get_wo_statistics(self) -> Dict[str, Any]:
        """获取工单统计"""
        total = self.db.query(WorkOrder).count()
        
        status_counts = self.db.query(
            WorkOrder.status,
            func.count(WorkOrder.id).label('count')
        ).group_by(WorkOrder.status).all()
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = self.db.query(WorkOrder).filter(WorkOrder.created_at >= today).count()
        
        # 进行中工单
        running_count = self.db.query(WorkOrder).filter(
            WorkOrder.status == WorkOrderStatus.RUNNING.value
        ).count()
        
        # 完成率
        completed_count = self.db.query(WorkOrder).filter(
            WorkOrder.status == WorkOrderStatus.COMPLETED.value
        ).count()
        completion_rate = round(completed_count / total * 100, 2) if total > 0 else 0
        
        return {
            "total": total,
            "today_count": today_count,
            "running_count": running_count,
            "completed_count": completed_count,
            "completion_rate": completion_rate,
            "status_distribution": {s.status: s.count for s in status_counts}
        }
    
    # --- 工艺参数 ---
    
    def get_process_params(
        self,
        wo_id: Optional[str] = None,
        process_step: Optional[int] = None
    ) -> List[ProcessParameter]:
        """获取工艺参数"""
        query = self.db.query(ProcessParameter)
        
        if wo_id:
            query = query.filter(ProcessParameter.wo_id == wo_id)
        if process_step is not None:
            query = query.filter(ProcessParameter.process_step == process_step)
        
        return query.all()
    
    def create_process_param(self, data: Dict[str, Any]) -> ProcessParameter:
        """创建工艺参数"""
        param = ProcessParameter(**data)
        self.db.add(param)
        self.db.commit()
        self.db.refresh(param)
        return param
    
    # --- 生产记录 ---
    
    def get_production_records(
        self,
        wo_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[ProductionRecord]:
        """获取生产记录"""
        query = self.db.query(ProductionRecord)
        
        if wo_id:
            query = query.filter(ProductionRecord.wo_id == wo_id)
        if start_date:
            query = query.filter(ProductionRecord.start_time >= start_date)
        if end_date:
            query = query.filter(ProductionRecord.start_time <= end_date)
        
        return query.order_by(desc(ProductionRecord.start_time)).limit(limit).all()
    
    def get_production_summary(self, wo_id: str) -> Dict[str, Any]:
        """获取生产汇总"""
        records = self.db.query(ProductionRecord).filter(
            ProductionRecord.wo_id == wo_id
        ).all()
        
        total_qty = sum(r.quantity for r in records)
        good_qty = sum(r.good_qty for r in records)
        scrap_qty = sum(r.scrap_qty for r in records)
        
        total_duration = sum(r.duration_minutes or 0 for r in records)
        
        return {
            "wo_id": wo_id,
            "total_records": len(records),
            "total_quantity": total_qty,
            "good_quantity": good_qty,
            "scrap_quantity": scrap_qty,
            "yield_rate": round(good_qty / total_qty * 100, 2) if total_qty > 0 else 0,
            "total_duration_minutes": total_duration
        }


# ============== EAP服务 ==============

class EAPService:
    """EAP设备数据服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # --- 设备管理 ---
    
    def get_equipments(
        self,
        status: Optional[str] = None,
        area_code: Optional[str] = None,
        equipment_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Equipment]:
        """获取设备列表"""
        query = self.db.query(Equipment)
        
        if status:
            query = query.filter(Equipment.status == status)
        if area_code:
            query = query.filter(Equipment.area_code == area_code)
        if equipment_type:
            query = query.filter(Equipment.equipment_type == equipment_type)
        if is_active is not None:
            query = query.filter(Equipment.is_active == is_active)
        
        return query.all()
    
    def get_equipment_by_id(self, equipment_id: str) -> Optional[Equipment]:
        """根据ID获取设备"""
        return self.db.query(Equipment).filter(Equipment.id == equipment_id).first()
    
    def get_equipment_by_code(self, equipment_code: str) -> Optional[Equipment]:
        """根据设备编码获取设备"""
        return self.db.query(Equipment).filter(Equipment.equipment_code == equipment_code).first()
    
    def create_equipment(self, data: Dict[str, Any]) -> Equipment:
        """创建设备"""
        equipment = Equipment(**data)
        self.db.add(equipment)
        self.db.commit()
        self.db.refresh(equipment)
        return equipment
    
    def update_equipment_status(self, equipment_id: str, status: str, reason: Optional[str] = None) -> Optional[Equipment]:
        """更新设备状态"""
        equipment = self.get_equipment_by_id(equipment_id)
        if not equipment:
            return None
        
        previous_status = equipment.status
        equipment.status = status
        equipment.updated_at = datetime.now()
        
        # 记录状态历史
        history = EquipmentStatusHistory(
            equipment_id=equipment_id,
            status=status,
            previous_status=previous_status,
            start_time=datetime.now(),
            reason_description=reason
        )
        self.db.add(history)
        
        # 更新上一个状态的结束时间
        last_history = self.db.query(EquipmentStatusHistory).filter(
            EquipmentStatusHistory.equipment_id == equipment_id,
            EquipmentStatusHistory.end_time.is_(None)
        ).order_by(desc(EquipmentStatusHistory.start_time)).first()
        
        if last_history and last_history.id != history.id:
            last_history.end_time = datetime.now()
            if last_history.start_time:
                last_history.duration_minutes = int(
                    (last_history.end_time - last_history.start_time).total_seconds() / 60
                )
        
        self.db.commit()
        return equipment
    
    def get_equipment_statistics(self) -> Dict[str, Any]:
        """获取设备统计"""
        total = self.db.query(Equipment).filter(Equipment.is_active == True).count()
        
        status_counts = self.db.query(
            Equipment.status,
            func.count(Equipment.id).label('count')
        ).filter(Equipment.is_active == True).group_by(Equipment.status).all()
        
        # OEE计算相关
        running_count = self.db.query(Equipment).filter(
            Equipment.status == EquipmentStatus.RUNNING.value
        ).count()
        
        error_count = self.db.query(Equipment).filter(
            Equipment.status == EquipmentStatus.ERROR.value
        ).count()
        
        return {
            "total": total,
            "running_count": running_count,
            "error_count": error_count,
            "status_distribution": {s.status: s.count for s in status_counts},
            "availability_rate": round(running_count / total * 100, 2) if total > 0 else 0
        }
    
    # --- 报警管理 ---
    
    def get_alarms(
        self,
        equipment_id: Optional[str] = None,
        alarm_level: Optional[str] = None,
        is_cleared: Optional[bool] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[EquipmentAlarm]:
        """获取报警列表"""
        query = self.db.query(EquipmentAlarm)
        
        if equipment_id:
            query = query.filter(EquipmentAlarm.equipment_id == equipment_id)
        if alarm_level:
            query = query.filter(EquipmentAlarm.alarm_level == alarm_level)
        if is_cleared is not None:
            query = query.filter(EquipmentAlarm.is_cleared == is_cleared)
        if start_date:
            query = query.filter(EquipmentAlarm.occur_time >= start_date)
        if end_date:
            query = query.filter(EquipmentAlarm.occur_time <= end_date)
        
        return query.order_by(desc(EquipmentAlarm.occur_time)).limit(limit).all()
    
    def create_alarm(self, data: Dict[str, Any]) -> EquipmentAlarm:
        """创建报警"""
        alarm = EquipmentAlarm(**data)
        self.db.add(alarm)
        self.db.commit()
        self.db.refresh(alarm)
        return alarm
    
    def clear_alarm(self, alarm_id: str, handled_by: str, handle_result: str) -> Optional[EquipmentAlarm]:
        """清除报警"""
        alarm = self.db.query(EquipmentAlarm).filter(EquipmentAlarm.id == alarm_id).first()
        if not alarm:
            return None
        
        alarm.is_cleared = True
        alarm.clear_time = datetime.now()
        alarm.handled_by = handled_by
        alarm.handle_time = datetime.now()
        alarm.handle_result = handle_result
        
        self.db.commit()
        return alarm
    
    def get_alarm_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """获取报警统计"""
        start_time = datetime.now() - timedelta(hours=hours)
        
        total = self.db.query(EquipmentAlarm).filter(
            EquipmentAlarm.occur_time >= start_time
        ).count()
        
        uncleared = self.db.query(EquipmentAlarm).filter(
            EquipmentAlarm.occur_time >= start_time,
            EquipmentAlarm.is_cleared == False
        ).count()
        
        level_counts = self.db.query(
            EquipmentAlarm.alarm_level,
            func.count(EquipmentAlarm.id).label('count')
        ).filter(EquipmentAlarm.occur_time >= start_time).group_by(
            EquipmentAlarm.alarm_level
        ).all()
        
        return {
            "total": total,
            "uncleared": uncleared,
            "time_range_hours": hours,
            "level_distribution": {l.alarm_level: l.count for l in level_counts}
        }
    
    # --- 运行参数 ---
    
    def get_runtime_params(
        self,
        equipment_id: str,
        param_code: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[EquipmentRuntimeParam]:
        """获取设备运行参数"""
        query = self.db.query(EquipmentRuntimeParam).filter(
            EquipmentRuntimeParam.equipment_id == equipment_id
        )
        
        if param_code:
            query = query.filter(EquipmentRuntimeParam.param_code == param_code)
        if start_time:
            query = query.filter(EquipmentRuntimeParam.timestamp >= start_time)
        if end_time:
            query = query.filter(EquipmentRuntimeParam.timestamp <= end_time)
        
        return query.order_by(desc(EquipmentRuntimeParam.timestamp)).limit(limit).all()
    
    def save_runtime_param(self, data: Dict[str, Any]) -> EquipmentRuntimeParam:
        """保存运行参数"""
        param = EquipmentRuntimeParam(**data)
        self.db.add(param)
        self.db.commit()
        self.db.refresh(param)
        return param


# ============== SPC服务 ==============

class SPCService:
    """SPC质量数据服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # --- 控制图管理 ---
    
    def get_control_charts(
        self,
        chart_type: Optional[str] = None,
        product_code: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[SPCControlChart]:
        """获取控制图列表"""
        query = self.db.query(SPCControlChart)
        
        if chart_type:
            query = query.filter(SPCControlChart.chart_type == chart_type)
        if product_code:
            query = query.filter(SPCControlChart.product_code == product_code)
        if is_active is not None:
            query = query.filter(SPCControlChart.is_active == is_active)
        
        return query.all()
    
    def get_control_chart_by_id(self, chart_id: str) -> Optional[SPCControlChart]:
        """根据ID获取控制图"""
        return self.db.query(SPCControlChart).filter(SPCControlChart.id == chart_id).first()
    
    def create_control_chart(self, data: Dict[str, Any]) -> SPCControlChart:
        """创建控制图"""
        chart = SPCControlChart(**data)
        self.db.add(chart)
        self.db.commit()
        self.db.refresh(chart)
        return chart
    
    # --- 数据点管理 ---
    
    def get_data_points(
        self,
        chart_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        is_out_of_control: Optional[bool] = None,
        limit: int = 500
    ) -> List[SPCDataPoint]:
        """获取控制图数据点"""
        query = self.db.query(SPCDataPoint).filter(SPCDataPoint.chart_id == chart_id)
        
        if start_time:
            query = query.filter(SPCDataPoint.sample_time >= start_time)
        if end_time:
            query = query.filter(SPCDataPoint.sample_time <= end_time)
        if is_out_of_control is not None:
            query = query.filter(SPCDataPoint.is_out_of_control == is_out_of_control)
        
        return query.order_by(asc(SPCDataPoint.sample_no)).limit(limit).all()
    
    def add_data_point(self, data: Dict[str, Any]) -> SPCDataPoint:
        """添加数据点"""
        point = SPCDataPoint(**data)
        self.db.add(point)
        self.db.commit()
        self.db.refresh(point)
        return point
    
    def calculate_control_limits(self, chart_id: str) -> Dict[str, float]:
        """计算控制限"""
        points = self.db.query(SPCDataPoint).filter(
            SPCDataPoint.chart_id == chart_id,
            SPCDataPoint.is_out_of_control == False
        ).order_by(desc(SPCDataPoint.sample_time)).limit(25).all()
        
        if len(points) < 2:
            return {}
        
        values = [p.x_value for p in points if p.x_value is not None]
        
        import statistics
        mean = statistics.mean(values)
        stdev = statistics.stdev(values)
        
        chart = self.get_control_chart_by_id(chart_id)
        if not chart:
            return {}
        
        if chart.chart_type in ['X-R', 'X-S']:
            ucl = mean + 3 * stdev
            lcl = mean - 3 * stdev
        else:
            ucl = mean + 3 * stdev
            lcl = max(0, mean - 3 * stdev)
        
        return {
            "mean": round(mean, 4),
            "ucl": round(ucl, 4),
            "lcl": round(lcl, 4),
            "stdev": round(stdev, 4)
        }
    
    # --- 异常点管理 ---
    
    def get_anomalies(
        self,
        chart_id: Optional[str] = None,
        is_cleared: Optional[bool] = None,
        severity: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[SPCAnomaly]:
        """获取异常点列表"""
        query = self.db.query(SPCAnomaly)
        
        if chart_id:
            query = query.filter(SPCAnomaly.chart_id == chart_id)
        if is_cleared is not None:
            query = query.filter(SPCAnomaly.is_cleared == is_cleared)
        if severity:
            query = query.filter(SPCAnomaly.severity == severity)
        if start_time:
            query = query.filter(SPCAnomaly.occur_time >= start_time)
        if end_date:
            query = query.filter(SPCAnomaly.occur_time <= end_date)
        
        return query.order_by(desc(SPCAnomaly.occur_time)).limit(limit).all()
    
    def create_anomaly(self, data: Dict[str, Any]) -> SPCAnomaly:
        """创建异常点记录"""
        anomaly = SPCAnomaly(**data)
        self.db.add(anomaly)
        self.db.commit()
        self.db.refresh(anomaly)
        return anomaly
    
    def clear_anomaly(self, anomaly_id: str, handled_by: str, handle_action: str, root_cause: str) -> Optional[SPCAnomaly]:
        """清除异常点"""
        anomaly = self.db.query(SPCAnomaly).filter(SPCAnomaly.id == anomaly_id).first()
        if not anomaly:
            return None
        
        anomaly.is_cleared = True
        anomaly.clear_time = datetime.now()
        anomaly.handled_by = handled_by
        anomaly.handle_time = datetime.now()
        anomaly.handle_action = handle_action
        anomaly.root_cause = root_cause
        
        self.db.commit()
        return anomaly
    
    def get_spc_summary(self) -> Dict[str, Any]:
        """获取SPC汇总统计"""
        total_charts = self.db.query(SPCControlChart).filter(
            SPCControlChart.is_active == True
        ).count()
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        today_anomalies = self.db.query(SPCAnomaly).filter(
            SPCAnomaly.occur_time >= today
        ).count()
        
        uncleared_anomalies = self.db.query(SPCAnomaly).filter(
            SPCAnomaly.is_cleared == False
        ).count()
        
        total_points = self.db.query(SPCDataPoint).count()
        
        out_of_control_points = self.db.query(SPCDataPoint).filter(
            SPCDataPoint.is_out_of_control == True
        ).count()
        
        return {
            "total_charts": total_charts,
            "today_anomalies": today_anomalies,
            "uncleared_anomalies": uncleared_anomalies,
            "total_data_points": total_points,
            "out_of_control_points": out_of_control_points,
            "control_rate": round(
                (total_points - out_of_control_points) / total_points * 100, 2
            ) if total_points > 0 else 100
        }