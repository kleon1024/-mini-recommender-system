#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
检查Redis中的用户浏览记录和过期时间
"""

import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from backend.redis_client import redis_client, USER_VIEWED_POSTS_PREFIX, VIEWED_POSTS_EXPIRE_TIME
from backend.redis_client import record_user_viewed_post, get_user_viewed_posts, has_user_viewed_post

def check_existing_records():
    print(f"消重系统过期时间: {VIEWED_POSTS_EXPIRE_TIME}秒 ({VIEWED_POSTS_EXPIRE_TIME/60/60/24:.1f}天)")
    
    print("\n已存储的用户浏览记录:")
    keys = redis_client.keys(f"{USER_VIEWED_POSTS_PREFIX}*")
    
    if not keys:
        print("没有找到任何用户浏览记录")
        return
    
    for key in keys:
        ttl = redis_client.ttl(key)
        members = redis_client.smembers(key)
        print(f"键: {key}")
        print(f"过期时间: {ttl}秒 ({ttl/60/60/24:.1f}天)")
        print(f"内容: {members}")
        print("---")

def test_add_new_record():
    print("\n测试添加新的浏览记录:")
    test_user = "test_user"
    test_post = "test_post_" + str(int(time.time()))
    
    # 添加新记录
    success = record_user_viewed_post(test_user, test_post)
    print(f"添加记录结果: {'成功' if success else '失败'}")
    
    # 验证记录是否存在
    key = f"{USER_VIEWED_POSTS_PREFIX}{test_user}"
    exists = redis_client.exists(key)
    print(f"键 {key} 是否存在: {exists}")
    
    if exists:
        ttl = redis_client.ttl(key)
        members = redis_client.smembers(key)
        print(f"过期时间: {ttl}秒 ({ttl/60/60/24:.1f}天)")
        print(f"内容: {members}")
        
        # 验证通过API函数
        viewed_posts = get_user_viewed_posts(test_user)
        has_viewed = has_user_viewed_post(test_user, test_post)
        print(f"通过API获取的浏览记录: {viewed_posts}")
        print(f"用户是否浏览过该帖子: {has_viewed}")

def main():
    check_existing_records()
    test_add_new_record()

if __name__ == "__main__":
    main()