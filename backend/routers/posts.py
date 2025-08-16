from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from database import get_db
from models.models import Post, User, Event
from schemas import schemas
from services.recommender import RecommenderService
from routers import likes, favorites
from redis_client import record_user_viewed_post

router = APIRouter()

@router.get("/posts", response_model=schemas.RecommendationResponse)
def get_posts(user_id: int = Query(..., description="用户ID"),
              count: int = Query(10, description="返回数量"),
              offset: int = Query(0, description="偏移量"),
              filters: Optional[str] = Query(None, description="过滤条件，JSON字符串格式"),
              db: Session = Depends(get_db)):
    """
    获取推荐内容列表
    集成了推荐引擎，根据用户ID返回个性化推荐内容
    """
    # 验证用户是否存在
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 使用推荐引擎获取推荐内容
    recommender = RecommenderService(db)
    recommendations = recommender.get_recommendations(user_id, count, offset, filters)
    
    return recommendations

@router.get("/posts/{post_id}", response_model=schemas.PostDetailResponse)
def get_post_detail(post_id: int = Path(..., description="帖子ID"),
                    user_id: Optional[int] = Query(None, description="用户ID，用于个性化相关推荐"),
                    db: Session = Depends(get_db)):
    """
    获取帖子详情
    如果提供了用户ID，还会返回个性化的相关推荐
    """
    # 获取帖子详情
    post = db.query(Post).filter(Post.post_id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # 增加浏览计数
    post.view_count += 1
    db.commit()
    
    # 如果提供了用户ID，记录用户浏览记录到Redis
    if user_id:
        record_user_viewed_post(user_id, post_id)
    
    # 获取作者信息
    author = db.query(User).filter(User.user_id == post.author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    
    # 构建响应数据
    response = schemas.PostDetailResponse(
        post_id=post.post_id,
        title=post.title,
        content=post.content,
        tags=post.tags,
        author_id=post.author_id,
        create_time=post.create_time,
        view_count=post.view_count,
        like_count=post.like_count,
        favorite_count=post.favorite_count,
        author=schemas.UserResponse(
            user_id=author.user_id,
            username=author.username,
            tags=author.tags,
            preferences=author.preferences,
            create_time=author.create_time
        ),
        is_liked=False,
        is_favorited=False
    )
    
    # 如果提供了用户ID，检查用户是否点赞和收藏了该帖子
    if user_id:
        # 检查用户是否点赞
        like_result = likes.check_like(db, user_id, post_id)
        response.is_liked = like_result["liked"]
        
        # 检查用户是否收藏
        favorite_result = favorites.check_favorite(db, user_id, post_id)
        response.is_favorited = favorite_result["favorited"]
    
    return response

@router.get("/posts/{post_id}/related", response_model=List[schemas.PostResponse])
def get_related_posts(post_id: int = Path(..., description="帖子ID"),
                      user_id: Optional[int] = Query(None, description="用户ID，用于个性化相关推荐"),
                      count: int = Query(5, description="返回数量"),
                      db: Session = Depends(get_db)):
    """
    获取相关推荐内容
    根据帖子ID和可选的用户ID返回相关推荐
    """
    # 获取帖子
    post = db.query(Post).filter(Post.post_id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # 基于标签的相关推荐
    post_tags = post.tags or []
    related_posts = []
    
    if post_tags:
        # 查询包含相同标签的帖子
        for tag in post_tags:
            tag_posts = db.query(Post).filter(
                Post.tags.contains([tag]),
                Post.post_id != post_id  # 排除当前帖子
            ).limit(count).all()
            related_posts.extend(tag_posts)
        
        # 去重
        related_posts = list({p.post_id: p for p in related_posts}.values())
    
    # 如果相关帖子不足，补充随机推荐
    if len(related_posts) < count:
        # 获取随机帖子（排除当前帖子和已有的相关帖子）
        existing_ids = [p.post_id for p in related_posts] + [post_id]
        random_posts = db.query(Post).filter(
            ~Post.post_id.in_(existing_ids)
        ).limit(count - len(related_posts)).all()
        
        related_posts.extend(random_posts)
    
    # 如果提供了用户ID，使用推荐引擎进行个性化排序
    if user_id:
        user = db.query(User).filter(User.user_id == user_id).first()
        if user:
            recommender = RecommenderService(db)
            related_posts = recommender._rank_posts(user, related_posts)
    
    return related_posts[:count]

@router.post("/posts", response_model=schemas.PostResponse, status_code=201)
def create_post(post: schemas.PostCreate, db: Session = Depends(get_db)):
    """
    创建新帖子
    """
    # 验证作者是否存在
    user = db.query(User).filter(User.user_id == post.author_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Author not found")
    
    # 创建帖子
    db_post = Post(
        title=post.title,
        content=post.content,
        author_id=post.author_id,
        tags=post.tags
    )
    
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    
    return db_post

@router.put("/posts/{post_id}", response_model=schemas.PostResponse)
def update_post(post_id: str, post_update: schemas.PostUpdate, db: Session = Depends(get_db)):
    """
    更新帖子
    """
    # 获取帖子
    db_post = db.query(Post).filter(Post.post_id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # 更新帖子
    if post_update.title is not None:
        db_post.title = post_update.title
    if post_update.content is not None:
        db_post.content = post_update.content
    if post_update.tags is not None:
        db_post.tags = post_update.tags
    
    db.commit()
    db.refresh(db_post)
    
    return db_post

@router.delete("/posts/{post_id}", status_code=204)
def delete_post(post_id: str, db: Session = Depends(get_db)):
    """
    删除帖子
    """
    # 获取帖子
    db_post = db.query(Post).filter(Post.post_id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # 删除帖子
    db.delete(db_post)
    db.commit()
    
    return None