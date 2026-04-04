import streamlit as st
import subprocess
import os
import hashlib
from typing import Dict, Any, Optional, List
from models.dag import DAGPipeline, DAGNode, NodeStatus
from state.manager import StateManager
from utils.helpers import get_resource_path, check_daemon_status, get_clawpanel_agents, get_agent_skills

def _get_node_state_hash(node: DAGNode) -> str:
    """计算节点状态的哈希值，用于判断是否需要更新
    
    Args:
        node: DAG节点
        
    Returns:
        状态哈希值
    """
    state_str = f"{node.node_id}:{node.status.value}:{node.start_time}:{node.end_time}"
    return hashlib.md5(state_str.encode()).hexdigest()

def _get_pipeline_state_hash(pipeline: DAGPipeline) -> str:
    """计算整个管线状态的哈希值
    
    Args:
        pipeline: DAG管线
        
    Returns:
        管线状态哈希值
    """
    hashes = [_get_node_state_hash(node) for node in pipeline.nodes.values()]
    return hashlib.md5("".join(hashes).encode()).hexdigest()

def render_header():
    """渲染页面头部"""
    st.title("🌌 赛博印钞机 Pro Mac版")
    status_badges = (
        "<span class='status-badge'>✅ 内置技能物理内聚合并</span>"
        "<span class='status-badge'>✅ Claude官方内核级Undercover Mode</span>"
        "<span class='status-badge'>✅ 多智能体网文工作室</span>"
        "<span class='status-badge'>✅ Kairos自主守护进程</span>"
        "<span class='status-badge'>🛡️ 企业级DAG事务保障</span>"
    )
    st.markdown(status_badges, unsafe_allow_html=True)

def render_daemon_panel(state: StateManager):
    """渲染守护进程控制面板
    
    Args:
        state: 应用状态
    """
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
                daemon_script_path = get_resource_path("claw_kairos_daemon.sh")
                subprocess.Popen([daemon_script_path, str(gen_hour)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setsid)
                st.success(f"✅ 守护进程已启动，每日凌晨{gen_hour}点自动生成章节")
                st.rerun()
    
    with col_daemon2:
        chapter_num_file = os.path.expanduser("~/OpenClaw_Arch/current_chapter.txt")
        if os.path.exists(chapter_num_file):
            with open(chapter_num_file, "r") as f:
                current_chapter_daemon = f.read().strip()
            st.info(f"📊 当前守护进程章节号：第{current_chapter_daemon}章 | 日志路径：~/OpenClaw_Arch/kairos_daemon.log")
        else:
            st.info("📊 守护进程章节号未初始化，首次生成后自动同步")

def render_dag_nodes(pipeline: DAGPipeline, placeholders: Dict, previous_hash: Optional[str] = None) -> Optional[str]:
    """渲染DAG节点状态，按需更新
    
    Args:
        pipeline: DAG管线
        placeholders: UI占位符字典
        previous_hash: 上次渲染的管线状态哈希值
        
    Returns:
        当前管线状态哈希值
    """
    current_hash = _get_pipeline_state_hash(pipeline)
    
    if previous_hash == current_hash:
        return current_hash
    
    node_list = list(pipeline.nodes.values())
    for i, (node_id, placeholder) in enumerate(placeholders.items()):
        if i < len(node_list):
            node = node_list[i]
            with placeholder:
                node_html = f"""
                <div class="node-card {node.status.value}">
                    <div style="font-weight: bold; font-size: 1.1em; margin-bottom: 0.5em;">{node.node_name}</div>
                    <div style="font-size: 0.9em; color: #64748b;">{node.description}</div>
                </div>
                """
                st.markdown(node_html, unsafe_allow_html=True)
    
    return current_hash

def render_main_panel(state: StateManager):
    """渲染核心操作区
    
    Args:
        state: 应用状态
    """
    st.markdown("### 🛋️ 究极躺平区（内置技能+全功能加持）")
    with st.container():
        col_lazy1, col_lazy2 = st.columns([1, 2])
        with col_lazy1:
            chapter_num = st.number_input("生成章节号", min_value=1, value=state.current_chapter, step=1)
            target_words = st.number_input("目标字数", min_value=1000, value=7500, step=500)
            
            st.markdown("---")
            st.subheader("🤖 龙虾Agent选择")
            if st.button("🔄 刷新Agent列表"):
                state.agents_list = get_clawpanel_agents()
                st.success("✅ Agent列表已刷新！")
            target_agent = st.selectbox(
                "选择要调用的Agent",
                options=state.agents_list,
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
    
    return (
        chapter_num, target_words, target_agent, enable_multi_agent, 
        enable_undercover, enable_mcp, enable_xcrawl, 
        enable_humanizer, custom_prompt, lazy_btn
    )

def render_tabs(state: StateManager, log_placeholder):
    """渲染标签页
    
    Args:
        state: 应用状态
        log_placeholder: 日志占位符
    """
    tab_memory, tab_log, tab_preview = st.tabs(["🏛️ 记忆宫殿", "📟 实时日志", "📖 章节预览"])

    with tab_memory:
        st.subheader("当前锁死的全局设定（结构化记忆系统）")
        setting_path = get_resource_path("novel_settings")
        if not os.path.exists(setting_path):
            os.makedirs(setting_path)
        setting_files = sorted([f for f in os.listdir(setting_path) if f.endswith(".md")])
        
        if setting_files:
            selected_file = st.selectbox("选择设定文件进行查看/微调", options=setting_files)
            with open(os.path.join(setting_path, selected_file), "r", encoding="utf-8") as f:
                file_content = f.read()
            edit_content = st.text_area(f"内容：{selected_file}", value=file_content, height=300)
            if st.button("💾 保存微调", type="primary"):
                with open(os.path.join(setting_path, selected_file), "w", encoding="utf-8") as f:
                    f.write(edit_content)
                st.success("✅ 修改已保存生效！")
        else:
            st.info("⚠️ 记忆宫殿空空如也，请重新运行部署脚本！")

    with tab_log:
        with log_placeholder:
            if state.log_display:
                _render_paginated_logs(state.log_display)
            elif os.path.exists(get_resource_path("system.log")):
                with open(get_resource_path("system.log"), "r", encoding="utf-8") as f:
                    lines = f.readlines()[-100:]
                _render_paginated_logs(lines)
            else:
                st.info("系统待命中，点击一键生成按钮启动...")

    with tab_preview:
        st.subheader("刚生成的章节预览（内置技能+Undercover模式）")
        st.markdown("---")
        if state.preview_content:
            st.markdown(state.preview_content)
        else:
            st.info("暂无最新生成的文章，请先点击一键生成按钮...")

def _render_paginated_logs(log_lines: List[str], page_size: int = 25):
    """渲染分页日志
    
    Args:
        log_lines: 日志行列表
        page_size: 每页显示的日志行数
    """
    if not log_lines:
        return
    
    total_lines = len(log_lines)
    total_pages = (total_lines + page_size - 1) // page_size
    
    if total_pages > 1:
        page_num = st.slider("选择日志页", min_value=1, max_value=total_pages, value=total_pages)
    else:
        page_num = 1
    
    start_idx = (page_num - 1) * page_size
    end_idx = min(start_idx + page_size, total_lines)
    
    st.code("".join(log_lines[start_idx:end_idx]), language="bash")
    
    if total_pages > 1:
        st.caption(f"显示日志 {start_idx + 1}-{end_idx}，共 {total_lines} 条")
