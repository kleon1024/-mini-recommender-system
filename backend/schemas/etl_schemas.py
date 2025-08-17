from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

# 数据库连接模式
class DatabaseConnectionBase(BaseModel):
    name: str
    description: Optional[str] = None
    connection_type: str
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

class DatabaseConnectionCreate(DatabaseConnectionBase):
    pass

class DatabaseConnectionResponse(DatabaseConnectionBase):
    # 修改为字符串类型的ID，避免JavaScript大整数精度问题
    connection_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class DatabaseConnectionTestResponse(BaseModel):
    success: bool
    message: str

# ETL任务模式
class ETLTaskBase(BaseModel):
    name: str
    description: Optional[str] = None
    task_type: str
    # 修改为接受字符串类型的ID，避免JavaScript大整数精度问题
    source_connection_id: str
    target_connection_id: Optional[str] = None
    config: Dict[str, Any]
    schedule: Optional[str] = None

class ETLTaskCreate(ETLTaskBase):
    run_immediately: bool = False

class ETLTaskResponse(ETLTaskBase):
    # 修改为字符串类型的ID，避免JavaScript大整数精度问题
    task_id: str
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class ETLTaskDetailResponse(ETLTaskResponse):
    source_connection: Optional[DatabaseConnectionResponse] = None
    target_connection: Optional[DatabaseConnectionResponse] = None
    
    class Config:
        orm_mode = True

# ETL任务历史模式
class ETLTaskHistoryBase(BaseModel):
    # 修改为字符串类型的ID，避免JavaScript大整数精度问题
    task_id: str
    status: str
    start_time: datetime
    end_time: datetime
    rows_processed: int
    error_message: Optional[str] = None

class ETLTaskHistoryCreate(ETLTaskHistoryBase):
    pass

class ETLTaskHistoryResponse(ETLTaskHistoryBase):
    # 修改为字符串类型的ID，避免JavaScript大整数精度问题
    history_id: str
    created_at: datetime
    
    class Config:
        orm_mode = True

# ETL日志模式
class ETLLogBase(BaseModel):
    # 修改为字符串类型的ID，避免JavaScript大整数精度问题
    task_id: str
    log_level: str
    message: str

class ETLLogCreate(ETLLogBase):
    pass

class ETLLogResponse(ETLLogBase):
    # 修改为字符串类型的ID，避免JavaScript大整数精度问题
    log_id: str
    timestamp: datetime
    
    class Config:
        orm_mode = True
        
# SQL测试模式
class SQLTestRequest(BaseModel):
    connection_id: int
    sql: str
    
class SQLTestResponse(BaseModel):
    success: bool
    message: str
    columns: Optional[List[str]] = None
    data: Optional[List[Dict[str, Any]]] = None
    rows_affected: Optional[int] = None
    error: Optional[str] = None