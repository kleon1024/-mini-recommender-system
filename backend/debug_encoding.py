#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
调试脚本：检查数据库中的中文编码问题
"""

import sys
from sqlalchemy.orm import Session
from database import get_db, engine
from models.models import Post, User
import json

def debug_database_encoding():
    """检查数据库中的中文编码"""
    print("\n===== 数据库连接信息 =====")
    print(f"数据库URL: {engine.url}")
    print(f"数据库驱动: {engine.driver}")
    
    # 获取数据库连接
    db = next(get_db())
    
    try:
        # 检查数据库字符集
        print("\n===== 数据库字符集 =====")
        from sqlalchemy import text
        result = db.execute(text("SHOW VARIABLES LIKE 'character_set%'"))
        for row in result:
            print(f"{row[0]}: {row[1]}")
        
        # 检查表字符集
        print("\n===== 表字符集 =====")
        result = db.execute(text("SHOW CREATE TABLE posts"))
        for row in result:
            print(row[1])
        
        # 读取帖子数据
        print("\n===== 帖子数据 =====")
        posts = db.query(Post).limit(3).all()
        
        for post in posts:
            print(f"\n帖子ID: {post.post_id}")
            print(f"标题: {post.title}")
            print(f"标题类型: {type(post.title)}")
            print(f"标题编码: {post.title.encode('utf-8')}")
            print(f"内容: {post.content}")
            
            # 检查JSON字段
            if post.tags:
                print(f"标签: {post.tags}")
                print(f"标签类型: {type(post.tags)}")
                if isinstance(post.tags, dict) and 'tags' in post.tags:
                    for tag in post.tags['tags']:
                        print(f"  - 标签: {tag}")
                        print(f"  - 标签类型: {type(tag)}")
                        print(f"  - 标签编码: {tag.encode('utf-8')}")
        
        # 转换为JSON并检查
        print("\n===== JSON序列化 =====")
        for post in posts:
            post_dict = {
                'title': post.title,
                'content': post.content,
                'tags': post.tags
            }
            
            # 默认序列化
            json_str = json.dumps(post_dict)
            print(f"默认JSON: {json_str}")
            
            # 不转义中文的序列化
            json_str_no_escape = json.dumps(post_dict, ensure_ascii=False)
            print(f"不转义JSON: {json_str_no_escape}")
            print(f"不转义JSON类型: {type(json_str_no_escape)}")
            print(f"不转义JSON编码: {json_str_no_escape.encode('utf-8')}")
            
    except Exception as e:
        print(f"错误: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_database_encoding()