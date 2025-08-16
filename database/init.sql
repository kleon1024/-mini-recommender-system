-- 迷你推荐系统数据库初始化脚本

-- 创建数据库并设置字符集
CREATE DATABASE IF NOT EXISTS recommender CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE recommender;

-- 设置连接字符集
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET collation_connection = utf8mb4_unicode_ci;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(64) NOT NULL,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tags JSON,
    preferences JSON
);

-- 内容表
CREATE TABLE IF NOT EXISTS posts (
    post_id BIGINT PRIMARY KEY,
    title VARCHAR(128) NOT NULL,
    content TEXT NOT NULL,
    author_id BIGINT NOT NULL,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tags JSON,
    view_count INT DEFAULT 0,
    like_count INT DEFAULT 0,
    favorite_count INT DEFAULT 0,
    FOREIGN KEY (author_id) REFERENCES users(user_id)
);

-- 行为表
CREATE TABLE IF NOT EXISTS events (
    event_id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    post_id BIGINT NOT NULL,
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
    feature_id BIGINT PRIMARY KEY,
    entity_type VARCHAR(32) NOT NULL,
    entity_id BIGINT NOT NULL,
    feature_type VARCHAR(32) NOT NULL,
    feature_value JSON NOT NULL,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 点赞表
CREATE TABLE IF NOT EXISTS likes (
    like_id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    post_id BIGINT NOT NULL,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (post_id) REFERENCES posts(post_id),
    UNIQUE KEY (user_id, post_id)
);

-- 收藏表
CREATE TABLE IF NOT EXISTS favorites (
    favorite_id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    post_id BIGINT NOT NULL,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (post_id) REFERENCES posts(post_id),
    UNIQUE KEY (user_id, post_id)
);

-- 创建索引
CREATE INDEX idx_posts_author ON posts(author_id);
CREATE INDEX idx_events_user ON events(user_id);
CREATE INDEX idx_events_post ON events(post_id);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_features_entity ON features(entity_type, entity_id);
CREATE INDEX idx_likes_user ON likes(user_id);
CREATE INDEX idx_likes_post ON likes(post_id);
CREATE INDEX idx_favorites_user ON favorites(user_id);
CREATE INDEX idx_favorites_post ON favorites(post_id);

-- 创建示例用户数据
INSERT INTO users (user_id, username, tags, preferences)
VALUES 
(1001, '张科技', '{"interests": ["科技", "编程", "AI"]}', '{"categories": ["科技", "编程"]}'),
(1002, '李旅行', '{"interests": ["旅游", "美食", "摄影"]}', '{"categories": ["旅游", "美食"]}'),
(1003, '王运动', '{"interests": ["体育", "健身", "篮球"]}', '{"categories": ["体育", "健身"]}'),
(1004, '赵艺术', '{"interests": ["音乐", "电影", "艺术"]}', '{"categories": ["音乐", "电影"]}'),
(1005, '刘游戏', '{"interests": ["科技", "游戏", "动漫"]}', '{"categories": ["科技", "游戏"]}'),
(1006, '陈医生', '{"interests": ["医疗", "健康", "科普"]}', '{"categories": ["医疗", "健康"]}'),
(1007, '杨厨师', '{"interests": ["烹饪", "美食", "营养"]}', '{"categories": ["烹饪", "美食"]}'),
(1008, '周设计', '{"interests": ["设计", "艺术", "创意"]}', '{"categories": ["设计", "艺术"]}'),
(1009, '吴教育', '{"interests": ["教育", "学习", "心理"]}', '{"categories": ["教育", "学习"]}'),
(1010, '郑金融', '{"interests": ["金融", "投资", "经济"]}', '{"categories": ["金融", "投资"]}'),
(1011, '孙摄影', '{"interests": ["摄影", "旅行", "艺术"]}', '{"categories": ["摄影", "旅行"]}'),
(1012, '马文学', '{"interests": ["文学", "阅读", "写作"]}', '{"categories": ["文学", "阅读"]}'),
(1013, '胡科学', '{"interests": ["科学", "物理", "天文"]}', '{"categories": ["科学", "物理"]}'),
(1014, '林环保', '{"interests": ["环保", "可持续", "自然"]}', '{"categories": ["环保", "自然"]}'),
(1015, '朱历史', '{"interests": ["历史", "文化", "考古"]}', '{"categories": ["历史", "文化"]}');

-- 创建示例内容数据
INSERT INTO posts (post_id, title, content, author_id, tags, view_count, like_count, favorite_count)
VALUES 
(2001, '人工智能入门指南', '本文介绍了人工智能的基础知识和应用场景，包括机器学习、深度学习和神经网络等核心概念。通过简单易懂的例子，帮助读者理解AI如何解决实际问题，以及未来可能的发展方向。', 1001, '{"tags": ["AI", "技术", "入门"]}', 120, 45, 10),
(2002, '东京旅游攻略', '东京是一个充满活力的城市，本文分享东京旅游的经验和建议，包括最佳旅游季节、必访景点、美食推荐、交通指南以及文化体验活动。特别介绍了如何像当地人一样体验这座城市的魅力。', 1002, '{"tags": ["旅游", "东京", "攻略"]}', 300, 120, 50),
(2003, '家庭健身计划', '不需要去健身房，在家也能进行高效的健身训练。本文提供了一套完整的居家锻炼计划，包括热身、力量训练、有氧运动和拉伸放松，适合不同健身水平的人群，帮助你在家也能保持健康的身体。', 1003, '{"tags": ["健身", "运动", "健康"]}', 200, 80, 30),
(2004, '2023年最值得期待的电影', '2023年有许多优秀的电影即将上映，本文为您推荐最值得期待的十部电影，涵盖科幻、动作、剧情、动画等多种类型，并分析了这些电影的看点、导演风格以及演员阵容。', 1004, '{"tags": ["电影", "娱乐", "推荐"]}', 250, 100, 40),
(2005, '最新游戏评测', '本文评测了最近发布的几款热门游戏，从画面、玩法、剧情、音效等多个维度进行分析，帮助玩家了解这些游戏的优缺点，以便做出更明智的购买决定。', 1005, '{"tags": ["游戏", "评测", "娱乐"]}', 180, 70, 20),
(2006, 'Python编程技巧', '分享一些Python编程中的实用技巧和最佳实践，包括代码优化、常用库的高效使用、调试技巧以及项目结构组织方法。这些技巧将帮助你提高编程效率和代码质量。', 1001, '{"tags": ["Python", "编程", "技巧"]}', 220, 90, 35),
(2007, '美食探店记', '探访城市里的隐藏美食，分享独特的味蕾体验。本文介绍了几家不为人知但味道绝佳的小店，包括他们的招牌菜品、价格、环境以及最佳用餐时间，让你发现更多美食惊喜。', 1002, '{"tags": ["美食", "探店", "推荐"]}', 150, 60, 15),
(2008, '篮球训练方法', '提高篮球技术的专业训练方法和技巧分享，包括投篮、运球、传球、防守等基本功的训练方法，以及如何提高比赛中的决策能力和团队配合。适合各个水平的篮球爱好者。', 1003, '{"tags": ["篮球", "训练", "技巧"]}', 160, 65, 18),
(2009, '古典音乐鉴赏', '介绍古典音乐的历史、流派和代表作品，从巴洛克时期到现代，带领读者了解不同时期的音乐特点和著名作曲家。同时提供了入门级的聆听建议，帮助音乐爱好者更好地欣赏古典音乐。', 1004, '{"tags": ["音乐", "古典", "艺术"]}', 130, 50, 12),
(2010, '人工智能在游戏中的应用', '探讨AI技术如何改变游戏产业和游戏体验，包括NPC行为、程序化内容生成、自适应难度调整等方面。分析了当前游戏中AI应用的案例，以及未来可能的创新方向。', 1005, '{"tags": ["AI", "游戏", "技术"]}', 210, 85, 32),
(2011, '中医养生指南', '介绍传统中医养生理念和实用方法，包括四季养生、食疗、穴位按摩和简易气功。结合现代生活方式，提供易于实践的养生建议，帮助读者平衡身心，增强体质。', 1006, '{"tags": ["中医", "养生", "健康"]}', 175, 68, 25),
(2012, '家常菜烹饪技巧', '分享制作美味家常菜的烹饪技巧和秘诀，从食材选择、刀工技巧到火候控制，全面提升家庭烹饪水平。特别介绍了几道适合新手的经典菜肴的详细做法。', 1007, '{"tags": ["烹饪", "家常菜", "美食"]}', 230, 95, 38),
(2013, 'UI设计趋势分析', '分析当前用户界面设计的主流趋势和创新方向，包括极简主义、新拟物化、沉浸式体验等风格的特点和应用案例。为设计师提供创作灵感和实用指导。', 1008, '{"tags": ["设计", "UI", "趋势"]}', 190, 75, 28),
(2014, '高效学习方法论', '基于认知科学研究，介绍高效学习的方法和策略，包括间隔重复、主动回忆、费曼技巧等实用技术。帮助学生和终身学习者优化学习过程，提高学习效果。', 1009, '{"tags": ["学习", "方法", "效率"]}', 280, 110, 45),
(2015, '个人投资入门', '为初学者提供个人投资的基础知识和实用建议，包括资产配置、风险管理、常见投资工具分析等内容。强调长期投资理念和避免常见投资误区的重要性。', 1010, '{"tags": ["投资", "理财", "入门"]}', 260, 105, 42),
(2016, '手机摄影技巧', '教你如何用手机拍出专业级照片，包括构图原则、光线运用、后期编辑等关键技巧。特别介绍了几种特殊场景（如夜景、人像、美食）的拍摄方法。', 1011, '{"tags": ["摄影", "手机", "技巧"]}', 240, 98, 36),
(2017, '当代文学赏析', '深入分析几部当代文学经典作品，探讨其艺术特色、主题思想和社会意义。通过细致的文本解读，帮助读者更好地理解和欣赏现代文学作品。', 1012, '{"tags": ["文学", "赏析", "当代"]}', 140, 55, 20),
(2018, '量子物理入门', '用通俗易懂的语言解释量子物理的基本概念和奇妙现象，如量子叠加、量子纠缠和测量问题。让非专业读者也能理解这一前沿科学领域的魅力。', 1013, '{"tags": ["物理", "量子", "科普"]}', 170, 65, 22),
(2019, '可持续生活指南', '提供实用的可持续生活建议，包括减少塑料使用、节约能源、可持续饮食等方面的具体做法。强调个人选择对环境保护的重要影响。', 1014, '{"tags": ["环保", "可持续", "生活"]}', 195, 78, 30),
(2020, '中国古代建筑艺术', '介绍中国古代建筑的历史发展、特色风格和文化内涵，包括宫殿、园林、寺庙等不同类型建筑的艺术价值和技术成就。配有丰富的案例分析。', 1015, '{"tags": ["建筑", "历史", "文化"]}', 185, 72, 26),
(2021, '深度学习框架比较', '详细比较当前主流深度学习框架（如TensorFlow、PyTorch等）的特点、优缺点和适用场景，帮助AI开发者选择最适合自己项目的工具。', 1001, '{"tags": ["深度学习", "框架", "AI"]}', 225, 92, 34),
(2022, '世界咖啡文化之旅', '带领读者探索世界各地的咖啡文化，包括不同国家的咖啡种类、烹煮方法和饮用习惯。同时介绍了一些值得一试的特色咖啡馆。', 1002, '{"tags": ["咖啡", "文化", "旅行"]}', 215, 88, 33),
(2023, '马拉松训练计划', '为准备参加马拉松的跑者提供系统的训练计划，包括体能建设、配速控制、营养补给和赛前准备等方面的专业建议。适合不同水平的跑步爱好者。', 1003, '{"tags": ["马拉松", "训练", "跑步"]}', 205, 82, 31),
(2024, '电影摄影艺术', '探讨电影摄影的艺术表现和技术手段，分析经典电影中的摄影风格和视觉语言。帮助电影爱好者更深入地理解电影的视觉叙事。', 1004, '{"tags": ["电影", "摄影", "艺术"]}', 165, 64, 24),
(2025, '独立游戏开发指南', '为独立游戏开发者提供从创意到发行的全流程指导，包括游戏设计、技术选择、资源管理和营销策略等关键环节的实用建议。', 1005, '{"tags": ["游戏开发", "独立游戏", "指南"]}', 235, 96, 37),
(2026, '常见疾病预防指南', '介绍常见疾病的预防方法和健康生活习惯，包括合理饮食、适当运动、定期体检等方面的建议。帮助读者提高健康意识，预防疾病发生。', 1006, '{"tags": ["健康", "预防", "医疗"]}', 255, 102, 41),
(2027, '世界美食探索', '带领读者探索世界各地的特色美食和饮食文化，介绍不同国家和地区的代表性菜肴、食材和烹饪技巧，以及背后的文化故事。', 1007, '{"tags": ["美食", "文化", "世界"]}', 275, 112, 44),
(2028, '平面设计原则', '详细讲解平面设计的基本原则和要素，包括排版、色彩、图形、空间等方面的知识和技巧。通过实例分析帮助设计师提升设计水平。', 1008, '{"tags": ["设计", "平面", "原则"]}', 155, 62, 23),
(2029, '儿童心理发展指南', '基于心理学研究，介绍儿童不同年龄阶段的心理发展特点和教育方法，帮助父母更好地理解孩子，建立健康的亲子关系。', 1009, '{"tags": ["心理", "儿童", "教育"]}', 265, 108, 43),
(2030, '股市投资策略', '分析不同的股票投资策略和方法，包括基本面分析、技术分析、价值投资等，并讨论它们的优缺点和适用条件。为投资者提供决策参考。', 1010, '{"tags": ["股票", "投资", "策略"]}', 245, 100, 39);

-- 创建示例点赞数据
INSERT INTO likes (like_id, user_id, post_id)
VALUES
(4001, 1001, 2005),
(4002, 1002, 2006),
(4003, 1003, 2007),
(4004, 1004, 2008),
(4005, 1005, 2009),
(4006, 1006, 2011),
(4007, 1007, 2012),
(4008, 1008, 2013),
(4009, 1009, 2014),
(4010, 1010, 2015),
(4011, 1011, 2016),
(4012, 1012, 2017),
(4013, 1013, 2018),
(4014, 1014, 2019),
(4015, 1015, 2020),
(4016, 1001, 2021),
(4017, 1002, 2022),
(4018, 1003, 2023),
(4019, 1004, 2024),
(4020, 1005, 2025),
(4021, 1006, 2026),
(4022, 1007, 2027),
(4023, 1008, 2028),
(4024, 1009, 2029),
(4025, 1010, 2030);

-- 创建示例收藏数据
INSERT INTO favorites (favorite_id, user_id, post_id, notes)
VALUES
(5001, 1001, 2010, '很有启发性的文章'),
(5002, 1002, 2006, '实用的编程技巧'),
(5003, 1003, 2008, '非常适合我的训练计划'),
(5004, 1004, 2008, '值得收藏的训练方法'),
(5005, 1005, 2009, '古典音乐入门必读'),
(5006, 1006, 2011, '中医养生精华'),
(5007, 1007, 2012, '家常菜必备技巧'),
(5008, 1008, 2013, '设计趋势参考'),
(5009, 1009, 2014, '学习方法论收藏'),
(5010, 1010, 2015, '投资入门指南'),
(5011, 1011, 2016, '手机摄影必备技巧'),
(5012, 1012, 2017, '文学赏析经典'),
(5013, 1013, 2018, '量子物理入门'),
(5014, 1014, 2019, '可持续生活指南'),
(5015, 1015, 2020, '中国古代建筑艺术'),
(5016, 1001, 2021, '深度学习框架比较'),
(5017, 1002, 2022, '咖啡文化之旅'),
(5018, 1003, 2023, '马拉松训练计划'),
(5019, 1004, 2024, '电影摄影艺术'),
(5020, 1005, 2025, '独立游戏开发指南');

-- 创建示例行为数据
INSERT INTO events (event_id, user_id, post_id, event_type, source, device_info)
VALUES 
(3001, 1001, 2005, 'view', 'home', '{"type": "mobile", "os": "iOS"}'),
(3002, 1001, 2005, 'like', 'detail', '{"type": "mobile", "os": "iOS"}'),
(3003, 1002, 2001, 'view', 'home', '{"type": "desktop", "os": "Windows"}'),
(3004, 1002, 2006, 'view', 'home', '{"type": "desktop", "os": "Windows"}'),
(3005, 1002, 2006, 'favorite', 'detail', '{"type": "desktop", "os": "Windows"}'),
(3006, 1003, 2002, 'view', 'search', '{"type": "mobile", "os": "Android"}'),
(3007, 1003, 2007, 'view', 'home', '{"type": "mobile", "os": "Android"}'),
(3008, 1003, 2007, 'like', 'detail', '{"type": "mobile", "os": "Android"}'),
(3009, 1004, 2003, 'view', 'home', '{"type": "tablet", "os": "iPadOS"}'),
(3010, 1004, 2008, 'view', 'recommendation', '{"type": "tablet", "os": "iPadOS"}'),
(3011, 1004, 2008, 'favorite', 'detail', '{"type": "tablet", "os": "iPadOS"}'),
(3012, 1005, 2004, 'view', 'home', '{"type": "desktop", "os": "macOS"}'),
(3013, 1005, 2009, 'view', 'search', '{"type": "desktop", "os": "macOS"}'),
(3014, 1005, 2009, 'like', 'detail', '{"type": "desktop", "os": "macOS"}'),
(3015, 1001, 2010, 'view', 'recommendation', '{"type": "mobile", "os": "iOS"}'),
(3016, 1006, 2011, 'view', 'home', '{"type": "mobile", "os": "Android"}'),
(3017, 1006, 2011, 'like', 'detail', '{"type": "mobile", "os": "Android"}'),
(3018, 1006, 2011, 'favorite', 'detail', '{"type": "mobile", "os": "Android"}'),
(3019, 1007, 2012, 'view', 'search', '{"type": "tablet", "os": "iPadOS"}'),
(3020, 1007, 2012, 'like', 'detail', '{"type": "tablet", "os": "iPadOS"}'),
(3021, 1008, 2013, 'view', 'home', '{"type": "desktop", "os": "Windows"}'),
(3022, 1008, 2013, 'favorite', 'detail', '{"type": "desktop", "os": "Windows"}'),
(3023, 1009, 2014, 'view', 'recommendation', '{"type": "mobile", "os": "iOS"}'),
(3024, 1009, 2014, 'like', 'detail', '{"type": "mobile", "os": "iOS"}'),
(3025, 1010, 2015, 'view', 'home', '{"type": "desktop", "os": "macOS"}'),
(3026, 1010, 2015, 'favorite', 'detail', '{"type": "desktop", "os": "macOS"}'),
(3027, 1011, 2016, 'view', 'search', '{"type": "mobile", "os": "Android"}'),
(3028, 1011, 2016, 'like', 'detail', '{"type": "mobile", "os": "Android"}'),
(3029, 1012, 2017, 'view', 'home', '{"type": "tablet", "os": "iPadOS"}'),
(3030, 1012, 2017, 'favorite', 'detail', '{"type": "tablet", "os": "iPadOS"}'),
(3031, 1013, 2018, 'view', 'recommendation', '{"type": "desktop", "os": "Windows"}'),
(3032, 1013, 2018, 'like', 'detail', '{"type": "desktop", "os": "Windows"}'),
(3033, 1014, 2019, 'view', 'home', '{"type": "mobile", "os": "iOS"}'),
(3034, 1014, 2019, 'favorite', 'detail', '{"type": "mobile", "os": "iOS"}'),
(3035, 1015, 2020, 'view', 'search', '{"type": "desktop", "os": "macOS"}'),
(3036, 1015, 2020, 'like', 'detail', '{"type": "desktop", "os": "macOS"}'),
(3037, 1001, 2021, 'view', 'home', '{"type": "mobile", "os": "iOS"}'),
(3038, 1001, 2021, 'like', 'detail', '{"type": "mobile", "os": "iOS"}'),
(3039, 1001, 2021, 'favorite', 'detail', '{"type": "mobile", "os": "iOS"}'),
(3040, 1002, 2022, 'view', 'recommendation', '{"type": "desktop", "os": "Windows"}'),
(3041, 1002, 2022, 'like', 'detail', '{"type": "desktop", "os": "Windows"}'),
(3042, 1003, 2023, 'view', 'home', '{"type": "mobile", "os": "Android"}'),
(3043, 1003, 2023, 'favorite', 'detail', '{"type": "mobile", "os": "Android"}'),
(3044, 1004, 2024, 'view', 'search', '{"type": "tablet", "os": "iPadOS"}'),
(3045, 1004, 2024, 'like', 'detail', '{"type": "tablet", "os": "iPadOS"}'),
(3046, 1005, 2025, 'view', 'home', '{"type": "desktop", "os": "macOS"}'),
(3047, 1005, 2025, 'favorite', 'detail', '{"type": "desktop", "os": "macOS"}'),
(3048, 1006, 2026, 'view', 'recommendation', '{"type": "mobile", "os": "Android"}'),
(3049, 1006, 2026, 'like', 'detail', '{"type": "mobile", "os": "Android"}'),
(3050, 1007, 2027, 'view', 'home', '{"type": "tablet", "os": "iPadOS"}'),
(3051, 1007, 2027, 'favorite', 'detail', '{"type": "tablet", "os": "iPadOS"}'),
(3052, 1008, 2028, 'view', 'search', '{"type": "desktop", "os": "Windows"}'),
(3053, 1008, 2028, 'like', 'detail', '{"type": "desktop", "os": "Windows"}'),
(3054, 1009, 2029, 'view', 'home', '{"type": "mobile", "os": "iOS"}'),
(3055, 1009, 2029, 'favorite', 'detail', '{"type": "mobile", "os": "iOS"}'),
(3056, 1010, 2030, 'view', 'recommendation', '{"type": "desktop", "os": "macOS"}'),
(3057, 1010, 2030, 'like', 'detail', '{"type": "desktop", "os": "macOS"}'),
(3058, 1010, 2030, 'favorite', 'detail', '{"type": "desktop", "os": "macOS"}'),
(3059, 1001, 2015, 'view', 'search', '{"type": "mobile", "os": "iOS"}'),
(3060, 1002, 2016, 'view', 'home', '{"type": "desktop", "os": "Windows"}'),
(3061, 1003, 2017, 'view', 'recommendation', '{"type": "mobile", "os": "Android"}'),
(3062, 1004, 2018, 'view', 'search', '{"type": "tablet", "os": "iPadOS"}'),
(3063, 1005, 2019, 'view', 'home', '{"type": "desktop", "os": "macOS"}'),
(3064, 1006, 2020, 'view', 'recommendation', '{"type": "mobile", "os": "Android"}'),
(3065, 1007, 2021, 'view', 'search', '{"type": "tablet", "os": "iPadOS"}'),
(3066, 1008, 2022, 'view', 'home', '{"type": "desktop", "os": "Windows"}'),
(3067, 1009, 2023, 'view', 'recommendation', '{"type": "mobile", "os": "iOS"}'),
(3068, 1010, 2024, 'view', 'search', '{"type": "desktop", "os": "macOS"}'),
(3069, 1011, 2025, 'view', 'home', '{"type": "mobile", "os": "Android"}'),
(3070, 1012, 2026, 'view', 'recommendation', '{"type": "tablet", "os": "iPadOS"}'),
(3071, 1013, 2027, 'view', 'search', '{"type": "desktop", "os": "Windows"}'),
(3072, 1014, 2028, 'view', 'home', '{"type": "mobile", "os": "iOS"}'),
(3073, 1015, 2029, 'view', 'recommendation', '{"type": "desktop", "os": "macOS"}'),
(3074, 1001, 2030, 'view', 'search', '{"type": "mobile", "os": "iOS"}'),
(3075, 1002, 2011, 'view', 'home', '{"type": "desktop", "os": "Windows"}'),
(3076, 1003, 2012, 'view', 'recommendation', '{"type": "mobile", "os": "Android"}'),
(3077, 1004, 2013, 'view', 'search', '{"type": "tablet", "os": "iPadOS"}'),
(3078, 1005, 2014, 'view', 'home', '{"type": "desktop", "os": "macOS"}'),
(3079, 1006, 2001, 'view', 'recommendation', '{"type": "mobile", "os": "Android"}'),
(3080, 1007, 2002, 'view', 'search', '{"type": "tablet", "os": "iPadOS"}');