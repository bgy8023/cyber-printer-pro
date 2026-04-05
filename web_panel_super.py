#!/usr/bin/env python3
"""
超级自定义面板 Web 入口
功能完整，小白友好，Agent 爱好者的天堂！
"""
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
    page_title="🚀 赛博印钞机 Pro - 超级面板",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

from ui.super_panel import render_super_main_panel

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

logger = Logger(get_resource_path("system_super.log"))
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

st.markdown("---")

config, lazy_btn = render_super_main_panel(state)

from ui.components import render_tabs

log_placeholder = st.empty()
render_tabs(state, log_placeholder)

if lazy_btn:
    chapter_num = config.get('chapter_num', state.current_chapter)
    chapter_title = f"第{chapter_num}章"
    pipeline_id = f"novel_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    state.reset()
    state.pipeline = executor.create_pipeline(pipeline_id)
    st.session_state.log_display = []
    st.session_state.rollback_data = {}
    logger.clear()
    
    render_dag_nodes(state.pipeline, node_placeholders)
    
    mode = config.get('mode', 'quick')
    
    context = {
        "chapter_num": chapter_num,
        "chapter_title": chapter_title,
        "target_words": config.get('target_words', 7500),
        "target_agent": config.get('target_agent', 'default'),
        "enable_openharness": config.get('advanced_config', {}).get('enable_openharness', False),
        "enable_multi_agent": config.get('enable_multi_agent', True),
        "enable_undercover": config.get('advanced_config', {}).get('enable_undercover', True),
        "enable_mcp": config.get('advanced_config', {}).get('enable_mcp', True),
        "enable_xcrawl": config.get('advanced_config', {}).get('enable_xcrawl', True),
        "enable_humanizer": config.get('enable_humanizer', True),
        "enable_skills": config.get('enable_skills', True),
        "custom_prompt": config.get('custom_prompt', '')
    }
    
    if mode == 'quick':
        platform = config.get('target_platform', '番茄小说')
        genre = config.get('genre', '玄幻修仙')
        style = config.get('writing_style', '热血爽文')
        context['custom_prompt'] = f"""平台：{platform}
类型：{genre}
风格：{style}
{context['custom_prompt']}"""
    
    advanced_config = config.get('advanced_config', {})
    if advanced_config:
        context.update({
            "temperature": advanced_config.get('temperature', 0.7),
            "top_p": advanced_config.get('top_p', 0.9),
            "max_tokens": advanced_config.get('max_tokens', 15000),
            "max_retries": advanced_config.get('max_retries', 3),
            "retry_delay": advanced_config.get('retry_delay', 5),
            "output_format": advanced_config.get('output_format', 'Markdown'),
            "save_raw_output": advanced_config.get('save_raw_output', True)
        })
    
    agent_config = config.get('agent_config', {})
    if agent_config:
        context['agent_config'] = agent_config
    
    selected_skills = config.get('selected_skills', [])
    if selected_skills:
        context['selected_skills'] = selected_skills
    
    tools_config = config.get('tools_config', {})
    if tools_config:
        context['tools_config'] = tools_config
    
    pipeline_config = config.get('pipeline_config', {})
    if pipeline_config:
        context['pipeline_config'] = pipeline_config
    
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
