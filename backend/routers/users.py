from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models.models import User, Event
from schemas import schemas

router = APIRouter()

@router.get("/users/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: int = Path(..., description="用户ID"), db: Session = Depends(get_db)):
    """
    获取用户信息
    """
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

@router.get("/users/{user_id}/activity", response_model=List[schemas.EventResponse])
def get_user_activity(user_id: int = Path(..., description="用户ID"),
                      limit: int = Query(20, description="返回数量"),
                      event_type: Optional[str] = Query(None, description="事件类型过滤"),
                      db: Session = Depends(get_db)):
    """
    获取用户活动历史
    """
    # 验证用户是否存在
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 构建查询
    query = db.query(Event).filter(Event.user_id == user_id)
    
    # 应用事件类型过滤
    if event_type:
        query = query.filter(Event.event_type == event_type)
    
    # 获取最近的活动
    activities = query.order_by(Event.timestamp.desc()).limit(limit).all()
    
    return activities

@router.post("/users", response_model=schemas.UserResponse, status_code=201)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    创建新用户
    """
    # 创建用户
    db_user = User(
        username=user.username,
        tags=user.tags,
        preferences=user.preferences
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.put("/users/{user_id}", response_model=schemas.UserResponse)
def update_user(user_id: int, user_update: schemas.UserUpdate, db: Session = Depends(get_db)):
    """
    更新用户信息
    """
    # 获取用户
    db_user = db.query(User).filter(User.user_id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 更新用户
    if user_update.username is not None:
        db_user.username = user_update.username
    if user_update.tags is not None:
        db_user.tags = user_update.tags
    if user_update.preferences is not None:
        db_user.preferences = user_update.preferences
    
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    删除用户
    """
    # 获取用户
    db_user = db.query(User).filter(User.user_id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 删除用户
    db.delete(db_user)
    db.commit()
    
    return None