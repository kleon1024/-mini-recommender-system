from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

# 点赞和收藏相关模式
class LikeBase(BaseModel):
    user_id: int
    post_id: int
    
class LikeCreate(LikeBase):
    pass

class LikeResponse(LikeBase):
    like_id: int
    create_time: datetime
    
    class Config:
        orm_mode = True

class FavoriteBase(BaseModel):
    user_id: int
    post_id: int
    
class FavoriteCreate(FavoriteBase):
    pass

class FavoriteResponse(FavoriteBase):
    favorite_id: int
    create_time: datetime
    
    class Config:
        orm_mode = True

# 用户相关模式
class UserBase(BaseModel):
    username: str
    tags: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None

class UserCreate(UserBase):
    pass

class UserUpdate(UserBase):
    username: Optional[str] = None

class UserResponse(UserBase):
    user_id: int
    create_time: datetime
    
    class Config:
        orm_mode = True

# 内容相关模式
class PostBase(BaseModel):
    title: str
    content: str
    tags: Optional[Dict[str, Any]] = None

class PostCreate(PostBase):
    author_id: int

class PostUpdate(PostBase):
    title: Optional[str] = None
    content: Optional[str] = None

class PostResponse(PostBase):
    post_id: int
    author_id: int
    create_time: datetime
    view_count: int
    like_count: int
    favorite_count: int
    
    class Config:
        orm_mode = True

class PostDetailResponse(PostResponse):
    author: UserResponse
    is_liked: Optional[bool] = False
    is_favorited: Optional[bool] = False
    
    class Config:
        orm_mode = True

# 行为相关模式
class EventBase(BaseModel):
    user_id: int
    post_id: int
    event_type: str
    source: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None
    extra: Optional[Dict[str, Any]] = None

class EventCreate(EventBase):
    pass

class EventResponse(EventBase):
    event_id: int
    timestamp: datetime
    
    class Config:
        orm_mode = True

# 批量事件上报
class BatchEventCreate(BaseModel):
    events: List[EventCreate]

# 特征相关模式
class FeatureBase(BaseModel):
    entity_type: str
    entity_id: int
    feature_type: str
    feature_value: Dict[str, Any]

class FeatureCreate(FeatureBase):
    pass

class FeatureUpdate(BaseModel):
    feature_value: Dict[str, Any]

class FeatureResponse(FeatureBase):
    feature_id: int
    update_time: datetime
    
    class Config:
        orm_mode = True

# 推荐相关模式
class RecommendationRequest(BaseModel):
    user_id: int
    count: int = 10
    offset: int = 0
    filters: Optional[Dict[str, Any]] = None

class RecommendationResponse(BaseModel):
    items: List[PostResponse]
    has_more: bool
    total: int

# 数据处理任务
class DataTaskCreate(BaseModel):
    task_type: str
    params: Optional[Dict[str, Any]] = None

class DataTaskResponse(BaseModel):
    task_id: int
    task_type: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None

# 模型训练任务
class ModelTaskCreate(BaseModel):
    model_type: str
    params: Optional[Dict[str, Any]] = None

class ModelTaskResponse(BaseModel):
    task_id: int
    model_type: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    metrics: Optional[Dict[str, Any]] = None