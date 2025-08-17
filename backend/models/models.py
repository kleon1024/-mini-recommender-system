from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime, JSON, func, UniqueConstraint, BigInteger
from sqlalchemy.orm import relationship
from database import Base
import time
import random
from datetime import datetime

# ETL相关模型
class DatabaseConnection(Base):
    __tablename__ = "database_connections"
    
    connection_id = Column(BigInteger, primary_key=True, default=lambda: generate_bigint_id())
    name = Column(String(100), nullable=False)
    description = Column(Text)
    connection_type = Column(String(20), nullable=False)  # mysql, postgres, redis
    host = Column(String(100), nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String(100))
    password = Column(String(100))
    database = Column(String(100))
    config = Column(JSON)  # 其他连接配置
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ETLTask(Base):
    __tablename__ = "etl_tasks"
    
    task_id = Column(BigInteger, primary_key=True, default=lambda: generate_bigint_id())
    name = Column(String(100), nullable=False)
    description = Column(Text)
    task_type = Column(String(50), nullable=False)  # mysql_to_postgres, postgres_to_redis, mysql_to_redis, custom_sql
    source_connection_id = Column(BigInteger, ForeignKey("database_connections.connection_id"))
    target_connection_id = Column(BigInteger, ForeignKey("database_connections.connection_id"), nullable=True)
    config = Column(JSON, nullable=False)  # 任务配置，如表名、查询、批量大小等
    schedule = Column(String(100))  # cron表达式
    status = Column(String(20), default="pending")  # pending, running, completed, failed, cancelled
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    result = Column(JSON)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    source_connection = relationship("DatabaseConnection", foreign_keys=[source_connection_id])
    target_connection = relationship("DatabaseConnection", foreign_keys=[target_connection_id])

class ETLTaskHistory(Base):
    __tablename__ = "etl_task_history"
    
    history_id = Column(BigInteger, primary_key=True, default=lambda: generate_bigint_id())
    task_id = Column(BigInteger, ForeignKey("etl_tasks.task_id"), nullable=False)
    status = Column(String(20), nullable=False)  # completed, failed
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    rows_processed = Column(Integer, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    task = relationship("ETLTask")

class ETLLog(Base):
    __tablename__ = "etl_logs"
    
    log_id = Column(BigInteger, primary_key=True, default=lambda: generate_bigint_id())
    task_id = Column(BigInteger, ForeignKey("etl_tasks.task_id"), nullable=False)
    log_level = Column(String(16), nullable=False)  # info, warning, error
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    task = relationship("ETLTask")

# 生成唯一的bigint ID
def generate_bigint_id():
    # 使用时间戳和随机数生成唯一ID
    timestamp = int(time.time() * 1000)  # 毫秒级时间戳
    random_part = random.randint(1000, 9999)  # 随机数部分
    return timestamp * 10000 + random_part  # 组合成唯一ID

# 用户模型
class User(Base):
    __tablename__ = "users"
    
    user_id = Column(BigInteger, primary_key=True, default=generate_bigint_id)
    username = Column(String(64), nullable=False)
    create_time = Column(DateTime, default=datetime.utcnow)
    tags = Column(JSON)
    preferences = Column(JSON)
    
    # 关系
    posts = relationship("Post", back_populates="author")
    events = relationship("Event", back_populates="user")

# 内容模型
class Post(Base):
    __tablename__ = "posts"
    
    post_id = Column(BigInteger, primary_key=True, default=generate_bigint_id)
    title = Column(String(128), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    create_time = Column(DateTime, default=datetime.utcnow)
    tags = Column(JSON)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    favorite_count = Column(Integer, default=0)
    
    # 关系
    author = relationship("User", back_populates="posts")
    events = relationship("Event", back_populates="post")

# 行为模型
class Event(Base):
    __tablename__ = "events"
    
    event_id = Column(BigInteger, primary_key=True, default=generate_bigint_id)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    post_id = Column(BigInteger, ForeignKey("posts.post_id"), nullable=False)
    event_type = Column(String(32), nullable=False)  # view, click, like, favorite, play, stay
    timestamp = Column(DateTime, default=datetime.utcnow)
    source = Column(String(64))
    device_info = Column(JSON)
    extra = Column(JSON)
    
    # 关系
    user = relationship("User", back_populates="events")
    post = relationship("Post", back_populates="events")

# 特征模型
class Feature(Base):
    __tablename__ = "features"
    
    feature_id = Column(BigInteger, primary_key=True, default=generate_bigint_id)
    entity_type = Column(String(32), nullable=False)  # user, post
    entity_id = Column(BigInteger, nullable=False)
    feature_type = Column(String(32), nullable=False)
    feature_value = Column(JSON, nullable=False)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# 点赞模型
class Like(Base):
    __tablename__ = "likes"
    
    like_id = Column(BigInteger, primary_key=True, default=generate_bigint_id)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    post_id = Column(BigInteger, ForeignKey("posts.post_id"), nullable=False)
    create_time = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("User")
    post = relationship("Post")
    
    # 确保用户对同一帖子只能点赞一次
    __table_args__ = (UniqueConstraint('user_id', 'post_id', name='uix_user_post_like'),)

# 收藏模型
class Favorite(Base):
    __tablename__ = "favorites"
    
    favorite_id = Column(BigInteger, primary_key=True, default=generate_bigint_id)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    post_id = Column(BigInteger, ForeignKey("posts.post_id"), nullable=False)
    create_time = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("User")
    post = relationship("Post")
    
    # 确保用户对同一帖子只能收藏一次
    __table_args__ = (UniqueConstraint('user_id', 'post_id', name='uix_user_post_favorite'),)