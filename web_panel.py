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
        st.session_state.agents_list = ['default']

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

def get_clawpanel_agents() -> List[str]:
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
    if log_placeholder:
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
            [GEN_SCRIPT_PATH, "0", prompt, "100", "default", "false", "false"],
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
            write_log(f"⚠️ [节点1] Agent {target_agent} 不在检测列表中，尝试使用default", log_placeholder)
        
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

def run_generate_content(pipeline: DAGPipeline, node_placeholders: Dict, log_placeholder, chapter_num: int, chapter_title: str, final_prompt: str, target_words: int, target_agent: str, enable_humanizer: bool, enable_multi_agent: bool) -> tuple[bool, str, int]:
    update_node_status(pipeline, "generate_content", NodeStatus.RUNNING, node_placeholders)
    write_log(f"🤖 [节点3] 开始多智能体创作（多Agent：{'已激活' if enable_multi_agent else '未激活'}）", log_placeholder)
    
    try:
        if GEN_SCRIPT_PATH and os.path.exists(GEN_SCRIPT_PATH):
            env = os.environ.copy()
            if hasattr(sys, '_MEIPASS'):
                env["APP_BUILTIN_RESOURCES"] = sys._MEIPASS
            
            process = subprocess.Popen(
                [GEN_SCRIPT_PATH, str(chapter_num), final_prompt, str(target_words), target_agent, "false", "true" if enable_multi_agent else "false"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                bufsize=1,
                universal_newlines=True,
                env=env
            )
            
            for line in process.stdout:
                if line.strip():
                    write_log(f"[Claude Core] {line.strip()}", log_placeholder)
            process.wait(timeout=300)
            if process.returncode not in [0, 124]:
                raise Exception(f"生成脚本执行失败，返回码：{process.returncode}")
        else:
            raise Exception("未找到生成脚本")
        
        write_log("📂 [节点3] 正在从输出目录提取小说正文...", log_placeholder)
        generated_content = extract_latest_novel_from_output()
        if not generated_content:
            raise Exception("无法从输出目录提取小说正文")
        
        generated_content = clean_mermaid_code(generated_content)
        real_chars = count_real_chars(generated_content)
        if real_chars < target_words * 0.95:
            raise Exception(f"字数不达标！目标{target_words}字，仅生成{real_chars}字")
        
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
        write_log("⚠️ [节点4] 已关闭去AI化处理，跳过本节点", log_placeholder)
        update_node_status(pipeline, "humanizer_process", NodeStatus.SKIPPED, node_placeholders)
        return True, raw_content
    
    try:
        write_log("🧹 [节点4] 正在调用Humanizer技能，二次去AI化", log_placeholder)
        prompt = f"请使用Humanizer技能，对下面的小说正文进行二次去AI化处理，严格保留原剧情、人设、爽点、节奏和字数，只去除残留的AI痕迹，让文本更像真人写的网文，直接输出改写后的完整正文，不要任何额外解释：\n\n{raw_content}"
        
        env = os.environ.copy()
        if hasattr(sys, '_MEIPASS'):
            env["APP_BUILTIN_RESOURCES"] = sys._MEIPASS
        
        process = subprocess.Popen(
            [os.path.join(OPENCLAW_WORKSPACE, "claw"), "chat", prompt, "--agent", target_agent, "--skills", "humanizer"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            bufsize=1,
            universal_newlines=True,
            env=env
        )
        
        humanized_content = ""
        for line in process.stdout:
            if line.strip() and not line.strip().startswith("[") and not line.strip().startswith("✅") and not line.strip().startswith("⚠️") and not line.strip().startswith("❌"):
                humanized_content += line + "\n"
            if line.strip():
                write_log(f"[Humanizer] {line.strip()}", log_placeholder)
        
        process.wait(timeout=180)
        if process.returncode != 0:
            raise Exception("Humanizer技能调用失败")
        
        if not humanized_content or len(humanized_content.strip()) < 100:
            raise Exception("去AI化处理后内容为空，保留原始正文")
        
        raw_chars = count_real_chars(raw_content)
        humanized_chars = count_real_chars(humanized_content)
        if humanized_chars < raw_chars * 0.9:
            write_log(f"⚠️ [节点4] 去AI化后字数缩水，原始{raw_chars}字，处理后{humanized_chars}字，保留原始正文", log_placeholder)
            humanized_content = raw_content
        else:
            st.session_state.preview_content = humanized_content
            write_log(f"✅ [节点4] 去AI化处理完成，处理后有效汉字：{humanized_chars}字", log_placeholder)
        
        update_node_status(pipeline, "humanizer_process", NodeStatus.SUCCESS, node_placeholders, result={"humanized_content": humanized_content})
        return True, humanized_content
    except Exception as e:
        write_log(f"❌ [节点4] 去AI化处理失败：{str(e)}，保留原始正文", log_placeholder)
        update_node_status(pipeline, "humanizer_process", NodeStatus.SUCCESS, node_placeholders)
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

# ================= 页面UI渲染 =================
st.title("🌌 赛博印钞机 Pro Mac版")
st.markdown("""
<span class='status-badge'>✅ 内置技能物理内聚合并</span>
<span class='status-badge'>✅ Claude官方内核级Undercover Mode</span>
<span class='status-badge'>✅ 多智能体网文工作室</span>
<span class='status-badge'>✅ Kairos自主守护进程</span>
<span class='status-badge'>🛡️ 企业级DAG事务保障</span>
""", unsafe_allow_html=True)
st.markdown("---")

# Kairos守护进程控制面板
st.subheader("⏰ Kairos自主守护进程（自动日更，彻底解放双手）")
daemon_status = check_daemon_status()
col_daemon1, col_daemon2 = st.columns([1, 3])
with col_daemon1:
    if daemon_status:
        st.success("✅ 守护进程运行中")
        if st.button("🛑 停止守护进程", type="secondary"):
            subprocess.run(["pkill", "-f", "claw_kairos_daemon"], capture_output=True)
            st.success("✅ 守护进程已停止")
            st.rerun()
    else:
        st.warning("⚠️ 守护进程未运行")
        gen_hour = st.number_input("每日自动生成时间（小时）", min_value=0, max_value=23, value=3)
        if st.button("🚀 启动守护进程", type="primary"):
            env = os.environ.copy()
            if hasattr(sys, '_MEIPASS'):
                env["APP_BUILTIN_RESOURCES"] = sys._MEIPASS
            subprocess.Popen([DAEMON_SCRIPT_PATH, str(gen_hour)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setsid, env=env)
            st.success(f"✅ 守护进程已启动，每日凌晨{gen_hour}点自动生成章节")
            st.rerun()
with col_daemon2:
    if os.path.exists(CHAPTER_NUM_FILE):
        current_chapter_daemon = open(CHAPTER_NUM_FILE, "r").read().strip()
        st.info(f"📊 当前守护进程章节号：第{current_chapter_daemon}章 | 日志路径：~/OpenClaw_Arch/kairos_daemon.log")
    else:
        st.info("📊 守护进程章节号未初始化，首次生成后自动同步")
st.markdown("---")

# DAG节点状态面板
st.subheader("📊 DAG工作流节点状态")
node_cols = st.columns(8)
node_placeholders = {}
for i, col in enumerate(node_cols):
    node_placeholders[f"node_{i}"] = col.empty()

# 初始化DAG管线
if st.session_state.pipeline is None:
    st.session_state.pipeline = init_dag_pipeline(f"init_{datetime.now().strftime('%Y%m%d%H%M%S')}")
render_dag_nodes(st.session_state.pipeline, node_placeholders)
st.markdown("---")

# 核心操作区
st.markdown("### 🛋️ 究极躺平区（内置技能+全功能加持）")
with st.container():
    col_lazy1, col_lazy2 = st.columns([1, 2])
    with col_lazy1:
        chapter_num = st.number_input("生成章节号", min_value=1, value=st.session_state.current_chapter, step=1)
        target_words = st.number_input("目标字数", min_value=1000, value=7500, step=500)
        
        st.markdown("---")
        st.subheader("🤖 龙虾Agent选择")
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
                st.warning(f"⚠️ 未检测到内置技能")
        
        st.markdown("---")
        st.subheader("🔧 核心功能开关")
        enable_multi_agent = st.checkbox("多智能体协调模式（网文工作室）", value=True)
        enable_undercover = st.checkbox("Undercover卧底模式（原生反AI）", value=True)
        enable_mcp = st.checkbox("MCP跨维工具（联网搜索）", value=True)
        enable_xcrawl = st.checkbox("xcrawl全网吞噬技能（深度爬取）", value=True)
        enable_humanizer = st.checkbox("Humanizer二次去AI化（过审保障）", value=True)

    with col_lazy2:
        custom_prompt = st.text_area(
            "一句话指令（内置技能加持，直接说脑洞就行）",
            height=150,
            placeholder="示例：使用brave-search搜索今天番茄小说最火的废土修仙打脸套路，拿到URL后用xcrawl爬取全文，提炼最狠的打脸语录，用多智能体模式生成第1章，Undercover模式原生反AI！\n（不填则用记忆宫殿自动生成）"
        )

st.markdown("###")
lazy_btn = st.button("🔥 一键躺平生成（内置技能+全功能加持）", type="primary", use_container_width=True)
st.markdown("---")

# 标签页
tab_memory, tab_log, tab_preview = st.tabs(["🏛️ 记忆宫殿", "📟 实时日志", "📖 章节预览"])

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

with tab_log:
    log_placeholder = st.empty()
    with log_placeholder:
        if st.session_state.log_display:
            st.code("\n".join(st.session_state.log_display), language="bash")
        elif os.path.exists(LOG_PATH):
            with open(LOG_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()[-25:]
                st.code("".join(lines), language="bash")
        else:
            st.info("系统待命中，点击一键生成按钮启动...")

with tab_preview:
    st.subheader("刚生成的章节预览（内置技能+Undercover模式）")
    st.markdown("---")
    if st.session_state.preview_content:
        st.markdown(st.session_state.preview_content)
    else:
        st.info("暂无最新生成的文章，请先点击一键生成按钮...")

# ================= 生成按钮触发逻辑 =================
if lazy_btn:
    chapter_title = f"第{chapter_num}章"
    pipeline_id = f"novel_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    st.session_state.pipeline = init_dag_pipeline(pipeline_id)
    st.session_state.log_display = []
    st.session_state.rollback_data = {}
    render_dag_nodes(st.session_state.pipeline, node_placeholders)
    
    mcp_servers = get_mcp_servers() if enable_mcp else []
    
    # 执行DAG全流程
    if run_init_check(st.session_state.pipeline, node_placeholders, log_placeholder, target_agent, enable_humanizer, enable_mcp, enable_xcrawl, enable_undercover, enable_multi_agent):
        success, final_prompt = run_load_settings(st.session_state.pipeline, node_placeholders, log_placeholder, chapter_num, custom_prompt, enable_mcp, mcp_servers, enable_xcrawl, enable_undercover, enable_multi_agent)
        if success:
            success, raw_content, real_chars = run_generate_content(st.session_state.pipeline, node_placeholders, log_placeholder, chapter_num, chapter_title, final_prompt, target_words, target_agent, enable_humanizer, enable_multi_agent)
            if success:
                success, final_content = run_humanizer_process(st.session_state.pipeline, node_placeholders, log_placeholder, raw_content, target_agent, enable_humanizer)
                if success:
                    run_update_plot(st.session_state.pipeline, node_placeholders, log_placeholder, final_content, chapter_num)
                    success, github_url, md5 = run_github_archive(st.session_state.pipeline, node_placeholders, log_placeholder, chapter_title, final_content)
                    if success:
                        final_chars = count_real_chars(final_content)
                        if run_notion_write(st.session_state.pipeline, node_placeholders, log_placeholder, chapter_title, final_content, github_url, md5, final_chars):
                            run_finish(st.session_state.pipeline, node_placeholders, log_placeholder)
                            st.success("🎉 全流程闭环完成！内置技能+Undercover模式+多智能体加持，质量拉满！下一章章节号已自动更新！")
                            st.rerun()
