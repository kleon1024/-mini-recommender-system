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
# 添加connect_args参数，确保每次连接都设置正确的字符集
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "init_command": "SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;",
    }
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建Base类
Base = declarative_base()

# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 初始化数据库
def init_db():
    # 在生产环境中，应该使用数据库迁移工具如Alembic
    # 这里为了简化，直接创建表
    from models import models
    Base.metadata.create_all(bind=engine)