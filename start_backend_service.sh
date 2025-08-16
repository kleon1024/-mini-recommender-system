#!/bin/bash

# 迷你推荐系统后端服务启动脚本（不安装依赖）

echo "===== 启动迷你推荐系统后端服务 ====="

# 定义颜色
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

# 进入后端目录
cd "$(dirname "$0")/backend" || exit

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo -e "${RED}错误: 虚拟环境不存在，请先运行 ./install_backend_deps.sh 安装依赖${NC}"
    exit 1
fi

# 激活虚拟环境
echo -e "${YELLOW}激活虚拟环境...${NC}"
source venv/bin/activate

# 启动后端服务
echo -e "${YELLOW}启动后端服务...${NC}"
python main.py