import sys
import os
import time
import json
import requests

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 测试配置
API_BASE_URL = "http://localhost:8000/api"
TEST_USER_ID = "user_1"  # 确保这是系统中存在的用户ID

# 直接导入Redis客户端进行测试
from backend.redis_client import record_user_viewed_post, get_user_viewed_posts, has_user_viewed_post, redis_client

def test_deduplication_flow():
    """
    测试消重系统的完整流程：
    1. 获取初始推荐列表
    2. 浏览其中一篇帖子
    3. 再次获取推荐列表，确认已浏览的帖子不在列表中
    """
    print("\n开始测试消重系统...")
    
    # 步骤1: 获取初始推荐列表
    print("\n步骤1: 获取初始推荐列表")
    response = requests.get(f"{API_BASE_URL}/posts?user_id={TEST_USER_ID}&count=10&offset=0")
    if response.status_code != 200:
        print(f"获取推荐列表失败: {response.status_code}")
        return False
    
    initial_recommendations = response.json()
    if not initial_recommendations.get("posts"):
        print("初始推荐列表为空，无法继续测试")
        return False
    
    print(f"初始推荐列表包含 {len(initial_recommendations['posts'])} 篇帖子")
    for i, post in enumerate(initial_recommendations['posts']):
        print(f"  {i+1}. {post['post_id']} - {post['title']}")
    
    # 选择第一篇帖子进行浏览
    post_to_view = initial_recommendations['posts'][0]
    post_id_to_view = post_to_view['post_id']
    post_title_to_view = post_to_view['title']
    
    print(f"\n选择浏览帖子: {post_id_to_view} - {post_title_to_view}")
    
    # 步骤2: 浏览选定的帖子
    print("\n步骤2: 浏览选定的帖子")
    # 先获取帖子详情，触发浏览事件
    detail_response = requests.get(f"{API_BASE_URL}/posts/{post_id_to_view}?user_id={TEST_USER_ID}")
    if detail_response.status_code != 200:
        print(f"获取帖子详情失败: {detail_response.status_code}")
        return False
    
    # 再创建一个明确的浏览事件
    event_data = {
        "user_id": TEST_USER_ID,
        "post_id": post_id_to_view,
        "event_type": "view",
        "event_data": {}
    }
    event_response = requests.post(f"{API_BASE_URL}/events", json=event_data)
    if event_response.status_code != 200:
        print(f"创建浏览事件失败: {event_response.status_code}")
        return False
    
    print(f"成功浏览帖子并创建浏览事件")
    
    # 等待一小段时间，确保Redis中的数据已更新
    print("\n等待2秒，确保Redis中的数据已更新...")
    time.sleep(2)
    
    # 步骤3: 再次获取推荐列表，确认已浏览的帖子不在列表中
    print("\n步骤3: 再次获取推荐列表，检查消重效果")
    new_response = requests.get(f"{API_BASE_URL}/posts?user_id={TEST_USER_ID}&count=10&offset=0")
    if new_response.status_code != 200:
        print(f"获取新推荐列表失败: {new_response.status_code}")
        return False
    
    new_recommendations = new_response.json()
    new_post_ids = [post['post_id'] for post in new_recommendations['posts']]
    
    print(f"新推荐列表包含 {len(new_recommendations['posts'])} 篇帖子")
    for i, post in enumerate(new_recommendations['posts']):
        print(f"  {i+1}. {post['post_id']} - {post['title']}")
    
    # 检查已浏览的帖子是否不在新的推荐列表中
    if post_id_to_view in new_post_ids:
        print(f"\n❌ 测试失败: 已浏览的帖子 {post_id_to_view} 仍然出现在新的推荐列表中")
        return False
    else:
        print(f"\n✅ 测试成功: 已浏览的帖子 {post_id_to_view} 不再出现在新的推荐列表中")
        return True

def test_redis_functions_directly():
    """
    直接测试Redis消重功能函数
    """
    print("\n开始直接测试Redis消重功能...")
    
    # 清理测试数据
    if redis_client:
        redis_client.delete(f"user:{TEST_USER_ID}:viewed_posts")
    
    # 测试记录浏览
    test_post_id = "test_post_123"
    success = record_user_viewed_post(TEST_USER_ID, test_post_id)
    print(f"记录用户浏览帖子结果: {success}")
    
    # 测试获取已浏览帖子
    viewed_posts = get_user_viewed_posts(TEST_USER_ID)
    print(f"用户已浏览帖子: {viewed_posts}")
    
    # 测试检查是否浏览过
    has_viewed = has_user_viewed_post(TEST_USER_ID, test_post_id)
    print(f"用户是否浏览过测试帖子: {has_viewed}")
    
    # 测试检查未浏览过的帖子
    has_viewed_another = has_user_viewed_post(TEST_USER_ID, "another_post_456")
    print(f"用户是否浏览过另一篇帖子: {has_viewed_another}")
    
    # 验证结果
    if success and test_post_id in viewed_posts and has_viewed and not has_viewed_another:
        print("\n✅ Redis消重功能测试通过!")
        return True
    else:
        print("\n❌ Redis消重功能测试失败!")
        return False

def main():
    print("===== Redis消重系统集成测试 =====")
    
    # 先测试Redis功能
    redis_test_result = test_redis_functions_directly()
    
    # 如果Redis功能测试通过，再测试完整流程
    if redis_test_result:
        print("\n继续测试完整消重流程...")
        api_test_result = test_deduplication_flow()
        if api_test_result:
            print("\n✅ 所有测试通过! Redis消重系统工作正常。")
        else:
            print("\n❌ API集成测试失败! Redis功能正常但API集成可能存在问题。")
    else:
        print("\n❌ Redis功能测试失败! 跳过API集成测试。")

if __name__ == "__main__":
    print("===== Redis消重系统集成测试 =====\n")
    # 先测试Redis功能
    redis_test_result = test_redis_functions_directly()
    
    # 如果Redis功能测试通过，再测试完整流程
    if redis_test_result:
        print("\n继续测试完整消重流程...")
        test_deduplication_flow()
    else:
        print("\nRedis功能测试失败，跳过完整流程测试。")