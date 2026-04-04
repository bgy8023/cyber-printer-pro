def get_css_styles() -> str:
    """获取CSS样式
    
    Returns:
        CSS样式字符串
    """
    return """
<style>
    .stApp { background-color: #f8fafc; color: #1e293b; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; border-bottom: 1px solid #e2e8f0; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: transparent; border-radius: 4px 4px 0px 0px; gap: 1px; padding-top: 10px; padding-bottom: 10px; }
    .stTabs [aria-selected="true"] { color: #2563eb !important; border-bottom: 2px solid #2563eb !important; }
    .stButton>button { background-color: #e11d48; color: #ffffff; border: none; font-weight: 600; border-radius: 8px; height: 3em; transition: all 0.2s; }
    .stButton>button:hover { background-color: #be123c; transform: scale(1.02); }
    .stTextArea>div>div>textarea, .stTextInput>div>div>input, .stSelectbox>div>div>div { background-color: #ffffff; color: #1e293b; border: 1px solid #e2e8f0; border-radius: 8px; }
    .log-container { background-color: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; font-family: 'Courier New', Courier, monospace; color: #0f172a; height: 300px; overflow-y: auto; }
    .status-badge { display: inline-block; padding: 4px 12px; border-radius: 999px; font-size: 14px; font-weight: bold; background: #f1f5f9; border: 1px solid #e2e8f0; margin-right: 10px; color: #1e293b; }
    .node-card { padding: 15px; border-radius: 8px; border: 2px solid #e2e8f0; background-color: #ffffff; text-align: center; transition: all 0.3s; }
    .node-card.idle { border-color: #cbd5e1; }
    .node-card.running { border-color: #f59e0b; animation: pulse 1.5s infinite; }
    .node-card.success { border-color: #10b981; }
    .node-card.failed { border-color: #ef4444; }
    @keyframes pulse { 0%, 100% { opacity: 1; box-shadow: 0 0 10px #f59e0b; } 50% { opacity: 0.7; box-shadow: none; } }
    .setting-card { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
</style>
"""
