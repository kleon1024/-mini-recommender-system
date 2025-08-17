from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
import logging

from database import get_db
from models.models import Event, User, Post
from schemas import schemas
from redis_client import record_user_viewed_post

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/events", response_model=schemas.EventResponse, status_code=201)
def create_event(event: schemas.EventCreate, db: Session = Depends(get_db)):
    """
    创建单个用户行为事件
    """
    # 验证用户是否存在
    user = db.query(User).filter(User.user_id == int(event.user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 验证帖子是否存在
    post = db.query(Post).filter(Post.post_id == int(event.post_id)).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # 创建事件
    db_event = Event(
        user_id=event.user_id,
        post_id=event.post_id,
        event_type=event.event_type,
        source=event.source,
        device_info=event.device_info,
        extra=event.extra
    )
    
    db.add(db_event)
    
    # 如果是点赞或收藏事件，更新帖子的计数
    if event.event_type == "like":
        post.like_count += 1
    elif event.event_type == "favorite":
        post.favorite_count += 1
    
    # 如果是浏览或点击事件，记录到Redis中用于消重
    if event.event_type in ["view", "click"]:
        record_user_viewed_post(event.user_id, event.post_id)
    
    db.commit()
    db.refresh(db_event)
    
    return db_event

@router.post("/events/batch", response_model=List[schemas.EventResponse], status_code=201)
def create_batch_events(batch: schemas.BatchEventCreate, db: Session = Depends(get_db)):
    """
    批量创建用户行为事件
    """
    # 验证所有用户和帖子是否存在
    user_ids = set([int(event.user_id) for event in batch.events])
    post_ids = set([int(event.post_id) for event in batch.events])
    
    users = db.query(User).filter(User.user_id.in_(user_ids)).all()
    posts = db.query(Post).filter(Post.post_id.in_(post_ids)).all()
    
    existing_user_ids = set([user.user_id for user in users])
    existing_post_ids = set([post.post_id for post in posts])
    
    # 创建事件
    db_events = []
    post_like_counts = {}
    post_favorite_counts = {}
    
    for event in batch.events:
        # 跳过不存在的用户或帖子
        if event.user_id not in existing_user_ids or event.post_id not in existing_post_ids:
            continue
        
        db_event = Event(
            user_id=event.user_id,
            post_id=event.post_id,
            event_type=event.event_type,
            source=event.source,
            device_info=event.device_info,
            extra=event.extra
        )
        
        db_events.append(db_event)
        
        # 统计点赞和收藏事件
        if event.event_type == "like":
            post_like_counts[event.post_id] = post_like_counts.get(event.post_id, 0) + 1
        elif event.event_type == "favorite":
            post_favorite_counts[event.post_id] = post_favorite_counts.get(event.post_id, 0) + 1
        
        # 如果是浏览或点击事件，记录到Redis中用于消重
        if event.event_type in ["view", "click"]:
            logger.info(f"事件系统: 记录用户[{event.user_id}]的[{event.event_type}]事件到消重系统, 帖子ID[{event.post_id}]")
            record_user_viewed_post(int(event.user_id), int(event.post_id))
    
    # 批量添加事件
    db.add_all(db_events)
    
    # 更新帖子的点赞和收藏计数
    for post in posts:
        if post.post_id in post_like_counts:
            post.like_count += post_like_counts[post.post_id]
        if post.post_id in post_favorite_counts:
            post.favorite_count += post_favorite_counts[post.post_id]
    
    db.commit()
    
    # 刷新所有事件
    for event in db_events:
        db.refresh(event)
    
    return db_events

@router.get("/events/user/{user_id}", response_model=List[schemas.EventResponse])
def get_user_events(user_id: int, limit: int = 50, db: Session = Depends(get_db)):
    """
    获取用户的行为历史
    """
    # 验证用户是否存在
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 获取用户事件
    events = db.query(Event).filter(Event.user_id == user_id).order_by(Event.timestamp.desc()).limit(limit).all()
    
    return events

@router.get("/events/post/{post_id}", response_model=List[schemas.EventResponse])
def get_post_events(post_id: int, limit: int = 50, db: Session = Depends(get_db)):
    """
    获取帖子的行为历史
    """
    # 验证帖子是否存在
    post = db.query(Post).filter(Post.post_id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # 获取帖子事件
    events = db.query(Event).filter(Event.post_id == post_id).order_by(Event.timestamp.desc()).limit(limit).all()
    
    return events