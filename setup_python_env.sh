#!/bin/bash

# 迷你推荐系统Python环境设置脚本

# 定义颜色
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

echo -e "${YELLOW}===== 设置迷你推荐系统Python环境 =====${NC}"

# 检查当前Python版本
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "当前Python版本: ${GREEN}${PYTHON_VERSION}${NC}"

# 进入后端目录
cd "$(dirname "$0")/backend" || exit

# 删除现有虚拟环境（如果存在）
if [ -d "venv" ]; then
    echo -e "${YELLOW}删除现有虚拟环境...${NC}"
    rm -rf venv
fi

# 创建新的虚拟环境
echo -e "${YELLOW}创建新的虚拟环境...${NC}"
python3 -m venv venv

# 激活虚拟环境
echo -e "${YELLOW}激活虚拟环境...${NC}"
source venv/bin/activate

# 升级pip、setuptools和wheel
echo -e "${YELLOW}升级pip、setuptools和wheel...${NC}"
pip install --upgrade pip setuptools wheel

# 设置环境变量，优先使用二进制包
export PIP_PREFER_BINARY=1

# 安装其他依赖
echo -e "${YELLOW}安装其他依赖...${NC}"
pip install -r requirements.txt --no-deps

# 验证安装
echo -e "${YELLOW}验证安装...${NC}"
if python -c "import fastapi, numpy, pandas, torch" &> /dev/null; then
    echo -e "${GREEN}环境设置成功!${NC}"
    echo -e "使用 ${YELLOW}source backend/venv/bin/activate${NC} 激活环境"
    echo -e "使用 ${YELLOW}python backend/main.py${NC} 启动服务"
else
    echo -e "${RED}环境设置失败，请检查错误信息${NC}"
    exit 1
fi