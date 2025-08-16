#!/bin/bash

# 迷你推荐系统后端依赖安装脚本

echo "===== 安装迷你推荐系统后端依赖 ====="

# 定义颜色
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

# 进入后端目录
cd "$(dirname "$0")/backend" || exit

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}创建Python虚拟环境...${NC}"
    python -m venv venv --without-pip
fi

# 激活虚拟环境
echo -e "${YELLOW}激活虚拟环境...${NC}"
source venv/bin/activate

curl -sS https://bootstrap.pypa.io/get-pip.py | python

# 安装依赖
echo -e "${YELLOW}安装依赖...${NC}"
# 先确保pip、setuptools和wheel是最新的
pip install --upgrade pip setuptools wheel
# 安装所有依赖
pip install -r requirements.txt --no-deps

echo -e "${GREEN}依赖安装完成!${NC}"