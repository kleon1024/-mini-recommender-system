#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复数据库中的中文编码问题
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

def fix_encoding():
    """修复数据库中的中文编码问题"""
    logger.info("===== 开始修复数据库中的中文编码问题 =====")
    
    # 获取数据库连接
    db = next(get_db())
    
    try:
        # 1. 获取所有帖子
        logger.info("\n===== 1. 获取所有帖子 =====")
        posts = db.query(Post).all()
        
        for post in posts:
            logger.info("处理帖子ID: %s", post.post_id)
            logger.info("原始标题: %s", post.title)
            logger.info("原始内容: %s", post.content[:30] + "..." if post.content and len(post.content) > 30 else post.content)
            
            # 2. 尝试修复标题和内容的编码
            # 方法2: 尝试多次解码编码来修复双重编码问题
            try:
                # 修复标题
                fixed_title = post.title
                # 尝试多次解码，直到不再包含编码字符
                for _ in range(3):  # 最多尝试3次
                    if '\xc3' in fixed_title or '\xe2' in fixed_title:
                        try:
                            fixed_title = fixed_title.encode('latin1').decode('utf-8')
                        except:
                            break
                    else:
                        break
                
                logger.info("修复后标题: %s", fixed_title)
                post.title = fixed_title
                
                # 修复内容
                if post.content:
                    fixed_content = post.content
                    for _ in range(3):  # 最多尝试3次
                        if '\xc3' in fixed_content or '\xe2' in fixed_content:
                            try:
                                fixed_content = fixed_content.encode('latin1').decode('utf-8')
                            except:
                                break
                        else:
                            break
                    
                    logger.info("修复后内容: %s", fixed_content[:30] + "..." if len(fixed_content) > 30 else fixed_content)
                    post.content = fixed_content
                
                # 修复标签
                if post.tags and isinstance(post.tags, dict) and 'tags' in post.tags:
                    fixed_tags = []
                    for tag in post.tags['tags']:
                        fixed_tag = tag
                        for _ in range(3):  # 最多尝试3次
                            if '\xc3' in fixed_tag or '\xe2' in fixed_tag:
                                try:
                                    fixed_tag = fixed_tag.encode('latin1').decode('utf-8')
                                except:
                                    break
                            else:
                                break
                        
                        fixed_tags.append(fixed_tag)
                        logger.info("修复后标签: %s", fixed_tag)
                    
                    post.tags = {'tags': fixed_tags}
            except Exception as e:
                logger.error("修复编码错误: %s", e)
                
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
    fix_encoding()