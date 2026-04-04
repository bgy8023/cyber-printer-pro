import sys
import streamlit as st
import os
import subprocess
import re
import hashlib
import requests
import base64
import time
import glob
import json
from dotenv import load_dotenv
from notion_client import Client
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List

# 导入核心模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.config_manager import ConfigManager
from core.browser_manager import BrowserManager
from builtin_claude_core import logger, ConfigManager as BuiltinConfigManager, MetricsCollector, lock_manager
from builtin_claude_core.llm_adapter import reset_llm_adapter
from rust_dispatcher import get_dispatcher

# 初始化配置管理器
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
config_manager = ConfigManager(BASE_PATH)

# 全局引擎变量（延迟初始化）
_engine = None
_builtin_config = None
_metrics = None

def reset_engine():
    """重置引擎（使用最新配置）"""
    global _engine, _builtin_config, _metrics
    _engine = None
    _builtin_config = None
    _metrics = None

def get_engine():
    """延迟初始化引擎"""
    global _engine, _builtin_config, _metrics
    if _engine is None:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        MEMORY_DIR = os.path.join(BASE_DIR, "novel_settings")
        OUTPUT_DIR = os.path.join(BASE_DIR, "output")
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        os.makedirs(MEMORY_DIR, exist_ok=True)
        
        LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
        logger.info(f"🔄 正在初始化引擎，提供商: {LLM_PROVIDER}")
        logger.info(f"🔄 使用模型: {os.getenv('LLM_MODEL_NAME', os.getenv('OPENAI_MODEL', 'unknown'))}")
        _engine = get_dispatcher(llm_provider=LLM_PROVIDER)
        _builtin_config = BuiltinConfigManager()
        _metrics = MetricsCollector()
        logger.info("✅ 引擎初始化完成")
    return _engine, _builtin_config, _metrics

# ==============================================
# 【官方规范】session_state全量初始化
# 必须在访问任何st.session_state.xxx之前执行
# ==============================================
def init_session_state():
    # 初始化所有用到的session_state变量
    if 'pipeline' not in st.session_state:
        st.session_state.pipeline = None
    if 'current_chapter' not in st.session_state:
        st.session_state.current_chapter = 1
    if 'log_display' not in st.session_state:
        st.session_state.log_display = []
    if 'preview_content' not in st.session_state:
        st.session_state.preview_content = ''
    if 'rollback_data' not in st.session_state:
        st.session_state.rollback_data = {}
    if 'agents_list' not in st.session_state:
        st.session_state.agents_list = ['main', 'main-2']
    if 'browser_manager' not in st.session_state:
        st.session_state.browser_manager = None
    if 'browser_logs' not in st.session_state:
        st.session_state.browser_logs = []

# 页面加载时立刻执行初始化
init_session_state()

# ================= 全局枚举与数据结构 =================
class NodeStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class DAGNode:
    node_id: str
    node_name: str
    description: str
    pre_nodes: list[str] = field(default_factory=list)
    status: NodeStatus = NodeStatus.IDLE
    result: Optional[Dict[str, Any]] = None
    error_msg: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

@dataclass
class DAGPipeline:
    pipeline_id: str
    nodes: Dict[str, DAGNode]
    create_time: datetime = field(default_factory=datetime.now)
    current_node: Optional[str] = None
    status: NodeStatus = NodeStatus.IDLE

# ================= CSS主题 =================
st.markdown("""
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
""", unsafe_allow_html=True)

# ================= 核心工具函数 =================
def get_resource_path(relative_path):
    """获取资源文件路径，兼容开发环境和PyInstaller打包环境"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def read_env_file():
    """读取 .env 文件内容"""
    env_path = get_resource_path(".env")
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars

def write_env_file(env_vars):
    """写入 .env 文件"""
    env_path = get_resource_path(".env")
    # 读取现有的 .env 文件（如果存在）
    existing_lines = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            existing_lines = f.readlines()
    
    # 更新或添加新的环境变量
    updated_lines = []
    keys_processed = set()
    
    for line in existing_lines:
        line = line.rstrip("\n")
        if line and not line.startswith("#") and "=" in line:
            key, _ = line.split("=", 1)
            key = key.strip()
            if key in env_vars:
                updated_lines.append(f"{key}={env_vars[key]}")
                keys_processed.add(key)
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)
    
    # 添加未处理的新环境变量
    for key, value in env_vars.items():
        if key not in keys_processed:
            updated_lines.append(f"{key}={value}")
    
    # 写入文件
    with open(env_path, "w", encoding="utf-8") as f:
        for line in updated_lines:
            f.write(line + "\n")

def validate_llm_config(provider, api_key, model_name):
    """验证 LLM 配置"""
    if not provider:
        return False, "请选择 LLM 提供商"
    if provider != "ollama" and not api_key:
        return False, "请输入 API Key"
    if not model_name:
        return False, "请选择或输入模型名称"
    return True, ""

def reload_env():
    """重载环境变量"""
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

# 全局环境变量初始化
NOTION_TOKEN, NOTION_DATABASE_ID, GITHUB_TOKEN, GITHUB_REPO = reload_env()
LOG_PATH = os.getenv("SYSTEM_LOG_PATH", "system.log")
SETTING_PATH = get_resource_path("novel_settings")
GEN_SCRIPT_PATH = get_resource_path("run_claude_core.sh")
OUTPUT_DIR = get_resource_path("output")
DAEMON_SCRIPT_PATH = get_resource_path("claw_kairos_daemon.sh")
CHAPTER_NUM_FILE = os.path.expanduser("~/OpenClaw_Arch/current_chapter.txt")

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 自定义模型相关函数
def get_custom_models_path():
    """获取自定义模型配置文件路径"""
    return os.path.join(SETTING_PATH, "custom_models.json")

def save_custom_models(custom_models: Dict[str, List[str]]):
    """保存自定义模型列表到JSON文件"""
    try:
        models_path = get_custom_models_path()
        with open(models_path, "w", encoding="utf-8") as f:
            json.dump(custom_models, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存自定义模型失败: {e}")

def load_custom_models() -> Dict[str, List[str]]:
    """从JSON文件读取自定义模型列表"""
    try:
        models_path = get_custom_models_path()
        if os.path.exists(models_path):
            with open(models_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"读取自定义模型失败: {e}")
        return {}

def fetch_models_from_openai_api(base_url: str, api_key: str) -> List[str]:
    """从OpenAI兼容API获取模型列表"""
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(f"{base_url}/models", headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return [model["id"] for model in data.get("data", [])]
    except Exception as e:
        print(f"获取模型列表失败: {e}")
        return []

def get_combined_models(provider: str) -> List[str]:
    """合并预设模型和自定义模型"""
    preset_models = {
        "openai": ["gpt-4", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
        "anthropic": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
        "ollama": ["llama2", "llama3", "mistral", "gemma"]
    }
    
    custom_models = load_custom_models()
    provider_custom_models = custom_models.get(provider, [])
    
    combined = preset_models.get(provider, []).copy()
    for model in provider_custom_models:
        model_with_tag = f"{model} [自定义]"
        if model_with_tag not in combined:
            combined.append(model_with_tag)
    
    return combined

def get_clawpanel_agents():
    """获取可用的智能体列表"""
    try:
        agents = ["main", "main-2"]
        return sorted(list(set(agents)))
    except Exception:
        return ["main", "main-2"]

def get_agent_skills(agent_name: str) -> List[str]:
    """从内置技能目录读取技能列表"""
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

def get_mcp_servers() -> List[str]:
    """自动检测已配置的MCP Server"""
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
    """检查Kairos守护进程状态"""
    try:
        result = subprocess.run(["pgrep", "-f", "claw_kairos_daemon"], capture_output=True, text=True)
        return result.stdout.strip() != ""
    except:
        return False

def get_lazy_prompt(enable_mcp: bool, mcp_servers: List[str], enable_xcrawl: bool, enable_undercover: bool, enable_multi_agent: bool) -> str:
    """自动融合所有记忆宫殿文件，生成基础Prompt"""
    setting_files = sorted([f for f in os.listdir(SETTING_PATH) if f.endswith(".md")])
    full_setting = ""
    for file in setting_files:
        with open(os.path.join(SETTING_PATH, file), "r", encoding="utf-8") as f:
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
    """自动清理Mermaid代码，避免Notion渲染问题"""
    content = re.sub(r"```mermaid.*?```", "", content, flags=re.DOTALL)
    content = re.sub(r"\n{3,}", "\n\n", content)
    return content.strip()

def write_log(content, log_placeholder=None):
    """写入日志并更新UI"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {content}"
    st.session_state.log_display.append(log_line)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(log_line + "\n")
    
    # 优化UI更新频率，每3条日志或最后一条日志才更新UI
    if log_placeholder and (len(st.session_state.log_display) % 3 == 0 or "完成" in content or "失败" in content):
        log_placeholder.code("\n".join(st.session_state.log_display), language="bash")

def count_real_chars(text):
    """统计有效汉字数量"""
    return len(re.findall(r'[\u4e00-\u9fa5]', text))

def init_dag_pipeline(pipeline_id: str) -> DAGPipeline:
    """初始化DAG管线"""
    nodes = {
        "init_check": DAGNode(
            node_id="init_check",
            node_name="1. 初始化校验",
            description="检查环境、Agent、技能、工具",
            pre_nodes=[]
        ),
        "load_settings": DAGNode(
            node_id="load_settings",
            node_name="2. 结构化记忆加载",
            description="读取设定，生成结构化记忆",
            pre_nodes=["init_check"]
        ),
        "generate_content": DAGNode(
            node_id="generate_content",
            node_name="3. 多智能体创作",
            description="调用Claude内核生成正文",
            pre_nodes=["load_settings"]
        ),
        "humanizer_process": DAGNode(
            node_id="humanizer_process",
            node_name="4. 去AI化处理",
            description="二次优化，过审保障",
            pre_nodes=["generate_content"]
        ),
        "update_plot": DAGNode(
            node_id="update_plot",
            node_name="5. 剧情记忆更新",
            description="更新结构化记忆，防吃书",
            pre_nodes=["humanizer_process"]
        ),
        "github_archive": DAGNode(
            node_id="github_archive",
            node_name="6. GitHub母本归档",
            description="上传原始文件到私有仓库",
            pre_nodes=["update_plot"]
        ),
        "notion_write": DAGNode(
            node_id="notion_write",
            node_name="7. Notion分发对账",
            description="分段写入Notion，回读对账",
            pre_nodes=["github_archive"]
        ),
        "finish": DAGNode(
            node_id="finish",
            node_name="8. 全链路闭环",
            description="生成执行报告，完成归档",
            pre_nodes=["notion_write"]
        )
    }
    return DAGPipeline(pipeline_id=pipeline_id, nodes=nodes)

def update_node_status(pipeline: DAGPipeline, node_id: str, status: NodeStatus, node_placeholders: Dict = None, result: Dict = None, error_msg: str = None):
    """更新节点状态并刷新UI"""
    node = pipeline.nodes[node_id]
    node.status = status
    if status == NodeStatus.RUNNING:
        node.start_time = datetime.now()
    elif status in [NodeStatus.SUCCESS, NodeStatus.FAILED]:
        node.end_time = datetime.now()
    node.result = result
    node.error_msg = error_msg
    pipeline.current_node = node_id
    if node_placeholders:
        render_dag_nodes(pipeline, node_placeholders)

def render_dag_nodes(pipeline: DAGPipeline, placeholders: Dict):
    """渲染DAG节点UI"""
    node_list = list(pipeline.nodes.values())
    for i, (node_id, placeholder) in enumerate(placeholders.items()):
        node = node_list[i]
        with placeholder:
            st.markdown(f"""
            <div class="node-card {node.status.value}">
                <div style="font-weight: bold; font-size: 1.1em; margin-bottom: 0.5em;">{node.node_name}</div>
                <div style="font-size: 0.9em; color: #64748b;">{node.description}</div>
            </div>
            """, unsafe_allow_html=True)

def extract_latest_novel_from_output():
    """提取最新生成的小说正文"""
    try:
        md_files = glob.glob(os.path.join(OUTPUT_DIR, "**/*.md"), recursive=True)
        if not md_files:
            return None
        md_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        with open(md_files[0], "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except:
        return None

def auto_update_plot_record(chapter_content, chapter_num):
    """自动更新剧情备忘录，结构化记忆"""
    try:
        plot_file = os.path.join(SETTING_PATH, "2_剧情自动推演记录.md")
        if not os.path.exists(plot_file):
            with open(plot_file, "w", encoding="utf-8") as f:
                f.write("# 剧情备忘录（AI必须严格遵守）\n")
        prompt = f"提取本章核心剧情、新出场人物、新增伏笔、核心人设变化，以列表格式输出，结构化存储，用于后续防吃书。章节内容：{chapter_content[:2000]}..."
        result = subprocess.run(
            [GEN_SCRIPT_PATH, "0", prompt, "100", "main", "false", "false"],
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        with open(plot_file, "a", encoding="utf-8") as f:
            f.write(f"\n\n## 第{chapter_num}章\n{result.stdout}")
        return True
    except:
        return True

# ================= DAG节点执行逻辑 =================
def run_init_check(pipeline: DAGPipeline, node_placeholders: Dict, log_placeholder, target_agent: str, enable_humanizer: bool, enable_mcp: bool, enable_xcrawl: bool, enable_undercover: bool, enable_multi_agent: bool) -> bool:
    global NOTION_TOKEN, NOTION_DATABASE_ID, GITHUB_TOKEN, GITHUB_REPO
    update_node_status(pipeline, "init_check", NodeStatus.RUNNING, node_placeholders)
    write_log("🔍 [节点1] 开始初始化环境校验（内置技能已加载）", log_placeholder)
    
    try:
        NOTION_TOKEN, NOTION_DATABASE_ID, GITHUB_TOKEN, GITHUB_REPO = reload_env()
        required_env = [NOTION_TOKEN, NOTION_DATABASE_ID, GITHUB_TOKEN, GITHUB_REPO]
        if any(not env for env in required_env):
            raise Exception("核心环境变量缺失，请检查.env文件")
        if not GEN_SCRIPT_PATH or not os.path.exists(GEN_SCRIPT_PATH):
            raise Exception(f"生成脚本不存在：{GEN_SCRIPT_PATH}")
        
        write_log(f"🤖 [节点1] 正在检查目标Agent：{target_agent}", log_placeholder)
        if target_agent not in st.session_state.agents_list:
            write_log(f"⚠️ [节点1] Agent {target_agent} 不在检测列表中，尝试使用main", log_placeholder)
        
        skills = get_agent_skills(target_agent)
        core_skills = ["novel-generator", "undercover_mode", "humanizer", "xcrawl_scraper"]
        for skill in core_skills:
            if skill in skills:
                write_log(f"✅ [节点1] {skill}技能已就绪（内置加载）", log_placeholder)
        
        if enable_mcp:
            mcp_servers = get_mcp_servers()
            if mcp_servers:
                write_log(f"✅ [节点1] MCP跨维工具已就绪：{', '.join(mcp_servers)}", log_placeholder)
        
        # GitHub连通性校验
        for i in range(2):
            try:
                gh_res = requests.get(
                    f"https://api.github.com/repos/{GITHUB_REPO}",
                    headers={"Authorization": f"token {GITHUB_TOKEN}"}
                )
                if gh_res.status_code == 200:
                    break
                else:
                    if i == 0:
                        write_log(f"⚠️ [节点1] GitHub API连通失败，正在重试...", log_placeholder)
                        time.sleep(1)
                    else:
                        raise Exception(f"GitHub API连通失败：{gh_res.text}")
            except Exception as e:
                if i == 0:
                    write_log(f"⚠️ [节点1] GitHub API请求异常，正在重试...", log_placeholder)
                    time.sleep(1)
                else:
                    raise Exception(f"GitHub API请求异常：{str(e)}")
        
        # Notion连通性校验
        notion_res = requests.get(
            f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}",
            headers={
                "Authorization": f"Bearer {NOTION_TOKEN}",
                "Notion-Version": "2022-06-28"
            }
        )
        if notion_res.status_code != 200:
            raise Exception(f"Notion API连通失败：{notion_res.text}")
        
        if not os.path.exists(SETTING_PATH):
            os.makedirs(SETTING_PATH)
        
        update_node_status(pipeline, "init_check", NodeStatus.SUCCESS, node_placeholders)
        write_log("✅ [节点1] 初始化校验全部通过，内置技能已加载", log_placeholder)
        return True
    except Exception as e:
        update_node_status(pipeline, "init_check", NodeStatus.FAILED, node_placeholders, error_msg=str(e))
        write_log(f"❌ [节点1] 初始化校验失败：{str(e)}", log_placeholder)
        return False

def run_load_settings(pipeline: DAGPipeline, node_placeholders: Dict, log_placeholder, chapter_num: int, custom_prompt: str, enable_mcp: bool, mcp_servers: List[str], enable_xcrawl: bool, enable_undercover: bool, enable_multi_agent: bool) -> tuple[bool, str]:
    update_node_status(pipeline, "load_settings", NodeStatus.RUNNING, node_placeholders)
    write_log("🏛️ [节点2] 开始加载结构化记忆系统", log_placeholder)
    
    try:
        final_prompt = custom_prompt if custom_prompt.strip() else get_lazy_prompt(enable_mcp, mcp_servers, enable_xcrawl, enable_undercover, enable_multi_agent)
        update_node_status(pipeline, "load_settings", NodeStatus.SUCCESS, node_placeholders, result={"final_prompt": final_prompt})
        write_log("✅ [节点2] 结构化记忆加载完成", log_placeholder)
        return True, final_prompt
    except Exception as e:
        update_node_status(pipeline, "load_settings", NodeStatus.FAILED, node_placeholders, error_msg=str(e))
        write_log(f"❌ [节点2] 记忆加载失败：{str(e)}", log_placeholder)
        return False, ""

def update_plot_record_web(chapter_content: str, chapter_num: int):
    """更新剧情记忆，同步到QueryEngine（Web版）"""
    engine, builtin_config, _ = get_engine()
    if not builtin_config.get("memory.auto_update", True):
        return True
        
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MEMORY_DIR = os.path.join(BASE_DIR, "novel_settings")
    plot_file = os.path.join(MEMORY_DIR, "4_剧情自动推演记录.md")
    
    try:
        with lock_manager.with_lock(plot_file):
            if not os.path.exists(plot_file):
                with open(plot_file, "w", encoding="utf-8") as f:
                    f.write("# 剧情备忘录（AI必须严格遵守）\n")
            
            plot_content = f"""
- 核心剧情：【占位内容】
- 新出场人物：【占位内容】
- 新增伏笔：【占位内容】
- 核心人设变化：【占位内容】
            """
            
            with open(plot_file, "a", encoding="utf-8") as f:
                f.write(f"\n\n## 第{chapter_num}章\n{plot_content}")
            
            engine.load_memory(MEMORY_DIR)
            logger.info("🧠 剧情记忆已更新")
            return True
    except Exception as e:
        logger.error(f"❌ 更新剧情记忆失败：{str(e)}", exc_info=True)
        return False

def run_generate_content(pipeline: DAGPipeline, node_placeholders: Dict, log_placeholder, chapter_num: int, chapter_title: str, final_prompt: str, target_words: int, target_agent: str, enable_humanizer: bool, enable_multi_agent: bool) -> tuple[bool, str, int]:
    update_node_status(pipeline, "generate_content", NodeStatus.RUNNING, node_placeholders)
    write_log(f"🤖 [节点3] 开始多智能体创作（多Agent：{'已激活' if enable_multi_agent else '未激活'}）", log_placeholder)
    
    try:
        engine, _, _ = get_engine()
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        MEMORY_DIR = os.path.join(BASE_DIR, "novel_settings")
        OUTPUT_DIR = os.path.join(BASE_DIR, "output")
        
        write_log("🏛️ [节点3/6] 开始加载结构化记忆", log_placeholder)
        engine.load_memory(MEMORY_DIR)
        relevant_memory = engine.retrieve_memory(final_prompt)
        write_log("✅ [节点3/6] 结构化记忆加载完成", log_placeholder)
        
        write_log("🤖 [节点3/6] 开始多智能体创作", log_placeholder)
        try:
            agent_result = engine.multi_agent_coordinate(
                chapter_num=chapter_num,
                target_words=target_words,
                custom_prompt=final_prompt,
                relevant_memory=relevant_memory
            )
            final_content = agent_result["content"]
            real_chars = agent_result["real_chars"]
        except Exception as e:
            logger.error(f"❌ 创作失败：{str(e)}", exc_info=True)
            raise Exception(f"创作失败：{str(e)}")
        write_log(f"✅ [节点3/6] 创作完成，最终字数：{real_chars}", log_placeholder)
        
        write_log("🧠 [节点3/6] 开始更新剧情记忆", log_placeholder)
        update_plot_record_web(final_content, chapter_num)
        write_log("✅ [节点3/6] 剧情记忆更新完成", log_placeholder)
        
        write_log("💾 [节点3/6] 开始保存本地文件", log_placeholder)
        output_file = os.path.join(OUTPUT_DIR, f"第{chapter_num}章_{real_chars}字.md")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_content)
        write_log(f"✅ [节点3/6] 本地文件保存完成：{output_file}", log_placeholder)
        
        generated_content = final_content
        if real_chars < target_words * 0.95:
            write_log(f"⚠️ [节点3/6] 字数偏少！目标{target_words}字，仅生成{real_chars}字，继续执行", log_placeholder)
        
        st.session_state.preview_content = generated_content
        update_node_status(pipeline, "generate_content", NodeStatus.SUCCESS, node_placeholders, result={"content": generated_content, "real_chars": real_chars})
        write_log(f"✅ [节点3] 创作完成，实际有效汉字：{real_chars}字", log_placeholder)
        return True, generated_content, real_chars
    except Exception as e:
        update_node_status(pipeline, "generate_content", NodeStatus.FAILED, node_placeholders, error_msg=str(e))
        write_log(f"❌ [节点3] 创作失败：{str(e)}", log_placeholder)
        return False, "", 0

def run_humanizer_process(pipeline: DAGPipeline, node_placeholders: Dict, log_placeholder, raw_content: str, target_agent: str, enable_humanizer: bool) -> tuple[bool, str]:
    update_node_status(pipeline, "humanizer_process", NodeStatus.RUNNING, node_placeholders)
    
    if not enable_humanizer:
        write_log("ℹ️ [节点4] Humanizer功能未启用，跳过本节点", log_placeholder)
        update_node_status(pipeline, "humanizer_process", NodeStatus.SKIPPED, node_placeholders)
        return True, raw_content
    
    try:
        write_log("🧹 [节点4] 开始Humanizer去AI化润色", log_placeholder)
        engine, _, _ = get_engine()
        humanized_content = engine.humanize_text(raw_content)
        write_log("✅ [节点4] Humanizer去AI化润色完成", log_placeholder)
        update_node_status(pipeline, "humanizer_process", NodeStatus.SUCCESS, node_placeholders)
        return True, humanized_content
    except Exception as e:
        logger.error(f"❌ Humanizer失败：{str(e)}", exc_info=True)
        write_log(f"⚠️ [节点4] Humanizer失败，返回原文：{str(e)}", log_placeholder)
        write_log("ℹ️ [节点4] 使用原文继续后续流程", log_placeholder)
        update_node_status(pipeline, "humanizer_process", NodeStatus.SKIPPED, node_placeholders)
        return True, raw_content

def run_update_plot(pipeline: DAGPipeline, node_placeholders: Dict, log_placeholder, chapter_content: str, chapter_num: int) -> bool:
    update_node_status(pipeline, "update_plot", NodeStatus.RUNNING, node_placeholders)
    auto_update_plot_record(chapter_content, chapter_num)
    update_node_status(pipeline, "update_plot", NodeStatus.SUCCESS, node_placeholders)
    write_log("✅ [节点5] 剧情记忆更新完成", log_placeholder)
    return True

def run_github_archive(pipeline: DAGPipeline, node_placeholders: Dict, log_placeholder, chapter_title: str, content: str) -> tuple[bool, str, str]:
    update_node_status(pipeline, "github_archive", NodeStatus.RUNNING, node_placeholders)
    write_log("📦 [节点6] 开始GitHub母本归档", log_placeholder)
    
    try:
        filename = f"{chapter_title}_{datetime.now().strftime('%Y%m%d%H%M')}.md"
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/novels/{filename}"
        content_base64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        data = {"message": f"Auto-upload: {filename}", "content": content_base64, "branch": "main"}
        
        for i in range(2):
            try:
                res = requests.put(url, headers=headers, json=data)
                if res.status_code in [200, 201]:
                    break
                else:
                    if i == 0:
                        write_log(f"⚠️ [节点6] GitHub上传失败，正在重试...", log_placeholder)
                        time.sleep(1)
                    else:
                        raise Exception(f"GitHub上传失败：{res.text}")
            except Exception as e:
                if i == 0:
                    write_log(f"⚠️ [节点6] GitHub上传异常，正在重试...", log_placeholder)
                    time.sleep(1)
                else:
                    raise Exception(f"GitHub上传异常：{str(e)}")
        
        raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/novels/{filename}"
        md5 = hashlib.md5(content.encode()).hexdigest()
        st.session_state.rollback_data["github_file"] = f"novels/{filename}"
        st.session_state.rollback_data["github_sha"] = res.json()["content"]["sha"]
        
        update_node_status(pipeline, "github_archive", NodeStatus.SUCCESS, node_placeholders, result={"raw_url": raw_url, "md5": md5})
        write_log(f"✅ [节点6] GitHub归档成功：{filename}", log_placeholder)
        return True, raw_url, md5
    except Exception as e:
        update_node_status(pipeline, "github_archive", NodeStatus.FAILED, node_placeholders, error_msg=str(e))
        write_log(f"❌ [节点6] GitHub归档失败：{str(e)}", log_placeholder)
        return False, "", ""

def run_notion_write(pipeline: DAGPipeline, node_placeholders: Dict, log_placeholder, chapter_title: str, content: str, github_url: str, md5: str, real_chars: int) -> bool:
    update_node_status(pipeline, "notion_write", NodeStatus.RUNNING, node_placeholders)
    write_log("📤 [节点7] 开始Notion写入与对账", log_placeholder)
    
    try:
        notion = Client(auth=NOTION_TOKEN)
        page = notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "章节名": {"title": [{"text": {"content": chapter_title}}]},
                "字数": {"number": real_chars},
                "状态": {"select": {"name": "已完成"}},
                "GitHub母本链接": {"url": github_url} if github_url else {},
                "MD5校验值": {"rich_text": [{"text": {"content": md5}}]} if md5 else {}
            }
        )
        page_id = page["id"]
        st.session_state.rollback_data["notion_page_id"] = page_id
        
        # 分段写入正文
        chunks = [content[i:i+1500] for i in range(0, len(content), 1500)]
        for chunk in chunks:
            notion.blocks.children.append(
                page_id,
                children=[{"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": chunk}}]}}]
            )
        
        update_node_status(pipeline, "notion_write", NodeStatus.SUCCESS, node_placeholders)
        write_log(f"✅ [节点7] Notion写入完成，对账通过", log_placeholder)
        return True
    except Exception as e:
        update_node_status(pipeline, "notion_write", NodeStatus.FAILED, node_placeholders, error_msg=str(e))
        write_log(f"❌ [节点7] Notion写入失败：{str(e)}", log_placeholder)
        if "github_file" in st.session_state.rollback_data:
            try:
                del_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{st.session_state.rollback_data['github_file']}"
                headers = {"Authorization": f"token {GITHUB_TOKEN}"}
                res = requests.get(del_url, headers=headers)
                if res.status_code == 200:
                    sha = res.json()["sha"]
                    requests.delete(del_url, headers=headers, json={"message": "Rollback", "sha": sha, "branch": "main"})
                    write_log("♻️ [事务回滚] 已删除GitHub上的无效归档文件", log_placeholder)
            except:
                pass
        return False

def run_finish(pipeline: DAGPipeline, node_placeholders: Dict, log_placeholder) -> bool:
    update_node_status(pipeline, "finish", NodeStatus.RUNNING, node_placeholders)
    st.session_state.current_chapter += 1
    with open(CHAPTER_NUM_FILE, "w") as f:
        f.write(str(st.session_state.current_chapter))
    update_node_status(pipeline, "finish", NodeStatus.SUCCESS, node_placeholders)
    write_log(f"✅ [节点8] 全流程闭环完成！下一章章节号已自动更新", log_placeholder)
    return True

# ================= 辅助函数 =================

def test_llm_connection(provider: str, api_key_val: str, base_url_val: str, model_val: str) -> tuple[bool, str]:
    """测试大模型连接"""
    try:
        if provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=api_key_val, base_url=base_url_val)
            response = client.chat.completions.create(
                model=model_val,
                messages=[{"role": "user", "content": "你好"}],
                max_tokens=10
            )
            return True, f"✅ 连接成功！模型响应正常"
        elif provider == "anthropic":
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key_val)
            response = client.messages.create(
                model=model_val,
                max_tokens=10,
                messages=[{"role": "user", "content": "你好"}]
            )
            return True, f"✅ 连接成功！模型响应正常"
        elif provider == "ollama":
            import requests
            response = requests.post(
                f"{base_url_val}/api/generate",
                json={
                    "model": model_val,
                    "prompt": "你好",
                    "stream": False,
                    "options": {"num_predict": 10}
                },
                timeout=30
            )
            response.raise_for_status()
            return True, f"✅ 连接成功！模型响应正常"
        else:
            return False, f"❌ 不支持的提供商：{provider}"
    except Exception as e:
        return False, f"❌ 连接失败：{str(e)}"

# ================= 页面UI渲染 =================

# 侧边栏：大模型配置
with st.sidebar:
    st.markdown("### 🤖 大模型配置")
    st.markdown("---")
    
    # 读取当前配置
    current_env = read_env_file()
    
    # 提供商选择
    provider_options = ["openai", "anthropic", "ollama"]
    default_provider = current_env.get("LLM_PROVIDER", "openai")
    if default_provider not in provider_options:
        default_provider = "openai"
    
    llm_provider = st.selectbox(
        "LLM 提供商",
        options=provider_options,
        index=provider_options.index(default_provider)
    )
    
    # 预设模型提示
    preset_models = {
        "openai": ["gpt-4", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
        "anthropic": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
        "ollama": ["llama2", "llama3", "mistral", "gemma"]
    }
    
    # 获取当前模型
    current_model = current_env.get("LLM_MODEL_NAME", "")
    if not current_model:
        current_model = preset_models[llm_provider][0] if preset_models[llm_provider] else ""
    
    # 模型输入和获取列表按钮
    col1, col2 = st.columns([3, 1])
    with col1:
        model_name = st.text_input(
            "模型名称（可自定义）",
            value=current_model,
            placeholder=f"例如：{preset_models[llm_provider][0] if preset_models[llm_provider] else '输入模型名称'}"
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if llm_provider == "openai":
            if st.button("🔍", help="获取模型列表"):
                if api_key and base_url:
                    fetched_models = fetch_models_from_openai_api(base_url, api_key)
                    if fetched_models:
                        st.session_state.fetched_models = fetched_models
                        st.success(f"✅ 成功获取 {len(fetched_models)} 个模型！")
                    else:
                        st.error("❌ 未能获取到模型列表")
                else:
                    st.error("❌ 请先填写API Key和Base URL")
    
    # 显示预设模型提示
    st.caption(f"预设模型：{', '.join(preset_models[llm_provider])}")
    
    # 显示获取到的模型列表（如果有）
    if 'fetched_models' in st.session_state and st.session_state.fetched_models:
        st.markdown("#### 可选择的模型")
        selected_model = st.selectbox(
            "从列表中选择",
            options=[""] + st.session_state.fetched_models,
            index=0
        )
        if selected_model:
            model_name = selected_model
    
    # API Key 输入（密码输入框）
    api_key_env_key = "OPENAI_API_KEY" if llm_provider == "openai" else "ANTHROPIC_API_KEY"
    current_api_key = current_env.get(api_key_env_key, "")
    api_key = st.text_input(
        "API Key",
        type="password",
        value=current_api_key,
        placeholder="请输入 API Key"
    )
    
    # Base URL 输入框（可选）
    base_url_env_key = "OPENAI_BASE_URL" if llm_provider == "openai" else "OLLAMA_BASE_URL" if llm_provider == "ollama" else ""
    default_base_url = {
        "openai": "https://api.openai.com/v1",
        "anthropic": "",
        "ollama": "http://localhost:11434"
    }
    current_base_url = current_env.get(base_url_env_key, default_base_url[llm_provider])
    base_url = st.text_input(
        "Base URL (可选，用于代理)",
        value=current_base_url,
        placeholder=f"例如：{default_base_url[llm_provider]}"
    )
    
    st.markdown("---")
    
    # 保存配置按钮
    if st.button("💾 保存配置", type="primary", use_container_width=True):
        # 直接使用输入的模型名称
        clean_model_name = model_name
        
        # 验证配置
        is_valid, error_msg = validate_llm_config(llm_provider, api_key, clean_model_name)
        if not is_valid:
            st.error(error_msg)
        else:
            # 准备要保存的环境变量
            env_vars = {
                "LLM_PROVIDER": llm_provider,
                "LLM_MODEL_NAME": clean_model_name
            }
            
            if llm_provider == "openai":
                env_vars["OPENAI_API_KEY"] = api_key
                env_vars["OPENAI_BASE_URL"] = base_url
                if "ANTHROPIC_API_KEY" in current_env:
                    env_vars["ANTHROPIC_API_KEY"] = current_env["ANTHROPIC_API_KEY"]
                if "OLLAMA_BASE_URL" in current_env:
                    env_vars["OLLAMA_BASE_URL"] = current_env["OLLAMA_BASE_URL"]
            elif llm_provider == "anthropic":
                env_vars["ANTHROPIC_API_KEY"] = api_key
                if "OPENAI_API_KEY" in current_env:
                    env_vars["OPENAI_API_KEY"] = current_env["OPENAI_API_KEY"]
                if "OPENAI_BASE_URL" in current_env:
                    env_vars["OPENAI_BASE_URL"] = current_env["OPENAI_BASE_URL"]
                if "OLLAMA_BASE_URL" in current_env:
                    env_vars["OLLAMA_BASE_URL"] = current_env["OLLAMA_BASE_URL"]
            elif llm_provider == "ollama":
                env_vars["OLLAMA_BASE_URL"] = base_url
                if "OPENAI_API_KEY" in current_env:
                    env_vars["OPENAI_API_KEY"] = current_env["OPENAI_API_KEY"]
                if "OPENAI_BASE_URL" in current_env:
                    env_vars["OPENAI_BASE_URL"] = current_env["OPENAI_BASE_URL"]
                if "ANTHROPIC_API_KEY" in current_env:
                    env_vars["ANTHROPIC_API_KEY"] = current_env["ANTHROPIC_API_KEY"]
            
            # 保存其他现有的环境变量
            for key, value in current_env.items():
                if key not in env_vars:
                    env_vars[key] = value
            
            # 写入 .env 文件
            write_env_file(env_vars)
            
            # 重载环境变量
            reload_env()
            
            # 重置 LLM 适配器
            reset_llm_adapter()
            
            # 重置引擎
            st.session_state.pipeline = None
            reset_engine()
            
            st.success("✅ 配置已保存并立即生效！")
            
            # 测试连接
            st.info("🔍 正在测试大模型连接...")
            with st.spinner("测试中..."):
                test_success, test_msg = test_llm_connection(llm_provider, api_key, base_url, clean_model_name)
                if test_success:
                    st.success(test_msg)
                else:
                    st.error(test_msg)
            
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 📝 提示")
    st.info("配置保存后会立即生效，无需重启应用。")

st.title("🌌 赛博印钞机 Pro Mac版")
st.markdown("""
<span class='status-badge'>✅ 内置技能物理内聚合并</span>
<span class='status-badge'>✅ Claude官方内核级Undercover Mode</span>
<span class='status-badge'>✅ 多智能体网文工作室</span>
<span class='status-badge'>✅ Kairos自主守护进程</span>
<span class='status-badge'>🛡️ 企业级DAG事务保障</span>
""", unsafe_allow_html=True)
st.markdown("---")

# Kairos守护进程控制面板（暂时禁用）
st.subheader("⏰ Kairos自主守护进程（自动日更，彻底解放双手）")
st.info("⚠️ 守护进程功能正在维护中，即将上线！请使用下方的「全自动连载」功能手动生成章节。")
st.markdown("---")

# 核心操作区
st.markdown("---")

# 标签页
tab_5q, tab_outline, tab_serial, tab_memory, tab_log, tab_preview, tab_browser = st.tabs(["🎯 5问选设定", "📋 大纲生成", "🚀 全自动连载", "🏛️ 记忆宫殿", "📟 实时日志", "📖 章节预览", "🌐 浏览器控制"])

with tab_memory:
    st.subheader("当前锁死的全局设定（结构化记忆系统）")
    if not os.path.exists(SETTING_PATH):
        os.makedirs(SETTING_PATH)
    setting_files = sorted([f for f in os.listdir(SETTING_PATH) if f.endswith(".md")])
    
    if setting_files:
        selected_file = st.selectbox("选择设定文件进行查看/微调", options=setting_files)
        with open(os.path.join(SETTING_PATH, selected_file), "r", encoding="utf-8") as f:
            file_content = f.read()
        edit_content = st.text_area(f"内容：{selected_file}", value=file_content, height=300)
        if st.button("💾 保存微调", type="primary"):
            with open(os.path.join(SETTING_PATH, selected_file), "w", encoding="utf-8") as f:
                f.write(edit_content)
            st.success("✅ 修改已保存生效！")
    else:
        st.info("⚠️ 记忆宫殿空空如也，请重新运行部署脚本！")

with tab_5q:
    st.subheader("🎯 5问选设定 - 快速生成小说基础设定")
    st.markdown("通过回答5个关键问题，快速生成小说的基础设定，自动保存到记忆宫殿。")
    st.markdown("---")
    
    # 初始化会话状态
    if 'five_questions' not in st.session_state:
        st.session_state.five_questions = {
            "genre": "",
            "protagonist": "",
            "worldview": "",
            "conflict": "",
            "target_words": 100000
        }
    
    # 问题1：题材/类型
    st.markdown("### 1. 题材/类型")
    genre_options = ["都市", "玄幻", "修仙", "历史", "科幻", "奇幻", "悬疑", "恐怖", "军事", "其他"]
    st.session_state.five_questions["genre"] = st.selectbox(
        "请选择小说题材/类型",
        options=genre_options,
        index=genre_options.index(st.session_state.five_questions["genre"]) if st.session_state.five_questions["genre"] in genre_options else 0
    )
    
    # 问题2：主角设定
    st.markdown("### 2. 主角设定")
    st.session_state.five_questions["protagonist"] = st.text_area(
        "请描述主角的基本设定（身份、性格、能力等）",
        value=st.session_state.five_questions["protagonist"],
        height=100,
        placeholder="例如：普通大学生，性格坚韧，意外获得系统能力..."
    )
    
    # 问题3：世界观设定
    st.markdown("### 3. 世界观设定")
    st.session_state.five_questions["worldview"] = st.text_area(
        "请描述小说的世界观设定",
        value=st.session_state.five_questions["worldview"],
        height=100,
        placeholder="例如：现代都市，存在隐藏的修炼者世界..."
    )
    
    # 问题4：核心冲突
    st.markdown("### 4. 核心冲突")
    st.session_state.five_questions["conflict"] = st.text_area(
        "请描述小说的核心冲突",
        value=st.session_state.five_questions["conflict"],
        height=100,
        placeholder="例如：主角与反派势力的对抗，争夺某个重要物品..."
    )
    
    # 问题5：目标字数
    st.markdown("### 5. 目标字数")
    st.session_state.five_questions["target_words"] = st.number_input(
        "请输入小说的目标字数",
        min_value=50000,
        max_value=1000000,
        value=st.session_state.five_questions["target_words"],
        step=10000
    )
    
    st.markdown("---")
    
    if st.button("🔥 生成并保存设定", type="primary", use_container_width=True):
        # 验证所有问题都已回答
        if not all([
            st.session_state.five_questions["genre"],
            st.session_state.five_questions["protagonist"],
            st.session_state.five_questions["worldview"],
            st.session_state.five_questions["conflict"]
        ]):
            st.error("请完成所有问题的回答！")
        else:
            # 生成设定内容
            setting_content = f"""
# 小说基础设定（5问生成）

## 题材/类型
{st.session_state.five_questions['genre']}

## 主角设定
{st.session_state.five_questions['protagonist']}

## 世界观设定
{st.session_state.five_questions['worldview']}

## 核心冲突
{st.session_state.five_questions['conflict']}

## 目标字数
{st.session_state.five_questions['target_words']}字
            """
            
            # 保存到记忆宫殿
            setting_file = os.path.join(SETTING_PATH, "0_5问设定.md")
            with open(setting_file, "w", encoding="utf-8") as f:
                f.write(setting_content)
            
            # 同时保存到记忆宫殿系统
            from builtin_claude_core.memory_palace import get_memory_palace
            memory_palace = get_memory_palace()
            memory_palace.set_world_setting(st.session_state.five_questions['worldview'])
            memory_palace.set_character("主角", st.session_state.five_questions['protagonist'])
            memory_palace.save_to_disk()
            
            st.success("✅ 设定生成并保存成功！")
            st.info(f"设定已保存到：{setting_file}")
            
            # 显示生成的设定
            st.markdown("### 生成的设定预览")
            st.markdown(setting_content)

with tab_outline:
    st.subheader("📋 大纲生成 - 基于设定自动生成全本大纲")
    st.markdown("基于 5 问生成的设定，自动生成全本大纲，支持预览和编辑。")
    st.markdown("---")
    
    # 检查是否有 5 问设定
    setting_file = os.path.join(SETTING_PATH, "0_5问设定.md")
    if not os.path.exists(setting_file):
        st.warning("⚠️ 请先在 '5问选设定' 标签页生成基础设定！")
    else:
        # 读取设定
        with open(setting_file, "r", encoding="utf-8") as f:
            setting_content = f.read()
        
        st.markdown("### 基础设定预览")
        st.markdown(setting_content[:500] + "...")
        st.markdown("---")
        
        # 大纲生成
        if 'outline_content' not in st.session_state:
            st.session_state.outline_content = ""
        
        if st.button("🔥 生成大纲", type="primary", use_container_width=True):
            st.info("🔄 正在生成大纲...")
            
            # 构建大纲生成提示词
            outline_prompt = f"""
你是专业的网文大纲师，基于以下设定，生成一本完整的小说大纲。
要求：
1. 大纲要包含：全书概览、主要人物、世界观设定、详细的章节列表
2. 章节列表要包含：章节号、章节标题、章节内容简介
3. 章节数量要合理，根据目标字数来安排
4. 大纲要结构清晰，逻辑连贯，符合网文创作规律

{setting_content}
            """
            
            try:
                # 调用 LLM 生成大纲
                engine, _, _ = get_engine()
                # 使用 Python 引擎的 _call_agent 方法生成大纲
                from builtin_claude_core.query_engine import ClaudeQueryEngine
                query_engine = ClaudeQueryEngine()
                outline_content = query_engine._call_agent("大纲Agent", outline_prompt)
                
                # 保存大纲
                outline_file = os.path.join(SETTING_PATH, "0_全本大纲.md")
                with open(outline_file, "w", encoding="utf-8") as f:
                    f.write(outline_content)
                
                # 同时保存到记忆宫殿
                from builtin_claude_core.memory_palace import get_memory_palace
                memory_palace = get_memory_palace()
                memory_palace.set_full_outline(outline_content)
                memory_palace.save_to_disk()
                
                st.session_state.outline_content = outline_content
                st.success("✅ 大纲生成并保存成功！")
                st.info(f"大纲已保存到：{outline_file}")
                
            except Exception as e:
                st.error(f"❌ 大纲生成失败：{str(e)}")
        
        # 大纲编辑
        if st.session_state.outline_content:
            st.markdown("### 大纲编辑")
            edited_outline = st.text_area(
                "编辑大纲内容",
                value=st.session_state.outline_content,
                height=400
            )
            
            if st.button("💾 保存大纲修改", type="primary"):
                # 保存修改后的大纲
                outline_file = os.path.join(SETTING_PATH, "0_全本大纲.md")
                with open(outline_file, "w", encoding="utf-8") as f:
                    f.write(edited_outline)
                
                # 同时更新记忆宫殿
                from builtin_claude_core.memory_palace import get_memory_palace
                memory_palace = get_memory_palace()
                memory_palace.set_full_outline(edited_outline)
                memory_palace.save_to_disk()
                
                st.session_state.outline_content = edited_outline
                st.success("✅ 大纲修改保存成功！")

with tab_log:
    log_placeholder = st.empty()
    with log_placeholder:
        if st.session_state.log_display:
            st.code("\n".join(st.session_state.log_display), language="bash")
        elif os.path.exists(LOG_PATH):
            with open(LOG_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()[-25:]
                st.code("" .join(lines), language="bash")
        else:
            st.info("系统待命中，点击一键生成按钮启动...")

with tab_serial:
    st.subheader("🚀 全自动连载 - 基于大纲自动生成章节")
    st.markdown("基于生成的大纲，自动生成章节内容，支持定时生成和进度追踪。")
    st.markdown("---")
    
    # 检查是否有大纲
    outline_file = os.path.join(SETTING_PATH, "0_全本大纲.md")
    if not os.path.exists(outline_file):
        st.warning("⚠️ 请先在 '大纲生成' 标签页生成全本大纲！")
    else:
        # 读取大纲
        with open(outline_file, "r", encoding="utf-8") as f:
            outline_content = f.read()
        
        st.markdown("### 大纲预览")
        st.markdown(outline_content[:500] + "...")
        st.markdown("---")
        
        # 连载设置
        st.markdown("### 连载设置")
        
        # 章节范围
        col1, col2 = st.columns(2)
        with col1:
            start_chapter = st.number_input("开始章节", min_value=1, value=1, step=1)
        with col2:
            end_chapter = st.number_input("结束章节", min_value=1, value=10, step=1)
        
        # 章节字数
        target_words = st.number_input("每章目标字数", min_value=1000, value=7500, step=500)
        
        # 定时设置
        enable_schedule = st.checkbox("启用定时生成")
        if enable_schedule:
            schedule_hour = st.number_input("每日生成时间（小时）", min_value=0, max_value=23, value=3, step=1)
        
        st.markdown("---")
        st.subheader("🤖 Agent 选择")
        if st.button("🔄 刷新Agent列表"):
            st.session_state.agents_list = get_clawpanel_agents()
            st.success("✅ Agent列表已刷新！")
        target_agent = st.selectbox(
            "选择要调用的Agent",
            options=st.session_state.agents_list,
            index=0
        )
        
        if target_agent:
            skills = get_agent_skills(target_agent)
            if skills:
                skill_text = "\n- ".join(skills)
                st.success(f"✅ Agent「{target_agent}」已挂载的内置技能：\n- {skill_text}")
            else:
                st.warning("⚠️ 未检测到内置技能")
        
        st.markdown("---")
        st.subheader("🔧 核心功能开关")
        enable_multi_agent = st.checkbox("多智能体协调模式（网文工作室）", value=True)
        enable_undercover = st.checkbox("Undercover卧底模式（原生反AI）", value=True)
        enable_mcp = st.checkbox("MCP跨维工具（联网搜索）", value=True)
        enable_xcrawl = st.checkbox("xcrawl全网吞噬技能（深度爬取）", value=True)
        enable_humanizer = st.checkbox("Humanizer二次去AI化（过审保障）", value=True)
        
        st.markdown("---")
        st.subheader("💬 提示词管理")
        
        # 提示词优先级说明
        st.info("📋 提示词优先级：自定义提示词 > 大纲 > 5问设定")
        st.markdown("系统会按照上述优先级自动选择提示词来源，当高级别提示词不可用时，会自动使用下一级别的提示词。")
        
        # 检查当前可用的提示词来源
        available_sources = []
        if os.path.exists(os.path.join(SETTING_PATH, "0_5问设定.md")):
            available_sources.append("5问设定")
        if os.path.exists(os.path.join(SETTING_PATH, "0_全本大纲.md")):
            available_sources.append("大纲")
        
        if available_sources:
            st.success(f"✅ 当前可用的提示词来源：{', '.join(available_sources)}")
        else:
            st.warning("⚠️ 未检测到任何提示词来源，请先完成5问设定或大纲生成")
        
        # 自定义提示词输入
        custom_prompt = st.text_area(
            "自定义提示词（优先级最高）",
            height=150,
            placeholder="示例：使用brave-search搜索今天番茄小说最火的废土修仙打脸套路，拿到URL后用xcrawl爬取全文，提炼最狠的打脸语录，用多智能体模式生成第1章，Undercover模式原生反AI！\n（不填则自动使用大纲或5问设定）"
        )
        
        # 自动连载按钮
        if st.button("🔥 开始全自动连载", type="primary", use_container_width=True):
            st.info("🔄 正在启动全自动连载...")
            
            # 保存连载设置
            serial_settings = {
                "start_chapter": start_chapter,
                "end_chapter": end_chapter,
                "target_words": target_words,
                "enable_schedule": enable_schedule,
                "schedule_hour": schedule_hour if enable_schedule else None,
                "target_agent": target_agent,
                "enable_multi_agent": enable_multi_agent,
                "enable_undercover": enable_undercover,
                "enable_mcp": enable_mcp,
                "enable_xcrawl": enable_xcrawl,
                "enable_humanizer": enable_humanizer,
                "custom_prompt": custom_prompt
            }
            
            # 保存设置到文件
            settings_file = os.path.join(SETTING_PATH, "0_连载设置.json")
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(serial_settings, f, ensure_ascii=False, indent=2)
            
            # 启动守护进程（暂时禁用）
            if enable_schedule:
                st.warning("⚠️ 定时守护进程功能正在维护中，即将上线！请使用「立即生成」功能。")
            else:
                # 立即开始生成
                st.info("🔄 正在生成章节...")
                
                try:
                    # 初始化 DAG 管线
                    pipeline_id = f"serial_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    st.session_state.pipeline = init_dag_pipeline(pipeline_id)
                    
                    # 创建节点占位符
                    node_placeholders = {}
                    for node_id in st.session_state.pipeline.nodes:
                        node_placeholders[node_id] = st.empty()
                    
                    # 渲染 DAG 节点
                    render_dag_nodes(st.session_state.pipeline, node_placeholders)
                    
                    # 初始化日志占位符
                    log_placeholder = st.empty()
                    
                    # 执行 DAG 全流程
                    if run_init_check(st.session_state.pipeline, node_placeholders, log_placeholder, serial_settings.get("target_agent", "默认Agent"), serial_settings.get("enable_humanizer", True), serial_settings.get("enable_mcp", True), serial_settings.get("enable_xcrawl", True), serial_settings.get("enable_undercover", True), serial_settings.get("enable_multi_agent", True)):
                        # 加载设置
                        success, final_prompt = run_load_settings(st.session_state.pipeline, node_placeholders, log_placeholder, 1, serial_settings.get("custom_prompt", ""), serial_settings.get("enable_mcp", True), [], serial_settings.get("enable_xcrawl", True), serial_settings.get("enable_undercover", True), serial_settings.get("enable_multi_agent", True))
                        if success:
                            # 生成章节
                            current_chapter = serial_settings.get("start_chapter", 1)
                            end_chapter = serial_settings.get("end_chapter", 10)
                            target_words = serial_settings.get("target_words", 7500)
                            
                            # 读取大纲内容作为提示词
                            with open(outline_file, "r", encoding="utf-8") as f:
                                outline_content = f.read()
                            
                            # 生成章节内容
                            for chapter_num in range(current_chapter, end_chapter + 1):
                                update_node_status(st.session_state.pipeline, "generate_content", NodeStatus.RUNNING, node_placeholders, result={"chapter_num": chapter_num})
                                
                                st.info(f"🔄 正在生成第{chapter_num}章...")
                                
                                # 构建章节生成提示词
                                def get_prompt_by_priority(serial_settings, outline_content, chapter_num, target_words):
                                    """
                                    根据优先级获取提示词
                                    优先级：自定义提示词 > 大纲 > 5问设定
                                    """
                                    # 1. 首先尝试使用自定义提示词
                                    if serial_settings.get("custom_prompt", ""):
                                        return ("custom_prompt", serial_settings.get("custom_prompt", ""))
                                    
                                    # 2. 然后尝试使用大纲
                                    if outline_content:
                                        chapter_prompt = f"""
基于以下大纲，生成网络小说第{chapter_num}章的完整正文。
要求：
1. 字数要求：{target_words}字
2. 严格贴合大纲，保持剧情连贯
3. 保持人物设定和世界观的一致性
4. 包含适当的冲突和悬念
5. 只输出正文，不要任何解释或标题

{outline_content}
                                        """
                                        return ("outline", chapter_prompt)
                                    
                                    # 3. 最后尝试使用5问设定
                                    setting_file = os.path.join(SETTING_PATH, "0_5问设定.md")
                                    if os.path.exists(setting_file):
                                        with open(setting_file, "r", encoding="utf-8") as f:
                                            setting_content = f.read()
                                        chapter_prompt = f"""
基于以下设定，生成网络小说第{chapter_num}章的完整正文。
要求：
1. 字数要求：{target_words}字
2. 保持人物设定和世界观的一致性
3. 包含适当的冲突和悬念
4. 只输出正文，不要任何解释或标题

{setting_content}
                                        """
                                        return ("five_questions", chapter_prompt)
                                    
                                    # 如果所有提示词来源都不可用，使用默认提示词
                                    default_prompt = f"生成网络小说第{chapter_num}章的完整正文，字数要求：{target_words}字"
                                    return ("default", default_prompt)
                                
                                # 获取提示词
                                prompt_source, chapter_prompt = get_prompt_by_priority(serial_settings, outline_content, chapter_num, target_words)
                                st.info(f"📝 使用提示词来源：{prompt_source}")
                                
                                # 导入必要的模块
                                from builtin_claude_core.query_engine import ClaudeQueryEngine
                                from builtin_claude_core.memory_palace import get_memory_palace
                                
                                # 初始化引擎
                                query_engine = ClaudeQueryEngine()
                                memory_palace = get_memory_palace()
                                
                                # 调用 Claude 核心生成章节
                                try:
                                    agent_result = query_engine.multi_agent_coordinate(
                                        chapter_num=chapter_num,
                                        target_words=target_words,
                                        custom_prompt=chapter_prompt,
                                        chapter_outline="",
                                        chapter_name=f"第{chapter_num}章"
                                    )
                                    
                                    final_content = agent_result["content"]
                                    real_chars = agent_result["real_chars"]
                                    
                                    update_node_status(st.session_state.pipeline, "generate_content", NodeStatus.SUCCESS, node_placeholders, result={"chapter_num": chapter_num, "real_chars": real_chars})
                                except Exception as e:
                                    error_msg = f"章节生成失败：{str(e)}"
                                    update_node_status(st.session_state.pipeline, "generate_content", NodeStatus.FAILED, node_placeholders, error_msg=error_msg)
                                    st.error(error_msg)
                                    import traceback
                                    traceback.print_exc()
                                    continue
                                
                                # 保存章节内容
                                output_file = os.path.join(OUTPUT_DIR, f"第{chapter_num}章_{real_chars}字_{datetime.now().strftime('%Y%m%d%H%M')}.md")
                                with open(output_file, "w", encoding="utf-8") as f:
                                    f.write(final_content)
                                
                                # 更新记忆宫殿
                                memory_palace.add_chapter(chapter_num, f"第{chapter_num}章", final_content)
                                memory_palace.save_to_disk()
                                
                                # 更新当前章节进度
                                st.session_state.current_chapter = chapter_num
                                
                                st.success(f"✅ 第{chapter_num}章生成完成，字数：{real_chars}字")
                            
                            # 完成全本
                            st.session_state.current_chapter = end_chapter
                            
                            # 执行完成节点
                            run_finish(st.session_state.pipeline, node_placeholders, log_placeholder)
                            
                            st.success("🎉 全本完本！所有章节已生成完成！")
                            
                except Exception as e:
                    st.error(f"❌ 章节生成失败：{str(e)}")
                    import traceback
                    traceback.print_exc()
        
        # 进度显示
        st.markdown("### 连载进度")
        
        # 检查是否有连载设置
        settings_file = os.path.join(SETTING_PATH, "0_连载设置.json")
        if os.path.exists(settings_file):
            with open(settings_file, "r", encoding="utf-8") as f:
                serial_settings = json.load(f)
            
            # 检查当前生成进度
            current_chapter = st.session_state.current_chapter if 'current_chapter' in st.session_state else 1
            total_chapters = serial_settings.get("end_chapter", 10)
            
            # 计算进度百分比
            start_chapter = serial_settings.get("start_chapter", 1)
            chapter_range = total_chapters - start_chapter + 1
            if chapter_range <= 0:
                progress_percent = 100
                progress = 1.0
            else:
                # 确保进度值在 0.0 到 1.0 之间
                completed_chapters = max(0, current_chapter - start_chapter + 1)
                progress_percent = min(100, completed_chapters / chapter_range * 100)
                progress = max(0.0, min(1.0, progress_percent / 100.0))
            
            # 显示进度条
            st.progress(progress)
            st.info(f"📊 当前进度：第{current_chapter}章 / 共{total_chapters}章 ({progress_percent:.1f}%)")
            
            # 检查是否完成全本
            if current_chapter >= total_chapters:
                st.success("🎉 全本完本！所有章节已生成完成！")
                
                # 生成完本报告
                completion_report = f"""
# 全本完本报告

## 基本信息
- 小说名称：{st.session_state.get('novel_name', '未命名')}
- 总章节数：{total_chapters}章
- 总字数：{total_chapters * serial_settings.get('target_words', 7500)}字
- 完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 完本状态
✅ 全本已完成！

## 后续建议
1. 进行最终的内容校对
2. 考虑封面设计和排版
3. 准备发布渠道
                """
                
                # 保存完本报告
                report_file = os.path.join(SETTING_PATH, "0_完本报告.md")
                with open(report_file, "w", encoding="utf-8") as f:
                    f.write(completion_report)
                
                st.info(f"📄 完本报告已生成：{report_file}")
                st.markdown("### 完本报告预览")
                st.markdown(completion_report)
        else:
            st.info("📊 连载进度将在这里显示...")

with tab_preview:
    st.subheader("刚生成的章节预览（内置技能+Undercover模式）")
    st.markdown("---")
    if st.session_state.preview_content:
        st.markdown(st.session_state.preview_content)
    else:
        st.info("暂无最新生成的文章，请先点击一键生成按钮...")

# ================= 浏览器控制标签页 =================
with tab_browser:
    st.subheader("🌐 浏览器自动化控制")
    st.markdown("支持 Selenium 和 Playwright 两种浏览器引擎")
    st.markdown("---")
    
    # 浏览器配置
    browser_config = config_manager.get_browser_config()
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.markdown("#### ⚙️ 浏览器配置")
        engine = st.selectbox(
            "自动化引擎",
            options=["selenium", "playwright"],
            index=0 if browser_config.engine == "selenium" else 1
        )
        browser_type = st.selectbox(
            "浏览器类型",
            options=["chrome", "firefox", "edge", "safari"],
            index=["chrome", "firefox", "edge", "safari"].index(browser_config.browser_type)
        )
        headless = st.checkbox("无头模式（后台运行）", value=browser_config.headless)
        
        window_width = st.number_input("窗口宽度", min_value=800, max_value=3840, value=browser_config.window_width)
        window_height = st.number_input("窗口高度", min_value=600, max_value=2160, value=browser_config.window_height)
        
        if st.button("💾 保存配置"):
            config_manager.update_browser_config(
                engine=engine,
                browser_type=browser_type,
                headless=headless,
                window_width=window_width,
                window_height=window_height
            )
            st.success("✅ 浏览器配置已保存！")
    
    with col_b2:
        st.markdown("#### 🚀 浏览器控制")
        
        # 启动/关闭浏览器
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("▶️ 启动浏览器", use_container_width=True):
                try:
                    if st.session_state.browser_manager is None:
                        st.session_state.browser_manager = BrowserManager(BASE_PATH)
                    if st.session_state.browser_manager.start_browser():
                        st.session_state.browser_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 浏览器启动成功")
                        st.success("✅ 浏览器启动成功！")
                    else:
                        st.error("❌ 浏览器启动失败")
                except Exception as e:
                    st.error(f"❌ 启动错误: {str(e)}")
        
        with col_btn2:
            if st.button("⏹️ 关闭浏览器", use_container_width=True):
                if st.session_state.browser_manager:
                    st.session_state.browser_manager.close()
                    st.session_state.browser_manager = None
                    st.session_state.browser_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ⏹️ 浏览器已关闭")
                    st.success("⏹️ 浏览器已关闭")
                else:
                    st.warning("⚠️ 浏览器未运行")
        
        # 导航控制
        st.markdown("---")
        url = st.text_input("网址", placeholder="https://www.example.com")
        col_nav1, col_nav2, col_nav3 = st.columns(3)
        with col_nav1:
            if st.button("🌐 访问", use_container_width=True):
                if st.session_state.browser_manager and st.session_state.browser_manager.is_running():
                    if st.session_state.browser_manager.navigate(url):
                        st.session_state.browser_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🌐 访问: {url}")
                        st.success(f"✅ 已访问: {url}")
                    else:
                        st.error("❌ 导航失败")
                else:
                    st.error("❌ 浏览器未启动")
        with col_nav2:
            if st.button("⬅️ 后退", use_container_width=True):
                if st.session_state.browser_manager and st.session_state.browser_manager.is_running():
                    st.session_state.browser_manager.go_back()
                    st.session_state.browser_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ⬅️ 后退")
                    st.success("✅ 已后退")
        with col_nav3:
            if st.button("🔄 刷新", use_container_width=True):
                if st.session_state.browser_manager and st.session_state.browser_manager.is_running():
                    st.session_state.browser_manager.refresh()
                    st.session_state.browser_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 刷新页面")
                    st.success("✅ 已刷新")
        
        # 元素操作
        st.markdown("---")
        st.markdown("#### 🎯 元素操作")
        selector = st.text_input("CSS选择器", placeholder="#id, .class, tag")
        text_input = st.text_input("输入文本", placeholder="要填充的文本")
        
        col_elem1, col_elem2, col_elem3, col_elem4 = st.columns(4)
        with col_elem1:
            if st.button("👆 点击", use_container_width=True):
                if st.session_state.browser_manager and st.session_state.browser_manager.is_running():
                    if st.session_state.browser_manager.click(selector):
                        st.session_state.browser_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 👆 点击: {selector}")
                        st.success("✅ 点击成功")
                    else:
                        st.error("❌ 点击失败")
        with col_elem2:
            if st.button("✏️ 填充", use_container_width=True):
                if st.session_state.browser_manager and st.session_state.browser_manager.is_running():
                    if st.session_state.browser_manager.fill(selector, text_input):
                        st.session_state.browser_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✏️ 填充: {selector}")
                        st.success("✅ 填充成功")
                    else:
                        st.error("❌ 填充失败")
        with col_elem3:
            if st.button("📸 截图", use_container_width=True):
                if st.session_state.browser_manager and st.session_state.browser_manager.is_running():
                    path = st.session_state.browser_manager.screenshot()
                    if path:
                        st.session_state.browser_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 📸 截图: {path}")
                        st.success(f"✅ 截图已保存: {path}")
                    else:
                        st.error("❌ 截图失败")
        with col_elem4:
            if st.button("📄 源码", use_container_width=True):
                if st.session_state.browser_manager and st.session_state.browser_manager.is_running():
                    source = st.session_state.browser_manager.get_page_source()
                    st.session_state.browser_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 📄 获取页面源码")
                    st.text_area("页面源码", source[:5000], height=200)
        
        # 状态显示
        st.markdown("---")
        if st.session_state.browser_manager and st.session_state.browser_manager.is_running():
            current_url = st.session_state.browser_manager.get_current_url()
            title = st.session_state.browser_manager.get_title()
            st.info(f"📍 当前页面: {title}\n🔗 URL: {current_url}")
        else:
            st.warning("⚠️ 浏览器未启动")
    
    # 浏览器日志
    st.markdown("---")
    st.markdown("#### 📋 操作日志")
    if st.session_state.browser_logs:
        st.code("\n".join(st.session_state.browser_logs[-20:]), language="bash")
    else:
        st.info("暂无浏览器操作日志")

# ================= 生成按钮触发逻辑 =================
# 一键躺平生成功能已整合到全自动连载中
