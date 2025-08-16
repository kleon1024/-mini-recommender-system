#!/bin/bash

# 迷你推荐系统前端启动脚本（不依赖Docker）

echo "===== 启动迷你推荐系统前端 ====="

# 检查Node.js是否安装
if ! command -v node &> /dev/null; then
    echo "错误: Node.js未安装，请先安装Node.js"
    exit 1
fi

# 定义颜色
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

# 进入前端目录
cd "$(dirname "$0")/frontend" || exit

# 安装依赖
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}安装依赖...${NC}"
    npm install
else
    echo -e "${GREEN}依赖已安装，跳过安装步骤...${NC}"
fi

# 启动前端服务
echo -e "${YELLOW}启动前端服务...${NC}"
npm start