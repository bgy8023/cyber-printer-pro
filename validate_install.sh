#!/bin/zsh
# 赛博印钞机 Pro 环境一键校验脚本
# 快速检查所有依赖、配置、环境是否正常

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 统计
PASS_COUNT=0
FAIL_COUNT=0
WARNING_COUNT=0

# 打印函数
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[PASS]${NC} $1"; ((PASS_COUNT++)); }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; ((WARNING_COUNT++)); }
error() { echo -e "${RED}[FAIL]${NC} $1"; ((FAIL_COUNT++)); }

# 标题
clear
echo -e "${GREEN}"
echo "============================================="
echo "  🧪 赛博印钞机 Pro 环境一键校验"
echo "============================================="
echo -e "${NC}"

# 1. 项目目录检查
info "1. 检查项目目录结构..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || { error "无法进入项目目录"; exit 1; }

REQUIRED_DIRS=("builtin_claude_core" "novel_settings" "output" "logs")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        success "目录存在：$dir"
    else
        error "目录缺失：$dir"
        mkdir -p "$dir" && success "已自动创建目录：$dir"
    fi
done

REQUIRED_FILES=("requirements.txt" "web_panel_ultra.py" "cyber_printer_ultimate.py" ".env.example")
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        success "文件存在：$file"
    else
        error "核心文件缺失：$file"
    fi
done

# 2. Python 环境检查
echo ""
info "2. 检查 Python 环境..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    error "未找到 Python 可执行文件"
    PYTHON_CMD=""
fi

if [ -n "$PYTHON_CMD" ]; then
    PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print('.'.join(map(str, sys.version_info[:3])))")
    PYTHON_MIN_VERSION="3.10.0"
    
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

    if version_compare "$PYTHON_VERSION" "$PYTHON_MIN_VERSION"; then
        success "Python 版本：$PYTHON_VERSION (符合要求，最低 $PYTHON_MIN_VERSION)"
    else
        error "Python 版本过低：$PYTHON_VERSION，需要至少 $PYTHON_MIN_VERSION"
    fi

    # 虚拟环境检查
    if [ -d "venv" ]; then
        success "Python 虚拟环境已存在"
        # 检查虚拟环境完整性
        if [ -f "venv/bin/activate" ]; then
            success "虚拟环境激活脚本正常"
        else
            error "虚拟环境损坏，缺少激活脚本"
        fi
    else
        warning "Python 虚拟环境不存在，首次启动会自动创建"
    fi
fi

# 3. 依赖检查
echo ""
info "3. 检查核心依赖..."
if [ -d "venv" ] && [ -f "venv/bin/pip" ]; then
    VENV_PIP="venv/bin/pip"
    # 检查依赖是否安装
    REQUIRED_PACKAGES=("streamlit" "openai" "python-dotenv" "pyyaml")
    for package in "${REQUIRED_PACKAGES[@]}"; do
        if $VENV_PIP show "$package" &> /dev/null; then
            success "依赖已安装：$package"
        else
            warning "依赖未安装：$package，首次启动会自动安装"
        fi
    done
else
    warning "虚拟环境未就绪，跳过依赖检查"
fi

# 4. Node.js 环境检查
echo ""
info "4. 检查 Node.js 环境..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node -v | sed 's/v//')
    success "Node.js 版本：$NODE_VERSION"
    if [ -f "package.json" ]; then
        success "package.json 配置文件正常"
    else
        error "package.json 缺失"
    fi
else
    warning "未找到 Node.js，x-crawl 爬虫功能将不可用"
fi

# 5. 环境变量配置检查
echo ""
info "5. 检查环境变量配置..."
if [ -f ".env" ]; then
    success ".env 配置文件已存在"
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
    if grep -q "LLM_MODEL_NAME=" .env; then
        success "LLM_MODEL_NAME 已配置"
    else
        warning "LLM_MODEL_NAME 未配置"
    fi
else
    warning ".env 配置文件不存在，首次启动会自动从模板复制"
fi

# 6. Git 安全配置检查
echo ""
info "6. 检查 Git 安全配置..."
if [ -d ".git" ]; then
    if [ -f ".git/hooks/pre-commit" ]; then
        success "Git pre-commit 敏感信息拦截钩子已安装"
    else
        warning "Git pre-commit 钩子未安装，敏感信息防护未生效"
    fi
    # 检查 .gitignore
    if grep -q ".env" .gitignore; then
        success ".env 已加入 .gitignore，不会被提交到仓库"
    else
        error ".env 未加入 .gitignore，存在密钥泄露风险"
    fi
else
    warning "非 Git 仓库，跳过 Git 安全检查"
fi

# 7. 守护进程配置检查
echo ""
info "7. 检查守护进程配置..."
if [ -f "com.cyberprinter.daemon.plist" ]; then
    success "launchd 守护进程配置文件正常"
else
    warning "launchd 守护进程配置文件缺失"
fi
if [ -f "install_daemon.sh" ]; then
    success "守护进程安装脚本正常"
    chmod +x install_daemon.sh
else
    warning "守护进程安装脚本缺失"
fi

# 最终统计
echo ""
echo "============================================="
echo -e "📊 校验结果统计"
echo -e "${GREEN}✅ 通过：${PASS_COUNT} 项${NC}"
echo -e "${YELLOW}⚠️  警告：${WARNING_COUNT} 项${NC}"
echo -e "${RED}❌ 失败：${FAIL_COUNT} 项${NC}"
echo "============================================="

if [ $FAIL_COUNT -eq 0 ] && [ $WARNING_COUNT -eq 0 ]; then
    echo -e "${GREEN}🎉 所有检查全部通过！环境完全正常${NC}"
    echo "可以直接运行 ./start_ultimate.command 启动面板"
elif [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${YELLOW}⚠️  环境基本正常，存在少量警告，不影响核心功能使用${NC}"
else
    echo -e "${RED}❌ 存在失败项，请修复后再使用${NC}"
fi
echo ""
