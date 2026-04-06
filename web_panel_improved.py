import streamlit as st
from datetime import datetime
from typing import Dict


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

st.set_page_config(
    page_title="OpenMars",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

from ui.components_improved import (
    render_header,
    render_main_panel_improved,
    render_dag_nodes
)

render_header()

st.markdown("---")

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

logger = Logger(get_resource_path("system.log"))
executor = DAGExecutor(nodes, logger)

if state.pipeline is None:
    state.pipeline = executor.create_pipeline(f"init_{datetime.now().strftime('%Y%m%d%H%M%S')}")

st.subheader("🔄 执行状态")
node_cols = st.columns(8)
node_placeholders: Dict = {}
for i, col in enumerate(node_cols):
    node_placeholders[f"node_{i}"] = col.empty()

render_dag_nodes(state.pipeline, node_placeholders)

st.markdown("---")

(
    chapter_num, target_words, target_agent, enable_openharness,
    enable_skills, enable_multi_agent, enable_humanizer,
    custom_prompt, lazy_btn
) = render_main_panel_improved(state)

from ui.components import render_tabs

log_placeholder = st.empty()
render_tabs(state, log_placeholder)

if lazy_btn:
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
        "target_words": target_words,
        "target_agent": target_agent,
        "enable_openharness": enable_openharness,
        "enable_multi_agent": enable_multi_agent,
        "enable_undercover": True,
        "enable_mcp": True,
        "enable_xcrawl": True,
        "enable_humanizer": enable_humanizer,
        "enable_skills": enable_skills,
        "custom_prompt": custom_prompt
    }
    
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
        st.rerun()
