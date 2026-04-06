import streamlit as st
import subprocess
import os
import hashlib
from typing import Dict, Any, Optional, List
from models.dag import DAGPipeline, DAGNode, NodeStatus
from state.manager import StateManager
from utils.helpers import get_resource_path, check_daemon_status, get_clawpanel_agents, get_agent_skills
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from builtin_claude_core.file_lock import lock_manager


def _get_node_state_hash(node: DAGNode) -> str:
    state_str = f"{node.node_id}:{node.status.value}:{node.start_time}:{node.end_time}"
    return hashlib.md5(state_str.encode()).hexdigest()


def _get_pipeline_state_hash(pipeline: DAGPipeline) -> str:
    hashes = [_get_node_state_hash(node) for node in pipeline.nodes.values()]
    return hashlib.md5("".join(hashes).encode()).hexdigest()


def render_header():
    """简洁的页面头部"""
    st.title("🚀 OpenMars")
    
    st.markdown("""
    <style>
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        margin: 4px;
        border-radius: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-size: 12px;
        font-weight: 500;
    }
    .quick-start-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 24px;
        color: white;
        margin-bottom: 24px;
    }
    .metric-card {
        background: #f8fafc;
        border-radius: 8px;
        padding: 16px;
        border: 1px solid #e2e8f0;
    }
    .section-divider {
        margin: 32px 0;
        border: none;
        height: 1px;
        background: #e2e8f0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    status_badges = (
        "<span class='status-badge'>✅ 内置技能</span>"
        "<span class='status-badge'>✅ 多智能体</span>"
        "<span class='status-badge'>✅ Undercover Mode</span>"
    )
    st.markdown(status_badges, unsafe_allow_html=True)


def render_quick_start():
    """新手快速入门区域"""
    with st.container():
        st.markdown("""
        <div class="quick-start-card">
            <h2 style="margin: 0 0 12px 0;">👋 欢迎使用OpenMars</h2>
            <p style="margin: 0 0 20px 0; opacity: 0.9;">一键生成专业网文小说，从大纲到发布全自动化</p>
            <div style="display: flex; gap: 12px; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 200px;">
                    <div style="font-size: 24px; margin-bottom: 4px;">📝</div>
                    <div style="font-weight: 600;">1. 选择配置</div>
                    <div style="font-size: 14px; opacity: 0.8;">设置章节、字数、目标平台</div>
                </div>
                <div style="flex: 1; min-width: 200px;">
                    <div style="font-size: 24px; margin-bottom: 4px;">🚀</div>
                    <div style="font-weight: 600;">2. 一键生成</div>
                    <div style="font-size: 14px; opacity: 0.8;">点击按钮，全自动生成</div>
                </div>
                <div style="flex: 1; min-width: 200px;">
                    <div style="font-size: 24px; margin-bottom: 4px;">📤</div>
                    <div style="font-weight: 600;">3. 导出发布</div>
                    <div style="font-size: 14px; opacity: 0.8;">支持多平台格式导出</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_metrics():
    """关键指标展示"""
    col1, col2, col3, col4 = st.columns(4)
    
    chapter_num_file = os.path.expanduser("~/OpenMars_Arch/current_chapter.txt")
    current_chapter = "1"
    if os.path.exists(chapter_num_file):
        with lock_manager.with_lock(chapter_num_file):
            with open(chapter_num_file, "r") as f:
                current_chapter = f.read().strip() or "1"
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div style="font-size: 12px; color: #64748b; margin-bottom: 4px;">当前章节</div>
            <div style="font-size: 28px; font-weight: 700; color: #1e293b;">第 {} 章</div>
        </div>
        """.format(current_chapter), unsafe_allow_html=True)
    
    with col2:
        output_dir = get_resource_path("output")
        file_count = 0
        if os.path.exists(output_dir):
            file_count = len([f for f in os.listdir(output_dir) if f.endswith('.md')])
        
        st.markdown("""
        <div class="metric-card">
            <div style="font-size: 12px; color: #64748b; margin-bottom: 4px;">已生成章节</div>
            <div style="font-size: 28px; font-weight: 700; color: #1e293b;">{} 章</div>
        </div>
        """.format(file_count), unsafe_allow_html=True)
    
    with col3:
        daemon_status = check_daemon_status()
        status_text = "运行中" if daemon_status else "未运行"
        status_color = "#10b981" if daemon_status else "#f59e0b"
        
        st.markdown("""
        <div class="metric-card">
            <div style="font-size: 12px; color: #64748b; margin-bottom: 4px;">自动更新</div>
            <div style="font-size: 28px; font-weight: 700; color: {};">{}</div>
        </div>
        """.format(status_color, status_text), unsafe_allow_html=True)
    
    with col4:
        from skill_loader import get_skill_loader
        try:
            loader = get_skill_loader()
            skill_count = len(loader.list_skills())
        except:
            skill_count = 4
        
        st.markdown("""
        <div class="metric-card">
            <div style="font-size: 12px; color: #64748b; margin-bottom: 4px;">专业技能</div>
            <div style="font-size: 28px; font-weight: 700; color: #1e293b;">{} 个</div>
        </div>
        """.format(skill_count), unsafe_allow_html=True)


def render_main_panel_improved(state: StateManager):
    """优化后的主面板 - 工业化、简洁、小白友好"""
    
    render_quick_start()
    
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    
    st.subheader("📊 实时状态")
    render_metrics()
    
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    
    st.subheader("⚙️ 生成配置")
    
    col_lazy1, col_lazy2 = st.columns([1, 1])
    
    with col_lazy1:
        col1, col2 = st.columns(2)
        
        with col1:
            chapter_num = st.number_input(
                "章节号",
                min_value=1,
                max_value=9999,
                value=state.current_chapter,
                help="要生成的章节编号"
            )
        
        with col2:
            target_words = st.number_input(
                "目标字数",
                min_value=500,
                max_value=50000,
                value=7500,
                step=500,
                help="每章目标字数，建议 7500 字"
            )
        
        agents = get_clawpanel_agents()
        if agents:
            target_agent = st.selectbox(
                "写作风格",
                options=agents,
                index=0,
                help="选择不同的写作风格"
            )
        else:
            target_agent = "default"
        
        st.markdown("---")
        st.subheader("🔧 功能开关")
        
        enable_openharness = st.checkbox(
            "🚀 使用 OpenHarness 增强引擎（Beta）",
            value=False,
            help="使用 OpenHarness 增强引擎（实验功能）"
        )
        
        enable_skills = st.checkbox(
            "🎯 网文创作专属技能增强",
            value=True,
            help="使用专业的网文创作技能指导生成"
        )
        
        enable_multi_agent = st.checkbox(
            "🤝 多智能体协作模式",
            value=True,
            help="多个智能体协作创作，质量更高"
        )
        
        enable_humanizer = st.checkbox(
            "🧹 Humanizer 二次去 AI 化",
            value=True,
            help="让内容更像真人写的，提高过审率"
        )
    
    with col_lazy2:
        custom_prompt = st.text_area(
            "自定义指令（可选）",
            height=120,
            placeholder="例如：写一个废土修仙打脸爽文，主角杀伐果断，300字一个小爽点...",
            help="有特殊要求可以在这里说明，不填则使用默认配置"
        )
        
        st.markdown("---")
        st.subheader("📝 生成历史")
        
        output_dir = get_resource_path("output")
        if os.path.exists(output_dir):
            files = sorted([f for f in os.listdir(output_dir) if f.endswith('.md')], reverse=True)
            if files:
                selected_file = st.selectbox(
                    "选择已生成的章节",
                    options=["-- 选择文件 --"] + files[:10],
                    help="查看或续写之前生成的章节"
                )
                
                if selected_file != "-- 选择文件 --":
                    file_path = os.path.join(output_dir, selected_file)
                    with lock_manager.with_lock(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    with st.expander("📖 查看内容"):
                        st.markdown(content)
            else:
                st.info("还没有生成任何章节")
        else:
            st.info("输出目录不存在，首次生成后自动创建")
    
    st.markdown("---")
    
    col_btn1, col_btn2 = st.columns([2, 1])
    
    with col_btn1:
        lazy_btn = st.button(
            "🔥 一键躺平生成",
            type="primary",
            use_container_width=True,
            help="点击开始全自动生成"
        )
    
    with col_btn2:
        if st.button("📚 查看帮助", use_container_width=True):
            st.session_state.show_help = not st.session_state.get('show_help', False)
    
    if st.session_state.get('show_help', False):
        with st.expander("💡 使用帮助", expanded=True):
            st.markdown("""
            ### 快速开始
            
            1. **设置章节号** - 从第 1 章开始，依次生成
            2. **设置目标字数** - 建议 7500 字/章，符合番茄/起点标准
            3. **选择写作风格** - 不同风格适合不同平台
            4. **点击一键生成** - 全自动生成，无需干预
            
            ### 功能说明
            
            - **网文创作专属技能** - 使用专业的大纲、人设、伏笔、平台适配技能
            - **多智能体协作** - 大纲师 + 主笔 + 校验师，质量更高
            - **Humanizer 去 AI 化** - 让内容更像真人写的
            
            ### 平台建议
            
            - **番茄小说**：节奏快，2000-3000字/章
            - **起点中文网**：世界观大，3000-5000字/章
            - **晋江文学城**：情感细腻，2000-4000字/章
            """)
    
    return (
        chapter_num, target_words, target_agent, enable_openharness, 
        enable_skills, enable_multi_agent, enable_humanizer,
        custom_prompt, lazy_btn
    )


def render_dag_nodes(pipeline: DAGPipeline, placeholders: Dict, previous_hash: Optional[str] = None) -> Optional[str]:
    """简洁的 DAG 节点渲染"""
    current_hash = _get_pipeline_state_hash(pipeline)
    
    if previous_hash == current_hash:
        return current_hash
    
    node_list = list(pipeline.nodes.values())
    for i, (node_id, placeholder) in enumerate(placeholders.items()):
        if i < len(node_list):
            node = node_list[i]
            status_emoji = {
                "PENDING": "⏳",
                "RUNNING": "🔄",
                "SUCCESS": "✅",
                "FAILED": "❌"
            }.get(node.status.value, "⏳")
            
            status_color = {
                "PENDING": "#94a3b8",
                "RUNNING": "#3b82f6",
                "SUCCESS": "#10b981",
                "FAILED": "#ef4444"
            }.get(node.status.value, "#94a3b8")
            
            with placeholder:
                st.markdown(f"""
                <div style="
                    background: {status_color}15;
                    border: 2px solid {status_color};
                    border-radius: 8px;
                    padding: 12px 16px;
                    margin-bottom: 8px;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="font-size: 20px; margin-right: 8px;">{status_emoji}</span>
                            <span style="font-weight: 600; font-size: 14px;">{node.node_name}</span>
                        </div>
                        <span style="
                            font-size: 12px;
                            color: {status_color};
                            font-weight: 500;
                        ">{node.status.value.upper()}</span>
                    </div>
                    <div style="font-size: 12px; color: #64748b; margin-top: 4px;">
                        {node.description}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    return current_hash


__all__ = [
    "render_header",
    "render_main_panel_improved",
    "render_dag_nodes",
    "render_quick_start",
    "render_metrics"
]
