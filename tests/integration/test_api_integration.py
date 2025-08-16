import requests
import unittest
import time

class TestAPIIntegration(unittest.TestCase):
    """集成测试：测试API端到端功能"""
    
    BASE_URL = "http://localhost:8000/api"
    USER_ID = "u1001"
    
    def setUp(self):
        # 等待服务启动
        max_retries = 5
        retry_count = 0
        while retry_count < max_retries:
            try:
                response = requests.get("http://localhost:8000/health")
                if response.status_code == 200:
                    break
            except requests.exceptions.ConnectionError:
                pass
            
            print(f"等待API服务启动...({retry_count+1}/{max_retries})")
            time.sleep(2)
            retry_count += 1
        
        if retry_count == max_retries:
            self.fail("无法连接到API服务")
    
    def test_get_recommendations(self):
        """测试获取推荐内容"""
        response = requests.get(
            f"{self.BASE_URL}/posts",
            params={"user_id": self.USER_ID, "count": 5}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # 验证响应结构
        self.assertIn("items", data)
        self.assertIn("has_more", data)
        self.assertIn("total", data)
        
        # 验证返回的推荐内容
        self.assertIsInstance(data["items"], list)
        if data["items"]:
            item = data["items"][0]
            self.assertIn("post_id", item)
            self.assertIn("title", item)
            self.assertIn("content", item)
    
    def test_post_event(self):
        """测试上报用户行为"""
        event_data = {
            "user_id": self.USER_ID,
            "post_id": "p1001",  # 假设存在的帖子ID
            "event_type": "view",
            "context": {"page": "home"}
        }
        
        response = requests.post(f"{self.BASE_URL}/events", json=event_data)
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("event_id", data)
    
    def test_get_post_detail(self):
        """测试获取帖子详情"""
        # 先获取推荐列表中的第一个帖子ID
        response = requests.get(
            f"{self.BASE_URL}/posts",
            params={"user_id": self.USER_ID, "count": 1}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        if not data["items"]:
            self.skipTest("没有可用的帖子进行测试")
        
        post_id = data["items"][0]["post_id"]
        
        # 获取帖子详情
        response = requests.get(f"{self.BASE_URL}/posts/{post_id}")
        
        self.assertEqual(response.status_code, 200)
        post_data = response.json()
        
        # 验证帖子详情
        self.assertEqual(post_data["post_id"], post_id)
        self.assertIn("title", post_data)
        self.assertIn("content", post_data)
    
    def test_get_related_posts(self):
        """测试获取相关推荐"""
        # 先获取推荐列表中的第一个帖子ID
        response = requests.get(
            f"{self.BASE_URL}/posts",
            params={"user_id": self.USER_ID, "count": 1}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        if not data["items"]:
            self.skipTest("没有可用的帖子进行测试")
        
        post_id = data["items"][0]["post_id"]
        
        # 获取相关推荐
        response = requests.get(
            f"{self.BASE_URL}/posts/{post_id}/related",
            params={"user_id": self.USER_ID, "count": 3}
        )
        
        self.assertEqual(response.status_code, 200)
        related_posts = response.json()
        
        # 验证相关推荐
        self.assertIsInstance(related_posts, list)
        if related_posts:
            self.assertNotEqual(related_posts[0]["post_id"], post_id)  # 相关推荐不应包含当前帖子

if __name__ == "__main__":
    unittest.main()