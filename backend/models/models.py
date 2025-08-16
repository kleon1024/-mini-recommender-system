from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime, JSON, func, UniqueConstraint, BigInteger
from sqlalchemy.orm import relationship
from database import Base
import time
import random
from datetime import datetime

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