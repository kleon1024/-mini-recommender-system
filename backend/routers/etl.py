from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Path, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import os
import json
import logging
from datetime import datetime, timedelta

from database import get_db
from models.models import User, Post, Event
from schemas import schemas
from schemas import etl_schemas
from services.etl_service import ETLService

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter()

# 获取所有ETL任务
@router.get("/etl/tasks", response_model=List[etl_schemas.ETLTaskResponse])
def get_etl_tasks(db: Session = Depends(get_db)):
    """
    获取所有ETL任务
    """
    etl_service = ETLService(db)
    return etl_service.get_all_tasks()

# 获取ETL任务详情
@router.get("/etl/tasks/{task_id}", response_model=etl_schemas.ETLTaskDetailResponse)
def get_etl_task(task_id: str = Path(..., description="任务ID"), db: Session = Depends(get_db)):
    """
    获取ETL任务详情
    """
    etl_service = ETLService(db)
    task = etl_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

# 创建ETL任务
@router.post("/etl/tasks", response_model=etl_schemas.ETLTaskResponse, status_code=201)
def create_etl_task(task: etl_schemas.ETLTaskCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    创建ETL任务
    """
    # 添加详细日志，记录接收到的任务数据
    logger.info(f"接收到创建任务请求: name={task.name}, task_type={task.task_type}")
    logger.info(f"源连接ID: {task.source_connection_id}, 类型={type(task.source_connection_id)}")
    logger.info(f"目标连接ID: {task.target_connection_id}, 类型={type(task.target_connection_id)}")
    logger.info(f"立即执行: {task.run_immediately}")
    
    etl_service = ETLService(db)
    new_task = etl_service.create_task(task)
    
    logger.info(f"任务创建成功: ID={new_task.task_id}")
    
    # 如果任务设置为立即执行，则在后台运行任务
    if task.run_immediately:
        logger.info(f"开始后台执行任务: {new_task.task_id}")
        background_tasks.add_task(etl_service.run_task, new_task.task_id)
    
    return new_task

# 运行ETL任务
@router.post("/etl/tasks/{task_id}/run", response_model=etl_schemas.ETLTaskResponse)
def run_etl_task(task_id: str = Path(..., description="任务ID"), background_tasks: BackgroundTasks = None, db: Session = Depends(get_db)):
    """
    运行ETL任务
    """
    # 添加详细日志，记录接收到的任务ID
    logger.info(f"接收到运行任务请求: task_id={task_id}, 类型={type(task_id)}")
    
    etl_service = ETLService(db)
    task = etl_service.get_task_by_id(task_id)
    if not task:
        logger.error(f"任务不存在: {task_id}")
        raise HTTPException(status_code=404, detail="Task not found")
    
    logger.info(f"找到任务: ID={task.task_id}, 名称={task.name}, 源连接ID={task.source_connection_id}")
    
    # 在后台运行任务
    if background_tasks:
        logger.info(f"开始后台运行任务: {task_id}")
        background_tasks.add_task(etl_service.run_task, task_id)
        return etl_service.update_task_status(task_id, "running")
    else:
        # 同步运行任务（用于测试）
        logger.info(f"开始同步运行任务: {task_id}")
        return etl_service.run_task(task_id)

# 取消ETL任务
@router.post("/etl/tasks/{task_id}/cancel", response_model=etl_schemas.ETLTaskResponse)
def cancel_etl_task(task_id: str = Path(..., description="任务ID"), db: Session = Depends(get_db)):
    """
    取消ETL任务
    """
    etl_service = ETLService(db)
    task = etl_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return etl_service.update_task_status(task_id, "cancelled")

# 更新ETL任务
@router.put("/etl/tasks/{task_id}", response_model=etl_schemas.ETLTaskResponse)
def update_etl_task(task_id: str = Path(..., description="任务ID"), task: etl_schemas.ETLTaskCreate = Body(...), db: Session = Depends(get_db)):
    """
    更新ETL任务
    """
    # 添加详细日志，记录接收到的任务数据
    logger.info(f"接收到更新任务请求: task_id={task_id}, 类型={type(task_id)}")
    logger.info(f"任务数据: name={task.name}, task_type={task.task_type}")
    logger.info(f"源连接ID: {task.source_connection_id}, 类型={type(task.source_connection_id)}")
    logger.info(f"目标连接ID: {task.target_connection_id}, 类型={type(task.target_connection_id)}")
    
    etl_service = ETLService(db)
    updated_task = etl_service.update_task(task_id, task)
    if not updated_task:
        logger.error(f"任务不存在: {task_id}")
        raise HTTPException(status_code=404, detail="Task not found")
    
    logger.info(f"任务更新成功: {updated_task.task_id}")
    return updated_task

# 删除ETL任务
@router.delete("/etl/tasks/{task_id}", status_code=204)
def delete_etl_task(task_id: str = Path(..., description="任务ID"), db: Session = Depends(get_db)):
    """
    删除ETL任务
    """
    etl_service = ETLService(db)
    task = etl_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    etl_service.delete_task(task_id)
    return {"status": "success"}

# 获取ETL任务执行历史
@router.get("/etl/tasks/{task_id}/history", response_model=List[etl_schemas.ETLTaskHistoryResponse])
def get_etl_task_history(task_id: str = Path(..., description="任务ID"), limit: int = Query(10, description="返回的历史记录数量"), db: Session = Depends(get_db)):
    """
    获取ETL任务执行历史
    """
    etl_service = ETLService(db)
    task = etl_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    history = etl_service.get_task_history(task_id, limit)
    return history

# 获取所有数据库连接
@router.get("/etl/connections", response_model=List[etl_schemas.DatabaseConnectionResponse])
def get_database_connections(db: Session = Depends(get_db)):
    """
    获取所有数据库连接
    """
    etl_service = ETLService(db)
    return etl_service.get_all_connections()

# 创建数据库连接
@router.post("/etl/connections", response_model=etl_schemas.DatabaseConnectionResponse, status_code=201)
def create_database_connection(connection: etl_schemas.DatabaseConnectionCreate, db: Session = Depends(get_db)):
    """
    创建数据库连接
    """
    etl_service = ETLService(db)
    return etl_service.create_connection(connection)

# 测试数据库连接
@router.post("/etl/connections/test", response_model=etl_schemas.DatabaseConnectionTestResponse)
def test_database_connection(connection: etl_schemas.DatabaseConnectionCreate, db: Session = Depends(get_db)):
    """
    测试数据库连接
    """
    etl_service = ETLService(db)
    return etl_service.test_connection(connection)

# 删除数据库连接
@router.delete("/etl/connections/{connection_id}", status_code=204)
def delete_database_connection(connection_id: str = Path(..., description="连接ID"), db: Session = Depends(get_db)):
    """
    删除数据库连接
    """
    etl_service = ETLService(db)
    connection = etl_service.get_connection_by_id(connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    etl_service.delete_connection(connection_id)
    return {"status": "success"}

# 测试SQL
@router.post("/etl/sql/test", response_model=etl_schemas.SQLTestResponse)
def test_sql(request: etl_schemas.SQLTestRequest, db: Session = Depends(get_db)):
    """
    测试SQL语句
    """
    etl_service = ETLService(db)
    connection = etl_service.get_connection_by_id(request.connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    result = etl_service.test_sql(request.connection_id, request.sql)
    return result