#!/bin/bash

# ============================================
# OpenMars 终极一键启动脚本
# 全中文提示、自动环境修复、错误兜底
# ============================================

clear
echo "============================================"
echo "  🚀 OpenMars - 终极一键启动"
echo "============================================"
echo ""

# 1. 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
echo "📍 项目目录: $SCRIPT_DIR"
echo ""

# 2. 检查 Python 版本
echo "🔍 检查 Python 环境..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PYTHON_VERSION=$($PYTHON_CMD --version | cut -d' ' -f2)
    echo "✅ Python $PYTHON_VERSION 已找到"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    PYTHON_VERSION=$($PYTHON_CMD --version | cut -d' ' -f2)
    echo "✅ Python $PYTHON_VERSION 已找到"
else
    echo "❌ 未找到 Python！请先安装 Python 3.8+"
    echo "💡 下载地址: https://www.python.org/downloads/"
    read -p "按回车键退出..."
    exit 1
fi
echo ""

# 3. 检查并创建虚拟环境
echo "🔧 检查虚拟环境..."
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    $PYTHON_CMD -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ 虚拟环境创建失败！"
        read -p "按回车键退出..."
        exit 1
    fi
    echo "✅ 虚拟环境创建成功"
else
    echo "✅ 虚拟环境已存在"
    
    # 检查虚拟环境是否损坏
    if [ ! -f "venv/bin/activate" ]; then
        echo "⚠️  虚拟环境已损坏，正在重建..."
        rm -rf venv
        $PYTHON_CMD -m venv venv
        echo "✅ 虚拟环境重建成功"
    fi
fi
echo ""

# 4. 激活虚拟环境
echo "🔌 激活虚拟环境..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ 虚拟环境激活失败！"
    read -p "按回车键退出..."
    exit 1
fi
echo "✅ 虚拟环境已激活"
echo ""

# 5. 检查并安装依赖
echo "📦 检查依赖..."
pip install -q -r requirements.txt
if [ $? -ne 0 ]; then
    echo "⚠️  依赖安装有问题，尝试重新安装..."
    pip install -r requirements.txt
fi
echo "✅ 依赖检查完成"
echo ""

# 6. 检查 .env 文件
echo "🔐 检查配置文件..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "📝 复制 .env.example 为 .env..."
        cp .env.example .env
        echo "⚠️  请编辑 .env 文件配置您的 API Key"
    else
        echo "❌ 未找到 .env.example 文件！"
    fi
else
    echo "✅ 配置文件已存在"
fi
echo ""

# 7. 检查端口占用
echo "🌐 检查端口..."
PORT=8501
if lsof -Pi :$PORT -sTCP:LISTEN -t &> /dev/null; then
    echo "⚠️  端口 $PORT 已被占用，正在释放..."
    lsof -ti :$PORT | xargs kill -9 2>/dev/null
    sleep 2
fi
echo "✅ 端口 $PORT 准备就绪"
echo ""

# 8. 获取本机 IP 地址
echo "📡 获取网络地址..."
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -n1)
echo "✅ 本地访问: http://localhost:$PORT"
if [ ! -z "$LOCAL_IP" ]; then
    echo "✅ 局域网访问: http://$LOCAL_IP:$PORT"
fi
echo ""

# 9. 自动打开浏览器
echo "🌍 正在打开浏览器..."
if command -v open &> /dev/null; then
    open "http://localhost:$PORT"
elif command -v xdg-open &> /dev/null; then
    xdg-open "http://localhost:$PORT"
fi

# 10. 启动 Streamlit
echo ""
echo "============================================"
echo "  🎉 启动 OpenMars Web 面板"
echo "============================================"
echo "💡 按 Ctrl+C 停止服务"
echo ""

streamlit run web_panel.py --server.port $PORT --server.address 0.0.0.0
