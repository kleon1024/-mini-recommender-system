# MySQL到PostgreSQL同步模块
# 负责MySQL到PostgreSQL的数据同步

import time
import json
import logging
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from models.models import ETLTask

# 配置日志
logger = logging.getLogger(__name__)

# 设置日志级别为DEBUG以显示更多信息
logger.setLevel(logging.DEBUG)

# 添加控制台处理器
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
# 调试辅助函数
def debug_print(message, obj=None):
    """打印调试信息，同时输出到日志"""
    if obj is not None:
        message = f"{message}: {obj}"
    print(f"[MySQL->PostgreSQL] {message}")
    logger.debug(message)

class MySQLToPostgresETL:
    """
    MySQL到PostgreSQL同步类
    负责MySQL到PostgreSQL的数据同步
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def execute(self, task: ETLTask) -> int:
        """
        执行MySQL到PostgreSQL的ETL任务
        返回处理的行数
        """
        debug_print(f"开始执行ETL任务: {task.name} (ID: {task.task_id})")
        
        # 解析配置
        config = task.config
        debug_print("任务配置", config)
        
        source_table = config.get("source_table")
        target_table = config.get("target_table")
        batch_size = config.get("batch_size", 1000)
        incremental_field = config.get("incremental_field")
        incremental_value = config.get("incremental_value")
        schema = config.get("schema", "public")
        max_retries = config.get("max_retries", 3)  # 最大重试次数
        
        debug_print(f"初始参数 - 源表: {source_table}, 目标表: {target_table}, 批次大小: {batch_size}")
        debug_print(f"增量字段: {incremental_field}, 增量值: {incremental_value}, Schema: {schema}")
        
        # 验证配置
        debug_print("开始验证配置...")
        self._validate_config(task, source_table, target_table)
        
        # 验证后重新获取可能已更新的值
        source_table = task.config.get("source_table")
        target_table = task.config.get("target_table")
        debug_print(f"验证后 - 源表: {source_table}, 目标表: {target_table}")
        
        # 源连接和目标连接
        mysql_conn = None
        pg_conn = None
        total_rows = 0
        
        try:
            # 获取MySQL连接
            debug_print("开始获取MySQL连接...")
            from .connection_manager import ConnectionManager
            connection_manager = ConnectionManager(self.db)
            
            connection = connection_manager.get_connection_by_id(task.source_connection_id)
            debug_print(f"源连接信息: ID={task.source_connection_id}, 类型={connection.connection_type if connection else 'None'}")
            
            if not connection or connection.connection_type != "mysql":
                error_msg = f"无效的MySQL连接: {task.source_connection_id}"
                debug_print(error_msg)
                raise ValueError(error_msg)
            
            debug_print(f"MySQL连接参数: 主机={connection.host}, 端口={connection.port}, 数据库={connection.database}")
            import pymysql
            mysql_conn = pymysql.connect(
                host=connection.host,
                port=connection.port,
                user=connection.username,
                password=connection.password,
                database=connection.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            debug_print("MySQL连接成功")
            
            # 获取PostgreSQL连接
            debug_print("开始获取PostgreSQL连接...")
            connection = connection_manager.get_connection_by_id(task.target_connection_id)
            debug_print(f"目标连接信息: ID={task.target_connection_id}, 类型={connection.connection_type if connection else 'None'}")
            
            if not connection or connection.connection_type != "postgres":
                error_msg = f"无效的PostgreSQL连接: {task.target_connection_id}"
                debug_print(error_msg)
                raise ValueError(error_msg)
            
            debug_print(f"PostgreSQL连接参数: 主机={connection.host}, 端口={connection.port}, 数据库={connection.database}")
            # 使用asyncpg替代psycopg2
            import asyncio
            import asyncpg
            
            # 创建事件循环并在其中运行异步连接
            debug_print("创建异步事件循环...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 使用同步方式获取异步连接
            debug_print("尝试连接PostgreSQL...")
            pg_conn = loop.run_until_complete(asyncpg.connect(
                host=connection.host,
                port=connection.port,
                user=connection.username,
                password=connection.password,
                database=connection.database
            ))
            debug_print("PostgreSQL连接成功")
            
            # 1. 验证目标表是否存在，如果不存在则创建
            debug_print(f"检查目标表是否存在: schema={schema}, table={target_table}")
            self._ensure_target_table_exists(mysql_conn, pg_conn, source_table, target_table, schema)
            
            # 2. 构建查询
            query = f"SELECT * FROM {source_table}"
            if incremental_field and incremental_value:
                query += f" WHERE {incremental_field} >= '{incremental_value}'"
            debug_print(f"构建查询SQL: {query}")
            
            # 3. 分批读取MySQL数据并写入PostgreSQL
            debug_print("开始分批读取MySQL数据并写入PostgreSQL...")
            with mysql_conn.cursor() as mysql_cursor:
                # 获取总行数
                count_query = f"SELECT COUNT(*) as count FROM ({query}) as t"
                debug_print(f"执行计数查询: {count_query}")
                mysql_cursor.execute(count_query)
                total_count = mysql_cursor.fetchone()['count']
                debug_print(f"查询结果总行数: {total_count}")
                
                if total_count == 0:
                    debug_print(f"没有新数据需要同步: {source_table} -> {target_table}")
                    return 0
                
                logger.info(f"需要同步 {total_count} 行数据")
                
                # 添加LIMIT和OFFSET进行分页查询
                for offset in range(0, total_count, batch_size):
                    current_batch = min(offset+batch_size, total_count) - offset
                    debug_print(f"处理批次 {offset}-{min(offset+batch_size, total_count)}, 共{current_batch}行")
                    batch_query = f"{query} LIMIT {batch_size} OFFSET {offset}"
                    debug_print(f"批次查询SQL: {batch_query}")
                    
                    # 重试机制
                    retry_count = 0
                    while retry_count < max_retries:
                        try:
                            # 读取一批数据
                            debug_print(f"从MySQL读取数据批次 {offset}-{min(offset+batch_size, total_count)}")
                            mysql_cursor.execute(batch_query)
                            rows = mysql_cursor.fetchall()
                            debug_print(f"获取到{len(rows)}行数据")
                            
                            if not rows:
                                debug_print("批次中没有数据，跳过")
                                break
                            
                            # 写入PostgreSQL
                            debug_print(f"开始写入{len(rows)}行数据到PostgreSQL...")
                            self._insert_batch_to_postgres(pg_conn, rows, target_table, schema)
                            
                            logger.info(f"已同步 {min(offset+batch_size, total_count)}/{total_count} 行")
                            debug_print(f"批次同步成功: {offset}-{min(offset+batch_size, total_count)}")
                            total_rows += len(rows)
                            break
                        except Exception as e:
                            retry_count += 1
                            error_msg = f"批次同步失败 ({retry_count}/{max_retries}): {str(e)}"
                            debug_print(error_msg)
                            if retry_count >= max_retries:
                                logger.error(f"批次同步失败，已达到最大重试次数: {e}")
                                debug_print(f"批次同步失败，已达到最大重试次数: {e}")
                                raise
                            logger.warning(f"批次同步失败，将重试: {e}")
                            debug_print(f"等待{2}秒后重试...")
                            time.sleep(2)  # 重试前等待2秒
            
            success_msg = f"表 {source_table} -> {target_table} 同步完成，共同步 {total_rows} 行"
            logger.info(success_msg)
            debug_print(success_msg)
            return total_rows
            
        except Exception as e:
            error_msg = f"MySQL到PostgreSQL同步失败: {e}"
            logger.error(error_msg)
            debug_print(error_msg)
            import traceback
            debug_print(f"错误详情: {traceback.format_exc()}")
            raise
        finally:
            debug_print("开始清理资源...")
            # 确保资源被正确释放
            if mysql_conn:
                try:
                    debug_print("关闭MySQL连接...")
                    mysql_conn.close()
                    debug_print("MySQL连接已关闭")
                except Exception as e:
                    logger.warning(f"关闭MySQL连接失败: {e}")
                    debug_print(f"关闭MySQL连接失败: {e}")
            
            if pg_conn:
                try:
                    debug_print("关闭PostgreSQL连接...")
                    # 使用异步方式关闭连接
                    asyncio.get_event_loop().run_until_complete(pg_conn.close())
                    debug_print("PostgreSQL连接已关闭")
                except Exception as e:
                    logger.warning(f"关闭PostgreSQL连接失败: {e}")
                    debug_print(f"关闭PostgreSQL连接失败: {e}")
            debug_print("资源清理完成")
    
    def _validate_config(self, task: ETLTask, source_table: Optional[str], target_table: Optional[str]) -> None:
        """
        验证任务配置
        修复源表和目标表为None的问题
        """
        debug_print(f"开始验证配置 - 任务ID: {task.task_id}, 名称: {task.name}")
        debug_print(f"初始值 - 源表: {source_table}, 目标表: {target_table}")
        
        # 设置默认值标志
        source_table_set = False
        target_table_set = False
        
        if not source_table:
            debug_print("源表名为空，尝试从任务名称中提取")
            # 尝试从任务名称中提取源表名
            if task.name:
                debug_print(f"分析任务名称: {task.name}")
                match = re.search(r'from\s+([\w\.]+)', task.name, re.IGNORECASE)
                if match:
                    source_table = match.group(1)
                    task.config["source_table"] = source_table
                    logger.info(f"从任务名称中提取源表名: {source_table}")
                    debug_print(f"成功从任务名称中提取源表名: {source_table}")
                    source_table_set = True
                else:
                    debug_print("任务名称中未找到'from'模式")
            else:
                debug_print("任务名称为空，无法提取源表名")
            
            # 如果仍然没有源表名，使用默认值
            if not source_table_set:
                source_table = "users"
                task.config["source_table"] = source_table
                logger.warning(f"无法从任务名称中提取源表名，使用默认值: {source_table}")
                debug_print(f"使用默认源表名: {source_table}")
        else:
            debug_print(f"源表名已存在: {source_table}")
        
        if not target_table:
            debug_print("目标表名为空，尝试从任务名称中提取")
            # 尝试从任务名称中提取目标表名
            if task.name:
                debug_print(f"分析任务名称: {task.name}")
                match = re.search(r'to\s+([\w\.]+)', task.name, re.IGNORECASE)
                if match:
                    target_table = match.group(1)
                    task.config["target_table"] = target_table
                    logger.info(f"从任务名称中提取目标表名: {target_table}")
                    debug_print(f"成功从任务名称中提取目标表名: {target_table}")
                    target_table_set = True
                else:
                    debug_print("任务名称中未找到'to'模式")
            else:
                debug_print("任务名称为空，无法提取目标表名")
            
            # 如果仍然没有目标表名，使用源表名作为目标表名
            if not target_table_set and source_table:
                target_table = source_table
                task.config["target_table"] = target_table
                logger.warning(f"无法从任务名称中提取目标表名，使用源表名作为目标表名: {target_table}")
                debug_print(f"使用源表名作为目标表名: {target_table}")
            # 如果源表名也为空，使用默认值
            elif not target_table_set:
                target_table = "users"
                task.config["target_table"] = target_table
                logger.warning(f"无法获取目标表名，使用默认值: {target_table}")
                debug_print(f"使用默认目标表名: {target_table}")
        else:
            debug_print(f"目标表名已存在: {target_table}")
        
        # 更新任务配置
        debug_print("提交配置更新到数据库")
        try:
            self.db.commit()
            debug_print("配置更新成功")
        except Exception as e:
            debug_print(f"配置更新失败: {e}")
            logger.error(f"配置更新失败: {e}")
        
        # 最终检查
        debug_print(f"最终配置 - 源表: {source_table}, 目标表: {target_table}")
        if not source_table or not target_table:
            error_msg = f"源表或目标表名不能为空: source={source_table}, target={target_table}"
            debug_print(f"配置验证失败: {error_msg}")
            raise ValueError(error_msg)
        
        debug_print("配置验证成功")
        return
    
    def _ensure_target_table_exists(self, mysql_conn, pg_conn, source_table, target_table, schema):
        """
        确保目标表存在，如果不存在则根据源表结构创建
        适配asyncpg异步连接
        """
        debug_print(f"确保目标表存在 - 源表: {source_table}, 目标表: {target_table}, Schema: {schema}")
        try:
            # 确保source_table和target_table不为None
            if not source_table or not target_table:
                error_msg = f"源表或目标表名不能为空: source={source_table}, target={target_table}"
                debug_print(error_msg)
                raise ValueError(error_msg)
                
            # 1. 获取源表结构
            debug_print(f"获取源表结构: {source_table}")
            with mysql_conn.cursor() as cursor:
                describe_sql = f"DESCRIBE {source_table}"
                debug_print(f"执行SQL: {describe_sql}")
                cursor.execute(describe_sql)
                columns = cursor.fetchall()
                debug_print(f"获取到{len(columns)}列")
                for i, col in enumerate(columns):
                    debug_print(f"列 {i+1}: {col['Field']} - 类型: {col['Type']} - 可空: {col['Null']} - 键: {col['Key']}")
            
            if not columns:
                error_msg = f"无法获取源表结构: {source_table}"
                debug_print(error_msg)
                raise ValueError(error_msg)
            
            # 2. 检查目标表是否存在
            # 提取表名（不含schema）
            table_name = target_table.split('.')[-1]
            debug_print(f"目标表名(不含schema): {table_name}")
            
            # 使用asyncpg异步方式检查schema和表
            import asyncio
            
            # 检查schema是否存在，不存在则创建
            debug_print(f"检查schema是否存在: {schema}")
            schema_check_sql = f"SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname = '{schema}')"
            debug_print(f"执行SQL: {schema_check_sql}")
            schema_exists = asyncio.get_event_loop().run_until_complete(
                pg_conn.fetchval(schema_check_sql)
            )
            debug_print(f"Schema {schema} 存在: {schema_exists}")
            
            if not schema_exists:
                debug_print(f"创建Schema: {schema}")
                create_schema_sql = f"CREATE SCHEMA IF NOT EXISTS {schema}"
                debug_print(f"执行SQL: {create_schema_sql}")
                asyncio.get_event_loop().run_until_complete(
                    pg_conn.execute(create_schema_sql)
                )
                debug_print(f"Schema {schema} 创建成功")
                
                # 检查表是否存在
                table_check_sql = f"""
                    SELECT EXISTS(
                        SELECT 1 
                        FROM information_schema.tables 
                        WHERE table_schema = '{schema}' AND table_name = '{table_name}'
                    )
                """
                debug_print(f"检查表是否存在: {schema}.{table_name}")
                debug_print(f"执行SQL: {table_check_sql}")
                table_exists = asyncio.get_event_loop().run_until_complete(
                    pg_conn.fetchval(table_check_sql)
                )
                debug_print(f"表 {schema}.{table_name} 存在: {table_exists}")
                
                if not table_exists:
                    # 3. 如果不存在，创建表
                    debug_print(f"开始生成建表SQL")
                    create_table_sql = self._generate_create_table_sql(columns, schema, table_name)
                    debug_print(f"生成的建表SQL:\n{create_table_sql}")
                    debug_print(f"执行建表SQL")
                    asyncio.get_event_loop().run_until_complete(
                        pg_conn.execute(create_table_sql)
                    )
                    success_msg = f"已创建目标表: {schema}.{table_name}"
                    logger.info(success_msg)
                    debug_print(success_msg)
                else:
                    debug_print(f"表 {schema}.{table_name} 已存在，无需创建")
            else:
                debug_print(f"Schema {schema} 已存在，检查表是否存在")
                # 检查表是否存在
                table_check_sql = f"""
                    SELECT EXISTS(
                        SELECT 1 
                        FROM information_schema.tables 
                        WHERE table_schema = '{schema}' AND table_name = '{table_name}'
                    )
                """
                debug_print(f"检查表是否存在: {schema}.{table_name}")
                debug_print(f"执行SQL: {table_check_sql}")
                table_exists = asyncio.get_event_loop().run_until_complete(
                    pg_conn.fetchval(table_check_sql)
                )
                debug_print(f"表 {schema}.{table_name} 存在: {table_exists}")
                
                if not table_exists:
                    # 如果不存在，创建表
                    debug_print(f"开始生成建表SQL")
                    create_table_sql = self._generate_create_table_sql(columns, schema, table_name)
                    debug_print(f"生成的建表SQL:\n{create_table_sql}")
                    debug_print(f"执行建表SQL")
                    asyncio.get_event_loop().run_until_complete(
                        pg_conn.execute(create_table_sql)
                    )
                    success_msg = f"已创建目标表: {schema}.{table_name}"
                    logger.info(success_msg)
                    debug_print(success_msg)
                else:
                    debug_print(f"表 {schema}.{table_name} 已存在，无需创建")
            
            debug_print(f"目标表检查/创建完成: {schema}.{table_name}")
        except Exception as e:
            error_msg = f"确保目标表存在失败: {e}"
            logger.error(error_msg)
            debug_print(error_msg)
            import traceback
            debug_print(f"错误详情: {traceback.format_exc()}")
            raise
    
    def _generate_create_table_sql(self, mysql_columns, schema, table_name):
        """
        根据MySQL表结构生成PostgreSQL建表SQL
        """
        debug_print(f"开始生成PostgreSQL建表SQL - Schema: {schema}, 表名: {table_name}")
        debug_print(f"MySQL列数: {len(mysql_columns)}")
        
        # MySQL到PostgreSQL类型映射
        type_mapping = {
            'int': 'integer',
            'bigint': 'bigint',
            'tinyint': 'smallint',
            'smallint': 'smallint',
            'mediumint': 'integer',
            'float': 'real',
            'double': 'double precision',
            'decimal': 'numeric',
            'char': 'character',
            'varchar': 'character varying',
            'text': 'text',
            'tinytext': 'text',
            'mediumtext': 'text',
            'longtext': 'text',
            'date': 'date',
            'datetime': 'timestamp',
            'timestamp': 'timestamp',
            'time': 'time',
            'year': 'integer',
            'blob': 'bytea',
            'tinyblob': 'bytea',
            'mediumblob': 'bytea',
            'longblob': 'bytea',
            'enum': 'character varying',
            'set': 'character varying',
            'json': 'jsonb'
        }
        debug_print("已加载MySQL到PostgreSQL类型映射")
        
        column_defs = []
        primary_key = None
        
        debug_print("开始处理每一列...")
        for i, column in enumerate(mysql_columns):
            column_name = column['Field']
            mysql_type = column['Type'].lower()
            debug_print(f"处理列 {i+1}/{len(mysql_columns)}: {column_name}, MySQL类型: {mysql_type}")
            
            # 提取基本类型和长度
            type_match = re.match(r'([a-z]+)(\(\d+\))?', mysql_type)
            if type_match:
                base_type = type_match.group(1)
                length = type_match.group(2) or ''
                debug_print(f"  提取的基本类型: {base_type}, 长度: {length}")
            else:
                base_type = mysql_type
                length = ''
                debug_print(f"  无法提取类型模式，使用整个类型: {base_type}")
            
            # 映射到PostgreSQL类型
            pg_type = type_mapping.get(base_type, 'text')
            debug_print(f"  映射到PostgreSQL类型: {pg_type}")
            if length and pg_type in ['character', 'character varying']:
                pg_type = f"{pg_type}{length}"
                debug_print(f"  添加长度后的PostgreSQL类型: {pg_type}")
            
            # 处理NULL约束
            null_constraint = "NULL" if column['Null'] == "YES" else "NOT NULL"
            debug_print(f"  NULL约束: {null_constraint}")
            
            # 处理默认值
            default_value = ""
            if column['Default'] is not None:
                if pg_type in ['integer', 'bigint', 'smallint', 'real', 'double precision', 'numeric']:
                    default_value = f"DEFAULT {column['Default']}"
                else:
                    default_value = f"DEFAULT '{column['Default']}'"
                debug_print(f"  默认值: {default_value}")
            
            # 处理主键
            if column['Key'] == 'PRI':
                primary_key = column_name
                debug_print(f"  检测到主键: {primary_key}")
            
            column_def = f"\"{column_name}\" {pg_type} {null_constraint} {default_value}".strip()
            debug_print(f"  列定义: {column_def}")
            column_defs.append(column_def)
        
        # 添加import_time字段
        import_time_def = '"import_time" timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP'
        debug_print(f"添加import_time字段: {import_time_def}")
        column_defs.append(import_time_def)
        
        # 构建CREATE TABLE语句
        create_table_sql = f"CREATE TABLE IF NOT EXISTS \"{schema}\".\"{table_name}\" (\n"
        create_table_sql += ",\n".join(column_defs)
        
        # 添加主键约束
        if primary_key:
            primary_key_clause = f",\nPRIMARY KEY (\"{primary_key}\")\n"
            debug_print(f"添加主键约束: {primary_key_clause.strip()}")
            create_table_sql += primary_key_clause
        else:
            debug_print("没有主键约束")
            create_table_sql += "\n"
        
        create_table_sql += ");"
        
        debug_print(f"生成的CREATE TABLE SQL语句长度: {len(create_table_sql)}字符")
        return create_table_sql
    
    def _insert_batch_to_postgres(self, pg_conn, rows, target_table, schema):
        """
        将一批数据插入到PostgreSQL表中
        适配asyncpg异步连接
        """
        debug_print(f"开始将数据批量插入PostgreSQL - 目标表: {schema}.{target_table}, 行数: {len(rows) if rows else 0}")
        if not rows:
            debug_print("没有数据需要插入，直接返回")
            return
        
        # 确保target_table不为None
        if not target_table:
            error_msg = "目标表名不能为空"
            debug_print(error_msg)
            raise ValueError(error_msg)
            
        # 提取表名（不含schema）
        table_name = target_table.split('.')[-1]
        debug_print(f"目标表名(不含schema): {table_name}")
        
        # 获取列名
        columns = list(rows[0].keys())
        debug_print(f"源数据列数: {len(columns)}")
        debug_print(f"列名: {', '.join(columns)}")
        
        # 添加import_time字段
        import_time = datetime.now()  # 使用datetime对象而不是字符串
        debug_print(f"添加import_time字段: {import_time}")
        columns.append('import_time')
        
        # 构建列名部分
        column_names = [f'"{col}"' for col in columns]
        column_part = ", ".join(column_names)
        debug_print(f"列名部分: {column_part}")
        
        # 构建参数占位符 - asyncpg使用$1, $2, $3格式
        placeholders = [f"${i+1}" for i in range(len(columns))]
        placeholder_part = ", ".join(placeholders)
        debug_print(f"参数占位符部分: {placeholder_part}")
        
        # 构建INSERT语句
        insert_sql = f"INSERT INTO \"{schema}\".\"{table_name}\" ({column_part}) VALUES ({placeholder_part})"
        debug_print(f"构建的INSERT语句: {insert_sql}")
        
        # 准备数据
        import asyncio
        debug_print("开始准备异步插入...")
        
        # 使用asyncpg批量插入
        try:
            # 创建批量插入任务
            async def insert_all():
                debug_print(f"开始事务，准备插入{len(rows)}行数据")
                # 开始事务
                async with pg_conn.transaction():
                    for i, row in enumerate(rows):
                        if i % 100 == 0 or i == len(rows) - 1:
                            debug_print(f"处理第{i+1}/{len(rows)}行数据")
                        
                        # 准备一行数据
                        row_values = []
                        for col in columns:
                            if col == 'import_time':
                                row_values.append(import_time)
                            else:
                                # 处理JSON字段
                                value = row.get(col)
                                # 如果值是字典或列表，将其转换为JSON字符串
                                if isinstance(value, (dict, list)):
                                    value = json.dumps(value)
                                    if i == 0:  # 只在第一行记录日志
                                        debug_print(f"列 {col} 检测到Python对象，已转换为JSON字符串")
                                # 如果值是字符串且看起来像JSON，保持原样
                                # PostgreSQL会自动处理JSON字符串
                                elif isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                                    if i == 0:  # 只在第一行记录日志
                                        debug_print(f"列 {col} 检测到JSON字符串格式")
                                # 处理日期时间字符串
                                elif isinstance(value, str) and re.match(r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}', value):
                                    try:
                                        value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                                        if i == 0:  # 只在第一行记录日志
                                            debug_print(f"列 {col} 检测到日期时间字符串，已转换为datetime对象: {value}")
                                    except ValueError:
                                        if i == 0:  # 只在第一行记录日志
                                            debug_print(f"列 {col} 日期时间字符串格式不正确，保持原样: {value}")
                                row_values.append(value)
                        
                        # 执行插入
                        if i == 0:  # 只在第一行记录日志
                            debug_print(f"第1行数据值类型: {[type(v).__name__ for v in row_values]}")
                        await pg_conn.execute(insert_sql, *row_values)
                debug_print(f"事务完成，成功插入{len(rows)}行数据")
            
            # 运行批量插入
            debug_print("开始执行异步插入任务")
            asyncio.get_event_loop().run_until_complete(insert_all())
            debug_print("异步插入任务完成")
            
        except Exception as e:
            error_msg = f"插入数据到PostgreSQL失败: {e}"
            debug_print(error_msg)
            debug_print(f"错误详情: {traceback.format_exc() if 'traceback' in globals() else ''}")
            # asyncpg会自动处理事务回滚
            raise Exception(error_msg)