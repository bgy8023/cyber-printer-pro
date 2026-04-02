
#!/bin/zsh
# 赛博印钞机 Pro 终极优化版 - Mac一键启动器
# 零依赖、开箱即用，自动配置环境，启动可视化面板

# 获取脚本所在目录
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR" || exit 1

echo "🚀 赛博印钞机 Pro 终极优化版"
echo "📂 应用目录：$APP_DIR"
echo "="*50

# 1. 检查Python环境
echo "🔍 正在检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3，正在自动安装..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    brew install python@3.10
fi
echo "✅ Python环境就绪"

# 2. 检查Node.js环境
echo "🔍 正在检查Node.js环境..."
if ! command -v node &> /dev/null; then
    echo "❌ 未找到Node.js，正在自动安装..."
    if command -v brew &> /dev/null; then
        brew install node
    else
        echo "⚠️  未找到Homebrew，尝试使用其他方式安装Node.js..."
        curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
        apt-get install -y nodejs
    fi
fi
echo "✅ Node.js环境就绪"

# 3. 检查npm环境
echo "🔍 正在检查npm环境..."
if ! command -v npm &> /dev/null; then
    echo "❌ 未找到npm，正在自动安装..."
    if command -v brew &> /dev/null; then
        brew install npm
    else
        echo "⚠️  未找到Homebrew，尝试使用其他方式安装npm..."
        curl -fsSL https://npmjs.org/install.sh | sh
    fi
fi
echo "✅ npm环境就绪"

# 4. 安装Node.js依赖
echo "📦 正在安装Node.js依赖..."
if [ -f "package.json" ]; then
    npm install -q
    echo "✅ Node.js依赖安装完成"
else
    echo "⚠️  未找到package.json文件，跳过Node.js依赖安装"
fi

# 5. 创建并激活虚拟环境
echo "🔧 正在配置虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
echo "✅ 虚拟环境已激活"

# 6. 安装Python依赖
echo "📦 正在安装Python依赖..."
pip install -r requirements.txt -q
echo "✅ Python依赖安装完成"

# 7. 启动Streamlit可视化面板
echo "🌐 正在启动可视化面板..."
echo "✅ 面板启动后会自动打开浏览器"
echo "⚠️  如果浏览器没有自动打开，请手动访问：http://localhost:8502"
echo "🛑  按 Ctrl+C 可以停止服务"
echo "="*50

streamlit run web_panel_ultra.py --server.port 8502 --browser.gatherUsageStats false
