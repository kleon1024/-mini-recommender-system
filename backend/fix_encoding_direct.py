#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
直接修复数据库中的中文编码问题
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

# 正确的中文数据
correct_data = {
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
    }
}

def fix_encoding_direct():
    """直接修复数据库中的中文编码问题"""
    logger.info("===== 开始直接修复数据库中的中文编码问题 =====")
    
    # 获取数据库连接
    db = next(get_db())
    
    try:
        # 获取所有帖子
        posts = db.query(Post).all()
        
        for post in posts:
            post_id = post.post_id
            logger.info("处理帖子ID: %s", post_id)
            
            if post_id in correct_data:
                # 更新标题和内容
                post.title = correct_data[post_id]['title']
                post.content = correct_data[post_id]['content']
                post.tags = {'tags': correct_data[post_id]['tags']}
                
                logger.info("已更新标题: %s", post.title)
                logger.info("已更新内容: %s", post.content[:30] + "..." if post.content and len(post.content) > 30 else post.content)
                logger.info("已更新标签: %s", post.tags['tags'])
            else:
                logger.warning("未找到帖子ID %s 的正确数据", post_id)
                
        # 提交更改
        db.commit()
        logger.info("所有更改已提交到数据库")
        
        # 验证修复结果
        logger.info("\n===== 验证修复结果 =====")
        posts = db.query(Post).all()
        
        for post in posts:
            logger.info("帖子ID: %s", post.post_id)
            logger.info("修复后标题: %s", post.title)
            logger.info("修复后内容: %s", post.content[:30] + "..." if post.content and len(post.content) > 30 else post.content)
            if post.tags and isinstance(post.tags, dict) and 'tags' in post.tags:
                logger.info("修复后标签: %s", post.tags['tags'])
            logger.info("---")
            
    except Exception as e:
        logger.error("错误: %s", e, exc_info=True)
        db.rollback()
        logger.info("已回滚所有更改")
    finally:
        db.close()

if __name__ == "__main__":
    fix_encoding_direct()