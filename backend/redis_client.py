from typing import Optional
import redis
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Redis连接配置
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Redis键前缀
USER_VIEWED_POSTS_PREFIX = "user:viewed:posts:"

# Redis过期时间（秒）
VIEWED_POSTS_EXPIRE_TIME = 60 * 60 * 24 * 30  # 30天

# 创建Redis客户端
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=True  # 自动将字节解码为字符串
)

# 检查Redis连接
def check_redis_connection() -> bool:
    try:
        return redis_client.ping()
    except redis.ConnectionError:
        return False

# 记录用户浏览的帖子
def record_user_viewed_post(user_id: int, post_id: int) -> bool:
    """
    记录用户浏览过的帖子到Redis
    """
    try:
        key = f"{USER_VIEWED_POSTS_PREFIX}{user_id}"
        # 将整数ID转换为字符串存储
        redis_client.sadd(key, str(post_id))
        redis_client.expire(key, VIEWED_POSTS_EXPIRE_TIME)  # 设置过期时间
        return True
    except Exception as e:
        print(f"记录用户浏览帖子失败: {e}")
        return False

# 获取用户浏览过的所有帖子ID
def get_user_viewed_posts(user_id: int) -> set:
    """
    获取用户浏览过的所有帖子ID，返回整数ID集合
    """
    try:
        key = f"{USER_VIEWED_POSTS_PREFIX}{user_id}"
        # 获取字符串ID并转换为整数
        str_ids = redis_client.smembers(key)
        # 将字符串ID转换为整数ID
        return {int(post_id) for post_id in str_ids}
    except Exception as e:
        print(f"获取用户浏览帖子失败: {e}")
        return set()

# 检查用户是否浏览过指定帖子
def has_user_viewed_post(user_id: int, post_id: int) -> bool:
    """
    检查用户是否浏览过指定帖子
    """
    try:
        key = f"{USER_VIEWED_POSTS_PREFIX}{user_id}"
        # 将整数ID转换为字符串进行查询
        return redis_client.sismember(key, str(post_id))
    except Exception as e:
        print(f"检查用户浏览帖子失败: {e}")
        return False