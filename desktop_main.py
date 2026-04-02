import webview
import threading
import subprocess
import time
import sys
import os
import requests

# 【核心修改】动态资源路径处理
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# 应用配置
APP_NAME = "赛博印钞机 Pro Mac版"
APP_VERSION = "1.0.0"
APP_WIDTH = 1400
APP_HEIGHT = 900
STREAMLIT_PORT = 8501
STREAMLIT_URL = f"http://localhost:{STREAMLIT_PORT}"

# 检查并初始化.env配置
def init_env_config():
    env_path = get_resource_path(".env")
    if not os.path.exists(env_path):
        env_content = '''# 赛博印钞机 Pro Mac版 配置文件
# 请填写以下配置，保存后重启应用

# Notion配置
NOTION_TOKEN=
NOTION_DATABASE_ID=

# GitHub配置
GITHUB_TOKEN=
GITHUB_REPO=

# 系统配置（可选，无需修改）
SYSTEM_LOG_PATH=system.log
GENERATE_SCRIPT_PATH=run_openclaw.sh
'''
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(env_content)
        return False
    from dotenv import load_dotenv
    load_dotenv(env_path)
    required_vars = ["NOTION_TOKEN", "NOTION_DATABASE_ID", "GITHUB_TOKEN", "GITHUB_REPO"]
    return all(os.getenv(var) for var in required_vars)

# 启动Streamlit服务
def start_streamlit():
    script_path = get_resource_path("web_panel.py")
    # 【核心修改】设置环境变量，让子进程知道内置资源目录
    env = os.environ.copy()
    if hasattr(sys, '_MEIPASS'):
        env["APP_BUILTIN_RESOURCES"] = sys._MEIPASS
    
    subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", script_path,
        "--server.headless", "true",
        "--server.port", str(STREAMLIT_PORT),
        "--browser.gatherUsageStats", "false"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)

# 等待服务启动
def wait_for_service():
    for i in range(30):
        try:
            requests.get(STREAMLIT_URL, timeout=1)
            return True
        except:
            time.sleep(1)
    return False

if __name__ == '__main__':
    # 配置校验
    if not init_env_config():
        config_html = f"""
        <html>
        <head><title>{APP_NAME} - 首次配置向导</title></head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 40px; max-width: 800px; margin: 0 auto; background: #f8fafc;">
            <h1 style="color: #e11d48;">🚀 {APP_NAME} v{APP_VERSION}</h1>
            <h2>首次启动，请完成核心配置</h2>
            <p>配置文件已自动生成在：<code style="background: #f1f5f9; padding: 4px 8px; border-radius: 4px;">{get_resource_path(".env")}</code></p>
            <p>请用「文本编辑」打开该文件，填写以下4项核心配置后重启应用：</p>
            <ul style="line-height: 2;">
                <li><code>NOTION_TOKEN</code>：你的Notion API Token</li>
                <li><code>NOTION_DATABASE_ID</code>：你的Notion数据库ID</li>
                <li><code>GITHUB_TOKEN</code>：你的GitHub Personal Access Token</li>
                <li><code>GITHUB_REPO</code>：你的GitHub仓库（格式：用户名/仓库名）</li>
            </ul>
            <p style="color: #64748b;">配置完成后，重启此应用即可解锁全部功能！</p>
        </body>
        </html>
        """
        webview.create_window(f"{APP_NAME} - 配置向导", html=config_html, width=900, height=650, resizable=False)
        webview.start()
        sys.exit(0)
    
    # 启动服务
    print(f"🚀 正在启动{APP_NAME}...")
    service_thread = threading.Thread(target=start_streamlit)
    service_thread.daemon = True
    service_thread.start()
    
    # 等待服务就绪
    print("⏳ 正在等待服务就绪...")
    if not wait_for_service():
        error_html = f"""
        <html>
        <head><title>{APP_NAME} - 启动失败</title></head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 40px; text-align: center;">
            <h1>❌ 启动失败</h1>
            <p>无法连接到Streamlit服务，请检查端口{STREAMLIT_PORT}是否被占用，或重启应用。</p>
        </body>
        </html>
        """
        webview.create_window(f"{APP_NAME} - 启动失败", html=error_html, width=600, height=400, resizable=False)
        webview.start()
        sys.exit(1)
    
    # 启动主窗口
    print("✅ 服务就绪，正在启动主窗口...")
    webview.create_window(
        f"{APP_NAME} v{APP_VERSION}",
        STREAMLIT_URL,
        width=APP_WIDTH,
        height=APP_HEIGHT,
        resizable=True,
        min_size=(1000, 700),
        text_select=True
    )
    webview.start()
