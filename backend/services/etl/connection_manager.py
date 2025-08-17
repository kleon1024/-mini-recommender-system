# 数据库连接管理模块
# 负责管理数据库连接的创建、测试和获取

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from models.models import DatabaseConnection
from schemas import etl_schemas

# 配置日志
logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    数据库连接管理类
    负责管理数据库连接的创建、测试和获取
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # 检查依赖是否可用
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
    
    def get_all_connections(self) -> List[DatabaseConnection]:
        """
        获取所有数据库连接
        """
        return self.db.query(DatabaseConnection).all()
    
    def get_connection_by_id(self, connection_id: str) -> Optional[DatabaseConnection]:
        """
        根据ID获取数据库连接
        """
        max_retries = 3
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                # 尝试执行查询
                result = self.db.query(DatabaseConnection).filter(DatabaseConnection.connection_id == connection_id).first()
                return result
            except Exception as e:
                # 记录错误
                retry_count += 1
                last_error = e
                logger.warning(f"获取连接失败，第{retry_count}次尝试: {e}")
                
                # 如果是连接错误，尝试重新连接
                try:
                    self.db.rollback()
                except Exception as rollback_error:
                    logger.error(f"回滚事务失败: {rollback_error}")
                
                # 如果已经达到最大重试次数，抛出异常
                if retry_count >= max_retries:
                    logger.error(f"获取连接失败，已达到最大重试次数: {e}")
                    break
                
                # 等待一段时间再重试
                import time
                time.sleep(1)  # 等待1秒再重试
        
        # 如果所有重试都失败，记录错误并返回None
        if last_error:
            logger.error(f"获取连接{connection_id}失败: {last_error}")
        
        return None
    
    def create_connection(self, connection_data: etl_schemas.DatabaseConnectionCreate) -> DatabaseConnection:
        """
        创建数据库连接
        """
        import uuid
        connection_id = str(uuid.uuid4())
        connection = DatabaseConnection(
            connection_id=connection_id,
            name=connection_data.name,
            description=connection_data.description,
            connection_type=connection_data.connection_type,
            host=connection_data.host,
            port=connection_data.port,
            username=connection_data.username,
            password=connection_data.password,
            database=connection_data.database,
            config=connection_data.config,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.db.add(connection)
        self.db.commit()
        self.db.refresh(connection)
        
        return connection
    
    def delete_connection(self, connection_id: str) -> bool:
        """
        删除数据库连接
        """
        connection = self.get_connection_by_id(connection_id)
        if connection:
            self.db.delete(connection)
            self.db.commit()
            return True
        return False
    
    def test_connection(self, connection_data: etl_schemas.DatabaseConnectionCreate) -> Dict[str, Any]:
        """
        测试数据库连接
        """
        try:
            if connection_data.connection_type == "mysql":
                if not self.pymysql_available:
                    return {"success": False, "message": "缺少pymysql依赖，MySQL连接功能不可用"}
                
                import pymysql
                conn = pymysql.connect(
                    host=connection_data.host,
                    port=connection_data.port,
                    user=connection_data.username,
                    password=connection_data.password,
                    db=connection_data.database,
                    charset='utf8mb4'
                )
                conn.close()
            elif connection_data.connection_type == "postgres":
                if not self.asyncpg_available:
                    return {"success": False, "message": "缺少asyncpg依赖，PostgreSQL连接功能不可用"}
                
                # 使用asyncpg进行异步连接测试
                import asyncio
                import asyncpg
                
                async def test_asyncpg_connection():
                    conn = await asyncpg.connect(
                        host=connection_data.host,
                        port=connection_data.port,
                        user=connection_data.username,
                        password=connection_data.password,
                        database=connection_data.database
                    )
                    await conn.close()
                
                # 运行异步测试函数
                asyncio.run(test_asyncpg_connection())
            elif connection_data.connection_type == "redis":
                if not self.redis_available:
                    return {"success": False, "message": "缺少redis依赖，Redis连接功能不可用"}
                
                import redis
                r = redis.Redis(
                    host=connection_data.host,
                    port=connection_data.port,
                    password=connection_data.password,
                    db=int(connection_data.database) if connection_data.database else 0,
                    decode_responses=True
                )
                r.ping()
            else:
                return {"success": False, "message": f"不支持的连接类型: {connection_data.connection_type}"}
            
            return {"success": True, "message": "连接成功"}
        except Exception as e:
            logger.error(f"连接测试失败: {e}")
            return {"success": False, "message": f"连接失败: {str(e)}"}
    
    def get_connection_engine(self, connection_id: str) -> Any:
        """
        获取数据库连接引擎
        """
        connection = self.get_connection_by_id(connection_id)
        if not connection:
            raise ValueError(f"连接不存在: {connection_id}")
        
        if connection.connection_type == "mysql":
            if not self.pymysql_available:
                raise ImportError("缺少pymysql依赖，MySQL连接功能不可用")
            
            return create_engine(f"mysql+pymysql://{connection.username}:{connection.password}@{connection.host}:{connection.port}/{connection.database}")
        elif connection.connection_type == "postgres":
            if not self.asyncpg_available:
                raise ImportError("缺少asyncpg依赖，PostgreSQL连接功能不可用")
            
            # 对于同步操作，使用SQLAlchemy引擎
            return create_engine(f"postgresql://{connection.username}:{connection.password}@{connection.host}:{connection.port}/{connection.database}")
        elif connection.connection_type == "redis":
            if not self.redis_available:
                raise ImportError("缺少redis依赖，Redis连接功能不可用")
            
            import redis
            return redis.Redis(
                host=connection.host,
                port=connection.port,
                password=connection.password,
                db=int(connection.database) if connection.database else 0,
                decode_responses=True
            )
        else:
            raise ValueError(f"不支持的连接类型: {connection.connection_type}")