#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
扩展版本的编码修复脚本，修复users和posts表中的中文编码问题，并增加更多数据
"""

import sys
import json
import logging
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import get_db, engine, Base
from models.models import Post, User

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 正确的用户数据
correct_users_data = {
    'u1001': {
        'username': 'user1',
        'tags': {
            'interests': ['科技', '编程', 'AI']
        },
        'preferences': {
            'categories': ['科技', '编程']
        }
    },
    'u1002': {
        'username': 'user2',
        'tags': {
            'interests': ['旅游', '美食', '摄影']
        },
        'preferences': {
            'categories': ['旅游', '美食']
        }
    },
    'u1003': {
        'username': 'user3',
        'tags': {
            'interests': ['体育', '健身', '篮球']
        },
        'preferences': {
            'categories': ['体育', '健身']
        }
    },
    'u1004': {
        'username': 'user4',
        'tags': {
            'interests': ['音乐', '电影', '艺术']
        },
        'preferences': {
            'categories': ['音乐', '电影']
        }
    },
    'u1005': {
        'username': 'user5',
        'tags': {
            'interests': ['科技', '游戏', '动漫']
        },
        'preferences': {
            'categories': ['科技', '游戏']
        }
    },
    # 新增用户
    'u1006': {
        'username': 'user6',
        'tags': {
            'interests': ['文学', '历史', '哲学']
        },
        'preferences': {
            'categories': ['文学', '历史']
        }
    },
    'u1007': {
        'username': 'user7',
        'tags': {
            'interests': ['设计', '艺术', '创意']
        },
        'preferences': {
            'categories': ['设计', '艺术']
        }
    }
}

# 正确的帖子数据
correct_posts_data = {
    'p1001': {
        'title': '人工智能入门指南',
        'content': '本文介绍了人工智能的基础知识和应用场景...',
        'tags': ['AI', '技术', '入门']
    },
    'p1002': {
        'title': '东京旅游攻略',
        'content': '东京是一个充满活力的城市，本文分享东京旅游的经验和建议...',
        'tags': ['旅游', '东京', '攻略']
    },
    'p1003': {
        'title': '家庭健身计划',
        'content': '不需要去健身房，在家也能保持健康的锻炼方法...',
        'tags': ['健身', '健康', '生活']
    },
    'p1004': {
        'title': '摄影技巧分享',
        'content': '提高摄影水平的实用技巧和经验分享...',
        'tags': ['摄影', '技巧', '艺术']
    },
    'p1005': {
        'title': '电影推荐：经典科幻片',
        'content': '盘点历年来最经典的科幻电影，带你领略未来世界的奇妙想象...',
        'tags': ['电影', '科幻', '娱乐']
    },
    'p1006': {
        'title': 'Python编程技巧',
        'content': '分享一些Python编程中的实用技巧和最佳实践...',
        'tags': ['Python', '编程', '技巧']
    },
    'p1007': {
        'title': '美食探店记',
        'content': '探访城市里的隐藏美食宝藏，带你品尝不同风味...',
        'tags': ['美食', '探店', '推荐']
    },
    'p1008': {
        'title': '篮球训练方法',
        'content': '提高篮球技术的专业训练方法和技巧分享...',
        'tags': ['篮球', '训练', '技巧']
    },
    'p1009': {
        'title': '古典音乐欣赏',
        'content': '介绍古典音乐的历史、流派和著名作品...',
        'tags': ['音乐', '古典', '艺术']
    },
    'p1010': {
        'title': '人工智能在游戏中的应用',
        'content': '探讨AI技术如何改变游戏体验和游戏开发...',
        'tags': ['AI', '游戏', '技术']
    },
    # 新增帖子
    'p1011': {
        'title': '中国古代文学赏析',
        'content': '探索中国古代文学的魅力，从诗词歌赋到小说戏曲...',
        'tags': ['文学', '历史', '中国']
    },
    'p1012': {
        'title': 'UI设计趋势分析',
        'content': '2025年UI设计的主要趋势和创新方向分析...',
        'tags': ['设计', 'UI', '趋势']
    },
    'p1013': {
        'title': '数据科学实战案例',
        'content': '通过实际案例学习数据分析和机器学习的应用...',
        'tags': ['数据科学', '机器学习', '案例']
    },
    'p1014': {
        'title': '健康饮食指南',
        'content': '科学合理的饮食方案，助你保持健康活力...',
        'tags': ['健康', '饮食', '生活']
    },
    'p1015': {
        'title': '户外摄影技巧',
        'content': '如何在自然环境中捕捉完美的照片...',
        'tags': ['摄影', '户外', '技巧']
    }
}

# 新增用户SQL
new_users_sql = """
INSERT INTO users (user_id, username, tags, preferences)
VALUES 
('u1006', 'user6', '{"interests": ["文学", "历史", "哲学"]}', '{"categories": ["文学", "历史"]}'),
('u1007', 'user7', '{"interests": ["设计", "艺术", "创意"]}', '{"categories": ["设计", "艺术"]}');
"""

# 新增帖子SQL
new_posts_sql = """
INSERT INTO posts (post_id, title, content, author_id, tags, view_count, like_count, favorite_count)
VALUES 
('p1011', '中国古代文学赏析', '探索中国古代文学的魅力，从诗词歌赋到小说戏曲...', 'u1006', '{"tags": ["文学", "历史", "中国"]}', 150, 60, 20),
('p1012', 'UI设计趋势分析', '2025年UI设计的主要趋势和创新方向分析...', 'u1007', '{"tags": ["设计", "UI", "趋势"]}', 180, 75, 25),
('p1013', '数据科学实战案例', '通过实际案例学习数据分析和机器学习的应用...', 'u1001', '{"tags": ["数据科学", "机器学习", "案例"]}', 200, 85, 30),
('p1014', '健康饮食指南', '科学合理的饮食方案，助你保持健康活力...', 'u1003', '{"tags": ["健康", "饮食", "生活"]}', 160, 65, 22),
('p1015', '户外摄影技巧', '如何在自然环境中捕捉完美的照片...', 'u1002', '{"tags": ["摄影", "户外", "技巧"]}', 170, 70, 24);
"""

def fix_encoding_extended():
    """扩展版本的编码修复函数，修复users和posts表中的中文编码问题，并增加更多数据"""
    logger.info("===== 开始扩展版本的编码修复 =====")
    
    # 获取数据库连接
    db = next(get_db())
    
    try:
        # 1. 修复用户数据
        logger.info("===== 修复用户数据 =====")
        users = db.query(User).all()
        
        for user in users:
            user_id = user.user_id
            logger.info("处理用户ID: %s", user_id)
            
            if user_id in correct_users_data:
                # 更新用户数据
                user.username = correct_users_data[user_id]['username']
                user.tags = correct_users_data[user_id]['tags']
                user.preferences = correct_users_data[user_id]['preferences']
                
                logger.info("已更新用户名: %s", user.username)
                logger.info("已更新兴趣标签: %s", user.tags['interests'])
                logger.info("已更新偏好分类: %s", user.preferences['categories'])
            else:
                logger.warning("未找到用户ID %s 的正确数据", user_id)
        
        # 2. 修复帖子数据
        logger.info("===== 修复帖子数据 =====")
        posts = db.query(Post).all()
        
        for post in posts:
            post_id = post.post_id
            logger.info("处理帖子ID: %s", post_id)
            
            if post_id in correct_posts_data:
                # 更新标题和内容
                post.title = correct_posts_data[post_id]['title']
                post.content = correct_posts_data[post_id]['content']
                post.tags = {'tags': correct_posts_data[post_id]['tags']}
                
                logger.info("已更新标题: %s", post.title)
                logger.info("已更新内容: %s", post.content[:30] + "..." if post.content and len(post.content) > 30 else post.content)
                logger.info("已更新标签: %s", post.tags['tags'])
            else:
                logger.warning("未找到帖子ID %s 的正确数据", post_id)
        
        # 3. 添加新用户
        logger.info("===== 添加新用户 =====")
        try:
            # 检查是否已存在新用户
            existing_user = db.query(User).filter(User.user_id == 'u1006').first()
            if not existing_user:
                db.execute(text(new_users_sql))
                logger.info("已添加新用户: u1006, u1007")
            else:
                logger.info("新用户已存在，跳过添加")
        except Exception as e:
            logger.error("添加新用户时出错: %s", str(e))
        
        # 4. 添加新帖子
        logger.info("===== 添加新帖子 =====")
        try:
            # 检查是否已存在新帖子
            existing_post = db.query(Post).filter(Post.post_id == 'p1011').first()
            if not existing_post:
                db.execute(text(new_posts_sql))
                logger.info("已添加新帖子: p1011-p1015")
            else:
                logger.info("新帖子已存在，跳过添加")
        except Exception as e:
            logger.error("添加新帖子时出错: %s", str(e))
        
        # 提交所有更改
        db.commit()
        logger.info("===== 所有更改已提交 =====")
        
    except Exception as e:
        logger.error("修复过程中出错: %s", str(e))
        db.rollback()
        logger.info("已回滚所有更改")
    finally:
        db.close()

if __name__ == "__main__":
    fix_encoding_extended()
    logger.info("===== 编码修复和数据扩展完成 =====")