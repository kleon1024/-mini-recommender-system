#!/bin/bash

# 初始化ETL任务脚本
# 该脚本用于执行init_etl_tasks.py，将mysql_to_postgres.py中的ETL任务转化为ETL任务记录并插入到MySQL数据库中

# 确保Python环境已激活
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 安装必要的依赖
pip install pymysql

# 执行初始化脚本
python init_etl_tasks.py "$@"

# 输出完成信息
echo "ETL任务初始化完成！"