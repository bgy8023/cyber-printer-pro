
#!/bin/bash

# 赛博印钞机 Pro - launchd 守护进程安装脚本

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_FILE="${SCRIPT_DIR}/com.cyberprinter.daemon.plist"
LAUNCHAGENTS_DIR="$HOME/Library/LaunchAgents"

# 确保日志目录存在
mkdir -p "${SCRIPT_DIR}/logs"

echo "🚀 赛博印钞机 Pro - launchd 守护进程管理"
echo "📂 脚本目录：${SCRIPT_DIR}"
echo "="*50

case "$1" in
    install)
        echo "🔧 正在安装守护进程..."
        
        # 复制 plist 文件到 LaunchAgents
        cp "${PLIST_FILE}" "${LAUNCHAGENTS_DIR}/"
        
        # 加载服务
        launchctl load "${LAUNCHAGENTS_DIR}/com.cyberprinter.daemon.plist"
        
        # 验证服务状态
        if launchctl list | grep -q com.cyberprinter.daemon; then
            echo "✅ 守护进程安装成功！"
            echo "📅 已设置每天凌晨 3:00 自动生成"
            echo "🔍 日志文件：${SCRIPT_DIR}/logs/daemon.out"
        else
            echo "❌ 守护进程安装失败！"
            echo "请检查权限并重新尝试"
        fi
        ;;
        
    uninstall)
        echo "🔧 正在卸载守护进程..."
        
        # 停止并卸载服务
        launchctl unload "${LAUNCHAGENTS_DIR}/com.cyberprinter.daemon.plist" 2>/dev/null
        rm -f "${LAUNCHAGENTS_DIR}/com.cyberprinter.daemon.plist"
        
        # 验证服务状态
        if ! launchctl list | grep -q com.cyberprinter.daemon; then
            echo "✅ 守护进程卸载成功！"
        else
            echo "❌ 守护进程卸载失败！"
            echo "请检查权限并重新尝试"
        fi
        ;;
        
    status)
        echo "🔍 正在检查守护进程状态..."
        
        if launchctl list | grep -q com.cyberprinter.daemon; then
            echo "✅ 守护进程已安装并运行"
            echo "📅 每天凌晨 3:00 自动生成"
        else
            echo "❌ 守护进程未安装"
            echo "使用 ./install_daemon.sh install 安装"
        fi
        ;;
        
    *)
        echo "📚 使用帮助："
        echo "  ./install_daemon.sh install   - 安装守护进程"
        echo "  ./install_daemon.sh uninstall - 卸载守护进程"
        echo "  ./install_daemon.sh status    - 检查守护进程状态"
        ;;
esac

echo "="*50
