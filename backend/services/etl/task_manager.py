# ETL任务管理模块
# 负责ETL任务的CRUD操作和历史记录

import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from models.models import ETLTask, ETLTaskHistory, generate_bigint_id
from schemas import etl_schemas

# 配置日志
logger = logging.getLogger(__name__)

class TaskManager:
    """
    ETL任务管理类
    负责ETL任务的CRUD操作和历史记录
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_tasks(self) -> List[ETLTask]:
        """
        获取所有ETL任务
        """
        return self.db.query(ETLTask).all()
    
    def get_task_by_id(self, task_id: int) -> Optional[ETLTask]:
        """
        根据ID获取ETL任务
        增强版：添加错误处理和重试机制
        """
        max_retries = 3
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                # 尝试执行查询
                result = self.db.query(ETLTask).filter(ETLTask.task_id == task_id).first()
                return result
            except Exception as e:
                # 记录错误
                retry_count += 1
                last_error = e
                logger.warning(f"获取任务失败，第{retry_count}次尝试: {e}")
                
                # 如果是连接错误，尝试重新连接
                try:
                    self.db.rollback()
                except Exception as rollback_error:
                    logger.error(f"回滚事务失败: {rollback_error}")
                
                # 如果已经达到最大重试次数，抛出异常
                if retry_count >= max_retries:
                    logger.error(f"获取任务失败，已达到最大重试次数: {e}")
                    break
                
                # 等待一段时间再重试
                import time
                time.sleep(1)  # 等待1秒再重试
        
        # 如果所有重试都失败，记录错误并返回None
        if last_error:
            logger.error(f"获取任务{task_id}失败: {last_error}")
        
        return None
    
    def create_task(self, task_data: etl_schemas.ETLTaskCreate) -> ETLTask:
        """
        创建ETL任务
        """
        logger.info(f"开始创建任务: 名称={task_data.name}, 类型={task_data.task_type}, 源连接ID={task_data.source_connection_id}, 目标连接ID={task_data.target_connection_id}")
        
        # 使用generate_bigint_id生成BigInteger类型的ID，而不是UUID
        from models.models import generate_bigint_id
        
        # 验证源连接和目标连接是否存在
        from models.models import DatabaseConnection
        
        logger.info(f"[创建任务] 开始验证源连接ID: {task_data.source_connection_id}")
        # 记录所有可用的连接ID，帮助调试
        all_connections = self.db.query(DatabaseConnection.connection_id).all()
        logger.info(f"[创建任务] 数据库中所有连接ID: {[conn[0] for conn in all_connections]}")
        
        if task_data.source_connection_id:
            logger.info(f"[创建任务] 查询源连接: {task_data.source_connection_id}")
            source_connection = self.db.query(DatabaseConnection).filter(DatabaseConnection.connection_id == task_data.source_connection_id).first()
            if not source_connection:
                error_msg = f"源连接不存在: {task_data.source_connection_id}，可用连接: {[conn[0] for conn in all_connections]}"
                logger.error(f"[创建任务] {error_msg}")
                raise ValueError(error_msg)
            else:
                logger.info(f"[创建任务] 找到源连接: {source_connection.name} (ID: {source_connection.connection_id})")
        
        if task_data.target_connection_id:
            logger.info(f"[创建任务] 查询目标连接: {task_data.target_connection_id}")
            target_connection = self.db.query(DatabaseConnection).filter(DatabaseConnection.connection_id == task_data.target_connection_id).first()
            if not target_connection:
                error_msg = f"目标连接不存在: {task_data.target_connection_id}，可用连接: {[conn[0] for conn in all_connections]}"
                logger.error(f"[创建任务] {error_msg}")
                if task_data.task_type in ["mysql_to_postgres", "postgres_to_redis", "mysql_to_redis"]:
                    logger.error(f"[创建任务] 任务类型 {task_data.task_type} 需要有效的目标连接，无法创建任务")
                    raise ValueError(error_msg)
                else:
                    logger.warning(f"[创建任务] 任务类型 {task_data.task_type} 可以没有目标连接，继续创建任务")
            else:
                logger.info(f"[创建任务] 找到目标连接: {target_connection.name} (ID: {target_connection.connection_id})")
        
        # 验证配置是否完整
        if task_data.task_type == "mysql_to_postgres":
            if not task_data.config.get("source_table") or not task_data.config.get("target_table"):
                logger.warning(f"MySQL到PostgreSQL任务缺少必要的配置: source_table, target_table")
        elif task_data.task_type == "postgres_to_redis" or task_data.task_type == "mysql_to_redis":
            if not task_data.config.get("source_query") or not task_data.config.get("key_field"):
                logger.warning(f"{task_data.task_type}任务缺少必要的配置: source_query, key_field")
        elif task_data.task_type == "custom_sql":
            if not task_data.config.get("sql"):
                logger.warning(f"自定义SQL任务缺少必要的配置: sql")
        
        # 创建任务，让数据库自动生成ID
        task = ETLTask(
            name=task_data.name,
            description=task_data.description,
            task_type=task_data.task_type,
            source_connection_id=task_data.source_connection_id,
            target_connection_id=task_data.target_connection_id,
            config=task_data.config,
            schedule=task_data.schedule,
            status="pending",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        logger.info(f"任务创建成功: ID={task.task_id}, 名称={task.name}, 源连接ID={task.source_connection_id}, 目标连接ID={task.target_connection_id}")
        return task
    
    def update_task_status(self, task_id: int, status: str) -> Optional[ETLTask]:
        """
        更新ETL任务状态
        """
        task = self.get_task_by_id(task_id)
        if task:
            task.status = status
            task.updated_at = datetime.now()
            self.db.commit()
            self.db.refresh(task)
            return task
        return None
    
    def update_task(self, task_id: int, task_data: etl_schemas.ETLTaskCreate) -> Optional[ETLTask]:
        """
        更新ETL任务
        """
        logger.info(f"开始更新任务: ID={task_id}, 名称={task_data.name}, 源连接ID={task_data.source_connection_id}, 目标连接ID={task_data.target_connection_id}")
        
        task = self.get_task_by_id(task_id)
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return None
        
        logger.info(f"找到任务: ID={task.task_id}, 名称={task.name}, 当前源连接ID={task.source_connection_id}, 当前目标连接ID={task.target_connection_id}")
        
        # 验证源连接和目标连接是否存在
        from models.models import DatabaseConnection
        
        logger.info(f"开始验证源连接ID: {task_data.source_connection_id}")
        # 记录所有可用的连接ID，帮助调试
        all_connections = self.db.query(DatabaseConnection.connection_id).all()
        logger.info(f"数据库中所有连接ID: {[conn[0] for conn in all_connections]}")
        
        if task_data.source_connection_id:
            logger.info(f"查询源连接: {task_data.source_connection_id}")
            source_connection = self.db.query(DatabaseConnection).filter(DatabaseConnection.connection_id == task_data.source_connection_id).first()
            if not source_connection:
                logger.error(f"源连接不存在: {task_data.source_connection_id}，可用连接: {[conn[0] for conn in all_connections]}")
                # 外键约束会失败，所以直接返回None
                return None
            else:
                logger.info(f"找到源连接: {source_connection.name} (ID: {source_connection.connection_id})")
        
        if task_data.target_connection_id:
            logger.info(f"查询目标连接: {task_data.target_connection_id}")
            target_connection = self.db.query(DatabaseConnection).filter(DatabaseConnection.connection_id == task_data.target_connection_id).first()
            if not target_connection:
                logger.error(f"目标连接不存在: {task_data.target_connection_id}，可用连接: {[conn[0] for conn in all_connections]}")
                # 如果目标连接是必需的，也应该返回None
                if task_data.task_type in ["mysql_to_postgres", "postgres_to_redis", "mysql_to_redis"]:
                    logger.error(f"任务类型 {task_data.task_type} 需要有效的目标连接，无法更新任务")
                    return None
                else:
                    logger.warning(f"任务类型 {task_data.task_type} 可以没有目标连接，继续更新任务")
            else:
                logger.info(f"找到目标连接: {target_connection.name} (ID: {target_connection.connection_id})")
        
        # 验证配置是否完整
        if task_data.task_type == "mysql_to_postgres":
            if not task_data.config.get("source_table") or not task_data.config.get("target_table"):
                logger.warning(f"MySQL到PostgreSQL任务缺少必要的配置: source_table, target_table")
        elif task_data.task_type == "postgres_to_redis" or task_data.task_type == "mysql_to_redis":
            if not task_data.config.get("source_query") or not task_data.config.get("key_field"):
                logger.warning(f"{task_data.task_type}任务缺少必要的配置: source_query, key_field")
        elif task_data.task_type == "custom_sql":
            if not task_data.config.get("sql"):
                logger.warning(f"自定义SQL任务缺少必要的配置: sql")
            
        # 更新任务属性
        task.name = task_data.name
        task.description = task_data.description
        task.task_type = task_data.task_type
        task.source_connection_id = task_data.source_connection_id
        task.target_connection_id = task_data.target_connection_id
        task.config = task_data.config
        task.schedule = task_data.schedule
        task.updated_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(task)
        
        logger.info(f"任务更新成功: ID={task.task_id}, 名称={task.name}, 源连接ID={task.source_connection_id}, 目标连接ID={task.target_connection_id}")
        return task
    
    def delete_task(self, task_id: int) -> bool:
        """
        删除ETL任务
        """
        task = self.get_task_by_id(task_id)
        if task:
            self.db.delete(task)
            self.db.commit()
            return True
        return False
    
    def get_task_history(self, task_id: int, limit: int = 10) -> List[ETLTaskHistory]:
        """
        获取ETL任务执行历史
        """
        return self.db.query(ETLTaskHistory).filter(
            ETLTaskHistory.task_id == task_id
        ).order_by(ETLTaskHistory.start_time.desc()).limit(limit).all()
    
    def add_task_history(self, task_id: int, status: str, start_time: datetime, end_time: datetime = None, 
                        rows_processed: int = 0, error_message: str = None) -> ETLTaskHistory:
        """
        添加ETL任务执行历史
        """
        # 使用generate_bigint_id函数生成BigInteger类型的ID
        history = ETLTaskHistory(
            task_id=task_id,
            status=status,
            start_time=start_time,
            end_time=end_time or datetime.now(),
            rows_processed=rows_processed,
            error_message=error_message
        )
        
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        
        return history