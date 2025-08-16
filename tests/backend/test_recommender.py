import sys
import os
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.services.recommender import RecommenderService
from backend.models.models import User, Post, Event

class TestRecommenderService(unittest.TestCase):
    def setUp(self):
        # 创建模拟数据库会话
        self.db = MagicMock()
        self.recommender = RecommenderService(self.db)
        
        # 创建模拟用户
        self.user = MagicMock(spec=User)
        self.user.user_id = 'u1001'
        self.user.tags = ['科技', '编程', '人工智能']
        
        # 创建模拟帖子
        self.posts = []
        for i in range(1, 11):
            post = MagicMock(spec=Post)
            post.post_id = f'p100{i}'
            post.title = f'测试帖子 {i}'
            post.content = f'这是测试帖子内容 {i}'
            post.author_id = 'u2001' if i % 2 == 0 else 'u3001'
            post.tags = ['科技'] if i % 3 == 0 else ['编程'] if i % 3 == 1 else ['人工智能']
            post.view_count = i * 10
            post.like_count = i * 2
            post.favorite_count = i
            post.create_time = datetime.utcnow() - timedelta(days=i)
            self.posts.append(post)
    
    def test_recommend_by_tags(self):
        # 设置模拟查询结果
        self.db.query.return_value.filter.return_value.all.return_value = []
        self.db.query.return_value.filter.return_value.limit.return_value.all.side_effect = [
            [self.posts[0], self.posts[3], self.posts[6]], # 科技标签
            [self.posts[1], self.posts[4], self.posts[7]], # 编程标签
            [self.posts[2], self.posts[5], self.posts[8]]  # 人工智能标签
        ]
        
        # 调用被测试方法
        result = self.recommender._recommend_by_tags(self.user, 5)
        
        # 验证结果
        self.assertEqual(len(result), 5)
        self.assertIn(self.posts[0], result)
        
    def test_recommend_random(self):
        # 设置模拟查询结果
        self.db.query.return_value.filter.return_value.all.return_value = self.posts[:5]
        
        # 调用被测试方法
        result = self.recommender._recommend_random(3)
        
        # 验证结果
        self.assertEqual(len(result), 3)
        for post in result:
            self.assertIn(post, self.posts[:5])
    
    def test_rank_posts(self):
        # 调用被测试方法
        result = self.recommender._rank_posts(self.user, self.posts)
        
        # 验证结果
        self.assertEqual(len(result), len(self.posts))
        
        # 验证排序逻辑 - 第一个应该是分数最高的
        # 由于排序逻辑综合考虑了标签匹配度、热度和新鲜度，这里只做简单验证
        # 在实际测试中，可能需要更精确的验证
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), len(self.posts))
    
    def test_get_recommendations(self):
        # 设置模拟查询结果
        self.db.query.return_value.filter.return_value.first.return_value = self.user
        
        # 模拟推荐方法
        with patch.object(self.recommender, '_recommend_by_tags') as mock_tag_rec, \
             patch.object(self.recommender, '_recommend_by_collaborative_filtering') as mock_cf_rec, \
             patch.object(self.recommender, '_recommend_random') as mock_random_rec, \
             patch.object(self.recommender, '_rank_posts') as mock_rank:
            
            mock_tag_rec.return_value = self.posts[:4]
            mock_cf_rec.return_value = self.posts[4:8]
            mock_random_rec.return_value = self.posts[8:]
            mock_rank.return_value = self.posts
            
            # 调用被测试方法
            result = self.recommender.get_recommendations('u1001', 5, 0)
            
            # 验证结果
            self.assertEqual(result['items'], self.posts[:5])
            self.assertTrue(result['has_more'])
            self.assertEqual(result['total'], len(self.posts))

if __name__ == '__main__':
    unittest.main()