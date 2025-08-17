-- 0) 规范：时区按业务口径（新加坡）
--    如你们全链路用 UTC，这里仅在“自然日去重”处做 AT TIME ZONE。
-- ============================================================

-- 1) schema + 目标用户维表
CREATE SCHEMA IF NOT EXISTS dw;

CREATE TABLE IF NOT EXISTS dw.dim_users (
  -- 基础属性
  user_id            BIGINT PRIMARY KEY,
  username           TEXT,
  create_time        TIMESTAMPTZ,
  tags               JSONB,
  preferences        JSONB,

  -- 最近30天交互（以自然日去重/聚合）
  active_days_30d    INTEGER NOT NULL DEFAULT 0,
  d30_view_cnt       BIGINT  NOT NULL DEFAULT 0,
  d30_like_cnt       BIGINT  NOT NULL DEFAULT 0,
  d30_fav_cnt        BIGINT  NOT NULL DEFAULT 0,
  d30_interact_cnt   BIGINT  NOT NULL DEFAULT 0,    -- 30天内 view+like+favorite 总和
  d30_last_active_ts TIMESTAMPTZ,                   -- 30天内最后一次活跃时间

  -- 全量累计（可用于整体画像）
  total_post_cnt     BIGINT  NOT NULL DEFAULT 0,    -- 作为作者在 raw.posts 的发文量（全量）
  total_view_cnt     BIGINT  NOT NULL DEFAULT 0,
  total_like_cnt     BIGINT  NOT NULL DEFAULT 0,
  total_fav_cnt      BIGINT  NOT NULL DEFAULT 0,
  last_active_ts     TIMESTAMPTZ,                   -- 全量维度最后一次活跃时间

  -- 分群（示例：按30日活跃天数）
  user_segment       TEXT,

  -- 维护字段
  update_time        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2) 基础索引（提高聚合性能）
CREATE INDEX IF NOT EXISTS idx_events_user_time    ON raw.events (user_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_events_user_type    ON raw.events (user_id, event_type);
CREATE INDEX IF NOT EXISTS idx_posts_author        ON raw.posts  (author_id);

-- 3) 计算 + 写入（UPSERT）
WITH
params AS (
  SELECT
    NOW()                                   AS now_utc,
    NOW() - INTERVAL '30 days'              AS start_30d,
    'Asia/Singapore'::text                  AS biz_tz
),
-- 最近30天活跃天数（自然日去重）
ev_30d_days AS (
  SELECT
    e.user_id,
    COUNT(DISTINCT (e.timestamp AT TIME ZONE (SELECT biz_tz FROM params))::date) AS active_days_30d
  FROM raw.events e, params p
  WHERE e.timestamp >= p.start_30d
  GROUP BY e.user_id
),
-- 最近30天分事件类型计数
ev_30d_types AS (
  SELECT
    e.user_id,
    SUM(CASE WHEN e.event_type = 'view'     THEN 1 ELSE 0 END) AS d30_view_cnt,
    SUM(CASE WHEN e.event_type = 'like'     THEN 1 ELSE 0 END) AS d30_like_cnt,
    SUM(CASE WHEN e.event_type = 'favorite' THEN 1 ELSE 0 END) AS d30_fav_cnt,
    COUNT(*)                                                   AS d30_interact_cnt,
    MAX(e.timestamp)                                           AS d30_last_active_ts
  FROM raw.events e, params p
  WHERE e.timestamp >= p.start_30d
  GROUP BY e.user_id
),
-- 全量累计（用于整体画像/排序）
ev_all AS (
  SELECT
    e.user_id,
    SUM(CASE WHEN e.event_type = 'view'     THEN 1 ELSE 0 END) AS total_view_cnt,
    SUM(CASE WHEN e.event_type = 'like'     THEN 1 ELSE 0 END) AS total_like_cnt,
    SUM(CASE WHEN e.event_type = 'favorite' THEN 1 ELSE 0 END) AS total_fav_cnt,
    MAX(e.timestamp)                                           AS last_active_ts
  FROM raw.events e
  GROUP BY e.user_id
),
-- 发文量（作者 → 用户）
post_all AS (
  SELECT
    p.author_id AS user_id,
    COUNT(*)    AS total_post_cnt
  FROM raw.posts p
  GROUP BY p.author_id
),
-- 汇总一行/人
src AS (
  SELECT
    u.user_id,
    u.username,
    u.create_time,
    u.tags::jsonb        AS tags,
    u.preferences::jsonb AS preferences,

    COALESCE(d.active_days_30d, 0) AS active_days_30d,
    COALESCE(t.d30_view_cnt,     0) AS d30_view_cnt,
    COALESCE(t.d30_like_cnt,     0) AS d30_like_cnt,
    COALESCE(t.d30_fav_cnt,      0) AS d30_fav_cnt,
    COALESCE(t.d30_interact_cnt, 0) AS d30_interact_cnt,
    t.d30_last_active_ts,

    COALESCE(p.total_post_cnt,  0) AS total_post_cnt,
    COALESCE(a.total_view_cnt,  0) AS total_view_cnt,
    COALESCE(a.total_like_cnt,  0) AS total_like_cnt,
    COALESCE(a.total_fav_cnt,   0) AS total_fav_cnt,
    a.last_active_ts,

    CASE
      WHEN COALESCE(d.active_days_30d, 0) >= 20 THEN 'A_高活跃'
      WHEN COALESCE(d.active_days_30d, 0) >= 10 THEN 'B_中活跃'
      WHEN COALESCE(d.active_days_30d, 0) >=  1 THEN 'C_轻活跃'
      ELSE 'D_沉默'
    END AS user_segment,

    NOW() AS update_time
  FROM raw.users u
  LEFT JOIN ev_30d_days d ON d.user_id = u.user_id
  LEFT JOIN ev_30d_types t ON t.user_id = u.user_id
  LEFT JOIN ev_all      a ON a.user_id = u.user_id
  LEFT JOIN post_all    p ON p.user_id = u.user_id
)

INSERT INTO dw.dim_users (
  user_id, username, create_time, tags, preferences,
  active_days_30d,
  d30_view_cnt, d30_like_cnt, d30_fav_cnt, d30_interact_cnt, d30_last_active_ts,
  total_post_cnt, total_view_cnt, total_like_cnt, total_fav_cnt, last_active_ts,
  user_segment, update_time
)
SELECT
  user_id, username, create_time, tags, preferences,
  active_days_30d,
  d30_view_cnt, d30_like_cnt, d30_fav_cnt, d30_interact_cnt, d30_last_active_ts,
  total_post_cnt, total_view_cnt, total_like_cnt, total_fav_cnt, last_active_ts,
  user_segment, update_time
FROM src
ON CONFLICT (user_id) DO UPDATE SET
  username          = EXCLUDED.username,
  create_time       = EXCLUDED.create_time,
  tags              = EXCLUDED.tags,
  preferences       = EXCLUDED.preferences,
  active_days_30d   = EXCLUDED.active_days_30d,
  d30_view_cnt      = EXCLUDED.d30_view_cnt,
  d30_like_cnt      = EXCLUDED.d30_like_cnt,
  d30_fav_cnt       = EXCLUDED.d30_fav_cnt,
  d30_interact_cnt  = EXCLUDED.d30_interact_cnt,
  d30_last_active_ts= EXCLUDED.d30_last_active_ts,
  total_post_cnt    = EXCLUDED.total_post_cnt,
  total_view_cnt    = EXCLUDED.total_view_cnt,
  total_like_cnt    = EXCLUDED.total_like_cnt,
  total_fav_cnt     = EXCLUDED.total_fav_cnt,
  last_active_ts    = EXCLUDED.last_active_ts,
  user_segment      = EXCLUDED.user_segment,
  update_time       = NOW();

-- 4) 校验
-- SELECT * FROM dw.dim_users ORDER BY user_id;
