from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List

from database import get_db
from models.models import Favorite, User, Post
from schemas import schemas

router = APIRouter()

@router.post("/favorites", response_model=schemas.FavoriteResponse, status_code=201)
def create_favorite(favorite: schemas.FavoriteCreate, db: Session = Depends(get_db)):
    """
    创建收藏
    """
    # 验证用户是否存在
    user = db.query(User).filter(User.user_id == favorite.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 验证帖子是否存在
    post = db.query(Post).filter(Post.post_id == favorite.post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # 检查是否已经收藏
    existing_favorite = db.query(
        Favorite.favorite_id,
        Favorite.user_id,
        Favorite.post_id,
        Favorite.create_time
    ).filter(
        Favorite.user_id == favorite.user_id,
        Favorite.post_id == favorite.post_id
    ).first()
    
    if existing_favorite:
        # 如果已经收藏，直接返回现有收藏
        result = {
            "favorite_id": existing_favorite.favorite_id,
            "user_id": existing_favorite.user_id,
            "post_id": existing_favorite.post_id,
            "create_time": existing_favorite.create_time
        }
        return result
    
    # 创建收藏，不包含notes字段
    db_favorite = Favorite(
        user_id=favorite.user_id,
        post_id=favorite.post_id
    )
    
    try:
        db.add(db_favorite)
        # 更新帖子的收藏计数
        post.favorite_count += 1
        db.commit()
        db.refresh(db_favorite)
        
        # 构造返回结果
        result = {
            "favorite_id": db_favorite.favorite_id,
            "user_id": db_favorite.user_id,
            "post_id": db_favorite.post_id,
            "create_time": db_favorite.create_time
        }
        return result
    except IntegrityError:
        db.rollback()
        # 如果发生冲突，返回已存在的收藏
        existing_favorite = db.query(
            Favorite.favorite_id,
            Favorite.user_id,
            Favorite.post_id,
            Favorite.create_time
        ).filter(
            Favorite.user_id == favorite.user_id,
            Favorite.post_id == favorite.post_id
        ).first()
        
        result = {
            "favorite_id": existing_favorite.favorite_id,
            "user_id": existing_favorite.user_id,
            "post_id": existing_favorite.post_id,
            "create_time": existing_favorite.create_time
        }
        return result

@router.delete("/favorites/{user_id}/{post_id}", status_code=204)
def delete_favorite(user_id: str, post_id: str, db: Session = Depends(get_db)):
    """
    取消收藏
    """
    # 验证用户是否存在
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 验证帖子是否存在
    post = db.query(Post).filter(Post.post_id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # 查找收藏记录
    favorite = db.query(Favorite).filter(
        Favorite.user_id == user_id,
        Favorite.post_id == post_id
    ).first()
    
    if not favorite:
        # 如果没有找到收藏记录，直接返回成功
        return {"status": "success"}
    
    # 删除收藏记录
    db.delete(favorite)
    
    # 更新帖子的收藏计数
    if post.favorite_count > 0:
        post.favorite_count -= 1
    
    db.commit()
    
    return {"status": "success"}

@router.get("/favorites/user/{user_id}", response_model=List[schemas.FavoriteResponse])
def get_user_favorites(user_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    获取用户的所有收藏
    """
    # 验证用户是否存在
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 获取用户的收藏列表，明确指定要查询的列，排除notes列
    favorites = db.query(
        Favorite.favorite_id,
        Favorite.user_id,
        Favorite.post_id,
        Favorite.create_time
    ).filter(Favorite.user_id == user_id).offset(skip).limit(limit).all()
    
    # 将查询结果转换为字典列表，并添加空的notes字段
    result = []
    for fav in favorites:
        result.append({
            "favorite_id": fav.favorite_id,
            "user_id": fav.user_id,
            "post_id": fav.post_id,
            "create_time": fav.create_time,
            "notes": None
        })
    
    return result

@router.get("/favorites/post/{post_id}", response_model=List[schemas.FavoriteResponse])
def get_post_favorites(post_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    获取帖子的所有收藏
    """
    # 验证帖子是否存在
    post = db.query(Post).filter(Post.post_id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # 获取帖子的收藏列表，明确指定要查询的列，排除notes列
    favorites = db.query(
        Favorite.favorite_id,
        Favorite.user_id,
        Favorite.post_id,
        Favorite.create_time
    ).filter(Favorite.post_id == post_id).offset(skip).limit(limit).all()
    
    # 将查询结果转换为字典列表，并添加空的notes字段
    result = []
    for fav in favorites:
        result.append({
            "favorite_id": fav.favorite_id,
            "user_id": fav.user_id,
            "post_id": fav.post_id,
            "create_time": fav.create_time,
            "notes": None
        })
    
    return result

@router.get("/favorites/check/{user_id}/{post_id}")
def check_favorite(user_id: str, post_id: str, db: Session = Depends(get_db)):
    """
    检查用户是否收藏了帖子
    """
    # 验证用户是否存在
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 验证帖子是否存在
    post = db.query(Post).filter(Post.post_id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # 查找收藏记录
    favorite = db.query(Favorite).filter(
        Favorite.user_id == user_id,
        Favorite.post_id == post_id
    ).first()
    
    return {"favorited": favorite is not None}