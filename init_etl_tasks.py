#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
初始化ETL任务脚本

该脚本用于将mysql_to_postgres.py中的ETL任务转化为ETL任务记录并直接插入到MySQL数据库中。
执行此脚本可以自动创建数据库连接和ETL任务记录。
"""

import os
import sys
import json
import logging
import argparse
import pymysql
import time
import random
from datetime import datetime

# 生成唯一的bigint ID，与models.py中的函数保持一致
def generate_bigint_id():
    # 使用时间戳和随机数生成唯一ID
    timestamp = int(time.time() * 1000)  # 毫秒级时间戳
    random_part = random.randint(1000, 9999)  # 随机数部分
    return timestamp * 10000 + random_part  # 组合成唯一ID

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("init_etl_tasks.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 数据库连接配置
MYSQL_CONFIG = {
    'host': 'localhost',  # 本地开发环境使用localhost
    'port': 3306,
    'user': 'user',
    'password': 'password',
    'db': 'recommender',
    'charset': 'utf8mb4'
}

# 表映射配置，与mysql_to_postgres.py保持一致
TABLE_MAPPINGS = {
    'users': 'raw.users',
    'posts': 'raw.posts',
    'events': 'raw.events',
    'features': 'raw.features',
    'likes': 'raw.likes',
    'favorites': 'raw.favorites'
}

# 增量同步的时间字段配置，与mysql_to_postgres.py保持一致
INCREMENTAL_FIELDS = {
    'users': 'create_time',
    'posts': 'create_time',
    'events': 'timestamp',
    'features': 'update_time',
    'likes': 'create_time',
    'favorites': 'create_time'
}

# 预定义的ETL任务
PREDEFINED_TASKS = [
    {
        "name": "MySQL到PostgreSQL全量同步",
        "description": "将MySQL中的所有表数据同步到PostgreSQL数据仓库",
        "task_type": "mysql_to_postgres",
        "config": {
            "tables": TABLE_MAPPINGS,
            "incremental": False,
            "batch_size": 10000
        },
        "schedule": "0 0 * * 0"  # 每周日凌晨执行
    },
    {
        "name": "MySQL到PostgreSQL增量同步",
        "description": "将MySQL中的新增数据同步到PostgreSQL数据仓库",
        "task_type": "mysql_to_postgres",
        "config": {
            "tables": TABLE_MAPPINGS,
            "incremental": True,
            "incremental_fields": INCREMENTAL_FIELDS,
            "batch_size": 10000
        },
        "schedule": "0 0 * * 1-6"  # 每周一至周六凌晨执行
    },
    {
        "name": "用户标签处理",
        "description": "从原始数据中提取用户标签并存储到fact_user_tags表",
        "task_type": "custom_sql",
        "config": {
            "sql": """
            TRUNCATE TABLE dw.fact_user_tags;
            
            INSERT INTO dw.fact_user_tags (user_id, tag_name, tag_weight, tag_source, update_time)
            SELECT 
                user_id, 
                tag_value->>'name' as tag_name, 
                COALESCE((tag_value->>'weight')::float, 1.0) as tag_weight,
                'explicit' as tag_source,
                NOW() as update_time
            FROM raw.users, 
                 jsonb_array_elements(CASE 
                    WHEN tags->>'interests' IS NOT NULL THEN 
                        jsonb_build_array(tags->'interests') 
                    ELSE 
                        tags->'interests' 
                    END) as tag_value
            WHERE tag_value->>'name' IS NOT NULL
            ON CONFLICT (user_id, tag_name) DO UPDATE 
            SET tag_weight = EXCLUDED.tag_weight,
                update_time = EXCLUDED.update_time;
                
            INSERT INTO dw.fact_user_tags (user_id, tag_name, tag_weight, tag_source, update_time)
            WITH post_tags AS (
                SELECT 
                    post_id,
                    jsonb_array_elements_text(tags->'tags') as tag_name
                FROM raw.posts
                WHERE tags->'tags' IS NOT NULL
            ),
            user_post_interactions AS (
                SELECT 
                    e.user_id,
                    pt.tag_name,
                    COUNT(CASE WHEN e.event_type = 'view' THEN 1 END) * 0.2 +
                    COUNT(CASE WHEN e.event_type = 'like' THEN 1 END) * 0.5 +
                    COUNT(CASE WHEN e.event_type = 'favorite' THEN 1 END) * 1.0 as weight
                FROM raw.events e
                JOIN post_tags pt ON e.post_id = pt.post_id
                WHERE e.event_type IN ('view', 'like', 'favorite')
                GROUP BY e.user_id, pt.tag_name
                HAVING COUNT(*) > 0
            )
            SELECT 
                user_id,
                tag_name,
                weight as tag_weight,
                'implicit' as tag_source,
                NOW() as update_time
            FROM user_post_interactions
            ON CONFLICT (user_id, tag_name) DO UPDATE 
            SET tag_weight = 
                CASE 
                    WHEN dw.fact_user_tags.tag_source = 'explicit' THEN dw.fact_user_tags.tag_weight 
                    ELSE (dw.fact_user_tags.tag_weight + EXCLUDED.tag_weight) / 2
                END,
                update_time = EXCLUDED.update_time;
            """,
            "target_connection": "postgres"
        },
        "schedule": "0 1 * * *"  # 每天凌晨1点执行
    },
    {
        "name": "内容标签处理",
        "description": "从原始数据中提取内容标签并存储到fact_post_tags表",
        "task_type": "custom_sql",
        "config": {
            "sql": """
            TRUNCATE TABLE dw.fact_post_tags;
            
            INSERT INTO dw.fact_post_tags (post_id, tag_name, tag_weight, tag_source, update_time)
            SELECT 
                post_id, 
                tag_value as tag_name, 
                1.0 as tag_weight,
                'explicit' as tag_source,
                NOW() as update_time
            FROM raw.posts, 
                 jsonb_array_elements_text(tags->'tags') as tag_value
            WHERE tag_value IS NOT NULL
            ON CONFLICT (post_id, tag_name) DO UPDATE 
            SET tag_weight = EXCLUDED.tag_weight,
                update_time = EXCLUDED.update_time;
            """,
            "target_connection": "postgres"
        },
        "schedule": "0 2 * * *"  # 每天凌晨2点执行
    },
    {
        "name": "用户行为漏斗分析",
        "description": "分析用户从浏览到点赞到收藏的转化过程",
        "task_type": "custom_sql",
        "config": {
            "sql": """
            WITH user_post_events AS (
                SELECT 
                    user_id,
                    post_id,
                    MIN(CASE WHEN event_type = 'view' THEN timestamp END) as view_time,
                    MIN(CASE WHEN event_type = 'like' THEN timestamp END) as like_time,
                    MIN(CASE WHEN event_type = 'favorite' THEN timestamp END) as favorite_time
                FROM raw.events
                WHERE timestamp >= NOW() - INTERVAL '30 days'
                  AND event_type IN ('view', 'like', 'favorite')
                GROUP BY user_id, post_id
                HAVING MIN(CASE WHEN event_type = 'view' THEN timestamp END) IS NOT NULL
            )
            INSERT INTO dw.fact_user_funnels (
                user_id, post_id, view_time, like_time, favorite_time, 
                view_to_like_seconds, view_to_favorite_seconds, 
                funnel_complete, funnel_date, update_time
            )
            SELECT 
                user_id,
                post_id,
                view_time,
                like_time,
                favorite_time,
                CASE 
                    WHEN view_time IS NOT NULL AND like_time IS NOT NULL 
                    THEN EXTRACT(EPOCH FROM (like_time - view_time)) 
                END as view_to_like_seconds,
                CASE 
                    WHEN view_time IS NOT NULL AND favorite_time IS NOT NULL 
                    THEN EXTRACT(EPOCH FROM (favorite_time - view_time)) 
                END as view_to_favorite_seconds,
                CASE 
                    WHEN view_time IS NOT NULL AND like_time IS NOT NULL AND favorite_time IS NOT NULL 
                    THEN TRUE 
                    ELSE FALSE 
                END as funnel_complete,
                view_time::DATE as funnel_date,
                NOW() as update_time
            FROM user_post_events
            ON CONFLICT (user_id, post_id, view_time) DO UPDATE 
            SET like_time = EXCLUDED.like_time,
                favorite_time = EXCLUDED.favorite_time,
                view_to_like_seconds = EXCLUDED.view_to_like_seconds,
                view_to_favorite_seconds = EXCLUDED.view_to_favorite_seconds,
                funnel_complete = EXCLUDED.funnel_complete,
                update_time = EXCLUDED.update_time;
            """,
            "target_connection": "postgres"
        },
        "schedule": "0 3 * * *"  # 每天凌晨3点执行
    },
    {
        "name": "用户维度表更新",
        "description": "更新用户维度表",
        "task_type": "custom_sql",
        "config": {
            "sql": """
            INSERT INTO dw.dim_users (
                user_id, username, create_time, tags, preferences,
                active_days_30d, active_days_7d, post_count, like_count, favorite_count, view_count,
                last_active_time, user_segment, update_time
            )
            SELECT 
                u.user_id,
                u.username,
                u.create_time,
                u.tags,
                u.preferences,
                COALESCE((
                    SELECT COUNT(DISTINCT e.timestamp::DATE)
                    FROM raw.events e
                    WHERE e.user_id = u.user_id
                      AND e.timestamp >= NOW() - INTERVAL '30 days'
                ), 0) as active_days_30d,
                COALESCE((
                    SELECT COUNT(DISTINCT e.timestamp::DATE)
                    FROM raw.events e
                    WHERE e.user_id = u.user_id
                      AND e.timestamp >= NOW() - INTERVAL '7 days'
                ), 0) as active_days_7d,
                COALESCE((
                    SELECT COUNT(*)
                    FROM raw.posts p
                    WHERE p.author_id = u.user_id
                ), 0) as post_count,
                COALESCE((
                    SELECT COUNT(*)
                    FROM raw.likes l
                    WHERE l.user_id = u.user_id
                ), 0) as like_count,
                COALESCE((
                    SELECT COUNT(*)
                    FROM raw.favorites f
                    WHERE f.user_id = u.user_id
                ), 0) as favorite_count,
                COALESCE((
                    SELECT COUNT(*)
                    FROM raw.events e
                    WHERE e.user_id = u.user_id
                      AND e.event_type = 'view'
                ), 0) as view_count,
                COALESCE((
                    SELECT MAX(e.timestamp)
                    FROM raw.events e
                    WHERE e.user_id = u.user_id
                ), u.create_time) as last_active_time,
                CASE
                    WHEN (
                        SELECT COUNT(DISTINCT e.timestamp::DATE)
                        FROM raw.events e
                        WHERE e.user_id = u.user_id
                          AND e.timestamp >= NOW() - INTERVAL '30 days'
                    ) >= 20 THEN 'highly_active'
                    WHEN (
                        SELECT COUNT(DISTINCT e.timestamp::DATE)
                        FROM raw.events e
                        WHERE e.user_id = u.user_id
                          AND e.timestamp >= NOW() - INTERVAL '30 days'
                    ) >= 10 THEN 'active'
                    WHEN (
                        SELECT COUNT(DISTINCT e.timestamp::DATE)
                        FROM raw.events e
                        WHERE e.user_id = u.user_id
                          AND e.timestamp >= NOW() - INTERVAL '30 days'
                    ) >= 5 THEN 'regular'
                    WHEN (
                        SELECT MAX(e.timestamp)
                        FROM raw.events e
                        WHERE e.user_id = u.user_id
                    ) >= NOW() - INTERVAL '30 days' THEN 'casual'
                    ELSE 'inactive'
                END as user_segment,
                NOW() as update_time
            FROM raw.users u
            ON CONFLICT (user_id) DO UPDATE 
            SET username = EXCLUDED.username,
                tags = EXCLUDED.tags,
                preferences = EXCLUDED.preferences,
                active_days_30d = EXCLUDED.active_days_30d,
                active_days_7d = EXCLUDED.active_days_7d,
                post_count = EXCLUDED.post_count,
                like_count = EXCLUDED.like_count,
                favorite_count = EXCLUDED.favorite_count,
                view_count = EXCLUDED.view_count,
                last_active_time = EXCLUDED.last_active_time,
                user_segment = EXCLUDED.user_segment,
                update_time = EXCLUDED.update_time;
            """,
            "target_connection": "postgres"
        },
        "schedule": "0 4 * * *"  # 每天凌晨4点执行
    },
    {
        "name": "内容维度表更新",
        "description": "更新内容维度表",
        "task_type": "custom_sql",
        "config": {
            "sql": """
            INSERT INTO dw.dim_posts (
                post_id, title, content, author_id, create_time, tags,
                view_count, like_count, favorite_count, ctr, like_ratio, favorite_ratio,
                popularity_score, update_time
            )
            SELECT 
                p.post_id,
                p.title,
                p.content,
                p.author_id,
                p.create_time,
                p.tags,
                p.view_count,
                p.like_count,
                p.favorite_count,
                CASE 
                    WHEN p.view_count > 0 THEN 
                        (SELECT COUNT(*) FROM raw.events e WHERE e.post_id = p.post_id AND e.event_type = 'click')::FLOAT / p.view_count 
                    ELSE 0 
                END as ctr,
                CASE 
                    WHEN p.view_count > 0 THEN p.like_count::FLOAT / p.view_count 
                    ELSE 0 
                END as like_ratio,
                CASE 
                    WHEN p.view_count > 0 THEN p.favorite_count::FLOAT / p.view_count 
                    ELSE 0 
                END as favorite_ratio,
                p.view_count * 0.3 + p.like_count * 0.5 + p.favorite_count * 1.0 as popularity_score,
                NOW() as update_time
            FROM raw.posts p
            ON CONFLICT (post_id) DO UPDATE 
            SET title = EXCLUDED.title,
                content = EXCLUDED.content,
                tags = EXCLUDED.tags,
                view_count = EXCLUDED.view_count,
                like_count = EXCLUDED.like_count,
                favorite_count = EXCLUDED.favorite_count,
                ctr = EXCLUDED.ctr,
                like_ratio = EXCLUDED.like_ratio,
                favorite_ratio = EXCLUDED.favorite_ratio,
                popularity_score = EXCLUDED.popularity_score,
                update_time = EXCLUDED.update_time;
            """,
            "target_connection": "postgres"
        },
        "schedule": "0 5 * * *"  # 每天凌晨5点执行
    }
]

def connect_mysql():
    """
    连接MySQL数据库
    """
    try:
        conn = pymysql.connect(
            host=MYSQL_CONFIG['host'],
            port=MYSQL_CONFIG['port'],
            user=MYSQL_CONFIG['user'],
            password=MYSQL_CONFIG['password'],
            db=MYSQL_CONFIG['db'],
            charset=MYSQL_CONFIG['charset'],
            cursorclass=pymysql.cursors.DictCursor
        )
        logger.info("MySQL连接成功")
        return conn
    except Exception as e:
        logger.error(f"MySQL连接失败: {e}")
        sys.exit(1)

def create_database_connections():
    """
    创建数据库连接记录
    """
    try:
        conn = connect_mysql()
        cursor = conn.cursor()
        
        # 检查是否已存在连接记录
        cursor.execute("SELECT COUNT(*) as count FROM database_connections")
        result = cursor.fetchone()
        
        if result['count'] > 0:
            logger.info("数据库连接记录已存在，跳过创建")
            return
        
        # 创建MySQL连接记录
        mysql_connection = {
            "name": "MySQL业务数据库",
            "description": "推荐系统的主要业务数据库",
            "connection_type": "mysql",
            "host": MYSQL_CONFIG['host'],
            "port": MYSQL_CONFIG['port'],
            "username": MYSQL_CONFIG['user'],
            "password": MYSQL_CONFIG['password'],
            "database": MYSQL_CONFIG['db'],
            "config": json.dumps({"charset": "utf8mb4"})
        }
        
        # 生成唯一ID
        connection_id = generate_bigint_id()
        
        cursor.execute("""
        INSERT INTO database_connections 
        (connection_id, name, description, connection_type, host, port, username, password, `database`, config, created_at, updated_at) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """, (
            connection_id,
            mysql_connection["name"],
            mysql_connection["description"],
            mysql_connection["connection_type"],
            mysql_connection["host"],
            mysql_connection["port"],
            mysql_connection["username"],
            mysql_connection["password"],
            mysql_connection["database"],
            mysql_connection["config"]
        ))
        mysql_connection_id = cursor.lastrowid
        
        # 创建PostgreSQL连接记录
        postgres_connection = {
            "name": "PostgreSQL数据仓库",
            "description": "用于数据分析的数据仓库",
            "connection_type": "postgres",
            "host": "localhost",  # 本地开发环境使用localhost
            "port": 5432,
            "username": "postgres",
            "password": "postgres",
            "database": "datawarehouse",
            "config": json.dumps({"sslmode": "disable"})
        }
        
        # 生成唯一ID
        postgres_connection_id = generate_bigint_id()
        
        cursor.execute("""
        INSERT INTO database_connections 
        (connection_id, name, description, connection_type, host, port, username, password, `database`, config, created_at, updated_at) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """, (
            postgres_connection_id,
            postgres_connection["name"],
            postgres_connection["description"],
            postgres_connection["connection_type"],
            postgres_connection["host"],
            postgres_connection["port"],
            postgres_connection["username"],
            postgres_connection["password"],
            postgres_connection["database"],
            postgres_connection["config"]
        ))
        postgres_connection_id = cursor.lastrowid
        
        # 创建Redis连接记录
        redis_connection = {
            "name": "Redis缓存",
            "description": "用于缓存推荐结果和消重",
            "connection_type": "redis",
            "host": "localhost",  # 本地开发环境使用localhost
            "port": 6379,
            "username": "",
            "password": "redispassword",
            "database": "0",
            "config": json.dumps({"decode_responses": True})
        }
        
        # 生成唯一ID
        redis_connection_id = generate_bigint_id()
        
        cursor.execute("""
        INSERT INTO database_connections 
        (connection_id, name, description, connection_type, host, port, username, password, `database`, config, created_at, updated_at) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """, (
            redis_connection_id,
            redis_connection["name"],
            redis_connection["description"],
            redis_connection["connection_type"],
            redis_connection["host"],
            redis_connection["port"],
            redis_connection["username"],
            redis_connection["password"],
            redis_connection["database"],
            redis_connection["config"]
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"成功创建数据库连接记录: MySQL(ID:{mysql_connection_id}), PostgreSQL(ID:{postgres_connection_id})")
        
        return {
            "mysql": connection_id,
            "postgres": postgres_connection_id,
            "redis": redis_connection_id
        }
    except Exception as e:
        logger.error(f"创建数据库连接记录失败: {e}")
        sys.exit(1)

def create_etl_tasks(connection_ids=None):
    """
    创建ETL任务记录
    """
    try:
        # 连接MySQL数据库
        mysql_conn = connect_mysql()
        mysql_cursor = mysql_conn.cursor()
        
        # 检查是否已存在任务记录
        mysql_cursor.execute("SELECT COUNT(*) as count FROM etl_tasks")
        result = mysql_cursor.fetchone()
        
        if result['count'] > 0:
            logger.info("ETL任务记录已存在，跳过创建")
            return
        
        # 首先查询已创建的数据库连接记录，获取真实的connection_id
        mysql_cursor.execute("SELECT connection_id, connection_type FROM database_connections")
        db_connections = mysql_cursor.fetchall()
        
        # 创建连接类型到connection_id的映射
        connection_type_map = {}
        for conn in db_connections:
            if conn['connection_type'] == 'mysql':
                connection_type_map['mysql'] = conn['connection_id']
            elif conn['connection_type'] == 'postgres':
                connection_type_map['postgres'] = conn['connection_id']
            elif conn['connection_type'] == 'redis':
                connection_type_map['redis'] = conn['connection_id']
        
        logger.info(f"数据库连接ID映射: {connection_type_map}")
        
        # 创建预定义的ETL任务
        for task in PREDEFINED_TASKS:
            # 根据任务类型设置源连接和目标连接
            source_connection_id = None
            target_connection_id = None
            
            # 初始化task_config
            task_config = task["config"].copy()
            
            if task["task_type"] == "mysql_to_postgres":
                source_connection_id = connection_type_map.get('mysql')
                target_connection_id = connection_type_map.get('postgres')
            elif task["task_type"] == "custom_sql":
                # 对于自定义SQL任务，设置源连接为PostgreSQL（因为SQL在PostgreSQL中执行）
                source_connection_id = connection_type_map.get('postgres')
                
                # 根据配置中的target_connection设置目标连接
                target_connection = task_config.get("target_connection")
                if target_connection and target_connection in connection_type_map:
                    target_connection_id = connection_type_map.get(target_connection)
                    # 移除config中的target_connection字段，因为它不是实际配置的一部分
                    task_config.pop("target_connection", None)
            
            # 生成唯一ID
            task_id = generate_bigint_id()
            
            mysql_cursor.execute("""
            INSERT INTO etl_tasks 
            (task_id, name, description, task_type, source_connection_id, target_connection_id, config, schedule, status, created_at, updated_at) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (
                task_id,
                task["name"],
                task["description"],
                task["task_type"],
                source_connection_id,
                target_connection_id,
                json.dumps(task_config),
                task["schedule"],
                "pending"
            ))
        
        # 提交事务
        mysql_conn.commit()
        mysql_cursor.close()
        mysql_conn.close()
        
        logger.info(f"成功创建{len(PREDEFINED_TASKS)}个ETL任务记录")
    except Exception as e:
        logger.error(f"创建ETL任务记录失败: {e}")
        sys.exit(1)

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='初始化ETL任务脚本')
    parser.add_argument('--force', action='store_true', help='强制重新创建所有记录')
    args = parser.parse_args()
    
    try:
        # 如果指定了force参数，则删除所有现有记录
        if args.force:
            conn = connect_mysql()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM etl_task_history")
            cursor.execute("DELETE FROM etl_tasks")
            cursor.execute("DELETE FROM database_connections")
            conn.commit()
            cursor.close()
            conn.close()
            logger.info("已删除所有现有记录")
        
        # 创建数据库连接记录
        create_database_connections()
        
        # 创建ETL任务记录
        create_etl_tasks({})  # 传入空字典，因为我们在函数内部会重新查询数据库连接
        
        logger.info("初始化ETL任务完成")
    except Exception as e:
        logger.error(f"初始化ETL任务失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()