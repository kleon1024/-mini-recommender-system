-- 1. 建 schema
CREATE SCHEMA IF NOT EXISTS dw;

-- 2. 建漏斗事实表
DROP TABLE IF EXISTS dw.fact_user_funnels;
CREATE TABLE dw.fact_user_funnels (
  user_id                  BIGINT NOT NULL,
  post_id                  BIGINT NOT NULL,
  view_time                TIMESTAMPTZ NOT NULL,
  like_time                TIMESTAMPTZ,
  favorite_time            TIMESTAMPTZ,
  view_to_like_seconds     DOUBLE PRECISION,
  view_to_favorite_seconds DOUBLE PRECISION,
  funnel_complete          BOOLEAN NOT NULL DEFAULT FALSE,
  funnel_date              DATE NOT NULL,
  update_time              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT fact_user_funnels_pk PRIMARY KEY (user_id, post_id, view_time)
);

-- 常用索引
CREATE INDEX idx_funnel_date ON dw.fact_user_funnels (funnel_date);
CREATE INDEX idx_funnel_post ON dw.fact_user_funnels (post_id);
CREATE INDEX idx_funnel_user ON dw.fact_user_funnels (user_id);

-- 3. 全量写入
WITH
-- 每个 (user, post) 的首个 view
first_view AS (
  SELECT DISTINCT ON (user_id, post_id)
    user_id,
    post_id,
    timestamp AS view_time
  FROM raw.events
  WHERE event_type = 'view'
  ORDER BY user_id, post_id, timestamp
),

-- 首个 like（必须在 view 之后）
first_like AS (
  SELECT DISTINCT ON (e.user_id, e.post_id)
    e.user_id, e.post_id, e.timestamp AS like_time
  FROM raw.events e
  JOIN first_view v
    ON v.user_id = e.user_id AND v.post_id = e.post_id
  WHERE e.event_type = 'like'
    AND e.timestamp >= v.view_time
  ORDER BY e.user_id, e.post_id, e.timestamp
),

-- 首个 favorite（必须在 view 之后）
first_fav AS (
  SELECT DISTINCT ON (e.user_id, e.post_id)
    e.user_id, e.post_id, e.timestamp AS favorite_time
  FROM raw.events e
  JOIN first_view v
    ON v.user_id = e.user_id AND v.post_id = e.post_id
  WHERE e.event_type = 'favorite'
    AND e.timestamp >= v.view_time
  ORDER BY e.user_id, e.post_id, e.timestamp
)

INSERT INTO dw.fact_user_funnels (
  user_id, post_id, view_time, like_time, favorite_time,
  view_to_like_seconds, view_to_favorite_seconds,
  funnel_complete, funnel_date, update_time
)
SELECT
  v.user_id,
  v.post_id,
  v.view_time,
  l.like_time,
  f.favorite_time,
  CASE WHEN l.like_time IS NOT NULL
       THEN EXTRACT(EPOCH FROM (l.like_time - v.view_time)) END AS view_to_like_seconds,
  CASE WHEN f.favorite_time IS NOT NULL
       THEN EXTRACT(EPOCH FROM (f.favorite_time - v.view_time)) END AS view_to_favorite_seconds,
  (l.like_time IS NOT NULL AND f.favorite_time IS NOT NULL) AS funnel_complete,
  v.view_time::date AS funnel_date,
  NOW() AS update_time
FROM first_view v
LEFT JOIN first_like l ON l.user_id = v.user_id AND l.post_id = v.post_id
LEFT JOIN first_fav  f ON f.user_id = v.user_id AND f.post_id = v.post_id;
