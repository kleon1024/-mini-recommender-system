from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 数据库连接配置
# 添加charset=utf8mb4参数确保正确处理中文字符
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://user:password@localhost:3306/recommender?charset=utf8mb4")

# 创建SQLAlchemy引擎
# 添加连接池配置和错误处理机制
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "init_command": "SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;",
    },
    # 连接池配置
    pool_size=10,                # 连接池大小
    max_overflow=20,            # 最大溢出连接数
    pool_timeout=30,            # 连接池获取连接的超时时间
    pool_recycle=1800,          # 连接回收时间(30分钟)
    pool_pre_ping=True,         # 连接前ping一下，确保连接有效
    # 错误处理
    isolation_level="READ COMMITTED"  # 事务隔离级别
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建Base类
Base = declarative_base()

# 获取数据库会话
def get_db():
    db = None
    try:
        db = SessionLocal()
        # 执行一个简单查询，确保连接有效
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        yield db
    except Exception as e:
        # 记录错误但不抛出，让应用继续运行
        import logging
        logging.error(f"数据库连接错误: {e}")
        # 如果已经创建了会话但出错，回滚任何未提交的事务
        if db is not None:
            try:
                db.rollback()
            except Exception as rollback_error:
                logging.error(f"回滚事务失败: {rollback_error}")
        # 重新抛出异常，让FastAPI处理
        raise
    finally:
        # 确保连接被关闭，即使发生异常
        if db is not None:
            try:
                db.close()
            except Exception as close_error:
                # 只记录错误，不抛出
                import logging
                logging.error(f"关闭数据库连接失败: {close_error}")

# 初始化数据库
def init_db():
    # 在生产环境中，应该使用数据库迁移工具如Alembic
    # 这里为了简化，直接创建表
    from models import models
    Base.metadata.create_all(bind=engine)