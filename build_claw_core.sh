#!/bin/zsh
# build_claw_core.sh - 一键编译 claw-code Rust 核心
# 架构师方案：完全可控、跨平台、插拔式算力引擎

set -e  # 遇到错误立即退出

echo "🚀 赛博印钞机 Pro - claw-code Rust 核心编译脚本"
echo "=================================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目路径
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAW_CODE_DIR="$PROJECT_DIR/claw-code"
BIN_DIR="$PROJECT_DIR/bin"

echo "📂 项目目录: $PROJECT_DIR"
echo "📂 二进制输出目录: $BIN_DIR"
echo ""

# 1. 检查系统要求
echo "🔍 检查系统要求..."

# 检查操作系统
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${YELLOW}⚠️  警告: 当前不是 macOS 系统，但脚本应该可以正常工作${NC}"
fi

# 检查网络连接
if ! ping -c 1 github.com &> /dev/null; then
    echo -e "${RED}❌ 错误: 无法连接到 GitHub，请检查网络连接${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 系统检查通过${NC}"
echo ""

# 2. 安装 Rust 环境
echo "🔧 安装 Rust 编译环境..."
if ! command -v rustc &> /dev/null; then
    echo "   Rust 未安装，开始安装..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source "$HOME/.cargo/env"
    echo -e "${GREEN}✅ Rust 安装完成${NC}"
else
    echo "   Rust 已安装: $(rustc --version)"
    echo -e "${GREEN}✅ Rust 环境就绪${NC}"
fi
echo ""

# 3. 克隆 claw-code 仓库
echo "📦 克隆 claw-code 仓库..."
if [ -d "$CLAW_CODE_DIR" ]; then
    echo "   目录已存在，更新代码..."
    cd "$CLAW_CODE_DIR"
    git fetch origin
    git checkout dev/rust
    git pull origin dev/rust
else
    echo "   克隆仓库..."
    git clone https://github.com/ultraworkers/claw-code.git "$CLAW_CODE_DIR"
    cd "$CLAW_CODE_DIR"
    git checkout dev/rust
fi
echo -e "${GREEN}✅ 代码准备完成${NC}"
echo ""

# 4. 编译 Release 版本
echo "🔨 编译 Release 版本（这可能需要几分钟）..."
cd "$CLAW_CODE_DIR/rust"
echo "   编译目标: claw-core"
cargo build --release 2>&1 | tee /tmp/claw-build.log

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 编译失败，请检查错误日志: /tmp/claw-build.log${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 编译成功${NC}"
echo ""

# 5. 复制二进制文件
echo "📋 复制二进制文件到项目目录..."
mkdir -p "$BIN_DIR"

# 查找编译好的二进制文件
CLAW_CORE_BIN="$CLAW_CODE_DIR/rust/target/release/claw-core"
if [ -f "$CLAW_CORE_BIN" ]; then
    cp "$CLAW_CORE_BIN" "$BIN_DIR/"
    chmod +x "$BIN_DIR/claw-core"
    echo -e "${GREEN}✅ 二进制文件已复制: $BIN_DIR/claw-core${NC}"
else
    # 尝试查找其他可能的二进制文件
    FOUND_BIN=$(find "$CLAW_CODE_DIR/rust/target/release" -maxdepth 1 -type f -perm +111 | head -1)
    if [ -n "$FOUND_BIN" ]; then
        cp "$FOUND_BIN" "$BIN_DIR/claw-core"
        chmod +x "$BIN_DIR/claw-core"
        echo -e "${GREEN}✅ 二进制文件已复制: $BIN_DIR/claw-core${NC}"
    else
        echo -e "${RED}❌ 错误: 找不到编译好的二进制文件${NC}"
        exit 1
    fi
fi
echo ""

# 6. 验证二进制文件
echo "🔍 验证二进制文件..."
if "$BIN_DIR/claw-core" --version &> /dev/null; then
    VERSION=$("$BIN_DIR/claw-core" --version 2>&1 | head -1)
    echo -e "${GREEN}✅ 二进制文件验证通过: $VERSION${NC}"
else
    echo -e "${YELLOW}⚠️  无法验证二进制文件版本，但文件已存在${NC}"
fi
echo ""

# 7. 更新 rust_dispatcher.py 配置
echo "⚙️  更新项目配置..."
RUST_DISPATCHER="$PROJECT_DIR/rust_dispatcher.py"
if [ -f "$RUST_DISPATCHER" ]; then
    # 检查是否已经有正确的二进制路径
    if grep -q "claw-core" "$RUST_DISPATCHER"; then
        echo "   rust_dispatcher.py 已配置"
    else
        echo "   请手动检查 rust_dispatcher.py 中的二进制路径配置"
    fi
fi
echo -e "${GREEN}✅ 配置检查完成${NC}"
echo ""

# 8. 完成提示
echo ""
echo "🎉 =============================================="
echo -e "${GREEN}✅ claw-code Rust 核心编译完成！${NC}"
echo "🎉 =============================================="
echo ""
echo "📊 编译信息:"
echo "   二进制文件: $BIN_DIR/claw-core"
echo "   文件大小: $(ls -lh $BIN_DIR/claw-core | awk '{print $5}')"
echo "   编译时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "🚀 下一步操作:"
echo "   1. 重启赛博印钞机: ./start_ultimate.command"
echo "   2. 或者运行: python cyber_printer_ultimate.py --chapter 1"
echo ""
echo "💡 提示:"
echo "   - Rust 核心会自动被 rust_dispatcher.py 检测和使用"
echo "   - 如果 Rust 核心启动失败，会自动降级到 Python 原生引擎"
echo "   - 查看日志: tail -f logs/system.log"
echo ""
echo "🎉 =============================================="
