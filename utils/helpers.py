import streamlit as st
import os
import sys
import re
import glob
import json
import subprocess
from dotenv import load_dotenv
from typing import Tuple, List, Optional, Dict, Any

# 全局路径变量
OPENCLAW_CONFIG_PATH = os.path.expanduser("~/.openclaw")
OPENCLAW_WORKSPACE = os.path.expanduser("~/.openclaw/workspace")


def get_llm_config() -> Dict[str, Any]:
    """获取LLM配置，支持中转池配置
    
    Returns:
        包含LLM配置的字典
    """
    env_path = get_resource_path(".env")
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
    
    # 按优先级获取 API base URL: API_BASE_URL > LLM_BASE_URL > OPENAI_BASE_URL > 默认值
    base_url = (
        os.getenv("API_BASE_URL")
        or os.getenv("LLM_BASE_URL")
        or os.getenv("OPENAI_BASE_URL")
        or "https://api.openai.com/v1"
    )
    
    # 按优先级获取 API key: LLM_API_KEY > OPENAI_API_KEY
    api_key = (
        os.getenv("LLM_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or ""
    )
    
    # 模型名称: LLM_MODEL_NAME > OPENAI_MODEL > 默认值
    model_name = (
        os.getenv("LLM_MODEL_NAME")
        or os.getenv("OPENAI_MODEL")
        or "gpt-4o"
    )
    
    # 其他配置
    timeout = int(os.getenv("LLM_TIMEOUT", "300"))
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    max_tokens = int(os.getenv("LLM_MAX_TOKENS", "16384"))
    max_retry = int(os.getenv("MAX_RETRY", "3"))
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    
    return {
        "provider": provider,
        "api_key": api_key,
        "base_url": base_url,
        "model": model_name,
        "timeout": timeout,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "max_retry": max_retry
    }

def get_resource_path(relative_path: str) -> str:
    """获取资源文件路径，兼容开发环境和PyInstaller打包环境
    
    Args:
        relative_path: 相对路径
        
    Returns:
        绝对路径
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def reload_env() -> Tuple[str, str, str, str]:
    """重载环境变量
    
    Returns:
        (NOTION_TOKEN, NOTION_DATABASE_ID, GITHUB_TOKEN, GITHUB_REPO)
    """
    env_path = get_resource_path(".env")
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
    else:
        load_dotenv(override=True)
    return (
        os.getenv("NOTION_TOKEN"),
        os.getenv("NOTION_DATABASE_ID"),
        os.getenv("GITHUB_TOKEN"),
        os.getenv("GITHUB_REPO")
    )

@st.cache_data(ttl=300)
def get_clawpanel_agents() -> List[str]:
    """获取可用的智能体列表
    
    Returns:
        智能体列表
    """
    try:
        agents = ["main", "main-2"]
        return sorted(list(set(agents)))
    except Exception:
        return ["main", "main-2"]

@st.cache_data(ttl=300)
def get_agent_skills(agent_name: str) -> List[str]:
    """从内置技能目录读取技能列表
    
    Args:
        agent_name: 智能体名称
        
    Returns:
        技能列表
    """
    try:
        skills = []
        builtin_skills_dir = get_resource_path("builtin_skills")
        if os.path.exists(builtin_skills_dir):
            skill_files = glob.glob(os.path.join(builtin_skills_dir, "*"))
            for skill_file in skill_files:
                if os.path.isdir(skill_file):
                    skills.append(os.path.basename(skill_file))
        return sorted(list(set(skills)))
    except:
        return []

@st.cache_data(ttl=60)
def get_mcp_servers() -> List[str]:
    """自动检测已配置的MCP Server
    
    Returns:
        MCP服务器列表
    """
    try:
        mcp_servers = []
        mcp_config_file = os.path.join(OPENCLAW_CONFIG_PATH, "mcp_config.json")
        if os.path.exists(mcp_config_file):
            with open(mcp_config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
                if "mcpServers" in config:
                    mcp_servers = list(config["mcpServers"].keys())
        return mcp_servers
    except:
        return []

def check_daemon_status() -> bool:
    """检查Kairos守护进程状态
    
    Returns:
        守护进程是否运行
    """
    try:
        result = subprocess.run(["pgrep", "-f", "claw_kairos_daemon"], capture_output=True, text=True)
        return result.stdout.strip() != ""
    except:
        return False

def get_lazy_prompt(enable_mcp: bool, mcp_servers: List[str], enable_xcrawl: bool, enable_undercover: bool, enable_multi_agent: bool) -> str:
    """自动融合所有记忆宫殿文件，生成基础Prompt
    
    Args:
        enable_mcp: 是否启用MCP
        mcp_servers: MCP服务器列表
        enable_xcrawl: 是否启用xcrawl
        enable_undercover: 是否启用Undercover模式
        enable_multi_agent: 是否启用多智能体
        
    Returns:
        生成的Prompt
    """
    setting_path = get_resource_path("novel_settings")
    setting_files = sorted([f for f in os.listdir(setting_path) if f.endswith(".md")])
    full_setting = ""
    for file in setting_files:
        with open(os.path.join(setting_path, file), "r", encoding="utf-8") as f:
            content = f.read()
            full_setting += f"【{file}】\n{content}\n\n"
    
    tool_prompt = ""
    if enable_mcp and mcp_servers:
        tool_prompt += f"""
【MCP跨维工具已激活】
你可以使用以下MCP工具来辅助创作：
- {', '.join(mcp_servers)}
如果需要了解最新网文热点/套路、搜索资料，请使用brave-search工具搜索。
"""
    if enable_xcrawl:
        tool_prompt += f"""
【xcrawl全网吞噬技能已激活】
你现在拥有了重型爬虫能力！如果需要深入了解某个网页的完整内容（比如爆款小说章节、热搜帖子、详细设定），请直接调用：
`node ~/.openclaw/workspace/skills/xcrawl_scraper/crawl.js <目标URL>`
拿到文本后，立即吸收其核心爽点、套路、设定或语录，无缝融合进你的小说里！
"""
    if enable_undercover:
        tool_prompt += f"""
【Undercover Mode卧底模式已激活】
你必须严格遵循卧底模式的规则，从思维链底层就规避AI写作特征，生成原生人类风格的网文，绝对不能出现AI高频词汇、固定句式、规则三等结构。
"""
    if enable_multi_agent:
        tool_prompt += f"""
【多智能体协调模式已激活】
你将分工完成创作，先规划大纲，再生成正文，最后校验优化，严格防吃书，保证爽点密度和字数达标。
你将分工完成创作，先规划大纲，再生成正文，最后校验优化，严格防吃书，保证爽点密度和字数达标。
"""
    
    return f"""
我不知道剧情该怎么发展了。请你严格读取【记忆宫殿】里的所有文件，自动根据这些顶级写作心法，推演并生成本章正文。
要求：
1. 自动凭空捏造一个符合世界观的反派或冲突事件来推进剧情。
2. 主角不要废话，直接用最震撼的方式降维打击，当场打脸。
3. 详细描写周围围观群众震惊、倒吸一口凉气的反应。
4. 结尾必须留一个悬念钩子，引出下一章的冲突。
5. 严格遵守记忆宫殿里的所有设定、爽点铁律、禁忌事项，绝对不允许主角吃瘪、吃书、结尾平淡。
你自己发散脑洞，直接给我输出完整的正文，不要多余的解释！

{tool_prompt}

【记忆宫殿所有文件内容】：
{full_setting}
"""

def clean_mermaid_code(content: str) -> str:
    """自动清理Mermaid代码，避免Notion渲染问题
    
    Args:
        content: 原始内容
        
    Returns:
        清理后的内容
    """
    content = re.sub(r"```mermaid.*?```", "", content, flags=re.DOTALL)
    content = re.sub(r"\n{3,}", "\n\n", content)
    return content.strip()

def count_real_chars(text: str) -> int:
    """统计有效汉字数量
    
    Args:
        text: 待统计文本
        
    Returns:
        汉字数量
    """
    return len(re.findall(r'[\u4e00-\u9fa5]', text))

def extract_latest_novel_from_output() -> Optional[str]:
    """提取最新生成的小说正文
    
    Returns:
        小说正文或None
    """
    try:
        output_dir = get_resource_path("output")
        md_files = glob.glob(os.path.join(output_dir, "**/*.md"), recursive=True)
        if not md_files:
            return None
        md_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        with open(md_files[0], "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except:
        return None

def auto_update_plot_record(chapter_content: str, chapter_num: int) -> bool:
    """自动更新剧情备忘录，结构化记忆
    
    Args:
        chapter_content: 章节内容
        chapter_num: 章节号
        
    Returns:
        是否成功
    """
    try:
        setting_path = get_resource_path("novel_settings")
        plot_file = os.path.join(setting_path, "2_剧情自动推演记录.md")
        if not os.path.exists(plot_file):
            with open(plot_file, "w", encoding="utf-8") as f:
                f.write("# 剧情备忘录（AI必须严格遵守）\n")
        prompt = f"提取本章核心剧情、新出场人物、新增伏笔、核心人设变化，以列表格式输出，结构化存储，用于后续防吃书。章节内容：{chapter_content[:2000]}..."
        gen_script_path = get_resource_path("run_claude_core.sh")
        result = subprocess.run(
            [gen_script_path, "0", prompt, "100", "default", "false", "false"],
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        with open(plot_file, "a", encoding="utf-8") as f:
            f.write(f"\n\n## 第{chapter_num}章\n{result.stdout}")
        return True
    except:
        return True
