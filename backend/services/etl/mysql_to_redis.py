# MySQL到Redis同步模块
# 负责MySQL到Redis的数据同步

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from models.models import ETLTask

# 配置日志
logger = logging.getLogger(__name__)

class MySQLToRedisETL:
    """
    MySQL到Redis同步类
    负责MySQL到Redis的数据同步
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def execute(self, task: ETLTask) -> int:
        """
        执行MySQL到Redis的ETL任务
        返回处理的行数
        """
        # 获取源连接和目标连接
        from .connection_manager import ConnectionManager
        connection_manager = ConnectionManager(self.db)
        
        source_engine = connection_manager.get_connection_engine(task.source_connection_id)
        redis_client = connection_manager.get_connection_engine(task.target_connection_id)
        
        # 解析配置
        config = task.config
        source_query = config.get("source_query")
        key_prefix = config.get("key_prefix", "")
        key_field = config.get("key_field")
        expire_seconds = config.get("expire_seconds")
        
        # 验证配置
        self._validate_config(task, source_query, key_field)
        
        try:
            # 导入pandas
            try:
                import pandas as pd
            except ImportError:
                raise ImportError("缺少pandas依赖，数据处理功能不可用")
            
            # 执行查询
            from sqlalchemy import text
            df = pd.read_sql(text(source_query), source_engine)
            
            if df.empty:
                logger.info("没有数据需要同步到Redis")
                return 0
            
            # 写入Redis
            total_rows = len(df)
            logger.info(f"需要同步 {total_rows} 行数据到Redis")
            
            for _, row in df.iterrows():
                key = f"{key_prefix}{row[key_field]}"
                value = row.to_json()
                redis_client.set(key, value)
                
                # 设置过期时间
                if expire_seconds:
                    redis_client.expire(key, int(expire_seconds))
            
            logger.info(f"同步到Redis完成，共 {total_rows} 行")
            return total_rows
        except Exception as e:
            logger.error(f"MySQL到Redis同步失败: {e}")
            raise
    
    def _validate_config(self, task: ETLTask, source_query: Optional[str], key_field: Optional[str]) -> None:
        """
        验证任务配置
        """
        if not source_query:
            # 尝试从任务名称中提取查询
            if task.name and 'mysql' in task.name.lower():
                # 使用默认查询
                source_query = f"SELECT * FROM users LIMIT 1000"
                task.config["source_query"] = source_query
                logger.warning(f"缺少source_query配置，使用默认值: {source_query}")
        
        if not key_field:
            # 使用默认键字段
            key_field = "id"
            task.config["key_field"] = key_field
            logger.warning(f"缺少key_field配置，使用默认值: {key_field}")
        
        # 更新任务配置
        self.db.commit()
        
        # 如果仍然无法获取必要配置，则抛出异常
        if not source_query or not key_field:
            raise ValueError(f"缺少必要的配置: source_query={source_query}, key_field={key_field}")