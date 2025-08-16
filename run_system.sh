#!/bin/bash

# 迷你推荐系统启动脚本

echo "===== 迷你推荐系统启动脚本 ====="

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "错误: Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 定义颜色
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

# 显示菜单
show_menu() {
    echo -e "\n${YELLOW}请选择操作:${NC}"
    echo "1. 启动系统"
    echo "2. 运行后端单元测试"
    echo "3. 运行集成测试"
    echo "4. 停止系统"
    echo "5. 退出"
    echo -n "请输入选项 [1-5]: "
    read -r option
}

# 启动系统
start_system() {
    echo -e "\n${YELLOW}正在启动迷你推荐系统...${NC}"
    cd "$(dirname "$0")/docker" || exit
    docker-compose up -d
    
    # 等待系统启动
    echo -e "\n${YELLOW}等待系统启动...${NC}"
    sleep 5
    
    # 检查服务是否正常运行
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        echo -e "${GREEN}后端API服务已启动!${NC}"
    else
        echo -e "${RED}后端API服务启动失败!${NC}"
    fi
    
    # 检查前端服务
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q "200\|304"; then
        echo -e "${GREEN}前端服务已启动!${NC}"
    else
        echo -e "${RED}前端服务启动失败!${NC}"
    fi
    
    echo -e "\n${GREEN}系统已启动:${NC}"
    echo -e "- 前端: ${YELLOW}http://localhost:3000${NC}"
    echo -e "- 后端API: ${YELLOW}http://localhost:8000${NC}"
    echo -e "- 数据库管理: ${YELLOW}http://localhost:8080${NC}"
}

# 运行后端单元测试
run_backend_tests() {
    echo -e "\n${YELLOW}运行后端单元测试...${NC}"
    cd "$(dirname "$0")" || exit
    
    # 使用Docker运行测试
    docker-compose -f docker/docker-compose.yml exec backend python -m unittest discover -s /app/tests/backend
    
    if [ $? -eq 0 ]; then
        echo -e "\n${GREEN}后端单元测试通过!${NC}"
    else
        echo -e "\n${RED}后端单元测试失败!${NC}"
    fi
}

# 运行集成测试
run_integration_tests() {
    echo -e "\n${YELLOW}运行集成测试...${NC}"
    echo -e "${YELLOW}注意: 请确保系统已经启动${NC}"
    cd "$(dirname "$0")" || exit
    
    # 使用Docker运行集成测试
    docker-compose -f docker/docker-compose.yml exec backend python -m unittest discover -s /app/tests/integration
    
    if [ $? -eq 0 ]; then
        echo -e "\n${GREEN}集成测试通过!${NC}"
    else
        echo -e "\n${RED}集成测试失败!${NC}"
    fi
}

# 停止系统
stop_system() {
    echo -e "\n${YELLOW}正在停止迷你推荐系统...${NC}"
    cd "$(dirname "$0")/docker" || exit
    docker-compose down
    echo -e "${GREEN}系统已停止${NC}"
}

# 主循环
while true; do
    show_menu
    case $option in
        1) start_system ;;
        2) run_backend_tests ;;
        3) run_integration_tests ;;
        4) stop_system ;;
        5) echo -e "\n${GREEN}再见!${NC}"; exit 0 ;;
        *) echo -e "\n${RED}无效选项，请重新选择${NC}" ;;
    esac
    
    echo -e "\n按Enter键继续..."
    read -r
done