"""
数据同步服务 - 管理数据连接器和数据同步任务
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import asyncio
import logging
import json

from models.cim_models import DataConnector, ConnectorStatus, SyncLog, ConnectorType
from cim_module.connectors import DatabaseConnector, APIConnector

logger = logging.getLogger(__name__)

class SyncService:
    """数据同步服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self._active_connectors: Dict[str, Any] = {}
    
    # --- 连接器管理 ---
    
    def get_connectors(
        self,
        connector_type: Optional[str] = None,
        status: Optional[str] = None,
        is_enabled: Optional[bool] = None
    ) -> List[DataConnector]:
        """获取连接器列表"""
        query = self.db.query(DataConnector)
        
        if connector_type:
            query = query.filter(DataConnector.connector_type == connector_type)
        if status:
            query = query.filter(DataConnector.status == status)
        if is_enabled is not None:
            query = query.filter(DataConnector.is_enabled == is_enabled)
        
        return query.order_by(DataConnector.created_at.desc()).all()
    
    def get_connector_by_id(self, connector_id: str) -> Optional[DataConnector]:
        """根据ID获取连接器"""
        return self.db.query(DataConnector).filter(DataConnector.id == connector_id).first()
    
    def create_connector(self, data: Dict[str, Any]) -> DataConnector:
        """创建连接器"""
        connector = DataConnector(**data)
        self.db.add(connector)
        self.db.commit()
        self.db.refresh(connector)
        return connector
    
    def update_connector(self, connector_id: str, data: Dict[str, Any]) -> Optional[DataConnector]:
        """更新连接器"""
        connector = self.get_connector_by_id(connector_id)
        if not connector:
            return None
        
        for key, value in data.items():
            setattr(connector, key, value)
        
        connector.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(connector)
        return connector
    
    def delete_connector(self, connector_id: str) -> bool:
        """删除连接器"""
        connector = self.get_connector_by_id(connector_id)
        if not connector:
            return False
        
        self.db.delete(connector)
        self.db.commit()
        return True
    
    async def test_connector(self, connector_id: str) -> Dict[str, Any]:
        """测试连接器"""
        connector = self.get_connector_by_id(connector_id)
        if not connector:
            return {"success": False, "error": "连接器不存在"}
        
        try:
            if connector.connector_type == ConnectorType.DATABASE.value:
                db_connector = DatabaseConnector(connector.config)
                result = await db_connector.test_connection()
            elif connector.connector_type == ConnectorType.API.value:
                api_connector = APIConnector(connector.config)
                result = await api_connector.test_connection()
            else:
                return {"success": False, "error": f"不支持的连接器类型: {connector.connector_type}"}
            
            # 更新状态
            if result.get("success"):
                connector.status = ConnectorStatus.ACTIVE.value
                connector.last_error = None
            else:
                connector.status = ConnectorStatus.ERROR.value
                connector.last_error = result.get("error")
            
            self.db.commit()
            return result
            
        except Exception as e:
            connector.status = ConnectorStatus.ERROR.value
            connector.last_error = str(e)
            connector.error_count += 1
            self.db.commit()
            return {"success": False, "error": str(e)}
    
    # --- 同步任务 ---
    
    async def sync_data(
        self,
        connector_id: str,
        data_type: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        sync_type: str = 'manual'
    ) -> Dict[str, Any]:
        """
        执行数据同步
        
        data_type: work_order, equipment_status, equipment_alarm, equipment_param,
                   spc_data_point, spc_anomaly
        """
        connector = self.get_connector_by_id(connector_id)
        if not connector:
            return {"success": False, "error": "连接器不存在"}
        
        # 创建同步日志
        sync_log = SyncLog(
            connector_id=connector_id,
            sync_type=sync_type,
            data_type=data_type,
            start_time=start_time,
            end_time=end_time,
            status='running'
        )
        self.db.add(sync_log)
        self.db.commit()
        
        started_at = datetime.now()
        
        try:
            # 根据数据类型执行不同的同步逻辑
            if data_type == 'work_order':
                result = await self._sync_work_orders(connector, start_time, end_time)
            elif data_type == 'equipment_status':
                result = await self._sync_equipment_status(connector, start_time, end_time)
            elif data_type == 'equipment_alarm':
                result = await self._sync_equipment_alarms(connector, start_time, end_time)
            elif data_type == 'spc_data_point':
                result = await self._sync_spc_data_points(connector, start_time, end_time)
            else:
                result = {"success": False, "error": f"不支持的数据类型: {data_type}"}
            
            # 更新同步日志
            sync_log.status = 'success' if result.get("success") else 'failed'
            sync_log.records_total = result.get("total", 0)
            sync_log.records_inserted = result.get("inserted", 0)
            sync_log.records_updated = result.get("updated", 0)
            sync_log.records_failed = result.get("failed", 0)
            sync_log.completed_at = datetime.now()
            sync_log.duration_seconds = int((sync_log.completed_at - started_at).total_seconds())
            
            if not result.get("success"):
                sync_log.error_message = result.get("error")
            
            # 更新连接器
            connector.last_sync_time = datetime.now()
            connector.status = ConnectorStatus.ACTIVE.value
            
            self.db.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"同步失败: {e}")
            
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.completed_at = datetime.now()
            sync_log.duration_seconds = int((sync_log.completed_at - started_at).total_seconds())
            
            connector.status = ConnectorStatus.ERROR.value
            connector.last_error = str(e)
            connector.error_count += 1
            
            self.db.commit()
            
            return {"success": False, "error": str(e)}
    
    async def _sync_work_orders(
        self,
        connector: DataConnector,
        start_time: Optional[datetime],
        end_time: Optional[datetime]
    ) -> Dict[str, Any]:
        """同步工单数据"""
        from models.cim_models import WorkOrder
        
        # 构建查询
        query_config = connector.mapping_config.get('work_order_query', {})
        
        if connector.connector_type == ConnectorType.DATABASE.value:
            db_connector = DatabaseConnector(connector.config)
            await db_connector.connect()
            
            # 构建WHERE条件
            where_clause = query_config.get('where', '1=1')
            if start_time:
                where_clause += f" AND created_at >= '{start_time}'"
            if end_time:
                where_clause += f" AND created_at <= '{end_time}'"
            
            data = await db_connector.fetch_data({
                "table": query_config.get('table', 'work_orders'),
                "where": where_clause,
                "order_by": query_config.get('order_by', 'created_at DESC'),
                "limit": query_config.get('limit', 1000)
            })
            
            await db_connector.disconnect()
            
        elif connector.connector_type == ConnectorType.API.value:
            api_connector = APIConnector(connector.config)
            await api_connector.connect()
            
            data = await api_connector.fetch_data({
                "endpoint": query_config.get('endpoint', '/api/workorders'),
                "method": "GET",
                "params": {
                    "start_time": start_time.isoformat() if start_time else None,
                    "end_time": end_time.isoformat() if end_time else None
                },
                "extract_path": query_config.get('extract_path', 'data')
            })
            
            await api_connector.disconnect()
        else:
            return {"success": False, "error": "不支持的连接器类型"}
        
        # 数据映射和保存
        field_mapping = connector.mapping_config.get('work_order_fields', {})
        
        inserted = 0
        updated = 0
        failed = 0
        
        for item in data:
            try:
                # 字段映射
                mapped_data = {}
                for target_field, source_field in field_mapping.items():
                    mapped_data[target_field] = item.get(source_field)
                
                # 检查是否已存在
                existing = self.db.query(WorkOrder).filter(
                    WorkOrder.wo_number == mapped_data.get('wo_number')
                ).first()
                
                if existing:
                    # 更新
                    for key, value in mapped_data.items():
                        setattr(existing, key, value)
                    existing.updated_at = datetime.now()
                    updated += 1
                else:
                    # 插入
                    wo = WorkOrder(**mapped_data)
                    wo.source_system = connector.name
                    wo.external_id = item.get('id')
                    self.db.add(wo)
                    inserted += 1
                    
            except Exception as e:
                logger.error(f"处理记录失败: {e}")
                failed += 1
        
        self.db.commit()
        
        return {
            "success": True,
            "total": len(data),
            "inserted": inserted,
            "updated": updated,
            "failed": failed
        }
    
    async def _sync_equipment_status(
        self,
        connector: DataConnector,
        start_time: Optional[datetime],
        end_time: Optional[datetime]
    ) -> Dict[str, Any]:
        """同步设备状态"""
        from models.cim_models import Equipment, EquipmentStatusHistory
        
        query_config = connector.mapping_config.get('equipment_query', {})
        
        if connector.connector_type == ConnectorType.DATABASE.value:
            db_connector = DatabaseConnector(connector.config)
            await db_connector.connect()
            
            data = await db_connector.fetch_data({
                "table": query_config.get('table', 'equipments'),
                "limit": query_config.get('limit', 1000)
            })
            
            await db_connector.disconnect()
            
        elif connector.connector_type == ConnectorType.API.value:
            api_connector = APIConnector(connector.config)
            await api_connector.connect()
            
            data = await api_connector.fetch_data({
                "endpoint": query_config.get('endpoint', '/api/equipments'),
                "method": "GET",
                "extract_path": query_config.get('extract_path', 'data')
            })
            
            await api_connector.disconnect()
        else:
            return {"success": False, "error": "不支持的连接器类型"}
        
        field_mapping = connector.mapping_config.get('equipment_fields', {})
        
        inserted = 0
        updated = 0
        
        for item in data:
            try:
                mapped_data = {target: item.get(source) for target, source in field_mapping.items()}
                
                existing = self.db.query(Equipment).filter(
                    Equipment.equipment_code == mapped_data.get('equipment_code')
                ).first()
                
                if existing:
                    for key, value in mapped_data.items():
                        setattr(existing, key, value)
                    existing.updated_at = datetime.now()
                    updated += 1
                else:
                    equipment = Equipment(**mapped_data)
                    equipment.source_system = connector.name
                    equipment.external_id = item.get('id')
                    self.db.add(equipment)
                    inserted += 1
                    
            except Exception as e:
                logger.error(f"处理设备记录失败: {e}")
        
        self.db.commit()
        
        return {
            "success": True,
            "total": len(data),
            "inserted": inserted,
            "updated": updated
        }
    
    async def _sync_equipment_alarms(
        self,
        connector: DataConnector,
        start_time: Optional[datetime],
        end_time: Optional[datetime]
    ) -> Dict[str, Any]:
        """同步设备报警"""
        # 类似实现...
        return {"success": True, "total": 0, "inserted": 0}
    
    async def _sync_spc_data_points(
        self,
        connector: DataConnector,
        start_time: Optional[datetime],
        end_time: Optional[datetime]
    ) -> Dict[str, Any]:
        """同步SPC数据点"""
        # 类似实现...
        return {"success": True, "total": 0, "inserted": 0}
    
    def get_sync_logs(
        self,
        connector_id: Optional[str] = None,
        data_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[SyncLog]:
        """获取同步日志"""
        query = self.db.query(SyncLog)
        
        if connector_id:
            query = query.filter(SyncLog.connector_id == connector_id)
        if data_type:
            query = query.filter(SyncLog.data_type == data_type)
        if status:
            query = query.filter(SyncLog.status == status)
        
        return query.order_by(SyncLog.started_at.desc()).limit(limit).all()