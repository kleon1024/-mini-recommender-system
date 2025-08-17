-- ===========================
-- 1) schema + 目标内容维表
-- ===========================
CREATE SCHEMA IF NOT EXISTS dw;

CREATE TABLE IF NOT EXISTS dw.dim_posts (
  -- 基础属性
  post_id             BIGINT PRIMARY KEY,
  title               TEXT,
  author_id           BIGINT,
  author_username     TEXT,
  create_time         TIMESTAMPTZ,
  tags                JSONB,

  -- 最近30天交互（自然日/类型聚合）
  d30_active_days     INTEGER NOT NULL DEFAULT 0,   -- 近30天有过任意事件的天数
  d30_unique_users    BIGINT  NOT NULL DEFAULT 0,   -- 近30天独立交互用户数
  d30_view_cnt        BIGINT  NOT NULL DEFAULT 0,
  d30_like_cnt        BIGINT  NOT NULL DEFAULT 0,
  d30_fav_cnt         BIGINT  NOT NULL DEFAULT 0,
  d30_interact_cnt    BIGINT  NOT NULL DEFAULT 0,   -- view+like+favorite 总和
  d30_last_event_ts   TIMESTAMPTZ,

  -- 全量累计（全链路）
  total_view_cnt      BIGINT  NOT NULL DEFAULT 0,
  total_like_cnt      BIGINT  NOT NULL DEFAULT 0,
  total_fav_cnt       BIGINT  NOT NULL DEFAULT 0,
  total_interact_cnt  BIGINT  NOT NULL DEFAULT 0,
  last_event_ts       TIMESTAMPTZ,

  -- 分层（示例：按近30天曝光/互动强度）
  content_segment     TEXT,

  -- 维护字段
  update_time         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ===========================
-- 2) 基础索引（提升聚合性能）
-- ===========================
CREATE INDEX IF NOT EXISTS idx_events_post_time
  ON raw.events (post_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_events_post_type
  ON raw.events (post_id, event_type);
CREATE INDEX IF NOT EXISTS idx_posts_author_time
  ON raw.posts (author_id, create_time);
CREATE INDEX IF NOT EXISTS idx_users_id
  ON raw.users (user_id);

-- ===========================
-- 3) 聚合 + UPSERT
-- ===========================
WITH
params AS (
  SELECT
    NOW() AS now_utc,
    NOW() - INTERVAL '30 days' AS start_30d,
    'Asia/Singapore'::text AS biz_tz
),

-- 近30天活跃天数（按自然日）
p30_days AS (
  SELECT
    e.post_id,
    COUNT(DISTINCT (e.timestamp AT TIME ZONE (SELECT biz_tz FROM params))::date) AS d30_active_days
  FROM raw.events e, params p
  WHERE e.timestamp >= p.start_30d
  GROUP BY e.post_id
),

-- 近30天独立用户数
p30_users AS (
  SELECT
    e.post_id,
    COUNT(DISTINCT e.user_id) AS d30_unique_users
  FROM raw.events e, params p
  WHERE e.timestamp >= p.start_30d
  GROUP BY e.post_id
),

-- 近30天按类型计数 + 最近一次事件
p30_types AS (
  SELECT
    e.post_id,
    SUM(CASE WHEN e.event_type = 'view'     THEN 1 ELSE 0 END) AS d30_view_cnt,
    SUM(CASE WHEN e.event_type = 'like'     THEN 1 ELSE 0 END) AS d30_like_cnt,
    SUM(CASE WHEN e.event_type = 'favorite' THEN 1 ELSE 0 END) AS d30_fav_cnt,
    COUNT(*)                                                   AS d30_interact_cnt,
    MAX(e.timestamp)                                          AS d30_last_event_ts
  FROM raw.events e, params p
  WHERE e.timestamp >= p.start_30d
  GROUP BY e.post_id
),

-- 全量累计（事件口径为准）
p_all AS (
  SELECT
    e.post_id,
    SUM(CASE WHEN e.event_type = 'view'     THEN 1 ELSE 0 END) AS total_view_cnt,
    SUM(CASE WHEN e.event_type = 'like'     THEN 1 ELSE 0 END) AS total_like_cnt,
    SUM(CASE WHEN e.event_type = 'favorite' THEN 1 ELSE 0 END) AS total_fav_cnt,
    COUNT(*)                                                   AS total_interact_cnt,
    MAX(e.timestamp)                                          AS last_event_ts
  FROM raw.events e
  GROUP BY e.post_id
),

-- 作者用户名（可选：也能直接从 raw.users 关联）
author_name AS (
  SELECT u.user_id, u.username
  FROM raw.users u
),

-- 汇总一行/内容
src AS (
  SELECT
    p.post_id,
    p.title,
    p.author_id,
    an.username                           AS author_username,
    p.create_time,
    p.tags::jsonb                         AS tags,

    COALESCE(d.d30_active_days,   0)      AS d30_active_days,
    COALESCE(uus.d30_unique_users,0)      AS d30_unique_users,
    COALESCE(t.d30_view_cnt,      0)      AS d30_view_cnt,
    COALESCE(t.d30_like_cnt,      0)      AS d30_like_cnt,
    COALESCE(t.d30_fav_cnt,       0)      AS d30_fav_cnt,
    COALESCE(t.d30_interact_cnt,  0)      AS d30_interact_cnt,
    t.d30_last_event_ts,

    COALESCE(a.total_view_cnt,    0)      AS total_view_cnt,
    COALESCE(a.total_like_cnt,    0)      AS total_like_cnt,
    COALESCE(a.total_fav_cnt,     0)      AS total_fav_cnt,
    COALESCE(a.total_interact_cnt,0)      AS total_interact_cnt,
    a.last_event_ts,

    CASE
      WHEN COALESCE(t.d30_view_cnt, 0) >= 1000 OR COALESCE(t.d30_like_cnt, 0) >= 100 THEN 'A_爆款苗头'
      WHEN COALESCE(t.d30_view_cnt, 0) >= 300  OR COALESCE(t.d30_like_cnt, 0) >= 30  THEN 'B_中等热度'
      WHEN COALESCE(t.d30_view_cnt, 0) >= 50   OR COALESCE(t.d30_like_cnt, 0) >= 5   THEN 'C_轻量曝光'
      ELSE 'D_低曝光'
    END AS content_segment,

    NOW() AS update_time
  FROM raw.posts p
  LEFT JOIN author_name an ON an.user_id = p.author_id
  LEFT JOIN p30_days  d    ON d.post_id  = p.post_id
  LEFT JOIN p30_users uus  ON uus.post_id= p.post_id
  LEFT JOIN p30_types t    ON t.post_id  = p.post_id
  LEFT JOIN p_all     a    ON a.post_id  = p.post_id
)

INSERT INTO dw.dim_posts (
  post_id, title, author_id, author_username, create_time, tags,
  d30_active_days, d30_unique_users, d30_view_cnt, d30_like_cnt, d30_fav_cnt, d30_interact_cnt, d30_last_event_ts,
  total_view_cnt, total_like_cnt, total_fav_cnt, total_interact_cnt, last_event_ts,
  content_segment, update_time
)
SELECT
  post_id, title, author_id, author_username, create_time, tags,
  d30_active_days, d30_unique_users, d30_view_cnt, d30_like_cnt, d30_fav_cnt, d30_interact_cnt, d30_last_event_ts,
  total_view_cnt, total_like_cnt, total_fav_cnt, total_interact_cnt, last_event_ts,
  content_segment, update_time
FROM src
ON CONFLICT (post_id) DO UPDATE SET
  title              = EXCLUDED.title,
  author_id          = EXCLUDED.author_id,
  author_username    = EXCLUDED.author_username,
  create_time        = EXCLUDED.create_time,
  tags               = EXCLUDED.tags,
  d30_active_days    = EXCLUDED.d30_active_days,
  d30_unique_users   = EXCLUDED.d30_unique_users,
  d30_view_cnt       = EXCLUDED.d30_view_cnt,
  d30_like_cnt       = EXCLUDED.d30_like_cnt,
  d30_fav_cnt        = EXCLUDED.d30_fav_cnt,
  d30_interact_cnt   = EXCLUDED.d30_interact_cnt,
  d30_last_event_ts  = EXCLUDED.d30_last_event_ts,
  total_view_cnt     = EXCLUDED.total_view_cnt,
  total_like_cnt     = EXCLUDED.total_like_cnt,
  total_fav_cnt      = EXCLUDED.total_fav_cnt,
  total_interact_cnt = EXCLUDED.total_interact_cnt,
  last_event_ts      = EXCLUDED.last_event_ts,
  content_segment    = EXCLUDED.content_segment,
  update_time        = NOW();

-- 验证
-- SELECT * FROM dw.dim_posts ORDER BY post_id;
