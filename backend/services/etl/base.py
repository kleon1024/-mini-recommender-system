# ETL服务基础模块
# 定义ETLService类，整合各个子模块的功能

import os
import sys
import time
import logging
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.orm import Session

# 导入子模块
from .connection_manager import ConnectionManager
from .task_manager import TaskManager
from .mysql_to_postgres import MySQLToPostgresETL
from .postgres_to_redis import PostgresToRedisETL
from .mysql_to_redis import MySQLToRedisETL
from .custom_sql import CustomSQLExecutor

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
        
        # 初始化各个子模块
        self.connection_manager = ConnectionManager(db)
        self.task_manager = TaskManager(db)
        self.mysql_to_postgres = MySQLToPostgresETL(db)
        self.postgres_to_redis = PostgresToRedisETL(db)
        self.mysql_to_redis = MySQLToRedisETL(db)
        self.custom_sql = CustomSQLExecutor(db)
        
        # 检查依赖是否可用
        self._check_dependencies()
    
    def _check_dependencies(self):
        """
        检查依赖是否可用
        """
        try:
            import pandas as pd
            self.pandas_available = True
        except ImportError:
            self.pandas_available = False
            logging.warning("缺少pandas依赖，数据处理功能不可用")
        
        try:
            import pymysql
            self.pymysql_available = True
        except ImportError:
            self.pymysql_available = False
            logging.warning("缺少pymysql依赖，MySQL连接功能不可用")
        
        try:
            import asyncpg
            self.asyncpg_available = True
        except ImportError:
            self.asyncpg_available = False
            logging.warning("缺少asyncpg依赖，PostgreSQL连接功能不可用")
        
        try:
            import redis
            self.redis_available = True
        except ImportError:
            self.redis_available = False
            logging.warning("缺少redis依赖，Redis连接功能不可用")
        
        if not all([self.pandas_available, self.pymysql_available, self.asyncpg_available, self.redis_available]):
            logging.warning("ETL服务部分功能不可用，缺少必要的依赖")
    
    # 任务管理相关方法 - 委托给TaskManager
    def get_all_tasks(self):
        return self.task_manager.get_all_tasks()
    
    def get_task_by_id(self, task_id):
        return self.task_manager.get_task_by_id(task_id)
    
    def create_task(self, task_data):
        return self.task_manager.create_task(task_data)
    
    def update_task_status(self, task_id, status):
        return self.task_manager.update_task_status(task_id, status)
    
    def update_task(self, task_id, task_data):
        return self.task_manager.update_task(task_id, task_data)
    
    def delete_task(self, task_id):
        return self.task_manager.delete_task(task_id)
    
    def get_task_history(self, task_id, limit=10):
        return self.task_manager.get_task_history(task_id, limit)
    
    def add_task_history(self, task_id, status, start_time, end_time=None, rows_processed=0, error_message=None):
        return self.task_manager.add_task_history(task_id, status, start_time, end_time, rows_processed, error_message)
    
    # 连接管理相关方法 - 委托给ConnectionManager
    def get_all_connections(self):
        return self.connection_manager.get_all_connections()
    
    def get_connection_by_id(self, connection_id):
        return self.connection_manager.get_connection_by_id(connection_id)
    
    def create_connection(self, connection_data):
        return self.connection_manager.create_connection(connection_data)
    
    def delete_connection(self, connection_id):
        return self.connection_manager.delete_connection(connection_id)
    
    def test_connection(self, connection_data):
        return self.connection_manager.test_connection(connection_data)
    
    def get_connection_engine(self, connection_id):
        return self.connection_manager.get_connection_engine(connection_id)
    
    # 任务执行相关方法
    def run_task(self, task_id: int):
        """
        运行ETL任务
        """
        task = self.get_task_by_id(task_id)
        if not task:
            raise ValueError(f"任务不存在: {task_id}")
        
        # 如果任务已经在运行，则返回
        if task_id in self.running_tasks:
            return task
        
        # 更新任务状态为运行中
        task = self.update_task_status(task_id, "running")
        
        # 记录任务开始时间
        start_time = datetime.now()
        
        # 在后台线程中运行任务
        thread = threading.Thread(target=self._execute_task, args=(task_id, start_time))
        thread.daemon = True
        thread.start()
        
        # 记录运行中的任务
        self.running_tasks[task_id] = thread
        
        return task
    
    def _execute_task(self, task_id: int, start_time: datetime):
        """
        执行ETL任务（在后台线程中运行）
        """
        task = None
        rows_processed = 0
        error_message = None
        end_time = None
        
        try:
            # 获取任务信息
            task = self.get_task_by_id(task_id)
            if not task:
                error_message = f"任务不存在: {task_id}"
                logger.error(error_message)
                return
            
            logger.info(f"开始执行任务: {task.name} (ID: {task_id})")
            
            # 根据任务类型执行不同的ETL逻辑
            if task.task_type == "mysql_to_postgres":
                rows_processed = self.mysql_to_postgres.execute(task)
            elif task.task_type == "postgres_to_redis":
                rows_processed = self.postgres_to_redis.execute(task)
            elif task.task_type == "mysql_to_redis":
                rows_processed = self.mysql_to_redis.execute(task)
            elif task.task_type == "custom_sql":
                rows_processed = self.custom_sql.execute(task)
            else:
                raise ValueError(f"不支持的任务类型: {task.task_type}")
            
            # 更新任务状态为完成
            self.update_task_status(task_id, "completed")
            logger.info(f"任务执行成功: {task.name} (ID: {task_id}), 处理了 {rows_processed} 行数据")
        except Exception as e:
            # 捕获并记录详细的异常信息
            import traceback
            error_detail = traceback.format_exc()
            error_message = f"{str(e)}\n\n{error_detail}"
            logger.error(f"任务执行失败: {task_id}\n{error_message}")
            
            # 更新任务状态为失败
            try:
                self.update_task_status(task_id, "failed")
            except Exception as update_error:
                logger.error(f"更新任务状态失败: {update_error}")
        finally:
            # 记录结束时间
            end_time = datetime.now()
            
            # 尝试记录任务执行历史
            try:
                self.add_task_history(
                    task_id=task_id,
                    status="completed" if error_message is None else "failed",
                    start_time=start_time,
                    end_time=end_time,
                    rows_processed=rows_processed,
                    error_message=error_message
                )
                logger.info(f"已记录任务历史: {task_id}")
            except Exception as history_error:
                logger.error(f"记录任务历史失败: {history_error}")
            
            # 从运行中的任务列表中移除
            try:
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]
                    logger.info(f"已从运行中任务列表移除: {task_id}")
            except Exception as remove_error:
                logger.error(f"从运行中任务列表移除失败: {remove_error}")
            
            # 记录任务总执行时间
            if start_time and end_time:
                duration = (end_time - start_time).total_seconds()
                logger.info(f"任务总执行时间: {duration:.2f} 秒")
            
            # 强制进行垃圾回收，释放内存
            import gc
            gc.collect()
    
    # SQL测试方法 - 委托给CustomSQLExecutor
    def test_sql(self, connection_id, sql):
        return self.custom_sql.test_sql(connection_id, sql)