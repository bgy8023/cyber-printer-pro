#!/bin/zsh
# 赛博印钞机 Pro 全本守护进程管理脚本
# 支持单章定时生成和全本自动完本模式

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR" || exit 1

PYTHON_PATH="$APP_DIR/venv/bin/python3"
DAEMON_SCRIPT="$APP_DIR/builtin_claude_core/kairos_daemon.py"

# 检查虚拟环境
if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ 虚拟环境不存在，请先运行 ./start_ultimate.command 初始化环境"
    exit 1
fi

# 检查参数
COMMAND=$1
NOVEL_NAME=$2

case $COMMAND in
    install)
        if [ -z "$NOVEL_NAME" ]; then
            echo "❌ 请指定小说名称，用法：./install_daemon.sh install <小说名称>"
            echo "示例：./install_daemon.sh install 我的第一本小说"
            exit 1
        fi
        echo "🚀 安装全本自动完本守护进程，小说：$NOVEL_NAME"
        $PYTHON_PATH $DAEMON_SCRIPT --novel-name "$NOVEL_NAME" --install
        ;;
    uninstall)
        if [ -z "$NOVEL_NAME" ]; then
            echo "❌ 请指定小说名称，用法：./install_daemon.sh uninstall <小说名称>"
            exit 1
        fi
        echo "🛑 卸载全本守护进程，小说：$NOVEL_NAME"
        $PYTHON_PATH $DAEMON_SCRIPT --novel-name "$NOVEL_NAME" --uninstall
        ;;
    status)
        if [ -z "$NOVEL_NAME" ]; then
            echo "❌ 请指定小说名称，用法：./install_daemon.sh status <小说名称>"
            exit 1
        fi
        echo "📊 查看守护进程状态，小说：$NOVEL_NAME"
        $PYTHON_PATH $DAEMON_SCRIPT --novel-name "$NOVEL_NAME" --status
        ;;
    run-once)
        if [ -z "$NOVEL_NAME" ]; then
            echo "❌ 请指定小说名称，用法：./install_daemon.sh run-once <小说名称>"
            exit 1
        fi
        echo "🚀 手动执行单次生成任务，小说：$NOVEL_NAME"
        $PYTHON_PATH $DAEMON_SCRIPT --novel-name "$NOVEL_NAME" --run-once
        ;;
    *)
        echo "赛博印钞机 Pro 全本守护进程管理脚本"
        echo ""
        echo "用法："
        echo "  ./install_daemon.sh install <小说名称>   安装全本守护进程"
        echo "  ./install_daemon.sh uninstall <小说名称> 卸载全本守护进程"
        echo "  ./install_daemon.sh status <小说名称>    查看守护进程状态"
        echo "  ./install_daemon.sh run-once <小说名称>  手动执行单次生成"
        echo ""
        echo "示例："
        echo "  ./install_daemon.sh install 废土修仙传"
        echo "  ./install_daemon.sh status 废土修仙传"
        ;;
esac
