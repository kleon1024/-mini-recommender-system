#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
全流程调试脚本：从数据库读取到API响应的整个过程
"""

import sys
import json
import logging
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import get_db, engine, Base
from models.models import Post, User
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from utils.json_utils import CustomJSONResponse

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_full_flow():
    """调试从数据库到API响应的完整流程"""
    logger.info("===== 开始全流程调试 =====")
    
    # 1. 数据库连接信息
    logger.info("数据库URL: %s", engine.url)
    logger.info("数据库驱动: %s", engine.driver)
    
    # 获取数据库连接
    db = next(get_db())
    
    try:
        # 2. 直接从数据库读取原始数据
        logger.info("\n===== 1. 直接从数据库读取原始数据 =====")
        posts_raw = db.execute(text("SELECT post_id, title, content FROM posts LIMIT 2"))
        
        for row in posts_raw:
            logger.info("原始数据 - 帖子ID: %s", row[0])
            logger.info("原始数据 - 标题: %s", row[1])
            logger.info("原始数据 - 标题类型: %s", type(row[1]))
            logger.info("原始数据 - 标题编码: %s", row[1].encode('utf-8'))
            logger.info("原始数据 - 内容: %s", row[2])
            logger.info("---")
        
        # 3. 通过ORM读取数据
        logger.info("\n===== 2. 通过ORM读取数据 =====")
        posts_orm = db.query(Post).limit(2).all()
        
        for post in posts_orm:
            logger.info("ORM数据 - 帖子ID: %s", post.post_id)
            logger.info("ORM数据 - 标题: %s", post.title)
            logger.info("ORM数据 - 标题类型: %s", type(post.title))
            logger.info("ORM数据 - 标题编码: %s", post.title.encode('utf-8'))
            logger.info("ORM数据 - 内容: %s", post.content)
            logger.info("---")
        
        # 4. 转换为Pydantic模型
        logger.info("\n===== 3. 转换为字典 =====")
        for post in posts_orm:
            post_dict = {
                'post_id': post.post_id,
                'title': post.title,
                'content': post.content,
                'tags': post.tags
            }
            
            logger.info("字典数据 - 帖子ID: %s", post_dict['post_id'])
            logger.info("字典数据 - 标题: %s", post_dict['title'])
            logger.info("字典数据 - 标题类型: %s", type(post_dict['title']))
            logger.info("字典数据 - 标题编码: %s", post_dict['title'].encode('utf-8'))
            logger.info("字典数据 - 内容: %s", post_dict['content'])
            logger.info("---")
        
        # 5. FastAPI的jsonable_encoder处理
        logger.info("\n===== 4. FastAPI的jsonable_encoder处理 =====")
        for post in posts_orm:
            post_dict = {
                'post_id': post.post_id,
                'title': post.title,
                'content': post.content,
                'tags': post.tags
            }
            
            encoded = jsonable_encoder(post_dict)
            logger.info("jsonable_encoder - 帖子ID: %s", encoded['post_id'])
            logger.info("jsonable_encoder - 标题: %s", encoded['title'])
            logger.info("jsonable_encoder - 标题类型: %s", type(encoded['title']))
            logger.info("jsonable_encoder - 内容: %s", encoded['content'])
            logger.info("---")
        
        # 6. 标准JSON序列化
        logger.info("\n===== 5. 标准JSON序列化 =====")
        for post in posts_orm:
            post_dict = {
                'post_id': post.post_id,
                'title': post.title,
                'content': post.content,
                'tags': post.tags
            }
            
            # 默认序列化
            json_str = json.dumps(post_dict)
            logger.info("默认JSON: %s", json_str)
            
            # 不转义中文的序列化
            json_str_no_escape = json.dumps(post_dict, ensure_ascii=False)
            logger.info("不转义JSON: %s", json_str_no_escape)
            logger.info("不转义JSON类型: %s", type(json_str_no_escape))
            logger.info("不转义JSON编码: %s", json_str_no_escape.encode('utf-8'))
            logger.info("---")
        
        # 7. 模拟FastAPI响应
        logger.info("\n===== 6. 模拟FastAPI响应 =====")
        for post in posts_orm:
            post_dict = {
                'post_id': post.post_id,
                'title': post.title,
                'content': post.content,
                'tags': post.tags
            }
            
            # 标准JSONResponse
            std_response = JSONResponse(content=post_dict)
            std_content = std_response.body.decode('utf-8')
            logger.info("标准JSONResponse: %s", std_content)
            
            # 自定义JSONResponse
            custom_response = CustomJSONResponse(content=post_dict)
            custom_content = custom_response.body.decode('utf-8')
            logger.info("自定义JSONResponse: %s", custom_content)
            logger.info("---")
        
    except Exception as e:
        logger.error("错误: %s", e, exc_info=True)
    finally:
        db.close()

if __name__ == "__main__":
    debug_full_flow()