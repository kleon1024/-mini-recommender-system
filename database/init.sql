-- 迷你推荐系统数据库初始化脚本

-- 创建数据库
CREATE DATABASE IF NOT EXISTS recommender;
USE recommender;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(64) PRIMARY KEY,
    username VARCHAR(64) NOT NULL,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tags JSON,
    preferences JSON
);

-- 内容表
CREATE TABLE IF NOT EXISTS posts (
    post_id VARCHAR(64) PRIMARY KEY,
    title VARCHAR(128) NOT NULL,
    content TEXT NOT NULL,
    author_id VARCHAR(64) NOT NULL,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tags JSON,
    view_count INT DEFAULT 0,
    like_count INT DEFAULT 0,
    favorite_count INT DEFAULT 0,
    FOREIGN KEY (author_id) REFERENCES users(user_id)
);

-- 行为表
CREATE TABLE IF NOT EXISTS events (
    event_id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    post_id VARCHAR(64) NOT NULL,
    event_type VARCHAR(32) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(64),
    device_info JSON,
    extra JSON,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (post_id) REFERENCES posts(post_id)
);

-- 特征表
CREATE TABLE IF NOT EXISTS features (
    feature_id VARCHAR(64) PRIMARY KEY,
    entity_type VARCHAR(32) NOT NULL,
    entity_id VARCHAR(64) NOT NULL,
    feature_type VARCHAR(32) NOT NULL,
    feature_value JSON NOT NULL,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_posts_author ON posts(author_id);
CREATE INDEX idx_events_user ON events(user_id);
CREATE INDEX idx_events_post ON events(post_id);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_features_entity ON features(entity_type, entity_id);

-- 创建示例用户数据
INSERT INTO users (user_id, username, tags, preferences)
VALUES 
('u1001', 'user1', '{"interests": ["科技", "编程", "AI"]}', '{"categories": ["科技", "编程"]}'),
('u1002', 'user2', '{"interests": ["旅游", "美食", "摄影"]}', '{"categories": ["旅游", "美食"]}'),
('u1003', 'user3', '{"interests": ["体育", "健身", "篮球"]}', '{"categories": ["体育", "健身"]}'),
('u1004', 'user4', '{"interests": ["音乐", "电影", "艺术"]}', '{"categories": ["音乐", "电影"]}'),
('u1005', 'user5', '{"interests": ["科技", "游戏", "动漫"]}', '{"categories": ["科技", "游戏"]}');

-- 创建示例内容数据
INSERT INTO posts (post_id, title, content, author_id, tags, view_count, like_count, favorite_count)
VALUES 
('p1001', '人工智能入门指南', '本文介绍了人工智能的基础知识和应用场景...', 'u1001', '{"tags": ["AI", "技术", "入门"]}', 120, 45, 10),
('p1002', '东京旅游攻略', '东京是一个充满活力的城市，本文分享东京旅游的经验和建议...', 'u1002', '{"tags": ["旅游", "东京", "攻略"]}', 300, 120, 50),
('p1003', '家庭健身计划', '不需要去健身房，在家也能进行高效的健身训练...', 'u1003', '{"tags": ["健身", "运动", "健康"]}', 200, 80, 30),
('p1004', '2023年最值得期待的电影', '2023年有许多优秀的电影即将上映，本文为您推荐...', 'u1004', '{"tags": ["电影", "娱乐", "推荐"]}', 250, 100, 40),
('p1005', '最新游戏评测', '本文评测了最近发布的几款热门游戏...', 'u1005', '{"tags": ["游戏", "评测", "娱乐"]}', 180, 70, 20),
('p1006', 'Python编程技巧', '分享一些Python编程中的实用技巧和最佳实践...', 'u1001', '{"tags": ["Python", "编程", "技巧"]}', 220, 90, 35),
('p1007', '美食探店记', '探访城市里的隐藏美食，分享独特的味蕾体验...', 'u1002', '{"tags": ["美食", "探店", "推荐"]}', 150, 60, 15),
('p1008', '篮球训练方法', '提高篮球技术的专业训练方法和技巧分享...', 'u1003', '{"tags": ["篮球", "训练", "技巧"]}', 160, 65, 18),
('p1009', '古典音乐鉴赏', '介绍古典音乐的历史、流派和代表作品...', 'u1004', '{"tags": ["音乐", "古典", "艺术"]}', 130, 50, 12),
('p1010', '人工智能在游戏中的应用', '探讨AI技术如何改变游戏产业和游戏体验...', 'u1005', '{"tags": ["AI", "游戏", "技术"]}', 210, 85, 32);

-- 创建示例行为数据
INSERT INTO events (event_id, user_id, post_id, event_type, source, device_info)
VALUES 
('e1001', 'u1001', 'p1005', 'view', 'home', '{"type": "mobile", "os": "iOS"}'),
('e1002', 'u1001', 'p1005', 'like', 'detail', '{"type": "mobile", "os": "iOS"}'),
('e1003', 'u1002', 'p1001', 'view', 'home', '{"type": "desktop", "os": "Windows"}'),
('e1004', 'u1002', 'p1006', 'view', 'home', '{"type": "desktop", "os": "Windows"}'),
('e1005', 'u1002', 'p1006', 'favorite', 'detail', '{"type": "desktop", "os": "Windows"}'),
('e1006', 'u1003', 'p1002', 'view', 'search', '{"type": "mobile", "os": "Android"}'),
('e1007', 'u1003', 'p1007', 'view', 'home', '{"type": "mobile", "os": "Android"}'),
('e1008', 'u1003', 'p1007', 'like', 'detail', '{"type": "mobile", "os": "Android"}'),
('e1009', 'u1004', 'p1003', 'view', 'home', '{"type": "tablet", "os": "iPadOS"}'),
('e1010', 'u1004', 'p1008', 'view', 'recommendation', '{"type": "tablet", "os": "iPadOS"}'),
('e1011', 'u1004', 'p1008', 'favorite', 'detail', '{"type": "tablet", "os": "iPadOS"}'),
('e1012', 'u1005', 'p1004', 'view', 'home', '{"type": "desktop", "os": "macOS"}'),
('e1013', 'u1005', 'p1009', 'view', 'search', '{"type": "desktop", "os": "macOS"}'),
('e1014', 'u1005', 'p1009', 'like', 'detail', '{"type": "desktop", "os": "macOS"}'),
('e1015', 'u1001', 'p1010', 'view', 'recommendation', '{"type": "mobile", "os": "iOS"}');