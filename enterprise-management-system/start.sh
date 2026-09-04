#!/bin/bash

# 企业员工管理系统启动脚本

echo "========================================="
echo "企业员工管理系统启动脚本"
echo "========================================="

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到Python3，请先安装Python 3.8+"
    exit 1
fi

# 检查PostgreSQL是否安装
if ! command -v psql &> /dev/null; then
    echo "错误：未找到PostgreSQL，请先安装PostgreSQL 12+"
    exit 1
fi

# 创建虚拟环境
echo "正在创建Python虚拟环境..."
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "正在安装Python依赖..."
pip install -r requirements.txt

# 初始化数据库
echo "正在初始化数据库..."
psql -U postgres -f database.sql

# 初始化应用数据库
echo "正在初始化应用数据..."
flask init-db

# 启动应用
echo "正在启动应用..."
echo "应用将在 http://localhost:5000 启动"
echo "默认管理员账号：admin"
echo "默认管理员密码：admin123"
echo "========================================="

flask run --host=0.0.0.0 --port=5000