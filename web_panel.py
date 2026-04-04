import streamlit as st
from datetime import datetime
from typing import Dict

# 初始化应用状态
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

init_session_state()
state = st.session_state.state

# 应用CSS样式
from ui.styles import get_css_styles
st.markdown(get_css_styles(), unsafe_allow_html=True)

# 渲染页面组件
from ui.components import (
    render_header,
    render_daemon_panel,
    render_dag_nodes,
    render_main_panel,
    render_tabs
)

render_header()
st.markdown("---")
render_daemon_panel(state)
st.markdown("---")

# DAG节点状态面板
st.subheader("📊 DAG工作流节点状态")
node_cols = st.columns(8)
node_placeholders: Dict = {}
for i, col in enumerate(node_cols):
    node_placeholders[f"node_{i}"] = col.empty()

# 初始化DAG管线
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
from utils.helpers import get_resource_path, get_mcp_servers

# 创建节点列表和执行器
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

logger = Logger(get_resource_path("system.log"))
executor = DAGExecutor(nodes, logger)

# 初始化DAG管线
if state.pipeline is None:
    state.pipeline = executor.create_pipeline(f"init_{datetime.now().strftime('%Y%m%d%H%M%S')}")

# 渲染DAG节点
render_dag_nodes(state.pipeline, node_placeholders)
st.markdown("---")

# 渲染核心操作区
(chapter_num, target_words, target_agent, enable_multi_agent, 
 enable_undercover, enable_mcp, enable_xcrawl, 
 enable_humanizer, custom_prompt, lazy_btn) = render_main_panel(state)

# 渲染标签页
log_placeholder = st.empty()
render_tabs(state, log_placeholder)

# 生成按钮触发逻辑
if lazy_btn:
    chapter_title = f"第{chapter_num}章"
    pipeline_id = f"novel_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # 重置状态
    state.reset()
    state.pipeline = executor.create_pipeline(pipeline_id)
    st.session_state.log_display = []
    st.session_state.rollback_data = {}
    logger.clear()
    
    # 重新渲染DAG节点
    render_dag_nodes(state.pipeline, node_placeholders)
    
    # 构建执行上下文
    context = {
        "chapter_num": chapter_num,
        "chapter_title": chapter_title,
        "target_words": target_words,
        "target_agent": target_agent,
        "enable_multi_agent": enable_multi_agent,
        "enable_undercover": enable_undercover,
        "enable_mcp": enable_mcp,
        "enable_xcrawl": enable_xcrawl,
        "enable_humanizer": enable_humanizer,
        "custom_prompt": custom_prompt
    }
    
    # 定义UI回调
    def update_logs(log_text):
        st.session_state.log_display = log_text.split("\n")
        with log_placeholder:
            st.code("\n".join(st.session_state.log_display), language="bash")
        # 更新DAG节点UI
        render_dag_nodes(state.pipeline, node_placeholders)
    
    # 执行DAG管线
    success = executor.execute(state.pipeline, context)
    
    if success:
        # 更新预览内容
        state.preview_content = context.get("final_content", "")
        st.success("🎉 全流程闭环完成！内置技能+Undercover模式+多智能体加持，质量拉满！下一章章节号已自动更新！")
        st.rerun()
