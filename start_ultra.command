
#!/bin/bash
# 赛博印钞机 Pro Ultra 一键启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

echo "========================================="
echo "  赛博印钞机 Pro Ultra"
echo "  v2.0.0"
echo "========================================="
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未找到 Python3"
    echo "请先安装 Python 3.10+"
    exit 1
fi

echo "✅ Python 版本检查通过"
python3 --version

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 首次运行，正在创建虚拟环境..."
    python3 -m venv venv
    echo "✅ 虚拟环境创建完成"
fi

# 激活虚拟环境
echo ""
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo ""
echo "📦 检查并安装依赖..."
pip install -q -r requirements.txt
echo "✅ 依赖安装完成"

# 创建必要的目录
mkdir -p logs
mkdir -p workspaces/default
mkdir -p configs

echo ""
echo "🚀 启动应用..."
echo ""
echo "应用将在浏览器中打开..."
echo "如果遇到问题，请查看 logs/ 目录下的日志文件"
echo ""

python3 desktop_main_ultra.py

