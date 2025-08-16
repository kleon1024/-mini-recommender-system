#!/bin/bash

# 迷你推荐系统后端启动脚本（包装脚本）

# 定义颜色
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

echo "===== 迷你推荐系统后端启动选项 ====="
echo -e "${YELLOW}1. 安装依赖并启动服务${NC}"
echo -e "${YELLOW}2. 仅启动服务（不安装依赖）${NC}"
echo -e "${YELLOW}3. 仅安装依赖（不启动服务）${NC}"

read -p "请选择操作 [1-3]: " choice

case $choice in
    1)
        # 安装依赖并启动服务
        echo -e "${GREEN}执行: 安装依赖并启动服务${NC}"
        bash "$(dirname "$0")/install_backend_deps.sh" && bash "$(dirname "$0")/start_backend_service.sh"
        ;;
    2)
        # 仅启动服务
        echo -e "${GREEN}执行: 仅启动服务${NC}"
        bash "$(dirname "$0")/start_backend_service.sh"
        ;;
    3)
        # 仅安装依赖
        echo -e "${GREEN}执行: 仅安装依赖${NC}"
        bash "$(dirname "$0")/install_backend_deps.sh"
        ;;
    *)
        echo -e "${RED}错误: 无效的选择${NC}"
        exit 1
        ;;
esac