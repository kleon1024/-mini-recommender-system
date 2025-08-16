from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List

from database import get_db
from models.models import Like, User, Post
from schemas import schemas

router = APIRouter()

@router.post("/likes", response_model=schemas.LikeResponse, status_code=201)
def create_like(like: schemas.LikeCreate, db: Session = Depends(get_db)):
    """
    创建点赞
    """
    # 验证用户是否存在
    user = db.query(User).filter(User.user_id == like.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 验证帖子是否存在
    post = db.query(Post).filter(Post.post_id == like.post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # 检查是否已经点赞
    existing_like = db.query(Like).filter(
        Like.user_id == like.user_id,
        Like.post_id == like.post_id
    ).first()
    
    if existing_like:
        return existing_like
    
    # 创建点赞
    db_like = Like(
        user_id=like.user_id,
        post_id=like.post_id
    )
    
    try:
        db.add(db_like)
        # 更新帖子的点赞计数
        post.like_count += 1
        db.commit()
        db.refresh(db_like)
        return db_like
    except IntegrityError:
        db.rollback()
        # 如果发生冲突，返回已存在的点赞
        existing_like = db.query(Like).filter(
            Like.user_id == like.user_id,
            Like.post_id == like.post_id
        ).first()
        return existing_like

@router.delete("/likes/{user_id}/{post_id}", status_code=204)
def delete_like(user_id: str, post_id: str, db: Session = Depends(get_db)):
    """
    取消点赞
    """
    # 验证用户是否存在
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 验证帖子是否存在
    post = db.query(Post).filter(Post.post_id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # 查找点赞记录
    like = db.query(Like).filter(
        Like.user_id == user_id,
        Like.post_id == post_id
    ).first()
    
    if not like:
        # 如果没有找到点赞记录，直接返回成功
        return {"status": "success"}
    
    # 删除点赞记录
    db.delete(like)
    
    # 更新帖子的点赞计数
    if post.like_count > 0:
        post.like_count -= 1
    
    db.commit()
    
    return {"status": "success"}

@router.get("/likes/user/{user_id}", response_model=List[schemas.LikeResponse])
def get_user_likes(user_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    获取用户的所有点赞
    """
    # 验证用户是否存在
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 获取用户的点赞列表
    likes = db.query(Like).filter(Like.user_id == user_id).offset(skip).limit(limit).all()
    
    return likes

@router.get("/likes/post/{post_id}", response_model=List[schemas.LikeResponse])
def get_post_likes(post_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    获取帖子的所有点赞
    """
    # 验证帖子是否存在
    post = db.query(Post).filter(Post.post_id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # 获取帖子的点赞列表
    likes = db.query(Like).filter(Like.post_id == post_id).offset(skip).limit(limit).all()
    
    return likes

@router.get("/likes/check/{user_id}/{post_id}")
def check_like(user_id: str, post_id: str, db: Session = Depends(get_db)):
    """
    检查用户是否点赞了帖子
    """
    # 验证用户是否存在
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 验证帖子是否存在
    post = db.query(Post).filter(Post.post_id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # 查找点赞记录
    like = db.query(Like).filter(
        Like.user_id == user_id,
        Like.post_id == post_id
    ).first()
    
    return {"liked": like is not None}