
#!/bin/zsh
# 赛博印钞机 Pro 终极优化版 - Mac一键启动器
# 零依赖、开箱即用，自动配置环境，启动可视化面板

# 获取脚本所在目录
APP_DIR="$(cd "$(dirname "$0")" &amp;&amp; pwd)"
cd "$APP_DIR" || exit 1

echo "🚀 赛博印钞机 Pro 终极优化版"
echo "📂 应用目录：$APP_DIR"
echo "="*50

# 1. 检查Python环境
echo "🔍 正在检查Python环境..."
if ! command -v python3 &amp;&gt; /dev/null; then
    echo "❌ 未找到Python3，正在自动安装..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    brew install python@3.10
fi
echo "✅ Python环境就绪"

# 2. 创建并激活虚拟环境
echo "🔧 正在配置虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
echo "✅ 虚拟环境已激活"

# 3. 安装依赖
echo "📦 正在安装依赖..."
pip install -r requirements.txt -q
echo "✅ 依赖安装完成"

# 4. 启动Streamlit可视化面板
echo "🌐 正在启动可视化面板..."
echo "✅ 面板启动后会自动打开浏览器"
echo "⚠️  如果浏览器没有自动打开，请手动访问：http://localhost:8502"
echo "🛑  按 Ctrl+C 可以停止服务"
echo "="*50

streamlit run web_panel_ultra.py --server.port 8502 --browser.gatherUsageStats false
