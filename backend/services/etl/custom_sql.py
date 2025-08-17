# 自定义SQL执行模块
# 负责执行自定义SQL语句

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from models.models import ETLTask

# 配置日志
logger = logging.getLogger(__name__)

class CustomSQLExecutor:
    """
    自定义SQL执行类
    负责执行自定义SQL语句
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def execute(self, task: ETLTask) -> int:
        """
        执行自定义SQL
        返回影响的行数
        """
        # 获取源连接
        from .connection_manager import ConnectionManager
        connection_manager = ConnectionManager(self.db)
        engine = connection_manager.get_connection_engine(task.source_connection_id)
        
        # 解析配置
        config = task.config
        sql = config.get("sql")
        
        # 验证配置
        self._validate_config(task, sql)
        
        try:
            # 检查连接类型
            import redis
            if isinstance(engine, redis.Redis):
                raise ValueError("不支持在Redis上执行自定义SQL")
            
            # 记录SQL信息
            logger.info(f"准备执行SQL: {task.name}, 连接ID: {task.source_connection_id}")
            logger.debug(f"SQL内容: {sql[:200]}..." if len(sql) > 200 else f"SQL内容: {sql}")
            
            # 执行SQL - 使用SQLAlchemy 2.0 API
            try:
                with engine.connect() as conn:
                    logger.debug("成功建立数据库连接")
                    result = conn.execute(text(sql))
                    rows_affected = result.rowcount
                    logger.debug(f"SQL执行完成，影响行数: {rows_affected}")
            except Exception as sql_e:
                logger.error(f"SQL执行过程中出错: {sql_e}")
                logger.error(f"SQL: {sql}")
                raise
            
            logger.info(f"执行自定义SQL完成，影响 {rows_affected} 行")
            return rows_affected
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"执行自定义SQL失败: {e}")
            logger.error(f"详细错误信息: {error_trace}")
            raise
    
    def _validate_config(self, task: ETLTask, sql: Optional[str]) -> None:
        """
        验证任务配置
        """
        if not sql:
            # 尝试从任务名称中提取SQL
            if task.name and 'sql' in task.name.lower():
                # 使用默认SQL
                sql = "SELECT 1"
                task.config["sql"] = sql
                logger.warning(f"缺少sql配置，使用默认值: {sql}")
            else:
                raise ValueError("缺少必要的配置: sql")
        
        # 更新任务配置
        self.db.commit()
    
    def test_sql(self, connection_id: str, sql: str) -> Dict[str, Any]:
        """
        测试SQL语句
        """
        try:
            # 获取连接
            from .connection_manager import ConnectionManager
            connection_manager = ConnectionManager(self.db)
            engine = connection_manager.get_connection_engine(connection_id)
            
            # 检查连接类型
            import redis
            if isinstance(engine, redis.Redis):
                return {
                    "success": False,
                    "message": "不支持在Redis上执行SQL",
                    "error": "不支持的连接类型"
                }
            
            # 执行SQL - 使用SQLAlchemy 2.0 API
            logger.debug(f"准备执行SQL: {sql[:100]}...")
            with engine.connect() as conn:
                logger.debug("成功建立数据库连接")
                result = conn.execute(text(sql))
                logger.debug(f"SQL执行完成，检查结果类型")
                
                # 如果是SELECT语句，返回结果集
                if result.returns_rows:
                    columns = result.keys()
                    data = [dict(row) for row in result]
                    return {
                        "success": True,
                        "message": f"查询成功，返回 {len(data)} 行数据",
                        "columns": columns,
                        "data": data
                    }
                else:
                    # 如果是非SELECT语句，返回影响的行数
                    return {
                        "success": True,
                        "message": f"执行成功，影响 {result.rowcount} 行",
                        "rows_affected": result.rowcount
                    }
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"测试SQL失败: {e}")
            logger.error(f"详细错误信息: {error_trace}")
            return {
                "success": False,
                "message": f"执行SQL失败: {str(e)}",
                "error": str(e),
                "traceback": error_trace
            }