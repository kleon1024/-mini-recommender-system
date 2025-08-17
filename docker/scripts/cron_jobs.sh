#!/bin/bash

# 数据分析系统定时任务脚本
# 用于定期执行数据同步和ETL流程

# 日志目录
LOG_DIR="/var/log/data_analysis"
mkdir -p "$LOG_DIR"

# 时间戳
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# 脚本目录
SCRIPT_DIR="$(dirname "$0")"

# 日志文件
LOG_FILE="$LOG_DIR/etl_$TIMESTAMP.log"

# 函数：执行全量同步
full_sync() {
    echo "开始执行全量同步..." | tee -a "$LOG_FILE"
    python "$SCRIPT_DIR/mysql_to_postgres.py" --full >> "$LOG_FILE" 2>&1
    if [ $? -eq 0 ]; then
        echo "全量同步完成" | tee -a "$LOG_FILE"
    else
        echo "全量同步失败，请查看日志文件：$LOG_FILE" | tee -a "$LOG_FILE"
    fi
}

# 函数：执行增量同步
incremental_sync() {
    echo "开始执行增量同步..." | tee -a "$LOG_FILE"
    python "$SCRIPT_DIR/mysql_to_postgres.py" >> "$LOG_FILE" 2>&1
    if [ $? -eq 0 ]; then
        echo "增量同步完成" | tee -a "$LOG_FILE"
    else
        echo "增量同步失败，请查看日志文件：$LOG_FILE" | tee -a "$LOG_FILE"
    fi
}

# 函数：仅执行ETL流程
etl_only() {
    echo "开始执行ETL流程..." | tee -a "$LOG_FILE"
    python "$SCRIPT_DIR/mysql_to_postgres.py" --etl-only >> "$LOG_FILE" 2>&1
    if [ $? -eq 0 ]; then
        echo "ETL流程完成" | tee -a "$LOG_FILE"
    else
        echo "ETL流程失败，请查看日志文件：$LOG_FILE" | tee -a "$LOG_FILE"
    fi
}

# 函数：仅执行数据同步
sync_only() {
    echo "开始执行数据同步..." | tee -a "$LOG_FILE"
    python "$SCRIPT_DIR/mysql_to_postgres.py" --sync-only >> "$LOG_FILE" 2>&1
    if [ $? -eq 0 ]; then
        echo "数据同步完成" | tee -a "$LOG_FILE"
    else
        echo "数据同步失败，请查看日志文件：$LOG_FILE" | tee -a "$LOG_FILE"
    fi
}

# 函数：清理旧日志
clean_old_logs() {
    echo "清理7天前的日志文件..." | tee -a "$LOG_FILE"
    find "$LOG_DIR" -name "etl_*.log" -type f -mtime +7 -delete
    echo "日志清理完成" | tee -a "$LOG_FILE"
}

# 主函数
main() {
    echo "===== 数据分析系统定时任务开始 $(date) ====="  | tee -a "$LOG_FILE"
    
    # 根据参数执行不同的任务
    case "$1" in
        "full")
            full_sync
            ;;
        "etl")
            etl_only
            ;;
        "sync")
            sync_only
            ;;
        *)
            incremental_sync
            ;;
    esac
    
    # 清理旧日志
    clean_old_logs
    
    echo "===== 数据分析系统定时任务结束 $(date) ====="  | tee -a "$LOG_FILE"
}

# 执行主函数
main "$@"