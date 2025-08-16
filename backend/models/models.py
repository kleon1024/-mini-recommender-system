from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime, JSON, func, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base
import uuid
from datetime import datetime

# 生成UUID
def generate_uuid():
    return str(uuid.uuid4())

# 用户模型
class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String(64), primary_key=True, default=generate_uuid)
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
    
    post_id = Column(String(64), primary_key=True, default=generate_uuid)
    title = Column(String(128), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(String(64), ForeignKey("users.user_id"), nullable=False)
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
    
    event_id = Column(String(64), primary_key=True, default=generate_uuid)
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False)
    post_id = Column(String(64), ForeignKey("posts.post_id"), nullable=False)
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
    
    feature_id = Column(String(64), primary_key=True, default=generate_uuid)
    entity_type = Column(String(32), nullable=False)  # user, post
    entity_id = Column(String(64), nullable=False)
    feature_type = Column(String(32), nullable=False)
    feature_value = Column(JSON, nullable=False)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# 点赞模型
class Like(Base):
    __tablename__ = "likes"
    
    like_id = Column(String(64), primary_key=True, default=generate_uuid)
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False)
    post_id = Column(String(64), ForeignKey("posts.post_id"), nullable=False)
    create_time = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("User")
    post = relationship("Post")
    
    # 确保用户对同一帖子只能点赞一次
    __table_args__ = (UniqueConstraint('user_id', 'post_id', name='uix_user_post_like'),)

# 收藏模型
class Favorite(Base):
    __tablename__ = "favorites"
    
    favorite_id = Column(String(64), primary_key=True, default=generate_uuid)
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False)
    post_id = Column(String(64), ForeignKey("posts.post_id"), nullable=False)
    create_time = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("User")
    post = relationship("Post")
    
    # 确保用户对同一帖子只能收藏一次
    __table_args__ = (UniqueConstraint('user_id', 'post_id', name='uix_user_post_favorite'),)