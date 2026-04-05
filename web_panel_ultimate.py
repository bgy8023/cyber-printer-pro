#!/usr/bin/env python3
"""
终极自定义面板 - 侧边栏 + 多工作区 + 大模型配置
2025-2026 年最佳设计实践
"""
import streamlit as st
from datetime import datetime
from typing import Dict, Any
import os

def init_session_state():
    """初始化所有session_state变量"""
    if 'state' not in st.session_state:
        from state.manager import StateManager
        st.session_state.state = StateManager()
        st.session_state.state.load_current_chapter()
    if 'log_display' not in st.session_state:
        st.session_state.log_display = []
    if 'rollback_data' not in st.session_state:
        st.session_state.rollback_data = {}
    if 'current_workspace' not in st.session_state:
        st.session_state.current_workspace = 'quick'
    if 'sidebar_expanded' not in st.session_state:
        st.session_state.sidebar_expanded = True

init_session_state()
state = st.session_state.state

st.set_page_config(
    page_title="🚀 赛博印钞机 Pro - 终极面板",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
/* 全局样式 */
.main .block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}

/* 侧边栏样式 */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
}

[data-testid="stSidebar"] [data-testid="stMarkdown"] h1,
[data-testid="stSidebar"] [data-testid="stMarkdown"] h2,
[data-testid="stSidebar"] [data-testid="stMarkdown"] h3 {
    color: white !important;
}

[data-testid="stSidebar"] label {
    color: #cbd5e1 !important;
}

/* 工作区按钮样式 */
.workspace-btn {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border-radius: 8px;
    border: none;
    background: transparent;
    color: #94a3b8;
    cursor: pointer;
    width: 100%;
    text-align: left;
    font-size: 14px;
    margin-bottom: 4px;
    transition: all 0.2s ease;
}

.workspace-btn:hover {
    background: rgba(255, 255, 255, 0.1);
    color: white;
}

.workspace-btn.active {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.workspace-icon {
    font-size: 18px;
    width: 24px;
    text-align: center;
}

/* 卡片样式 */
.ultimate-card {
    background: white;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 16px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.ultimate-card h3 {
    margin: 0 0 16px 0;
    color: #1e293b;
    font-size: 18px;
    font-weight: 600;
}

/* 大模型配置样式 */
.llm-config-section {
    background: #f8fafc;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
}

.llm-config-section h4 {
    margin: 0 0 12px 0;
    color: #475569;
    font-size: 14px;
    font-weight: 600;
}

/* 状态栏样式 */
.status-bar {
    display: flex;
    gap: 16px;
    padding: 12px 24px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    color: white;
    margin-bottom: 24px;
}

.status-item {
    display: flex;
    flex-direction: column;
}

.status-label {
    font-size: 12px;
    opacity: 0.8;
    margin-bottom: 2px;
}

.status-value {
    font-size: 20px;
    font-weight: 700;
}

/* 生成按钮样式 */
.generate-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 16px 32px;
    border-radius: 12px;
    font-size: 18px;
    font-weight: 600;
    cursor: pointer;
    width: 100%;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.generate-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.generate-btn:active {
    transform: translateY(0);
}

/* 分隔线 */
.section-divider {
    border: none;
    height: 1px;
    background: #e2e8f0;
    margin: 24px 0;
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("# 🚀 赛博印钞机")
    st.markdown("---")
    
    workspaces = {
        'quick': {'icon': '⚡', 'name': '快速模式', 'desc': '30秒上手'},
        'config': {'icon': '⚙️', 'name': '生成配置', 'desc': '详细参数'},
        'llm': {'icon': '🤖', 'name': '大模型配置', 'desc': 'API设置'},
        'skills': {'icon': '🎯', 'name': '技能配置', 'desc': '专业技能'},
        'agents': {'icon': '👥', 'name': '智能体配置', 'desc': '协作模式'},
        'tools': {'icon': '🛠️', 'name': '工具配置', 'desc': '创作工具'},
        'history': {'icon': '📜', 'name': '历史记录', 'desc': '已生成章节'},
        'settings': {'icon': '🔧', 'name': '系统设置', 'desc': '高级选项'}
    }
    
    st.markdown("### 📂 工作区")
    
    for ws_id, ws_info in workspaces.items():
        is_active = st.session_state.current_workspace == ws_id
        btn_style = "workspace-btn active" if is_active else "workspace-btn"
        
        if st.button(
            f"{ws_info['icon']} {ws_info['name']}",
            key=f"ws_{ws_id}",
            use_container_width=True
        ):
            st.session_state.current_workspace = ws_id
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 📊 状态")
    
    chapter_num_file = os.path.expanduser("~/OpenMars_Arch/current_chapter.txt")
    current_chapter = "1"
    if os.path.exists(chapter_num_file):
        with open(chapter_num_file, "r") as f:
            current_chapter = f.read().strip() or "1"
    
    from utils.helpers import get_resource_path
    output_dir = get_resource_path("output")
    file_count = 0
    if os.path.exists(output_dir):
        file_count = len([f for f in os.listdir(output_dir) if f.endswith('.md')])
    
    st.metric("当前章节", f"第 {current_chapter} 章")
    st.metric("已生成", f"{file_count} 章")

current_ws = st.session_state.current_workspace

st.title(f"{workspaces[current_ws]['icon']} {workspaces[current_ws]['name']}")
st.markdown(f"<p style='color: #64748b; margin-top: -8px; margin-bottom: 24px;'>{workspaces[current_ws]['desc']}</p>", unsafe_allow_html=True)

if current_ws == 'quick':
    col1, col2 = st.columns([3, 1])
    
    with col1:
        with st.container():
            st.markdown('<div class="ultimate-card">', unsafe_allow_html=True)
            st.markdown("### 👋 欢迎使用赛博印钞机")
            st.markdown("最简单的配置，小白也能轻松使用！")
            
            c1, c2 = st.columns(2)
            with c1:
                chapter_num = st.number_input("📖 章节号", min_value=1, max_value=9999, value=state.current_chapter)
                target_words = st.number_input("✍️ 目标字数", min_value=500, max_value=50000, value=7500, step=500)
            
            with c2:
                target_platform = st.selectbox("📱 目标平台", ["番茄小说", "起点中文网", "晋江文学城", "纵横中文网", "飞卢小说网"])
                genre = st.selectbox("🎨 小说类型", ["玄幻修仙", "都市异能", "穿越重生", "科幻未来", "悬疑推理", "历史架空", "游戏竞技"])
            
            writing_style = st.selectbox("✒️ 写作风格", ["热血爽文", "轻松搞笑", "细腻情感", "严肃史诗", "快节奏"])
            custom_prompt = st.text_area("💡 自定义指令（可选）", height=80, placeholder="例如：写一个废土修仙打脸爽文，主角杀伐果断...")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        with st.container():
            st.markdown('<div class="ultimate-card">', unsafe_allow_html=True)
            st.markdown("### 🚀 一键生成")
            
            enable_skills = st.checkbox("🎯 技能增强", value=True)
            enable_multi_agent = st.checkbox("👥 多智能体", value=True)
            enable_humanizer = st.checkbox("🧹 去AI化", value=True)
            
            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
            
            lazy_btn = st.button("🔥 一键躺平生成", type="primary", use_container_width=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

elif current_ws == 'config':
    with st.container():
        st.markdown('<div class="ultimate-card">', unsafe_allow_html=True)
        st.markdown("### ⚙️ 生成配置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            chapter_num = st.number_input("章节号", min_value=1, max_value=9999, value=state.current_chapter)
            target_words = st.number_input("目标字数", min_value=500, max_value=50000, value=7500, step=500)
            min_words = st.number_input("最小字数", min_value=100, max_value=target_words, value=max(100, target_words - 1000), step=100)
            chapter_title = st.text_input("章节标题（可选）", placeholder="例如：第1章 觉醒")
        
        with col2:
            from utils.helpers import get_clawpanel_agents
            agents = get_clawpanel_agents()
            target_agent = st.selectbox("写作风格", agents if agents else ["default"])
            temperature = st.slider("创造性（Temperature）", 0.0, 2.0, 0.7, 0.1)
            top_p = st.slider("Top-P 采样", 0.1, 1.0, 0.9, 0.05)
            max_tokens = st.number_input("Max Tokens", min_value=1000, max_value=100000, value=15000, step=1000)
        
        custom_prompt = st.text_area("自定义指令", height=100)
        
        st.markdown('</div>', unsafe_allow_html=True)

elif current_ws == 'llm':
    with st.container():
        st.markdown('<div class="ultimate-card">', unsafe_allow_html=True)
        st.markdown("### 🤖 大模型配置")
        
        llm_provider = st.selectbox("LLM 提供商", ["OpenAI", "Anthropic", "DeepSeek", "MiniMax", "自定义"])
        
        st.markdown('<div class="llm-config-section">', unsafe_allow_html=True)
        st.markdown("#### 🔑 API 配置")
        
        api_key = st.text_input("API Key", type="password", placeholder="sk-...")
        api_base = st.text_input("API Base URL", placeholder="https://api.example.com/v1")
        api_model = st.text_input("Model", placeholder="gpt-4, claude-3, etc.")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="llm-config-section">', unsafe_allow_html=True)
        st.markdown("#### ⚙️ 生成参数")
        
        col1, col2 = st.columns(2)
        with col1:
            temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
            top_p = st.slider("Top-P", 0.1, 1.0, 0.9, 0.05)
        with col2:
            max_tokens = st.number_input("Max Tokens", min_value=1000, max_value=100000, value=15000, step=1000)
            max_retries = st.number_input("重试次数", min_value=1, max_value=10, value=3)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="llm-config-section">', unsafe_allow_html=True)
        st.markdown("#### 💾 保存配置")
        
        if st.button("💾 保存到 .env", type="primary"):
            env_path = ".env"
            lines = []
            if os.path.exists(env_path):
                with open(env_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            
            new_lines = []
            found_keys = set()
            
            for line in lines:
                line = line.strip()
                if line.startswith('OPENAI_API_KEY=') and api_key:
                    new_lines.append(f'OPENAI_API_KEY={api_key}\n')
                    found_keys.add('OPENAI_API_KEY')
                elif line.startswith('OPENAI_API_BASE=') and api_base:
                    new_lines.append(f'OPENAI_API_BASE={api_base}\n')
                    found_keys.add('OPENAI_API_BASE')
                elif line.startswith('OPENAI_MODEL=') and api_model:
                    new_lines.append(f'OPENAI_MODEL={api_model}\n')
                    found_keys.add('OPENAI_MODEL')
                else:
                    new_lines.append(line + '\n')
            
            if api_key and 'OPENAI_API_KEY' not in found_keys:
                new_lines.append(f'OPENAI_API_KEY={api_key}\n')
            if api_base and 'OPENAI_API_BASE' not in found_keys:
                new_lines.append(f'OPENAI_API_BASE={api_base}\n')
            if api_model and 'OPENAI_MODEL' not in found_keys:
                new_lines.append(f'OPENAI_MODEL={api_model}\n')
            
            with open(env_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            st.success("✅ 配置已保存到 .env")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

elif current_ws == 'skills':
    with st.container():
        st.markdown('<div class="ultimate-card">', unsafe_allow_html=True)
        st.markdown("### 🎯 技能配置")
        
        from skill_loader import get_skill_loader
        
        try:
            loader = get_skill_loader()
            all_skills = loader.list_skills()
            
            skill_descriptions = {
                'novel-outline': {
                    'name': '📋 小说大纲规划专家',
                    'desc': '帮助规划完整的小说大纲，包括主线、支线、节奏把控',
                    'recommended': True
                },
                'character-design': {
                    'name': '🎭 人物塑造专家',
                    'desc': '设计立体的人物形象，包括外貌、性格、背景、成长弧光',
                    'recommended': True
                },
                'foreshadowing': {
                    'name': '🎯 伏笔设计与回收专家',
                    'desc': '巧妙埋设伏笔，后期完美回收，让剧情更有张力',
                    'recommended': True
                },
                'platform-adapter': {
                    'name': '📱 平台适配与格式导出',
                    'desc': '根据目标平台调整节奏、格式、敏感词处理',
                    'recommended': True
                }
            }
            
            enable_all_skills = st.checkbox("🎯 一键启用所有技能（推荐）", value=True)
            
            st.markdown('---')
            
            selected_skills = []
            for skill_id in all_skills:
                skill_info = skill_descriptions.get(skill_id, {
                    'name': skill_id,
                    'desc': '自定义技能',
                    'recommended': False
                })
                
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{skill_info['name']}** {'⭐ 推荐' if skill_info['recommended'] else ''}")
                    st.markdown(f"<p style='color: #64748b; margin-top: 4px;'>{skill_info['desc']}</p>", unsafe_allow_html=True)
                with col2:
                    use_skill = st.checkbox(
                        f"启用",
                        value=enable_all_skills or skill_info['recommended'],
                        key=f"skill_{skill_id}"
                    )
                    if use_skill:
                        selected_skills.append(skill_id)
                
                st.markdown('---')
            
            st.info(f"已选择 {len(selected_skills)} 个技能")
            
        except Exception as e:
            st.error(f"技能加载失败: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)

elif current_ws == 'agents':
    with st.container():
        st.markdown('<div class="ultimate-card">', unsafe_allow_html=True)
        st.markdown("### 👥 智能体配置")
        
        enable_multi_agent = st.checkbox("🤝 启用多智能体协作模式", value=True)
        
        if enable_multi_agent:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🎯 核心智能体")
                enable_outliner = st.checkbox("📋 大纲师", value=True, help="负责规划章节大纲和节奏")
                enable_writer = st.checkbox("✍️ 主笔", value=True, help="负责主要内容创作")
                enable_editor = st.checkbox("✏️ 编辑/校验师", value=True, help="负责校验和优化")
            
            with col2:
                st.markdown("#### 🔧 辅助智能体")
                enable_researcher = st.checkbox("🔍 研究员", value=False, help="负责资料收集和研究")
                enable_character_designer = st.checkbox("🎭 人设师", value=False, help="负责人物设计和一致性检查")
                enable_plot_architect = st.checkbox("🏗️ 剧情架构师", value=False, help="负责剧情连贯性和伏笔设计")
            
            st.markdown('---')
            
            st.markdown("#### ⚙️ 协作参数")
            col3, col4 = st.columns(2)
            with col3:
                agent_rounds = st.slider("协作轮次", 1, 5, 2, help="智能体之间的协作轮次")
                max_iterations = st.number_input("最大迭代次数", 1, 10, 3)
            with col4:
                temperature = st.slider("创造性", 0.0, 2.0, 0.7, 0.1)
                top_p = st.slider("Top-P", 0.1, 1.0, 0.9, 0.05)
        
        st.markdown('</div>', unsafe_allow_html=True)

elif current_ws == 'tools':
    with st.container():
        st.markdown('<div class="ultimate-card">', unsafe_allow_html=True)
        st.markdown("### 🛠️ 工具配置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### ✅ 质量工具")
            enable_character_validator = st.checkbox("🎭 人设一致性校验", value=True)
            enable_plot_coherence = st.checkbox("📖 剧情连贯性检测", value=True)
            enable_foreshadowing_detector = st.checkbox("🎯 伏笔检测与管理", value=True)
        
        with col2:
            st.markdown("#### 📝 实用工具")
            enable_sensitive_word_check = st.checkbox("🔍 敏感词检测", value=True)
            enable_quality_score = st.checkbox("⭐ 质量评分", value=True)
            enable_auto_continue = st.checkbox("🔄 自动连续生成", value=False)
        
        if enable_auto_continue:
            max_chapters = st.number_input("连续生成章节数", 2, 100, 10)
        
        st.markdown('</div>', unsafe_allow_html=True)

elif current_ws == 'history':
    with st.container():
        st.markdown('<div class="ultimate-card">', unsafe_allow_html=True)
        st.markdown("### 📜 历史记录")
        
        from utils.helpers import get_resource_path
        output_dir = get_resource_path("output")
        
        if os.path.exists(output_dir):
            files = sorted([f for f in os.listdir(output_dir) if f.endswith('.md')], reverse=True)
            
            if files:
                selected_file = st.selectbox("选择已生成的章节", ["-- 选择文件 --"] + files[:20])
                
                if selected_file != "-- 选择文件 --":
                    file_path = os.path.join(output_dir, selected_file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    st.markdown('---')
                    st.markdown(f"### 📖 {selected_file}")
                    st.markdown(content)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button("📥 下载文件", content, file_name=selected_file)
            else:
                st.info("还没有生成任何章节")
        else:
            st.info("输出目录不存在，首次生成后自动创建")
        
        st.markdown('</div>', unsafe_allow_html=True)

elif current_ws == 'settings':
    with st.container():
        st.markdown('<div class="ultimate-card">', unsafe_allow_html=True)
        st.markdown("### 🔧 系统设置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🚀 功能开关")
            enable_openharness = st.checkbox("OpenHarness 增强引擎（Beta）", value=False)
            enable_undercover = st.checkbox("Undercover 模式", value=True)
            enable_mcp = st.checkbox("MCP 工具调用", value=True)
            enable_xcrawl = st.checkbox("XCrawl 网络爬取", value=True)
        
        with col2:
            st.markdown("#### 📁 输出设置")
            output_format = st.selectbox("输出格式", ["Markdown", "TXT", "HTML"])
            save_raw_output = st.checkbox("保存原始输出", value=True)
            auto_save = st.checkbox("自动保存", value=True)
        
        st.markdown('---')
        
        st.markdown("#### 🔄 DAG 节点配置")
        nodes = [
            ('init_check', '1. 初始化校验', True),
            ('load_settings', '2. 结构化记忆加载', True),
            ('generate_content', '3. 多智能体创作', True),
            ('humanizer_process', '4. 去AI化处理', True),
            ('update_plot', '5. 剧情记忆更新', True),
            ('github_archive', '6. GitHub母本归档', False),
            ('notion_write', '7. Notion分发对账', False),
            ('finish', '8. 全链路闭环', True)
        ]
        
        for node_id, node_name, default_enabled in nodes:
            st.checkbox(node_name, value=default_enabled, key=f"node_{node_id}")
        
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

from models.dag import DAGPipeline
from nodes.init_check import InitCheckNode
from nodes.load_settings import LoadSettingsNode
from nodes.generate_content import GenerateContentNode
from nodes.humanizer_process import HumanizerProcessNode
from nodes.update_plot import UpdatePlotNode
from nodes.github_archive import GitHubArchiveNode
from nodes.notion_write import NotionWriteNode
from nodes.finish import FinishNode
from dag.pipeline import DAGExecutor
from utils.logger import Logger
from utils.helpers import get_resource_path

nodes = [
    InitCheckNode(),
    LoadSettingsNode(),
    GenerateContentNode(),
    HumanizerProcessNode(),
    UpdatePlotNode(),
    GitHubArchiveNode(),
    NotionWriteNode(),
    FinishNode()
]

logger = Logger(get_resource_path("system_ultimate.log"))
executor = DAGExecutor(nodes, logger)

if state.pipeline is None:
    state.pipeline = executor.create_pipeline(f"init_{datetime.now().strftime('%Y%m%d%H%M%S')}")

st.subheader("🔄 执行状态")
node_cols = st.columns(8)
node_placeholders: Dict = {}
for i, col in enumerate(node_cols):
    node_placeholders[f"node_{i}"] = col.empty()

from ui.components_improved import render_dag_nodes
render_dag_nodes(state.pipeline, node_placeholders)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

from ui.components import render_tabs

log_placeholder = st.empty()
render_tabs(state, log_placeholder)

if 'lazy_btn' in locals() and lazy_btn:
    chapter_num = locals().get('chapter_num', state.current_chapter)
    chapter_title = f"第{chapter_num}章"
    pipeline_id = f"novel_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    state.reset()
    state.pipeline = executor.create_pipeline(pipeline_id)
    st.session_state.log_display = []
    st.session_state.rollback_data = {}
    logger.clear()
    
    render_dag_nodes(state.pipeline, node_placeholders)
    
    context = {
        "chapter_num": chapter_num,
        "chapter_title": chapter_title,
        "target_words": locals().get('target_words', 7500),
        "target_agent": locals().get('target_agent', 'default'),
        "enable_openharness": locals().get('enable_openharness', False),
        "enable_multi_agent": locals().get('enable_multi_agent', True),
        "enable_undercover": locals().get('enable_undercover', True),
        "enable_mcp": locals().get('enable_mcp', True),
        "enable_xcrawl": locals().get('enable_xcrawl', True),
        "enable_humanizer": locals().get('enable_humanizer', True),
        "enable_skills": locals().get('enable_skills', True),
        "custom_prompt": locals().get('custom_prompt', '')
    }
    
    if 'target_platform' in locals() and 'genre' in locals() and 'writing_style' in locals():
        context['custom_prompt'] = f"""平台：{locals()['target_platform']}
类型：{locals()['genre']}
风格：{locals()['writing_style']}
{context['custom_prompt']}"""
    
    def update_logs(log_text):
        logs = log_text.split("\n")
        st.session_state.log_display = logs
        state.log_display = logs
        with log_placeholder:
            st.code("\n".join(logs), language="bash")
        render_dag_nodes(state.pipeline, node_placeholders)
    
    success = executor.execute(state.pipeline, context)
    
    if success:
        state.preview_content = context.get("final_content", "")
        st.success("🎉 全流程闭环完成！")
        st.balloons()
        st.rerun()
