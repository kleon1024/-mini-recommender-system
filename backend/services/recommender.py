from typing import List, Dict, Any, Optional
import random
import json
import logging
from sqlalchemy.orm import Session
from models.models import User, Post, Event, Feature
import numpy as np
from datetime import datetime, timedelta
from redis_client import get_user_viewed_posts

# 配置日志
logger = logging.getLogger(__name__)

class RecommenderService:
    """
    推荐引擎服务类，实现基础的推荐算法
    MVP阶段实现简单的基于标签的推荐和协同过滤
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_recommendations(self, user_id: str, count: int = 10, offset: int = 0, filters: Optional[str] = None) -> Dict[str, Any]:
        """
        获取推荐内容
        根据用户ID、数量、偏移量和过滤条件获取推荐内容
        """
        # 解析过滤条件
        filter_dict = {}
        if filters:
            try:
                filter_dict = json.loads(filters)
                if not isinstance(filter_dict, dict):
                    filter_dict = {}
            except json.JSONDecodeError:
                # 如果JSON解析失败，忽略filters
                pass
        
        # 添加用户ID到过滤条件，用于随机推荐时过滤已浏览内容
        filter_dict['user_id'] = user_id
                
        # 获取用户信息
        user = self.db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return {"items": [], "has_more": False, "total": 0}
        
        # 根据用户标签和偏好进行推荐
        recommended_posts = self._recommend_by_tags(user, count * 2, filter_dict)  # 获取更多候选，以便后续排序
        
        # 如果基于标签的推荐不足，补充协同过滤推荐
        if len(recommended_posts) < count * 2:
            cf_posts = self._recommend_by_collaborative_filtering(user, count * 2 - len(recommended_posts), filter_dict)
            recommended_posts.extend(cf_posts)
        
        # 如果推荐仍然不足，补充随机推荐
        if len(recommended_posts) < count:
            random_posts = self._recommend_random(count - len(recommended_posts), filter_dict)
            recommended_posts.extend(random_posts)
        
        # 对推荐结果进行排序
        ranked_posts = self._rank_posts(user, recommended_posts)
        
        # 分页处理
        start = offset
        end = offset + count
        result_posts = ranked_posts[start:end]
        
        # 确保所有帖子的tags字段保持原始的JSON格式
        # 数据库中的tags字段是JSON格式，前端期望它是一个对象，包含tags数组
        # 不需要额外处理，保持原样即可
        
        # 构建响应
        return {
            "items": result_posts,
            "has_more": end < len(ranked_posts),
            "total": len(ranked_posts)
        }
    
    def _recommend_by_tags(self, user: User, count: int, filters: Optional[Dict[str, Any]] = None) -> List[Post]:
        """
        基于标签的推荐算法
        """
        # 获取用户标签
        user_tags = []
        if user.tags and isinstance(user.tags, dict) and 'interests' in user.tags:
            user_tags = user.tags['interests']
        if not user_tags:
            return []
        
        # 查询包含用户标签的帖子
        posts = []
        for tag in user_tags:
            # 构建基本查询
            # 数据库中的tags字段是JSON格式，需要检查tags.tags数组是否包含指定标签
            query = self.db.query(Post).filter(Post.tags['tags'].contains([tag]))
            
            # 应用过滤条件
            if filters:
                # 按类别过滤
                if 'category' in filters:
                    query = query.filter(Post.category == filters['category'])
                
                # 按创建时间过滤
                if 'created_after' in filters:
                    query = query.filter(Post.created_at >= filters['created_after'])
                
                # 按作者过滤
                if 'author_id' in filters:
                    query = query.filter(Post.author_id == filters['author_id'])
            
            # 获取结果
            tag_posts = query.limit(count).all()
            posts.extend(tag_posts)
        
        # 去重
        unique_posts = list({post.post_id: post for post in posts}.values())
        logger.info(f"推荐系统: 用户[{user.user_id}]推荐前去重后的帖子数量: {len(unique_posts)}")
        
        # 获取用户已浏览的帖子ID（优先从Redis获取，Redis不可用时从数据库获取）
        redis_viewed_post_ids = get_user_viewed_posts(user.user_id)
        
        # 如果Redis中没有数据，则从数据库获取
        if not redis_viewed_post_ids:
            logger.info(f"推荐系统: 用户[{user.user_id}]的Redis消重数据为空，从数据库获取")
            db_viewed_post_ids = set([
                event.post_id for event in self.db.query(Event).filter(
                    Event.user_id == user.user_id,
                    Event.event_type.in_(["view", "click"])
                ).all()
            ])
            viewed_post_ids = db_viewed_post_ids
            logger.info(f"推荐系统: 用户[{user.user_id}]从数据库获取的已浏览帖子数量: {len(viewed_post_ids)}")
        else:
            viewed_post_ids = redis_viewed_post_ids
            logger.info(f"推荐系统: 用户[{user.user_id}]从Redis获取的已浏览帖子数量: {len(viewed_post_ids)}")
        
        # 过滤掉已浏览的帖子
        filtered_posts = [post for post in unique_posts if post.post_id not in viewed_post_ids]
        logger.info(f"推荐系统: 用户[{user.user_id}]消重后的推荐帖子数量: {len(filtered_posts)}, 过滤掉: {len(unique_posts) - len(filtered_posts)}篇")
        
        # 记录被过滤掉的帖子ID
        if len(unique_posts) > len(filtered_posts):
            filtered_post_ids = [post.post_id for post in unique_posts if post.post_id in viewed_post_ids]
            logger.info(f"推荐系统: 用户[{user.user_id}]被过滤掉的帖子IDs: {filtered_post_ids}")
        
        return filtered_posts[:count]
    
    def _recommend_by_collaborative_filtering(self, user: User, count: int, filters: Optional[Dict[str, Any]] = None) -> List[Post]:
        """
        基于协同过滤的推荐算法
        MVP阶段使用简化版的基于用户的协同过滤
        """
        # 获取用户的行为数据
        user_events = self.db.query(Event).filter(
            Event.user_id == user.user_id,
            Event.event_type.in_(["like", "favorite"])
        ).all()
        
        if not user_events:
            return []
        
        # 获取用户喜欢/收藏的帖子ID
        user_post_ids = [event.post_id for event in user_events]
        
        # 找到与当前用户有相似行为的用户
        similar_users = self.db.query(Event.user_id).filter(
            Event.post_id.in_(user_post_ids),
            Event.user_id != user.user_id,
            Event.event_type.in_(["like", "favorite"])
        ).distinct().all()
        
        similar_user_ids = [u[0] for u in similar_users]
        
        if not similar_user_ids:
            return []
        
        # 获取相似用户喜欢/收藏的帖子
        similar_user_events = self.db.query(Event).filter(
            Event.user_id.in_(similar_user_ids),
            Event.event_type.in_(["like", "favorite"])
        ).all()
        
        # 统计帖子被喜欢/收藏的次数
        post_counts = {}
        for event in similar_user_events:
            if event.post_id not in user_post_ids:  # 排除用户已经喜欢/收藏的帖子
                post_counts[event.post_id] = post_counts.get(event.post_id, 0) + 1
        
        # 按照被喜欢/收藏的次数排序
        sorted_post_ids = sorted(post_counts.keys(), key=lambda x: post_counts[x], reverse=True)
        
        # 获取排序后的帖子
        recommended_posts = []
        if sorted_post_ids:
            # 构建基本查询
            query = self.db.query(Post).filter(Post.post_id.in_(sorted_post_ids[:count]))
            
            # 应用过滤条件
            if filters:
                # 按类别过滤
                if 'category' in filters:
                    query = query.filter(Post.category == filters['category'])
                
                # 按创建时间过滤
                if 'created_after' in filters:
                    query = query.filter(Post.created_at >= filters['created_after'])
                
                # 按作者过滤
                if 'author_id' in filters:
                    query = query.filter(Post.author_id == filters['author_id'])
            
            # 获取结果
        recommended_posts = query.all()
        
        # 获取用户已浏览的帖子ID（优先从Redis获取，Redis不可用时从数据库获取）
        redis_viewed_post_ids = get_user_viewed_posts(user.user_id)
        
        # 如果Redis中没有数据，则从数据库获取
        if not redis_viewed_post_ids:
            db_viewed_post_ids = set([
                event.post_id for event in self.db.query(Event).filter(
                    Event.user_id == user.user_id,
                    Event.event_type.in_(["view", "click"])
                ).all()
            ])
            viewed_post_ids = db_viewed_post_ids
        else:
            viewed_post_ids = redis_viewed_post_ids
        
        # 过滤掉已浏览的帖子
        filtered_posts = [post for post in recommended_posts if post.post_id not in viewed_post_ids]
        
        return filtered_posts
    
    def _recommend_random(self, count: int, filters: Optional[Dict[str, Any]] = None) -> List[Post]:
        """
        随机推荐
        """
        # 构建基本查询 - 最近一周的帖子
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        query = self.db.query(Post).filter(Post.create_time >= one_week_ago)
        
        # 应用过滤条件
        if filters:
            # 按类别过滤
            if 'category' in filters:
                query = query.filter(Post.category == filters['category'])
            
            # 按创建时间过滤
            if 'created_after' in filters:
                query = query.filter(Post.created_at >= filters['created_after'])
            
            # 按作者过滤
            if 'author_id' in filters:
                query = query.filter(Post.author_id == filters['author_id'])
        
        # 获取结果
        recent_posts = query.all()
        
        # 如果最近一周的帖子不足，则获取所有帖子（仍然应用过滤条件）
        if len(recent_posts) < count:
            query = self.db.query(Post)
            
            # 应用过滤条件
            if filters:
                # 按类别过滤
                if 'category' in filters:
                    query = query.filter(Post.category == filters['category'])
                
                # 按创建时间过滤
                if 'created_after' in filters:
                    query = query.filter(Post.created_at >= filters['created_after'])
                
                # 按作者过滤
                if 'author_id' in filters:
                    query = query.filter(Post.author_id == filters['author_id'])
            
            # 获取结果
            recent_posts = query.all()
        
        # 获取用户已浏览的帖子ID（优先从Redis获取，Redis不可用时从数据库获取）
        user_id = filters.get('user_id') if filters else None
        if user_id:
            redis_viewed_post_ids = get_user_viewed_posts(user_id)
            
            # 如果Redis中没有数据，则从数据库获取
            if not redis_viewed_post_ids:
                db_viewed_post_ids = set([
                    event.post_id for event in self.db.query(Event).filter(
                        Event.user_id == user_id,
                        Event.event_type.in_(["view", "click"])
                    ).all()
                ])
                viewed_post_ids = db_viewed_post_ids
            else:
                viewed_post_ids = redis_viewed_post_ids
            
            # 过滤掉已浏览的帖子
            recent_posts = [post for post in recent_posts if post.post_id not in viewed_post_ids]
        
        # 随机选择
        if len(recent_posts) <= count:
            return recent_posts
        else:
            return random.sample(recent_posts, count)
    
    def _rank_posts(self, user: User, posts: List[Post]) -> List[Post]:
        """
        对推荐结果进行排序
        MVP阶段使用简单的排序规则：
        1. 根据用户标签匹配度
        2. 根据帖子热度（浏览量、点赞量、收藏量）
        3. 根据时间新鲜度
        """
        user_tags = set(user.tags or [])
        
        # 计算每个帖子的分数
        post_scores = []
        for post in posts:
            # 标签匹配度分数
            post_tags = set(post.tags or [])
            tag_score = len(user_tags.intersection(post_tags)) if user_tags else 0
            
            # 热度分数 = 浏览量 * 0.1 + 点赞量 * 0.5 + 收藏量 * 1.0
            popularity_score = post.view_count * 0.1 + post.like_count * 0.5 + post.favorite_count * 1.0
            
            # 时间新鲜度分数，最近发布的帖子分数更高
            time_diff = (datetime.utcnow() - post.create_time).total_seconds() / 86400  # 转换为天数
            freshness_score = max(0, 7 - time_diff) / 7  # 最近7天内的帖子，分数从1递减到0
            
            # 总分 = 标签匹配度 * 2.0 + 热度 * 1.0 + 新鲜度 * 1.5
            total_score = tag_score * 2.0 + popularity_score * 1.0 + freshness_score * 1.5
            
            post_scores.append((post, total_score))
        
        # 按分数降序排序
        sorted_posts = [post for post, score in sorted(post_scores, key=lambda x: x[1], reverse=True)]
        
        return sorted_posts