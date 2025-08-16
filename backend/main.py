from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn
import os

# 导入自定义JSONResponse
from utils.json_utils import CustomJSONResponse

# 导入本地模块
from database import get_db, init_db
from models import models
from schemas import schemas
from routers import posts, events, users, data, model_api, likes, favorites
from redis_client import check_redis_connection

# 创建FastAPI应用
app = FastAPI(
    title="迷你推荐系统API",
    description="迷你推荐系统后端API服务",
    version="0.1.0"
)

# 配置JSON响应，确保中文字符不被转义
app.json_response_class = CustomJSONResponse

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境应该限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(posts.router, prefix="/api", tags=["posts"])
app.include_router(events.router, prefix="/api", tags=["events"])
app.include_router(users.router, prefix="/api", tags=["users"])
app.include_router(data.router, prefix="/api", tags=["data"])
app.include_router(model_api.router, prefix="/api", tags=["models"])
app.include_router(likes.router, prefix="/api", tags=["likes"])
app.include_router(favorites.router, prefix="/api", tags=["favorites"])

# 启动事件
@app.on_event("startup")
def startup_event():
    # 初始化数据库
    init_db()
    
    # 检查Redis连接
    redis_connected = check_redis_connection()
    if not redis_connected:
        print("警告: Redis连接失败，消重系统将使用数据库进行消重")

# 健康检查
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# 根路由
@app.get("/")
def read_root():
    return {"message": "Welcome to Mini Recommender System API"}

# 直接运行时的入口点
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)