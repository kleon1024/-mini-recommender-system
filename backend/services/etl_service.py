# ETL服务模块
# 重构版：将ETL服务拆分为多个子模块，提高代码可维护性

# 导入必要的依赖
import logging
import uuid
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

# 导入模型
from models.models import ETLTask, ETLTaskHistory, DatabaseConnection
from schemas import etl_schemas

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ETLService:
    """
    ETL服务类，用于管理和执行ETL任务
    重构版：将功能拆分为多个子模块，提高代码可维护性
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.running_tasks = {}
        
        # 检查依赖是否可用
        try:
            import pandas as pd
            self.pandas_available = True
        except ImportError:
            self.pandas_available = False
            logger.warning("缺少pandas依赖，数据处理功能不可用")
        
        try:
            import pymysql
            self.pymysql_available = True
        except ImportError:
            self.pymysql_available = False
            logger.warning("缺少pymysql依赖，MySQL连接功能不可用")
        
        try:
            import asyncpg
            self.asyncpg_available = True
        except ImportError:
            self.asyncpg_available = False
            logger.warning("缺少asyncpg依赖，PostgreSQL连接功能不可用")
        
        try:
            import redis
            self.redis_available = True
        except ImportError:
            self.redis_available = False
            logger.warning("缺少redis依赖，Redis连接功能不可用")
        
        if not all([self.pandas_available, self.pymysql_available, self.asyncpg_available, self.redis_available]):
            logger.warning("ETL服务部分功能不可用，缺少必要的依赖")
    
    # 基本方法实现
    def get_all_tasks(self) -> List[ETLTask]:
        """
        获取所有ETL任务
        """
        return self.db.query(ETLTask).all()
    
    def get_task_by_id(self, task_id: int) -> Optional[ETLTask]:
        """
        根据ID获取ETL任务
        使用etl/task_manager.py中的实现
        """
        # 导入TaskManager
        from .etl.task_manager import TaskManager
        
        # 创建TaskManager实例
        task_manager = TaskManager(self.db)
        
        # 调用TaskManager的get_task_by_id方法
        return task_manager.get_task_by_id(task_id)
    
    def create_task(self, task_data: etl_schemas.ETLTaskCreate) -> ETLTask:
        """
        创建ETL任务
        使用etl/task_manager.py中的实现
        """
        # 导入TaskManager
        from .etl.task_manager import TaskManager
        
        # 创建TaskManager实例
        task_manager = TaskManager(self.db)
        
        # 调用TaskManager的create_task方法
        return task_manager.create_task(task_data)
    
    def update_task_status(self, task_id: int, status: str) -> Optional[ETLTask]:
        """
        更新ETL任务状态
        使用etl/task_manager.py中的实现
        """
        # 导入TaskManager
        from .etl.task_manager import TaskManager
        
        # 创建TaskManager实例
        task_manager = TaskManager(self.db)
        
        # 调用TaskManager的update_task_status方法
        return task_manager.update_task_status(task_id, status)
    
    def update_task(self, task_id: int, task_data: etl_schemas.ETLTaskCreate) -> Optional[ETLTask]:
        """
        更新ETL任务
        使用etl/task_manager.py中的实现
        """
        # 导入TaskManager
        from .etl.task_manager import TaskManager
        
        # 创建TaskManager实例
        task_manager = TaskManager(self.db)
        
        # 调用TaskManager的update_task方法
        return task_manager.update_task(task_id, task_data)
    
    def delete_task(self, task_id: int) -> bool:
        """
        删除ETL任务
        使用etl/task_manager.py中的实现
        """
        # 导入TaskManager
        from .etl.task_manager import TaskManager
        
        # 创建TaskManager实例
        task_manager = TaskManager(self.db)
        
        # 调用TaskManager的delete_task方法
        return task_manager.delete_task(task_id)
    
    def get_task_history(self, task_id: int, limit: int = 10) -> List[ETLTaskHistory]:
        """
        获取ETL任务执行历史
        使用etl/task_manager.py中的实现
        """
        # 导入TaskManager
        from .etl.task_manager import TaskManager
        
        # 创建TaskManager实例
        task_manager = TaskManager(self.db)
        
        # 调用TaskManager的get_task_history方法
        return task_manager.get_task_history(task_id, limit)
    
    def add_task_history(self, task_id: int, status: str, start_time: datetime, end_time: datetime = None, 
                        rows_processed: int = 0, error_message: str = None) -> Optional[ETLTaskHistory]:
        """
        添加ETL任务执行历史
        使用etl/task_manager.py中的实现
        """
        # 导入TaskManager
        from .etl.task_manager import TaskManager
        
        # 创建TaskManager实例
        task_manager = TaskManager(self.db)
        
        # 调用TaskManager的add_task_history方法
        return task_manager.add_task_history(
            task_id=task_id,
            status=status,
            start_time=start_time,
            end_time=end_time,
            rows_processed=rows_processed,
            error_message=error_message
        )
    
    def get_all_connections(self) -> List[DatabaseConnection]:
        """
        获取所有数据库连接
        使用etl/connection_manager.py中的实现
        """
        # 导入ConnectionManager
        from .etl.connection_manager import ConnectionManager
        
        # 创建ConnectionManager实例
        connection_manager = ConnectionManager(self.db)
        
        # 调用ConnectionManager的get_all_connections方法
        return connection_manager.get_all_connections()
    
    def get_connection_by_id(self, connection_id: str) -> Optional[DatabaseConnection]:
        """
        根据ID获取数据库连接
        使用etl/connection_manager.py中的实现
        """
        # 导入ConnectionManager
        from .etl.connection_manager import ConnectionManager
        
        # 创建ConnectionManager实例
        connection_manager = ConnectionManager(self.db)
        
        # 调用ConnectionManager的get_connection_by_id方法
        return connection_manager.get_connection_by_id(connection_id)
    
    def create_connection(self, connection_data: etl_schemas.DatabaseConnectionCreate) -> DatabaseConnection:
        """
        创建数据库连接
        使用etl/connection_manager.py中的实现
        """
        # 导入ConnectionManager
        from .etl.connection_manager import ConnectionManager
        
        # 创建ConnectionManager实例
        connection_manager = ConnectionManager(self.db)
        
        # 调用ConnectionManager的create_connection方法
        return connection_manager.create_connection(connection_data)
    
    def delete_connection(self, connection_id: str) -> bool:
        """
        删除数据库连接
        使用etl/connection_manager.py中的实现
        """
        # 导入ConnectionManager
        from .etl.connection_manager import ConnectionManager
        
        # 创建ConnectionManager实例
        connection_manager = ConnectionManager(self.db)
        
        # 调用ConnectionManager的delete_connection方法
        return connection_manager.delete_connection(connection_id)
    
    def test_connection(self, connection_data: etl_schemas.DatabaseConnectionCreate) -> Dict[str, Any]:
        """
        测试数据库连接
        使用etl/connection_manager.py中的实现
        """
        # 导入ConnectionManager
        from .etl.connection_manager import ConnectionManager
        
        # 创建ConnectionManager实例
        connection_manager = ConnectionManager(self.db)
        
        # 调用ConnectionManager的test_connection方法
        return connection_manager.test_connection(connection_data)
    
    def get_connection_engine(self, connection_id: str) -> Any:
        """
        获取数据库连接引擎
        使用etl/connection_manager.py中的实现
        """
        # 导入ConnectionManager
        from .etl.connection_manager import ConnectionManager
        
        # 创建ConnectionManager实例
        connection_manager = ConnectionManager(self.db)
        
        # 调用ConnectionManager的get_connection_engine方法
        return connection_manager.get_connection_engine(connection_id)
    
    def run_task(self, task_id: str) -> ETLTask:
        """
        运行ETL任务
        使用etl/base.py中的实现
        """
        # 导入ETLService基类
        from .etl.base import ETLService as ETLServiceBase
        
        # 创建ETLServiceBase实例
        etl_service_base = ETLServiceBase(self.db)
        
        # 调用基类的run_task方法
        return etl_service_base.run_task(task_id)
    
    def _execute_task(self, task_id: str, start_time: datetime):
        """
        执行ETL任务（在后台线程中运行）
        使用etl/base.py中的实现
        """
        # 导入ETLService基类
        from .etl.base import ETLService as ETLServiceBase
        
        # 创建ETLServiceBase实例
        etl_service_base = ETLServiceBase(self.db)
        
        # 调用基类的_execute_task方法
        return etl_service_base._execute_task(task_id, start_time)
    
    def test_sql(self, connection_id: str, sql: str) -> Dict[str, Any]:
        """
        测试SQL语句
        使用etl/custom_sql.py中的实现
        """
        # 导入CustomSQLExecutor
        from .etl.custom_sql import CustomSQLExecutor
        
        # 创建CustomSQLExecutor实例
        custom_sql = CustomSQLExecutor(self.db)
        
        # 调用CustomSQLExecutor的test_sql方法
        return custom_sql.test_sql(connection_id, sql)