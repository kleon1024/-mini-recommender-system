#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MySQL到PostgreSQL数据同步脚本

该脚本用于定期将MySQL中的业务数据同步到PostgreSQL数据仓库中，用于数据分析。
支持增量同步和全量同步两种模式。
"""

import os
import sys
import time
import json
import logging
import argparse
from datetime import datetime, timedelta
import pymysql
import psycopg2
import pandas as pd
from sqlalchemy import create_engine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mysql_to_postgres_sync.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 数据库连接配置
MYSQL_CONFIG = {
    'host': 'mysql',
    'port': 3306,
    'user': 'user',
    'password': 'password',
    'db': 'recommender',
    'charset': 'utf8mb4'
}

POSTGRES_CONFIG = {
    'host': 'postgres',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'dbname': 'datawarehouse'
}

# 表映射配置
TABLE_MAPPINGS = {
    'users': 'raw.users',
    'posts': 'raw.posts',
    'events': 'raw.events',
    'features': 'raw.features',
    'likes': 'raw.likes',
    'favorites': 'raw.favorites'
}

# 增量同步的时间字段配置
INCREMENTAL_FIELDS = {
    'users': 'create_time',
    'posts': 'create_time',
    'events': 'timestamp',
    'features': 'update_time',
    'likes': 'create_time',
    'favorites': 'create_time'
}

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

def connect_postgres():
    """
    连接PostgreSQL数据库
    """
    try:
        conn = psycopg2.connect(
            host=POSTGRES_CONFIG['host'],
            port=POSTGRES_CONFIG['port'],
            user=POSTGRES_CONFIG['user'],
            password=POSTGRES_CONFIG['password'],
            dbname=POSTGRES_CONFIG['dbname']
        )
        logger.info("PostgreSQL连接成功")
        return conn
    except Exception as e:
        logger.error(f"PostgreSQL连接失败: {e}")
        sys.exit(1)

def get_sqlalchemy_engines():
    """
    获取SQLAlchemy引擎，用于pandas数据传输
    """
    mysql_uri = f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['db']}"
    postgres_uri = f"postgresql://{POSTGRES_CONFIG['user']}:{POSTGRES_CONFIG['password']}@{POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}/{POSTGRES_CONFIG['dbname']}"
    
    mysql_engine = create_engine(mysql_uri)
    postgres_engine = create_engine(postgres_uri)
    
    return mysql_engine, postgres_engine

def get_last_sync_time(pg_conn, table_name):
    """
    获取上次同步时间
    """
    try:
        cursor = pg_conn.cursor()
        cursor.execute(f"SELECT MAX(import_time) FROM {table_name}")
        result = cursor.fetchone()
        cursor.close()
        
        if result and result[0]:
            # 返回上次同步时间，减去1小时以确保不会遗漏数据
            return result[0] - timedelta(hours=1)
        else:
            # 如果没有同步记录，返回30天前的时间
            return datetime.now() - timedelta(days=30)
    except Exception as e:
        logger.error(f"获取上次同步时间失败: {e}")
        # 默认返回7天前
        return datetime.now() - timedelta(days=7)

def sync_table(mysql_engine, postgres_engine, mysql_table, pg_table, incremental=True, batch_size=10000):
    """
    同步单个表的数据
    """
    try:
        logger.info(f"开始同步表 {mysql_table} -> {pg_table}")
        
        # 获取上次同步时间（仅增量同步时使用）
        last_sync_time = None
        if incremental:
            with postgres_engine.connect() as conn:
                last_sync_time = get_last_sync_time(conn, pg_table)
                logger.info(f"上次同步时间: {last_sync_time}")
        
        # 构建查询
        query = f"SELECT * FROM {mysql_table}"
        if incremental and last_sync_time and mysql_table in INCREMENTAL_FIELDS:
            time_field = INCREMENTAL_FIELDS[mysql_table]
            query += f" WHERE {time_field} >= '{last_sync_time}'"
        
        # 使用pandas读取MySQL数据
        logger.info(f"执行查询: {query}")
        df = pd.read_sql(query, mysql_engine)
        
        if df.empty:
            logger.info(f"没有新数据需要同步: {mysql_table}")
            return 0
        
        # 添加导入时间
        df['import_time'] = datetime.now()
        
        # 处理JSON字段
        for col in df.columns:
            if df[col].dtype == 'object':
                # 尝试将可能的JSON字符串转换为字典
                try:
                    sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                    if sample and isinstance(sample, str) and (sample.startswith('{') or sample.startswith('[')):
                        df[col] = df[col].apply(lambda x: json.loads(x) if isinstance(x, str) and x else x)
                except Exception as e:
                    logger.warning(f"列 {col} JSON转换失败: {e}")
        
        # 分批写入PostgreSQL
        total_rows = len(df)
        logger.info(f"需要同步 {total_rows} 行数据")
        
        for i in range(0, total_rows, batch_size):
            batch_df = df.iloc[i:i+batch_size]
            batch_df.to_sql(
                pg_table.split('.')[-1],  # 提取表名（不含schema）
                postgres_engine,
                schema=pg_table.split('.')[0] if '.' in pg_table else None,
                if_exists='append',
                index=False
            )
            logger.info(f"已同步 {min(i+batch_size, total_rows)}/{total_rows} 行")
        
        logger.info(f"表 {mysql_table} -> {pg_table} 同步完成")
        return total_rows
    except Exception as e:
        logger.error(f"同步表 {mysql_table} 失败: {e}")
        return 0

def sync_all_tables(incremental=True):
    """
    同步所有配置的表
    """
    mysql_engine, postgres_engine = get_sqlalchemy_engines()
    
    total_synced = 0
    start_time = time.time()
    
    for mysql_table, pg_table in TABLE_MAPPINGS.items():
        rows_synced = sync_table(mysql_engine, postgres_engine, mysql_table, pg_table, incremental)
        total_synced += rows_synced
    
    end_time = time.time()
    logger.info(f"所有表同步完成，共同步 {total_synced} 行数据，耗时 {end_time - start_time:.2f} 秒")

def process_user_tags():
    """
    处理用户标签，从原始数据中提取用户标签并存储到fact_user_tags表
    """
    try:
        logger.info("开始处理用户标签")
        
        # 连接PostgreSQL
        conn = connect_postgres()
        cursor = conn.cursor()
        
        # 清空现有的用户标签表（可选，也可以使用增量更新）
        cursor.execute("TRUNCATE TABLE dw.fact_user_tags")
        
        # 从用户表中提取显式标签
        cursor.execute("""
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
                update_time = EXCLUDED.update_time
        """)
        
        # 从用户行为中提取隐式标签
        cursor.execute("""
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
                update_time = EXCLUDED.update_time
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("用户标签处理完成")
    except Exception as e:
        logger.error(f"处理用户标签失败: {e}")

def process_post_tags():
    """
    处理内容标签，从原始数据中提取内容标签并存储到fact_post_tags表
    """
    try:
        logger.info("开始处理内容标签")
        
        # 连接PostgreSQL
        conn = connect_postgres()
        cursor = conn.cursor()
        
        # 清空现有的内容标签表（可选，也可以使用增量更新）
        cursor.execute("TRUNCATE TABLE dw.fact_post_tags")
        
        # 从内容表中提取显式标签
        cursor.execute("""
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
                update_time = EXCLUDED.update_time
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("内容标签处理完成")
    except Exception as e:
        logger.error(f"处理内容标签失败: {e}")

def process_user_funnels():
    """
    处理用户行为漏斗，分析用户从浏览到点赞到收藏的转化过程
    """
    try:
        logger.info("开始处理用户行为漏斗")
        
        # 连接PostgreSQL
        conn = connect_postgres()
        cursor = conn.cursor()
        
        # 获取最近一次处理的时间
        cursor.execute("SELECT MAX(update_time) FROM dw.fact_user_funnels")
        last_process_time = cursor.fetchone()[0]
        
        if last_process_time:
            # 减去1天以确保不会遗漏数据
            last_process_time = last_process_time - timedelta(days=1)
        else:
            # 如果没有处理记录，处理最近30天的数据
            last_process_time = datetime.now() - timedelta(days=30)
        
        logger.info(f"处理 {last_process_time} 之后的用户行为漏斗")
        
        # 分析用户行为漏斗
        cursor.execute("""
            WITH user_post_events AS (
                SELECT 
                    user_id,
                    post_id,
                    MIN(CASE WHEN event_type = 'view' THEN timestamp END) as view_time,
                    MIN(CASE WHEN event_type = 'like' THEN timestamp END) as like_time,
                    MIN(CASE WHEN event_type = 'favorite' THEN timestamp END) as favorite_time
                FROM raw.events
                WHERE timestamp >= %s
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
                update_time = EXCLUDED.update_time
        """, (last_process_time,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("用户行为漏斗处理完成")
    except Exception as e:
        logger.error(f"处理用户行为漏斗失败: {e}")

def update_dim_users():
    """
    更新用户维度表
    """
    try:
        logger.info("开始更新用户维度表")
        
        # 连接PostgreSQL
        conn = connect_postgres()
        cursor = conn.cursor()
        
        # 更新用户维度表
        cursor.execute("""
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
                update_time = EXCLUDED.update_time
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("用户维度表更新完成")
    except Exception as e:
        logger.error(f"更新用户维度表失败: {e}")

def update_dim_posts():
    """
    更新内容维度表
    """
    try:
        logger.info("开始更新内容维度表")
        
        # 连接PostgreSQL
        conn = connect_postgres()
        cursor = conn.cursor()
        
        # 更新内容维度表
        cursor.execute("""
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
                update_time = EXCLUDED.update_time
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("内容维度表更新完成")
    except Exception as e:
        logger.error(f"更新内容维度表失败: {e}")

def update_fact_events():
    """
    更新事件事实表
    """
    try:
        logger.info("开始更新事件事实表")
        
        # 连接PostgreSQL
        conn = connect_postgres()
        cursor = conn.cursor()
        
        # 获取最近一次处理的时间
        cursor.execute("SELECT MAX(event_time) FROM dw.fact_events")
        last_process_time = cursor.fetchone()[0]
        
        if last_process_time:
            # 减去1天以确保不会遗漏数据
            last_process_time = last_process_time - timedelta(days=1)
        else:
            # 如果没有处理记录，处理最近30天的数据
            last_process_time = datetime.now() - timedelta(days=30)
        
        logger.info(f"处理 {last_process_time} 之后的事件数据")
        
        # 更新事件事实表
        cursor.execute("""
            INSERT INTO dw.fact_events (
                event_id, user_id, post_id, event_type, event_time, source, device_type, os
            )
            SELECT 
                e.event_id,
                e.user_id,
                e.post_id,
                e.event_type,
                e.timestamp as event_time,
                e.source,
                (e.device_info->>'type')::VARCHAR as device_type,
                (e.device_info->>'os')::VARCHAR as os
            FROM raw.events e
            WHERE e.timestamp >= %s
            ON CONFLICT (event_id, event_time) DO UPDATE 
            SET user_id = EXCLUDED.user_id,
                post_id = EXCLUDED.post_id,
                event_type = EXCLUDED.event_type,
                source = EXCLUDED.source,
                device_type = EXCLUDED.device_type,
                os = EXCLUDED.os
        """, (last_process_time,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("事件事实表更新完成")
    except Exception as e:
        logger.error(f"更新事件事实表失败: {e}")

def update_user_activity_analysis():
    """
    更新用户活跃度分析
    """
    try:
        logger.info("开始更新用户活跃度分析")
        
        # 连接PostgreSQL
        conn = connect_postgres()
        cursor = conn.cursor()
        
        # 更新用户活跃度分析
        cursor.execute("""
            INSERT INTO mart.user_activity_analysis (
                analysis_date, total_users, active_users_1d, active_users_7d, active_users_30d,
                new_users, returning_users, churned_users, average_events_per_user, update_time
            )
            WITH date_series AS (
                SELECT generate_series(
                    COALESCE((SELECT MAX(analysis_date) FROM mart.user_activity_analysis), CURRENT_DATE - INTERVAL '30 days')::DATE + INTERVAL '1 day',
                    CURRENT_DATE - INTERVAL '1 day',
                    INTERVAL '1 day'
                )::DATE as analysis_date
            ),
            daily_stats AS (
                SELECT 
                    d.analysis_date,
                    (SELECT COUNT(*) FROM raw.users) as total_users,
                    (SELECT COUNT(DISTINCT user_id) 
                     FROM raw.events 
                     WHERE timestamp::DATE = d.analysis_date) as active_users_1d,
                    (SELECT COUNT(DISTINCT user_id) 
                     FROM raw.events 
                     WHERE timestamp::DATE BETWEEN d.analysis_date - INTERVAL '6 days' AND d.analysis_date) as active_users_7d,
                    (SELECT COUNT(DISTINCT user_id) 
                     FROM raw.events 
                     WHERE timestamp::DATE BETWEEN d.analysis_date - INTERVAL '29 days' AND d.analysis_date) as active_users_30d,
                    (SELECT COUNT(*) 
                     FROM raw.users 
                     WHERE create_time::DATE = d.analysis_date) as new_users,
                    (SELECT COUNT(DISTINCT user_id) 
                     FROM raw.events 
                     WHERE timestamp::DATE = d.analysis_date
                       AND user_id IN (
                           SELECT DISTINCT user_id 
                           FROM raw.events 
                           WHERE timestamp::DATE BETWEEN d.analysis_date - INTERVAL '30 days' AND d.analysis_date - INTERVAL '1 day'
                       )) as returning_users,
                    (SELECT COUNT(DISTINCT user_id) 
                     FROM raw.events 
                     WHERE timestamp::DATE = d.analysis_date - INTERVAL '1 day'
                       AND user_id NOT IN (
                           SELECT DISTINCT user_id 
                           FROM raw.events 
                           WHERE timestamp::DATE = d.analysis_date
                       )) as churned_users,
                    (SELECT COALESCE(COUNT(*) / NULLIF(COUNT(DISTINCT user_id), 0), 0) 
                     FROM raw.events 
                     WHERE timestamp::DATE = d.analysis_date) as average_events_per_user
                FROM date_series d
            )
            SELECT 
                analysis_date,
                total_users,
                active_users_1d,
                active_users_7d,
                active_users_30d,
                new_users,
                returning_users,
                churned_users,
                average_events_per_user,
                NOW() as update_time
            FROM daily_stats
            ON CONFLICT (analysis_date) DO UPDATE 
            SET total_users = EXCLUDED.total_users,
                active_users_1d = EXCLUDED.active_users_1d,
                active_users_7d = EXCLUDED.active_users_7d,
                active_users_30d = EXCLUDED.active_users_30d,
                new_users = EXCLUDED.new_users,
                returning_users = EXCLUDED.returning_users,
                churned_users = EXCLUDED.churned_users,
                average_events_per_user = EXCLUDED.average_events_per_user,
                update_time = EXCLUDED.update_time
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("用户活跃度分析更新完成")
    except Exception as e:
        logger.error(f"更新用户活跃度分析失败: {e}")

def update_content_performance_analysis():
    """
    更新内容表现分析
    """
    try:
        logger.info("开始更新内容表现分析")
        
        # 连接PostgreSQL
        conn = connect_postgres()
        cursor = conn.cursor()
        
        # 更新内容表现分析
        cursor.execute("""
            INSERT INTO mart.content_performance_analysis (
                analysis_date, total_posts, new_posts, total_views, total_likes, total_favorites,
                average_ctr, average_like_ratio, average_favorite_ratio, top_tags, update_time
            )
            WITH date_series AS (
                SELECT generate_series(
                    COALESCE((SELECT MAX(analysis_date) FROM mart.content_performance_analysis), CURRENT_DATE - INTERVAL '30 days')::DATE + INTERVAL '1 day',
                    CURRENT_DATE - INTERVAL '1 day',
                    INTERVAL '1 day'
                )::DATE as analysis_date
            ),
            daily_stats AS (
                SELECT 
                    d.analysis_date,
                    (SELECT COUNT(*) FROM raw.posts) as total_posts,
                    (SELECT COUNT(*) 
                     FROM raw.posts 
                     WHERE create_time::DATE = d.analysis_date) as new_posts,
                    (SELECT SUM(view_count) FROM raw.posts) as total_views,
                    (SELECT SUM(like_count) FROM raw.posts) as total_likes,
                    (SELECT SUM(favorite_count) FROM raw.posts) as total_favorites,
                    (SELECT AVG(CASE WHEN view_count > 0 THEN like_count::FLOAT / view_count ELSE 0 END) 
                     FROM raw.posts) as average_like_ratio,
                    (SELECT AVG(CASE WHEN view_count > 0 THEN favorite_count::FLOAT / view_count ELSE 0 END) 
                     FROM raw.posts) as average_favorite_ratio,
                    (SELECT AVG(
                        CASE 
                            WHEN view_count > 0 THEN 
                                (SELECT COUNT(*) FROM raw.events e WHERE e.post_id = p.post_id AND e.event_type = 'click')::FLOAT / view_count 
                            ELSE 0 
                        END
                     ) 
                     FROM raw.posts p) as average_ctr,
                    (SELECT jsonb_agg(tag_info)
                     FROM (
                         SELECT jsonb_build_object(
                             'tag', tag_name,
                             'count', COUNT(*)
                         ) as tag_info
                         FROM dw.fact_post_tags
                         GROUP BY tag_name
                         ORDER BY COUNT(*) DESC
                         LIMIT 10
                     ) t) as top_tags
                FROM date_series d
            )
            SELECT 
                analysis_date,
                total_posts,
                new_posts,
                total_views,
                total_likes,
                total_favorites,
                average_ctr,
                average_like_ratio,
                average_favorite_ratio,
                top_tags,
                NOW() as update_time
            FROM daily_stats
            ON CONFLICT (analysis_date) DO UPDATE 
            SET total_posts = EXCLUDED.total_posts,
                new_posts = EXCLUDED.new_posts,
                total_views = EXCLUDED.total_views,
                total_likes = EXCLUDED.total_likes,
                total_favorites = EXCLUDED.total_favorites,
                average_ctr = EXCLUDED.average_ctr,
                average_like_ratio = EXCLUDED.average_like_ratio,
                average_favorite_ratio = EXCLUDED.average_favorite_ratio,
                top_tags = EXCLUDED.top_tags,
                update_time = EXCLUDED.update_time
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("内容表现分析更新完成")
    except Exception as e:
        logger.error(f"更新内容表现分析失败: {e}")

def update_recommendation_performance_analysis():
    """
    更新推荐效果分析
    """
    try:
        logger.info("开始更新推荐效果分析")
        
        # 连接PostgreSQL
        conn = connect_postgres()
        cursor = conn.cursor()
        
        # 更新推荐效果分析
        cursor.execute("""
            INSERT INTO mart.recommendation_performance_analysis (
                analysis_date, total_recommendations, clicked_recommendations, recommendation_ctr,
                average_view_duration, like_from_recommendation, favorite_from_recommendation,
                recommendation_sources, update_time
            )
            WITH date_series AS (
                SELECT generate_series(
                    COALESCE((SELECT MAX(analysis_date) FROM mart.recommendation_performance_analysis), CURRENT_DATE - INTERVAL '30 days')::DATE + INTERVAL '1 day',
                    CURRENT_DATE - INTERVAL '1 day',
                    INTERVAL '1 day'
                )::DATE as analysis_date
            ),
            daily_stats AS (
                SELECT 
                    d.analysis_date,
                    (SELECT COUNT(*) 
                     FROM raw.events 
                     WHERE event_type = 'view' 
                       AND source IN ('recommendation', 'home')
                       AND timestamp::DATE = d.analysis_date) as total_recommendations,
                    (SELECT COUNT(*) 
                     FROM raw.events 
                     WHERE event_type = 'click' 
                       AND source IN ('recommendation', 'home')
                       AND timestamp::DATE = d.analysis_date) as clicked_recommendations,
                    CASE 
                        WHEN (SELECT COUNT(*) 
                              FROM raw.events 
                              WHERE event_type = 'view' 
                                AND source IN ('recommendation', 'home')
                                AND timestamp::DATE = d.analysis_date) > 0 
                        THEN (SELECT COUNT(*) 
                              FROM raw.events 
                              WHERE event_type = 'click' 
                                AND source IN ('recommendation', 'home')
                                AND timestamp::DATE = d.analysis_date)::FLOAT / 
                             (SELECT COUNT(*) 
                              FROM raw.events 
                              WHERE event_type = 'view' 
                                AND source IN ('recommendation', 'home')
                                AND timestamp::DATE = d.analysis_date) 
                        ELSE 0 
                    END as recommendation_ctr,
                    (SELECT AVG(EXTRACT(EPOCH FROM (MAX(timestamp) - MIN(timestamp)))) 
                     FROM raw.events 
                     WHERE event_type IN ('view', 'click') 
                       AND source IN ('recommendation', 'home')
                       AND timestamp::DATE = d.analysis_date 
                     GROUP BY user_id, post_id) as average_view_duration,
                    (SELECT COUNT(*) 
                     FROM raw.events 
                     WHERE event_type = 'like' 
                       AND post_id IN (
                           SELECT DISTINCT post_id 
                           FROM raw.events 
                           WHERE event_type = 'view' 
                             AND source IN ('recommendation', 'home')
                             AND timestamp::DATE = d.analysis_date
                       )
                       AND timestamp::DATE = d.analysis_date) as like_from_recommendation,
                    (SELECT COUNT(*) 
                     FROM raw.events 
                     WHERE event_type = 'favorite' 
                       AND post_id IN (
                           SELECT DISTINCT post_id 
                           FROM raw.events 
                           WHERE event_type = 'view' 
                             AND source IN ('recommendation', 'home')
                             AND timestamp::DATE = d.analysis_date
                       )
                       AND timestamp::DATE = d.analysis_date) as favorite_from_recommendation,
                    (SELECT jsonb_object_agg(source, count)
                     FROM (
                         SELECT 
                             source,
                             COUNT(*) as count
                         FROM raw.events
                         WHERE event_type = 'view'
                           AND timestamp::DATE = d.analysis_date
                         GROUP BY source
                     ) s) as recommendation_sources
                FROM date_series d
            )
            SELECT 
                analysis_date,
                total_recommendations,
                clicked_recommendations,
                recommendation_ctr,
                average_view_duration,
                like_from_recommendation,
                favorite_from_recommendation,
                recommendation_sources,
                NOW() as update_time
            FROM daily_stats
            ON CONFLICT (analysis_date) DO UPDATE 
            SET total_recommendations = EXCLUDED.total_recommendations,
                clicked_recommendations = EXCLUDED.clicked_recommendations,
                recommendation_ctr = EXCLUDED.recommendation_ctr,
                average_view_duration = EXCLUDED.average_view_duration,
                like_from_recommendation = EXCLUDED.like_from_recommendation,
                favorite_from_recommendation = EXCLUDED.favorite_from_recommendation,
                recommendation_sources = EXCLUDED.recommendation_sources,
                update_time = EXCLUDED.update_time
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("推荐效果分析更新完成")
    except Exception as e:
        logger.error(f"更新推荐效果分析失败: {e}")

def update_user_similarity_matrix():
    """
    更新用户相似度矩阵
    """
    try:
        logger.info("开始更新用户相似度矩阵")
        
        # 连接PostgreSQL
        conn = connect_postgres()
        cursor = conn.cursor()
        
        # 更新用户相似度矩阵
        cursor.execute("""
            TRUNCATE TABLE mart.user_similarity_matrix;
            
            INSERT INTO mart.user_similarity_matrix (
                user_id_a, user_id_b, similarity_score, common_interests, update_time
            )
            WITH user_tags AS (
                SELECT 
                    user_id,
                    jsonb_object_agg(tag_name, tag_weight) as tag_weights
                FROM dw.fact_user_tags
                GROUP BY user_id
            ),
            user_pairs AS (
                SELECT 
                    a.user_id as user_id_a,
                    b.user_id as user_id_b
                FROM user_tags a
                CROSS JOIN user_tags b
                WHERE a.user_id < b.user_id
            ),
            common_tags AS (
                SELECT 
                    p.user_id_a,
                    p.user_id_b,
                    jsonb_object_agg(
                        t.tag_name, 
                        jsonb_build_object(
                            'weight_a', t.weight_a,
                            'weight_b', t.weight_b
                        )
                    ) as common_tags
                FROM user_pairs p
                JOIN (
                    SELECT 
                        a.user_id as user_id_a,
                        b.user_id as user_id_b,
                        a.tag_name,
                        a.tag_weight as weight_a,
                        b.tag_weight as weight_b
                    FROM dw.fact_user_tags a
                    JOIN dw.fact_user_tags b ON a.tag_name = b.tag_name
                    WHERE a.user_id < b.user_id
                ) t ON p.user_id_a = t.user_id_a AND p.user_id_b = t.user_id_b
                GROUP BY p.user_id_a, p.user_id_b
            )
            SELECT 
                p.user_id_a,
                p.user_id_b,
                CASE 
                    WHEN c.common_tags IS NULL THEN 0
                    ELSE (
                        SELECT 
                            SUM(((c.common_tags->tag_name->>'weight_a')::float * (c.common_tags->tag_name->>'weight_b')::float)) /
                            SQRT(SUM((c.common_tags->tag_name->>'weight_a')::float * (c.common_tags->tag_name->>'weight_a')::float) * 
                                 SUM((c.common_tags->tag_name->>'weight_b')::float * (c.common_tags->tag_name->>'weight_b')::float))
                        FROM jsonb_object_keys(c.common_tags) as tag_name
                    )
                END as similarity_score,
                COALESCE(c.common_tags, '{}'::jsonb) as common_interests,
                NOW() as update_time
            FROM user_pairs p
            LEFT JOIN common_tags c ON p.user_id_a = c.user_id_a AND p.user_id_b = c.user_id_b
            WHERE CASE 
                    WHEN c.common_tags IS NULL THEN 0
                    ELSE (
                        SELECT 
                            SUM(((c.common_tags->tag_name->>'weight_a')::float * (c.common_tags->tag_name->>'weight_b')::float)) /
                            SQRT(SUM((c.common_tags->tag_name->>'weight_a')::float * (c.common_tags->tag_name->>'weight_a')::float) * 
                                 SUM((c.common_tags->tag_name->>'weight_b')::float * (c.common_tags->tag_name->>'weight_b')::float))
                        FROM jsonb_object_keys(c.common_tags) as tag_name
                    )
                  END > 0
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("用户相似度矩阵更新完成")
    except Exception as e:
        logger.error(f"更新用户相似度矩阵失败: {e}")

def update_post_similarity_matrix():
    """
    更新内容相似度矩阵
    """
    try:
        logger.info("开始更新内容相似度矩阵")
        
        # 连接PostgreSQL
        conn = connect_postgres()
        cursor = conn.cursor()
        
        # 更新内容相似度矩阵
        cursor.execute("""
            TRUNCATE TABLE mart.post_similarity_matrix;
            
            INSERT INTO mart.post_similarity_matrix (
                post_id_a, post_id_b, similarity_score, common_tags, update_time
            )
            WITH post_tags AS (
                SELECT 
                    post_id,
                    jsonb_object_agg(tag_name, tag_weight) as tag_weights
                FROM dw.fact_post_tags
                GROUP BY post_id
            ),
            post_pairs AS (
                SELECT 
                    a.post_id as post_id_a,
                    b.post_id as post_id_b
                FROM post_tags a
                CROSS JOIN post_tags b
                WHERE a.post_id < b.post_id
            ),
            common_tags AS (
                SELECT 
                    p.post_id_a,
                    p.post_id_b,
                    jsonb_object_agg(
                        t.tag_name, 
                        jsonb_build_object(
                            'weight_a', t.weight_a,
                            'weight_b', t.weight_b
                        )
                    ) as common_tags
                FROM post_pairs p
                JOIN (
                    SELECT 
                        a.post_id as post_id_a,
                        b.post_id as post_id_b,
                        a.tag_name,
                        a.tag_weight as weight_a,
                        b.tag_weight as weight_b
                    FROM dw.fact_post_tags a
                    JOIN dw.fact_post_tags b ON a.tag_name = b.tag_name
                    WHERE a.post_id < b.post_id
                ) t ON p.post_id_a = t.post_id_a AND p.post_id_b = t.post_id_b
                GROUP BY p.post_id_a, p.post_id_b
            )
            SELECT 
                p.post_id_a,
                p.post_id_b,
                CASE 
                    WHEN c.common_tags IS NULL THEN 0
                    ELSE (
                        SELECT 
                            SUM(((c.common_tags->tag_name->>'weight_a')::float * (c.common_tags->tag_name->>'weight_b')::float)) /
                            SQRT(SUM((c.common_tags->tag_name->>'weight_a')::float * (c.common_tags->tag_name->>'weight_a')::float) * 
                                 SUM((c.common_tags->tag_name->>'weight_b')::float * (c.common_tags->tag_name->>'weight_b')::float))
                        FROM jsonb_object_keys(c.common_tags) as tag_name
                    )
                END as similarity_score,
                COALESCE(c.common_tags, '{}'::jsonb) as common_tags,
                NOW() as update_time
            FROM post_pairs p
            LEFT JOIN common_tags c ON p.post_id_a = c.post_id_a AND p.post_id_b = c.post_id_b
            WHERE CASE 
                    WHEN c.common_tags IS NULL THEN 0
                    ELSE (
                        SELECT 
                            SUM(((c.common_tags->tag_name->>'weight_a')::float * (c.common_tags->tag_name->>'weight_b')::float)) /
                            SQRT(SUM((c.common_tags->tag_name->>'weight_a')::float * (c.common_tags->tag_name->>'weight_a')::float) * 
                                 SUM((c.common_tags->tag_name->>'weight_b')::float * (c.common_tags->tag_name->>'weight_b')::float))
                        FROM jsonb_object_keys(c.common_tags) as tag_name
                    )
                  END > 0
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("内容相似度矩阵更新完成")
    except Exception as e:
        logger.error(f"更新内容相似度矩阵失败: {e}")

def generate_user_recommendation_pool():
    """
    生成用户推荐池
    """
    try:
        logger.info("开始生成用户推荐池")
        
        # 连接PostgreSQL
        conn = connect_postgres()
        cursor = conn.cursor()
        
        # 清空现有的推荐池
        cursor.execute("TRUNCATE TABLE mart.user_recommendation_pool")
        
        # 基于协同过滤生成推荐池
        cursor.execute("""
            INSERT INTO mart.user_recommendation_pool (
                user_id, post_id, score, reason, is_consumed, create_time
            )
            WITH user_liked_posts AS (
                SELECT 
                    l.user_id,
                    l.post_id
                FROM raw.likes l
                UNION
                SELECT 
                    f.user_id,
                    f.post_id
                FROM raw.favorites f
            ),
            similar_users AS (
                SELECT 
                    usm.user_id_a as user_id,
                    usm.user_id_b as similar_user_id,
                    usm.similarity_score
                FROM mart.user_similarity_matrix usm
                WHERE usm.similarity_score > 0.5
                UNION ALL
                SELECT 
                    usm.user_id_b as user_id,
                    usm.user_id_a as similar_user_id,
                    usm.similarity_score
                FROM mart.user_similarity_matrix usm
                WHERE usm.similarity_score > 0.5
            ),
            cf_recommendations AS (
                SELECT 
                    su.user_id,
                    ulp.post_id,
                    su.similarity_score as score,
                    'collaborative_filtering' as reason
                FROM similar_users su
                JOIN user_liked_posts ulp ON su.similar_user_id = ulp.user_id
                WHERE NOT EXISTS (
                    SELECT 1 
                    FROM user_liked_posts 
                    WHERE user_id = su.user_id AND post_id = ulp.post_id
                )
                AND NOT EXISTS (
                    SELECT 1 
                    FROM raw.events e 
                    WHERE e.user_id = su.user_id AND e.post_id = ulp.post_id AND e.event_type = 'view'
                )
            ),
            content_based_recommendations AS (
                SELECT 
                    ulp.user_id,
                    psm.post_id_b as post_id,
                    psm.similarity_score as score,
                    'content_based' as reason
                FROM user_liked_posts ulp
                JOIN mart.post_similarity_matrix psm ON ulp.post_id = psm.post_id_a
                WHERE psm.similarity_score > 0.5
                AND NOT EXISTS (
                    SELECT 1 
                    FROM user_liked_posts 
                    WHERE user_id = ulp.user_id AND post_id = psm.post_id_b
                )
                AND NOT EXISTS (
                    SELECT 1 
                    FROM raw.events e 
                    WHERE e.user_id = ulp.user_id AND e.post_id = psm.post_id_b AND e.event_type = 'view'
                )
                UNION ALL
                SELECT 
                    ulp.user_id,
                    psm.post_id_a as post_id,
                    psm.similarity_score as score,
                    'content_based' as reason
                FROM user_liked_posts ulp
                JOIN mart.post_similarity_matrix psm ON ulp.post_id = psm.post_id_b
                WHERE psm.similarity_score > 0.5
                AND NOT EXISTS (
                    SELECT 1 
                    FROM user_liked_posts 
                    WHERE user_id = ulp.user_id AND post_id = psm.post_id_a
                )
                AND NOT EXISTS (
                    SELECT 1 
                    FROM raw.events e 
                    WHERE e.user_id = ulp.user_id AND e.post_id = psm.post_id_a AND e.event_type = 'view'
                )
            ),
            tag_based_recommendations AS (
                SELECT 
                    fut.user_id,
                    fpt.post_id,
                    fut.tag_weight * fpt.tag_weight as score,
                    'tag_based' as reason
                FROM dw.fact_user_tags fut
                JOIN dw.fact_post_tags fpt ON fut.tag_name = fpt.tag_name
                WHERE fut.tag_weight > 0.5
                AND NOT EXISTS (
                    SELECT 1 
                    FROM user_liked_posts 
                    WHERE user_id = fut.user_id AND post_id = fpt.post_id
                )
                AND NOT EXISTS (
                    SELECT 1 
                    FROM raw.events e 
                    WHERE e.user_id = fut.user_id AND e.post_id = fpt.post_id AND e.event_type = 'view'
                )
            ),
            popularity_recommendations AS (
                SELECT 
                    u.user_id,
                    p.post_id,
                    p.popularity_score / 100 as score,
                    'popularity' as reason
                FROM raw.users u
                CROSS JOIN dw.dim_posts p
                WHERE p.popularity_score > (
                    SELECT AVG(popularity_score) FROM dw.dim_posts
                )
                AND NOT EXISTS (
                    SELECT 1 
                    FROM user_liked_posts 
                    WHERE user_id = u.user_id AND post_id = p.post_id
                )
                AND NOT EXISTS (
                    SELECT 1 
                    FROM raw.events e 
                    WHERE e.user_id = u.user_id AND e.post_id = p.post_id AND e.event_type = 'view'
                )
            ),
            combined_recommendations AS (
                SELECT * FROM cf_recommendations
                UNION ALL
                SELECT * FROM content_based_recommendations
                UNION ALL
                SELECT * FROM tag_based_recommendations
                UNION ALL
                SELECT * FROM popularity_recommendations
            ),
            ranked_recommendations AS (
                SELECT 
                    user_id,
                    post_id,
                    score,
                    reason,
                    ROW_NUMBER() OVER (PARTITION BY user_id, post_id ORDER BY score DESC) as rn
                FROM combined_recommendations
            )
            SELECT 
                user_id,
                post_id,
                score,
                reason,
                FALSE as is_consumed,
                NOW() as create_time
            FROM ranked_recommendations
            WHERE rn = 1
        """)
        
        # 将推荐池写入Redis
        cursor.execute("""
            SELECT 
                user_id,
                jsonb_agg(
                    jsonb_build_object(
                        'post_id', post_id,
                        'score', score,
                        'reason', reason
                    )
                ) as recommendations
            FROM mart.user_recommendation_pool
            GROUP BY user_id
        """)
        
        # 获取推荐池数据
        recommendations = cursor.fetchall()
        
        # 连接Redis
        redis_conn = redis.Redis(
            host='redis',
            port=6379,
            password='redispassword',
            decode_responses=True
        )
        
        # 将推荐池写入Redis
        for user_id, recs in recommendations:
            redis_key = f"user:{user_id}:recommendations"
            redis_conn.set(redis_key, json.dumps(recs))
            redis_conn.expire(redis_key, 60 * 60 * 24)  # 设置24小时过期
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("用户推荐池生成完成")
    except Exception as e:
        logger.error(f"生成用户推荐池失败: {e}")

def run_etl_pipeline():
    """
    运行完整的ETL流程
    """
    try:
        logger.info("开始运行ETL流程")
        
        # 1. 同步原始数据
        sync_all_tables(incremental=True)
        
        # 2. 处理标签数据
        process_user_tags()
        process_post_tags()
        
        # 3. 处理用户行为漏斗
        process_user_funnels()
        
        # 4. 更新维度表
        update_dim_users()
        update_dim_posts()
        
        # 5. 更新事实表
        update_fact_events()
        
        # 6. 更新分析表
        update_user_activity_analysis()
        update_content_performance_analysis()
        update_recommendation_performance_analysis()
        
        # 7. 更新相似度矩阵
        update_user_similarity_matrix()
        update_post_similarity_matrix()
        
        # 8. 生成推荐池
        generate_user_recommendation_pool()
        
        logger.info("ETL流程运行完成")
    except Exception as e:
        logger.error(f"ETL流程运行失败: {e}")

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='MySQL到PostgreSQL数据同步脚本')
    parser.add_argument('--full', action='store_true', help='执行全量同步')
    parser.add_argument('--sync-only', action='store_true', help='只同步原始数据，不执行ETL流程')
    parser.add_argument('--etl-only', action='store_true', help='只执行ETL流程，不同步原始数据')
    args = parser.parse_args()
    
    try:
        if args.etl_only:
            # 只执行ETL流程
            run_etl_pipeline()
        elif args.sync_only:
            # 只同步原始数据
            sync_all_tables(incremental=not args.full)
        else:
            # 执行完整流程
            sync_all_tables(incremental=not args.full)
            run_etl_pipeline()
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()