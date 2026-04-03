#!/bin/zsh
# 赛博印钞机 Pro V2.3 一键启动脚本
# 自动检查环境、安装依赖、启动面板，小白零门槛

# 配置项
APP_NAME="赛博印钞机 Pro V2.3"
PYTHON_MIN_VERSION="3.10.0"
REQUIRED_FILES=("requirements.txt" "web_panel_ultra.py" "builtin_claude_core")
PORT=8502

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 标题
clear
echo -e "${GREEN}"
echo "============================================="
echo "  🚀 赛博印钞机 Pro V2.3 一键启动器"
echo "  基于 Claude Code 原生实现 | 工业级网文创作系统"
echo "============================================="
echo -e "${NC}"

# 1. 检查工作目录
info "检查项目目录..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || { error "无法进入项目目录"; exit 1; }

# 检查必要文件
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -e "$file" ]; then
        error "必要文件缺失：$file，请确认在正确的项目目录"
        exit 1
    fi
done
success "项目目录检查通过"

# 2. 检查 Python 版本
info "检查 Python 环境..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    error "未找到 Python，请先安装 Python 3.10+"
    info "安装命令：brew install python3"
    exit 1
fi

# 版本检查
PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print('.'.join(map(str, sys.version_info[:3])))")
info "当前 Python 版本：$PYTHON_VERSION"

# 版本比较
version_compare() {
    [ "$1" = "$2" ] && return 0
    local IFS=.
    local i ver1=($1) ver2=($2)
    for ((i=0; i<${#ver1[@]}; i++)); do
        if [[ ${ver1[i]} -lt ${ver2[i]} ]]; then
            return 1
        elif [[ ${ver1[i]} -gt ${ver2[i]} ]]; then
            return 0
        fi
    done
    return 0
}

if ! version_compare "$PYTHON_VERSION" "$PYTHON_MIN_VERSION"; then
    error "Python 版本过低，需要至少 $PYTHON_MIN_VERSION，当前版本 $PYTHON_VERSION"
    info "升级命令：brew upgrade python3"
    exit 1
fi
success "Python 环境检查通过"

# 3. 检查 Node.js 环境
info "检查 Node.js 环境..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node -v | sed 's/v//')
    info "当前 Node.js 版本：$NODE_VERSION"
    success "Node.js 环境检查通过"
else
    warning "未找到 Node.js，x-crawl 爬虫功能将不可用"
    info "如需使用爬虫功能，请安装 Node.js：brew install node"
fi

# 4. 创建/激活虚拟环境
info "配置 Python 虚拟环境..."
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    info "首次启动，创建虚拟环境..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        error "虚拟环境创建失败"
        exit 1
    fi
    success "虚拟环境创建完成"
fi

# 激活虚拟环境
info "激活虚拟环境..."
source "$VENV_DIR/bin/activate"
if [ $? -ne 0 ]; then
    error "虚拟环境激活失败"
    exit 1
fi
success "虚拟环境激活完成"

# 5. 安装 Python 依赖
info "检查 Python 依赖..."
pip install -r requirements.txt -q
if [ $? -ne 0 ]; then
    error "Python 依赖安装失败"
    exit 1
fi
success "Python 依赖检查/安装完成"

# 6. 安装 Node.js 依赖
if command -v npm &> /dev/null; then
    info "检查 Node.js 依赖..."
    npm install --silent
    if [ $? -ne 0 ]; then
        warning "Node.js 依赖安装失败，爬虫功能可能不可用"
    else
        success "Node.js 依赖检查/安装完成"
    fi
fi

# 7. 检查环境变量配置
info "检查环境变量配置..."
if [ ! -f ".env" ]; then
    warning "未找到 .env 配置文件，已自动从模板复制"
    cp .env.example .env
    info "请编辑 .env 文件填写你的大模型 API Key，否则核心功能不可用"
else
    # 检查核心配置
    if grep -q "LLM_API_KEY=" .env && ! grep -q "LLM_API_KEY=你的大模型_API_Key" .env; then
        success "LLM_API_KEY 已配置"
    else
        warning "LLM_API_KEY 未配置，核心生成功能将不可用"
    fi
    if grep -q "LLM_BASE_URL=" .env; then
        success "LLM_BASE_URL 已配置"
    else
        warning "LLM_BASE_URL 未配置"
    fi
fi

# 8. 启动可视化面板
echo ""
success "所有环境检查通过！"
info "正在启动可视化面板..."
info "面板地址：http://localhost:$PORT"
info "按 Ctrl+C 停止面板"
echo "============================================="
echo ""

# 启动 Streamlit
$PYTHON_CMD -m streamlit run web_panel_ultra.py --server.port $PORT --server.address 0.0.0.0

# 退出处理
if [ $? -eq 0 ]; then
    success "面板已正常退出"
else
    error "面板启动失败，请检查错误日志"
    exit 1
fi
