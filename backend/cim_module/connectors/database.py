"""
数据库连接器 - 支持多种数据库直连
"""
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
import logging

from .base import BaseConnector

logger = logging.getLogger(__name__)

class DatabaseConnector(BaseConnector):
    """数据库连接器 - 支持MySQL、PostgreSQL、SQL Server、Oracle等"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.connection = None
        self.engine = None
        self.db_type = config.get('db_type', 'mysql')
    
    async def connect(self) -> bool:
        """建立数据库连接"""
        try:
            if self.db_type == 'mysql':
                import pymysql
                self.connection = pymysql.connect(
                    host=self.config.get('host', 'localhost'),
                    port=self.config.get('port', 3306),
                    database=self.config.get('database'),
                    user=self.config.get('username'),
                    password=self.config.get('password'),
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor
                )
            elif self.db_type == 'postgresql':
                import psycopg2
                from psycopg2.extras import RealDictCursor
                self.connection = psycopg2.connect(
                    host=self.config.get('host', 'localhost'),
                    port=self.config.get('port', 5432),
                    database=self.config.get('database'),
                    user=self.config.get('username'),
                    password=self.config.get('password'),
                    cursor_factory=RealDictCursor
                )
            elif self.db_type == 'mssql':
                import pymssql
                self.connection = pymssql.connect(
                    server=self.config.get('host', 'localhost'),
                    port=self.config.get('port', 1433),
                    database=self.config.get('database'),
                    user=self.config.get('username'),
                    password=self.config.get('password')
                )
            elif self.db_type == 'sqlite':
                import sqlite3
                from sqlite3 import Row
                self.connection = sqlite3.connect(self.config.get('database'))
                self.connection.row_factory = Row
            else:
                raise ValueError(f"不支持的数据库类型: {self.db_type}")
            
            self.is_connected = True
            logger.info(f"数据库连接成功: {self.db_type}@{self.config.get('host')}")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"数据库连接失败: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """断开数据库连接"""
        try:
            if self.connection:
                self.connection.close()
                self.connection = None
            self.is_connected = False
            return True
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"断开连接失败: {e}")
            return False
    
    async def test_connection(self) -> Dict[str, Any]:
        """测试数据库连接"""
        try:
            if not self.is_connected:
                success = await self.connect()
                if not success:
                    return {"success": False, "error": self.last_error}
            
            cursor = self.connection.cursor()
            
            # 根据数据库类型执行不同的测试查询
            if self.db_type == 'mysql':
                cursor.execute("SELECT VERSION() as version")
            elif self.db_type == 'postgresql':
                cursor.execute("SELECT version() as version")
            elif self.db_type == 'mssql':
                cursor.execute("SELECT @@VERSION as version")
            elif self.db_type == 'sqlite':
                cursor.execute("SELECT sqlite_version() as version")
            
            result = cursor.fetchone()
            version = result['version'] if isinstance(result, dict) else result[0]
            
            return {
                "success": True,
                "version": version,
                "db_type": self.db_type
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def fetch_data(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从数据库获取数据
        
        query格式:
        {
            "table": "table_name",      # 表名
            "columns": ["col1", "col2"], # 列名(可选)
            "where": "status='active'",  # WHERE条件(可选)
            "order_by": "created_at DESC", # 排序(可选)
            "limit": 100,               # 限制数量(可选)
            "sql": "SELECT * FROM..."   # 或者直接提供SQL
        }
        """
        try:
            if not self.is_connected:
                await self.connect()
            
            cursor = self.connection.cursor()
            
            # 如果直接提供了SQL，则使用SQL
            if 'sql' in query:
                sql = query['sql']
            else:
                # 构建SQL
                table = query.get('table')
                columns = query.get('columns', ['*'])
                
                sql = f"SELECT {', '.join(columns)} FROM {table}"
                
                if 'where' in query:
                    sql += f" WHERE {query['where']}"
                
                if 'order_by' in query:
                    sql += f" ORDER BY {query['order_by']}"
                
                if 'limit' in query:
                    sql += f" LIMIT {query['limit']}"
            
            cursor.execute(sql)
            rows = cursor.fetchall()
            
            # 转换为字典列表
            if self.db_type == 'sqlite':
                results = [dict(row) for row in rows]
            else:
                results = [dict(row) for row in rows]
            
            return results
            
        except Exception as e:
            logger.error(f"查询数据失败: {e}")
            raise
    
    async def execute_query(self, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """执行自定义SQL查询"""
        try:
            if not self.is_connected:
                await self.connect()
            
            cursor = self.connection.cursor()
            
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            
            rows = cursor.fetchall()
            
            if self.db_type == 'sqlite':
                return [dict(row) for row in rows]
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"执行查询失败: {e}")
            raise
    
    async def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """获取表结构信息"""
        try:
            if not self.is_connected:
                await self.connect()
            
            cursor = self.connection.cursor()
            
            if self.db_type == 'mysql':
                cursor.execute(f"""
                    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = %s AND TABLE_SCHEMA = DATABASE()
                """, (table_name,))
            elif self.db_type == 'postgresql':
                cursor.execute(f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = %s
                """, (table_name,))
            elif self.db_type == 'mssql':
                cursor.execute(f"""
                    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = %s
                """, (table_name,))
            elif self.db_type == 'sqlite':
                cursor.execute(f"PRAGMA table_info({table_name})")
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"获取表结构失败: {e}")
            raise
    
    async def get_tables(self) -> List[str]:
        """获取数据库中的所有表"""
        try:
            if not self.is_connected:
                await self.connect()
            
            cursor = self.connection.cursor()
            
            if self.db_type == 'mysql':
                cursor.execute("SHOW TABLES")
                return [list(row.values())[0] for row in cursor.fetchall()]
            elif self.db_type == 'postgresql':
                cursor.execute("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'public'
                """)
                return [row['tablename'] for row in cursor.fetchall()]
            elif self.db_type == 'mssql':
                cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES")
                return [row['TABLE_NAME'] for row in cursor.fetchall()]
            elif self.db_type == 'sqlite':
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                return [row['name'] for row in cursor.fetchall()]
            
            return []
            
        except Exception as e:
            logger.error(f"获取表列表失败: {e}")
            raise