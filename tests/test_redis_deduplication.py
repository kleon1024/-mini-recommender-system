import sys
import os
import unittest
import json
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入需要测试的模块
from backend.redis_client import record_user_viewed_post, get_user_viewed_posts, has_user_viewed_post
from backend.services.recommender import RecommenderService

class TestRedisDeduplication(unittest.TestCase):
    
    @patch('backend.redis_client.redis_client')
    def test_record_user_viewed_post(self, mock_redis):
        """测试记录用户浏览帖子功能"""
        # 设置模拟对象
        mock_redis.sadd.return_value = 1
        mock_redis.expire.return_value = True
        
        # 调用被测试的函数
        result = record_user_viewed_post('test_user', 'test_post')
        
        # 验证结果
        self.assertTrue(result)
        mock_redis.sadd.assert_called_once_with('user:test_user:viewed_posts', 'test_post')
        mock_redis.expire.assert_called_once()
    
    @patch('backend.redis_client.redis_client')
    def test_get_user_viewed_posts(self, mock_redis):
        """测试获取用户已浏览帖子列表功能"""
        # 设置模拟对象
        mock_redis.smembers.return_value = {b'post1', b'post2', b'post3'}
        
        # 调用被测试的函数
        result = get_user_viewed_posts('test_user')
        
        # 验证结果
        self.assertEqual(result, {'post1', 'post2', 'post3'})
        mock_redis.smembers.assert_called_once_with('user:test_user:viewed_posts')
    
    @patch('backend.redis_client.redis_client')
    def test_has_user_viewed_post(self, mock_redis):
        """测试检查用户是否已浏览帖子功能"""
        # 设置模拟对象
        mock_redis.sismember.return_value = True
        
        # 调用被测试的函数
        result = has_user_viewed_post('test_user', 'test_post')
        
        # 验证结果
        self.assertTrue(result)
        mock_redis.sismember.assert_called_once_with('user:test_user:viewed_posts', 'test_post')
    
    @patch('backend.services.recommender.get_user_viewed_posts')
    @patch('backend.services.recommender.RecommenderService._recommend_by_tags')
    def test_recommender_deduplication(self, mock_recommend_by_tags, mock_get_viewed_posts):
        """测试推荐系统的消重功能"""
        # 创建模拟的数据库会话和用户
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.user_id = 'test_user'
        mock_db.query().filter().first.return_value = mock_user
        
        # 创建模拟的帖子
        mock_posts = []
        for i in range(10):
            mock_post = MagicMock()
            mock_post.post_id = f'post{i}'
            mock_posts.append(mock_post)
        
        # 设置模拟的已浏览帖子
        viewed_posts = {'post1', 'post3', 'post5', 'post7', 'post9'}
        mock_get_viewed_posts.return_value = viewed_posts
        
        # 设置模拟的推荐结果
        mock_recommend_by_tags.return_value = mock_posts
        
        # 创建推荐服务实例并调用获取推荐方法
        recommender = RecommenderService(mock_db)
        result = recommender.get_recommendations('test_user', 5, 0, '{}')
        
        # 验证结果中不包含已浏览的帖子
        result_post_ids = [post.post_id for post in result['posts']]
        for post_id in viewed_posts:
            self.assertNotIn(post_id, result_post_ids)

if __name__ == '__main__':
    unittest.main()