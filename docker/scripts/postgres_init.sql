-- 数据仓库初始化脚本

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- 用于文本搜索
CREATE EXTENSION IF NOT EXISTS "vector"; -- 用于向量搜索

-- 创建模式
CREATE SCHEMA IF NOT EXISTS raw; -- 原始数据
CREATE SCHEMA IF NOT EXISTS stage; -- 中间处理数据
CREATE SCHEMA IF NOT EXISTS dw; -- 数据仓库
CREATE SCHEMA IF NOT EXISTS mart; -- 数据集市

-- 原始数据表 - 用户表
CREATE TABLE IF NOT EXISTS raw.users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(64) NOT NULL,
    create_time TIMESTAMP,
    tags JSONB,
    preferences JSONB,
    import_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 原始数据表 - 内容表
CREATE TABLE IF NOT EXISTS raw.posts (
    post_id BIGINT PRIMARY KEY,
    title VARCHAR(128) NOT NULL,
    content TEXT NOT NULL,
    author_id BIGINT NOT NULL,
    create_time TIMESTAMP,
    tags JSONB,
    view_count INT DEFAULT 0,
    like_count INT DEFAULT 0,
    favorite_count INT DEFAULT 0,
    import_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 原始数据表 - 行为表
CREATE TABLE IF NOT EXISTS raw.events (
    event_id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    post_id BIGINT NOT NULL,
    event_type VARCHAR(32) NOT NULL,
    timestamp TIMESTAMP,
    source VARCHAR(64),
    device_info JSONB,
    extra JSONB,
    import_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 原始数据表 - 特征表
CREATE TABLE IF NOT EXISTS raw.features (
    feature_id BIGINT PRIMARY KEY,
    entity_type VARCHAR(32) NOT NULL,
    entity_id BIGINT NOT NULL,
    feature_type VARCHAR(32) NOT NULL,
    feature_value JSONB NOT NULL,
    update_time TIMESTAMP,
    import_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 原始数据表 - 点赞表
CREATE TABLE IF NOT EXISTS raw.likes (
    like_id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    post_id BIGINT NOT NULL,
    create_time TIMESTAMP,
    import_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 原始数据表 - 收藏表
CREATE TABLE IF NOT EXISTS raw.favorites (
    favorite_id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    post_id BIGINT NOT NULL,
    create_time TIMESTAMP,
    notes TEXT,
    import_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 数据仓库表 - 用户维度表
CREATE TABLE IF NOT EXISTS dw.dim_users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(64) NOT NULL,
    create_time TIMESTAMP,
    tags JSONB,
    preferences JSONB,
    user_vector VECTOR(384), -- 用户向量表示
    active_days_30d INT DEFAULT 0, -- 30天活跃天数
    active_days_7d INT DEFAULT 0, -- 7天活跃天数
    post_count INT DEFAULT 0, -- 发布内容数
    like_count INT DEFAULT 0, -- 点赞数
    favorite_count INT DEFAULT 0, -- 收藏数
    view_count INT DEFAULT 0, -- 浏览数
    last_active_time TIMESTAMP, -- 最后活跃时间
    user_segment VARCHAR(32), -- 用户分群
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 数据仓库表 - 内容维度表
CREATE TABLE IF NOT EXISTS dw.dim_posts (
    post_id BIGINT PRIMARY KEY,
    title VARCHAR(128) NOT NULL,
    content TEXT NOT NULL,
    author_id BIGINT NOT NULL,
    create_time TIMESTAMP,
    tags JSONB,
    content_vector VECTOR(384), -- 内容向量表示
    view_count INT DEFAULT 0,
    like_count INT DEFAULT 0,
    favorite_count INT DEFAULT 0,
    ctr FLOAT DEFAULT 0, -- 点击率
    like_ratio FLOAT DEFAULT 0, -- 点赞率
    favorite_ratio FLOAT DEFAULT 0, -- 收藏率
    popularity_score FLOAT DEFAULT 0, -- 流行度分数
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 数据仓库表 - 事件事实表
CREATE TABLE IF NOT EXISTS dw.fact_events (
    event_id BIGINT,
    user_id BIGINT NOT NULL,
    post_id BIGINT NOT NULL,
    event_type VARCHAR(32) NOT NULL,
    event_time TIMESTAMP NOT NULL,
    source VARCHAR(64),
    device_type VARCHAR(32),
    os VARCHAR(32),
    event_date DATE GENERATED ALWAYS AS (event_time::DATE) STORED,
    event_hour INT GENERATED ALWAYS AS (EXTRACT(HOUR FROM event_time)) STORED,
    PRIMARY KEY (event_id, event_time)
) PARTITION BY RANGE (event_date);

-- 创建最近30天的分区
DO $$
BEGIN
    FOR i IN 0..30 LOOP
        EXECUTE format('CREATE TABLE IF NOT EXISTS dw.fact_events_%s PARTITION OF dw.fact_events FOR VALUES FROM (%L) TO (%L)',
                      to_char(CURRENT_DATE - i, 'YYYYMMDD'),
                      CURRENT_DATE - i,
                      CURRENT_DATE - i + 1);
    END LOOP;
END $$;

-- 数据仓库表 - 用户行为漏斗事实表
CREATE TABLE IF NOT EXISTS dw.fact_user_funnels (
    funnel_id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    post_id BIGINT NOT NULL,
    view_time TIMESTAMP,
    like_time TIMESTAMP,
    favorite_time TIMESTAMP,
    view_to_like_seconds INT, -- 浏览到点赞的时间（秒）
    view_to_favorite_seconds INT, -- 浏览到收藏的时间（秒）
    funnel_complete BOOLEAN, -- 是否完成完整漏斗
    funnel_date DATE,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 数据仓库表 - 用户标签事实表
CREATE TABLE IF NOT EXISTS dw.fact_user_tags (
    user_tag_id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    tag_name VARCHAR(64) NOT NULL,
    tag_weight FLOAT NOT NULL, -- 标签权重
    tag_source VARCHAR(32) NOT NULL, -- 标签来源：explicit（用户明确设置）, implicit（系统推断）
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, tag_name)
);

-- 数据仓库表 - 内容标签事实表
CREATE TABLE IF NOT EXISTS dw.fact_post_tags (
    post_tag_id SERIAL PRIMARY KEY,
    post_id BIGINT NOT NULL,
    tag_name VARCHAR(64) NOT NULL,
    tag_weight FLOAT NOT NULL, -- 标签权重
    tag_source VARCHAR(32) NOT NULL, -- 标签来源：explicit（作者设置）, implicit（系统推断）
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (post_id, tag_name)
);

-- 数据集市表 - 用户活跃度分析
CREATE TABLE IF NOT EXISTS mart.user_activity_analysis (
    analysis_id SERIAL PRIMARY KEY,
    analysis_date DATE NOT NULL,
    total_users INT NOT NULL,
    active_users_1d INT NOT NULL, -- 日活
    active_users_7d INT NOT NULL, -- 周活
    active_users_30d INT NOT NULL, -- 月活
    new_users INT NOT NULL, -- 新增用户
    returning_users INT NOT NULL, -- 回访用户
    churned_users INT NOT NULL, -- 流失用户
    average_events_per_user FLOAT NOT NULL, -- 人均事件数
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (analysis_date)
);

-- 数据集市表 - 内容表现分析
CREATE TABLE IF NOT EXISTS mart.content_performance_analysis (
    analysis_id SERIAL PRIMARY KEY,
    analysis_date DATE NOT NULL,
    total_posts INT NOT NULL,
    new_posts INT NOT NULL, -- 新增内容
    total_views INT NOT NULL, -- 总浏览量
    total_likes INT NOT NULL, -- 总点赞量
    total_favorites INT NOT NULL, -- 总收藏量
    average_ctr FLOAT NOT NULL, -- 平均点击率
    average_like_ratio FLOAT NOT NULL, -- 平均点赞率
    average_favorite_ratio FLOAT NOT NULL, -- 平均收藏率
    top_tags JSONB, -- 热门标签
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (analysis_date)
);

-- 数据集市表 - 推荐效果分析
CREATE TABLE IF NOT EXISTS mart.recommendation_performance_analysis (
    analysis_id SERIAL PRIMARY KEY,
    analysis_date DATE NOT NULL,
    total_recommendations INT NOT NULL, -- 总推荐次数
    clicked_recommendations INT NOT NULL, -- 被点击的推荐数
    recommendation_ctr FLOAT NOT NULL, -- 推荐点击率
    average_view_duration FLOAT, -- 平均浏览时长（秒）
    like_from_recommendation INT NOT NULL, -- 推荐导致的点赞数
    favorite_from_recommendation INT NOT NULL, -- 推荐导致的收藏数
    recommendation_sources JSONB, -- 各推荐来源的效果
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (analysis_date)
);

-- 数据集市表 - 用户相似度矩阵（协同过滤用）
CREATE TABLE IF NOT EXISTS mart.user_similarity_matrix (
    matrix_id SERIAL PRIMARY KEY,
    user_id_a BIGINT NOT NULL,
    user_id_b BIGINT NOT NULL,
    similarity_score FLOAT NOT NULL, -- 相似度分数
    common_interests JSONB, -- 共同兴趣
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id_a, user_id_b)
);

-- 数据集市表 - 内容相似度矩阵
CREATE TABLE IF NOT EXISTS mart.post_similarity_matrix (
    matrix_id SERIAL PRIMARY KEY,
    post_id_a BIGINT NOT NULL,
    post_id_b BIGINT NOT NULL,
    similarity_score FLOAT NOT NULL, -- 相似度分数
    common_tags JSONB, -- 共同标签
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (post_id_a, post_id_b)
);

-- 数据集市表 - 用户推荐池
CREATE TABLE IF NOT EXISTS mart.user_recommendation_pool (
    pool_id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    post_id BIGINT NOT NULL,
    score FLOAT NOT NULL, -- 推荐分数
    reason VARCHAR(64), -- 推荐原因
    is_consumed BOOLEAN DEFAULT FALSE, -- 是否已消费
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, post_id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_raw_users_create_time ON raw.users(create_time);
CREATE INDEX IF NOT EXISTS idx_raw_posts_author ON raw.posts(author_id);
CREATE INDEX IF NOT EXISTS idx_raw_posts_create_time ON raw.posts(create_time);
CREATE INDEX IF NOT EXISTS idx_raw_events_user ON raw.events(user_id);
CREATE INDEX IF NOT EXISTS idx_raw_events_post ON raw.events(post_id);
CREATE INDEX IF NOT EXISTS idx_raw_events_type ON raw.events(event_type);
CREATE INDEX IF NOT EXISTS idx_raw_events_timestamp ON raw.events(timestamp);
CREATE INDEX IF NOT EXISTS idx_raw_features_entity ON raw.features(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_raw_likes_user ON raw.likes(user_id);
CREATE INDEX IF NOT EXISTS idx_raw_likes_post ON raw.likes(post_id);
CREATE INDEX IF NOT EXISTS idx_raw_favorites_user ON raw.favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_raw_favorites_post ON raw.favorites(post_id);

CREATE INDEX IF NOT EXISTS idx_dim_users_create_time ON dw.dim_users(create_time);
CREATE INDEX IF NOT EXISTS idx_dim_users_last_active ON dw.dim_users(last_active_time);
CREATE INDEX IF NOT EXISTS idx_dim_users_segment ON dw.dim_users(user_segment);
CREATE INDEX IF NOT EXISTS idx_dim_posts_author ON dw.dim_posts(author_id);
CREATE INDEX IF NOT EXISTS idx_dim_posts_create_time ON dw.dim_posts(create_time);
CREATE INDEX IF NOT EXISTS idx_dim_posts_popularity ON dw.dim_posts(popularity_score);

CREATE INDEX IF NOT EXISTS idx_fact_events_user ON dw.fact_events(user_id);
CREATE INDEX IF NOT EXISTS idx_fact_events_post ON dw.fact_events(post_id);
CREATE INDEX IF NOT EXISTS idx_fact_events_type ON dw.fact_events(event_type);
CREATE INDEX IF NOT EXISTS idx_fact_events_date ON dw.fact_events(event_date);
CREATE INDEX IF NOT EXISTS idx_fact_events_hour ON dw.fact_events(event_hour);

CREATE INDEX IF NOT EXISTS idx_fact_user_funnels_user ON dw.fact_user_funnels(user_id);
CREATE INDEX IF NOT EXISTS idx_fact_user_funnels_post ON dw.fact_user_funnels(post_id);
CREATE INDEX IF NOT EXISTS idx_fact_user_funnels_date ON dw.fact_user_funnels(funnel_date);
CREATE INDEX IF NOT EXISTS idx_fact_user_funnels_complete ON dw.fact_user_funnels(funnel_complete);

CREATE INDEX IF NOT EXISTS idx_fact_user_tags_user ON dw.fact_user_tags(user_id);
CREATE INDEX IF NOT EXISTS idx_fact_user_tags_tag ON dw.fact_user_tags(tag_name);
CREATE INDEX IF NOT EXISTS idx_fact_user_tags_weight ON dw.fact_user_tags(tag_weight);

CREATE INDEX IF NOT EXISTS idx_fact_post_tags_post ON dw.fact_post_tags(post_id);
CREATE INDEX IF NOT EXISTS idx_fact_post_tags_tag ON dw.fact_post_tags(tag_name);
CREATE INDEX IF NOT EXISTS idx_fact_post_tags_weight ON dw.fact_post_tags(tag_weight);

CREATE INDEX IF NOT EXISTS idx_user_similarity_user_a ON mart.user_similarity_matrix(user_id_a);
CREATE INDEX IF NOT EXISTS idx_user_similarity_user_b ON mart.user_similarity_matrix(user_id_b);
CREATE INDEX IF NOT EXISTS idx_user_similarity_score ON mart.user_similarity_matrix(similarity_score);

CREATE INDEX IF NOT EXISTS idx_post_similarity_post_a ON mart.post_similarity_matrix(post_id_a);
CREATE INDEX IF NOT EXISTS idx_post_similarity_post_b ON mart.post_similarity_matrix(post_id_b);
CREATE INDEX IF NOT EXISTS idx_post_similarity_score ON mart.post_similarity_matrix(similarity_score);

CREATE INDEX IF NOT EXISTS idx_user_recommendation_user ON mart.user_recommendation_pool(user_id);
CREATE INDEX IF NOT EXISTS idx_user_recommendation_post ON mart.user_recommendation_pool(post_id);
CREATE INDEX IF NOT EXISTS idx_user_recommendation_score ON mart.user_recommendation_pool(score);
CREATE INDEX IF NOT EXISTS idx_user_recommendation_consumed ON mart.user_recommendation_pool(is_consumed);

-- 创建视图
-- 用户行为漏斗视图
CREATE OR REPLACE VIEW mart.vw_user_funnel_analysis AS
SELECT
    funnel_date,
    COUNT(*) AS total_funnels,
    COUNT(view_time) AS view_count,
    COUNT(like_time) AS like_count,
    COUNT(favorite_time) AS favorite_count,
    COUNT(CASE WHEN funnel_complete THEN 1 END) AS complete_funnels,
    ROUND(COUNT(like_time)::FLOAT / NULLIF(COUNT(view_time), 0) * 100, 2) AS view_to_like_rate,
    ROUND(COUNT(favorite_time)::FLOAT / NULLIF(COUNT(like_time), 0) * 100, 2) AS like_to_favorite_rate,
    ROUND(COUNT(favorite_time)::FLOAT / NULLIF(COUNT(view_time), 0) * 100, 2) AS view_to_favorite_rate,
    ROUND(AVG(view_to_like_seconds) FILTER (WHERE view_to_like_seconds IS NOT NULL), 2) AS avg_view_to_like_seconds,
    ROUND(AVG(view_to_favorite_seconds) FILTER (WHERE view_to_favorite_seconds IS NOT NULL), 2) AS avg_view_to_favorite_seconds
FROM dw.fact_user_funnels
GROUP BY funnel_date
ORDER BY funnel_date DESC;

-- 用户活跃度趋势视图
CREATE OR REPLACE VIEW mart.vw_user_activity_trend AS
SELECT
    analysis_date,
    active_users_1d,
    active_users_7d,
    active_users_30d,
    new_users,
    returning_users,
    churned_users,
    ROUND(active_users_1d::FLOAT / LAG(active_users_1d) OVER (ORDER BY analysis_date) * 100 - 100, 2) AS daily_active_growth,
    ROUND(new_users::FLOAT / active_users_1d * 100, 2) AS new_user_percentage,
    ROUND(churned_users::FLOAT / LAG(active_users_1d) OVER (ORDER BY analysis_date) * 100, 2) AS churn_rate
FROM mart.user_activity_analysis
ORDER BY analysis_date DESC;

-- 内容表现趋势视图
CREATE OR REPLACE VIEW mart.vw_content_performance_trend AS
SELECT
    analysis_date,
    new_posts,
    total_views,
    total_likes,
    total_favorites,
    average_ctr,
    average_like_ratio,
    average_favorite_ratio,
    ROUND(total_views::FLOAT / LAG(total_views) OVER (ORDER BY analysis_date) * 100 - 100, 2) AS views_growth,
    ROUND(total_likes::FLOAT / LAG(total_likes) OVER (ORDER BY analysis_date) * 100 - 100, 2) AS likes_growth,
    ROUND(total_favorites::FLOAT / LAG(total_favorites) OVER (ORDER BY analysis_date) * 100 - 100, 2) AS favorites_growth
FROM mart.content_performance_analysis
ORDER BY analysis_date DESC;

-- 推荐效果趋势视图
CREATE OR REPLACE VIEW mart.vw_recommendation_performance_trend AS
SELECT
    analysis_date,
    total_recommendations,
    clicked_recommendations,
    recommendation_ctr,
    average_view_duration,
    like_from_recommendation,
    favorite_from_recommendation,
    ROUND(clicked_recommendations::FLOAT / total_recommendations * 100, 2) AS click_rate,
    ROUND(like_from_recommendation::FLOAT / clicked_recommendations * 100, 2) AS like_rate,
    ROUND(favorite_from_recommendation::FLOAT / clicked_recommendations * 100, 2) AS favorite_rate,
    ROUND(recommendation_ctr::FLOAT / LAG(recommendation_ctr) OVER (ORDER BY analysis_date) * 100 - 100, 2) AS ctr_growth
FROM mart.recommendation_performance_analysis
ORDER BY analysis_date DESC;