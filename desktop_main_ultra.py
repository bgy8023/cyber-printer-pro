
import webview
import threading
import subprocess
import time
import sys
import os
import requests
from pathlib import Path

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

APP_NAME = "赛博印钞机 Pro Ultra"
APP_VERSION = "2.0.0"
APP_WIDTH = 1600
APP_HEIGHT = 1000
STREAMLIT_PORT = 8502
STREAMLIT_URL = f"http://localhost:{STREAMLIT_PORT}"

def init_env_config():
    env_path = get_resource_path(".env")
    if not os.path.exists(env_path):
        env_content = '''# 赛博印钞机 Pro Ultra 配置文件
# 请填写以下配置，保存后重启应用

# Notion配置（可选）
NOTION_TOKEN=
NOTION_DATABASE_ID=

# GitHub配置（可选）
GITHUB_TOKEN=
GITHUB_REPO=

# 系统配置（可选，无需修改）
SYSTEM_LOG_PATH=logs/system.log
GENERATE_SCRIPT_PATH=run_openclaw.sh
'''
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(env_content)
        return False
    from dotenv import load_dotenv
    load_dotenv(env_path)
    return True

def start_streamlit():
    script_path = get_resource_path("web_panel_ultra.py")
    env = os.environ.copy()
    if hasattr(sys, '_MEIPASS'):
        env["APP_BUILTIN_RESOURCES"] = sys._MEIPASS
    
    subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", script_path,
        "--server.headless", "true",
        "--server.port", str(STREAMLIT_PORT),
        "--browser.gatherUsageStats", "false",
        "--server.enableCORS", "false"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)

def wait_for_service():
    for i in range(60):
        try:
            requests.get(STREAMLIT_URL, timeout=1)
            return True
        except:
            time.sleep(1)
    return False

if __name__ == '__main__':
    if not init_env_config():
        config_html = f"""
        <html>
        <head><title>{APP_NAME} - 首次配置向导</title></head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 40px; max-width: 800px; margin: 0 auto; background: linear-gradient(135deg, #0f172a, #1e293b); color: #e2e8f0; min-height: 100vh;">
            <h1 style="color: #3b82f6; font-size: 2.5em; margin-bottom: 10px;">🚀 {APP_NAME}</h1>
            <h2 style="color: #94a3b8; font-weight: 400; margin-top: 0;">v{APP_VERSION}</h2>
            <div style="background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 24px; margin: 30px 0;">
                <h3 style="color: #f1f5f9; margin-top: 0;">✨ 欢迎使用赛博印钞机 Pro Ultra！</h3>
                <p style="color: #94a3b8; line-height: 1.8;">配置文件已自动生成在：<code style="background: #0f172a; padding: 6px 12px; border-radius: 6px; color: #60a5fa;">{get_resource_path(".env")}</code></p>
                <p style="color: #94a3b8; line-height: 1.8;">请用「文本编辑」打开该文件，配置你的环境变量后重启应用。</p>
            </div>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">
                <div style="background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px;">
                    <h4 style="color: #60a5fa; margin-top: 0;">📖 小说生成</h4>
                    <p style="color: #94a3b8; font-size: 0.9em;">多种小说类型模板，一键生成</p>
                </div>
                <div style="background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px;">
                    <h4 style="color: #a78bfa; margin-top: 0;">🗂️ 多工作区</h4>
                    <p style="color: #94a3b8; font-size: 0.9em;">独立工作区，项目隔离管理</p>
                </div>
                <div style="background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px;">
                    <h4 style="color: #f472b6; margin-top: 0;">🤖 Agent管理</h4>
                    <p style="color: #94a3b8; font-size: 0.9em;">灵活配置和管理你的AI Agent</p>
                </div>
                <div style="background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px;">
                    <h4 style="color: #10b981; margin-top: 0;">🩺 系统诊断</h4>
                    <p style="color: #94a3b8; font-size: 0.9em;">全面的系统健康检查</p>
                </div>
            </div>
        </body>
        </html>
        """
        webview.create_window(f"{APP_NAME} - 配置向导", html=config_html, width=1000, height=800, resizable=True)
        webview.start()
        sys.exit(0)
    
    print(f"🚀 正在启动{APP_NAME}...")
    service_thread = threading.Thread(target=start_streamlit)
    service_thread.daemon = True
    service_thread.start()
    
    print("⏳ 正在等待服务就绪...")
    if not wait_for_service():
        error_html = f"""
        <html>
        <head><title>{APP_NAME} - 启动失败</title></head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 40px; text-align: center; background: #0f172a; color: #e2e8f0; min-height: 100vh;">
            <h1 style="color: #ef4444;">❌ 启动失败</h1>
            <p style="color: #94a3b8;">无法连接到Streamlit服务，请检查端口{STREAMLIT_PORT}是否被占用，或重启应用。</p>
        </body>
        </html>
        """
        webview.create_window(f"{APP_NAME} - 启动失败", html=error_html, width=600, height=400, resizable=False)
        webview.start()
        sys.exit(1)
    
    print("✅ 服务就绪，正在启动主窗口...")
    webview.create_window(
        f"{APP_NAME} v{APP_VERSION}",
        STREAMLIT_URL,
        width=APP_WIDTH,
        height=APP_HEIGHT,
        resizable=True,
        min_size=(1200, 800),
        text_select=True
    )
    webview.start()

