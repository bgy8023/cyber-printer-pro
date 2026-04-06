"""
超级自定义面板组件 - 功能完整，小白友好
"""
import streamlit as st
import os
from typing import Dict, Any, List
from models.dag import DAGPipeline
from state.manager import StateManager
from utils.helpers import get_resource_path


def render_super_header():
    """超级面板头部"""
    st.markdown("""
    <style>
    .super-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 24px;
        border-radius: 16px;
        color: white;
        margin-bottom: 24px;
    }
    .super-header h1 {
        margin: 0 0 8px 0;
        font-size: 32px;
    }
    .super-header p {
        margin: 0;
        opacity: 0.9;
    }
    .tab-group {
        display: flex;
        gap: 8px;
        margin-bottom: 24px;
    }
    .tab-btn {
        padding: 8px 16px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        background: white;
        cursor: pointer;
        font-size: 14px;
    }
    .tab-btn.active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
    }
    .config-card {
        background: #f8fafc;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        border: 1px solid #e2e8f0;
    }
    .config-card h4 {
        margin: 0 0 16px 0;
        color: #1e293b;
    }
    .skill-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px;
        background: white;
        border-radius: 8px;
        margin-bottom: 8px;
        border: 1px solid #e2e8f0;
    }
    .agent-config {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="super-header">
        <h1>🚀 OpenMars - 超级自定义面板</h1>
        <p>功能完整，小白友好，Agent 爱好者的天堂！</p>
    </div>
    """, unsafe_allow_html=True)


def render_tab_selector():
    """标签页选择器"""
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = 'quick'
    
    tabs = {
        'quick': '⚡ 快速模式',
        'basic': '📝 基础配置',
        'skills': '🎯 技能配置',
        'agents': '🤖 智能体配置',
        'advanced': '🔧 高级配置',
        'tools': '🛠️ 工具配置',
        'pipeline': '🔄 节点配置'
    }
    
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    cols = [col1, col2, col3, col4, col5, col6, col7]
    
    for idx, (key, label) in enumerate(tabs.items()):
        with cols[idx]:
            if st.button(label, key=f"tab_{key}", use_container_width=True):
                st.session_state.active_tab = key
    
    return st.session_state.active_tab


def render_quick_mode(state: StateManager):
    """快速模式 - 小白友好"""
    st.markdown("""
    <div class="config-card">
        <h4>👋 快速模式 - 30秒上手</h4>
        <p>最简单的配置，一键生成，小白也能轻松使用！</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        chapter_num = st.number_input(
            "📖 章节号",
            min_value=1,
            max_value=9999,
            value=state.current_chapter,
            help="要生成的章节编号"
        )
        
        target_words = st.number_input(
            "✍️ 目标字数",
            min_value=500,
            max_value=50000,
            value=7500,
            step=500,
            help="每章目标字数，建议 7500 字"
        )
        
        target_platform = st.selectbox(
            "📱 目标平台",
            options=[
                "番茄小说",
                "起点中文网",
                "晋江文学城",
                "纵横中文网",
                "飞卢小说网",
                "自定义"
            ],
            index=0,
            help="选择目标平台，自动适配节奏和格式"
        )
    
    with col2:
        genre = st.selectbox(
            "🎨 小说类型",
            options=[
                "玄幻修仙",
                "都市异能",
                "穿越重生",
                "科幻未来",
                "悬疑推理",
                "历史架空",
                "游戏竞技",
                "自定义"
            ],
            index=0,
            help="选择小说类型，自动调整写作风格"
        )
        
        writing_style = st.selectbox(
            "✒️ 写作风格",
            options=[
                "热血爽文",
                "轻松搞笑",
                "细腻情感",
                "严肃史诗",
                "快节奏",
                "自定义"
            ],
            index=0,
            help="选择写作风格"
        )
        
        custom_prompt = st.text_area(
            "💡 自定义指令（可选）",
            height=100,
            placeholder="例如：写一个废土修仙打脸爽文，主角杀伐果断...",
            help="有特殊要求可以在这里说明"
        )
    
    st.markdown("---")
    
    col_btn1, col_btn2 = st.columns([3, 1])
    
    with col_btn1:
        lazy_btn = st.button(
            "🔥 一键躺平生成",
            type="primary",
            use_container_width=True
        )
    
    with col_btn2:
        if st.button("📚 查看帮助", use_container_width=True):
            st.session_state.show_help = not st.session_state.get('show_help', False)
    
    if st.session_state.get('show_help', False):
        with st.expander("💡 使用帮助", expanded=True):
            st.markdown("""
            ### 快速模式使用说明
            
            1. **设置章节号** - 从第 1 章开始，依次生成
            2. **设置目标字数** - 建议 7500 字/章
            3. **选择目标平台** - 自动适配节奏和格式
            4. **选择小说类型** - 自动调整写作风格
            5. **点击一键生成** - 全自动生成，无需干预
            
            ### 平台建议
            
            - **番茄小说**：节奏快，2000-3000字/章
            - **起点中文网**：世界观大，3000-5000字/章
            - **晋江文学城**：情感细腻，2000-4000字/章
            """)
    
    return (
        chapter_num, target_words, target_platform, genre, 
        writing_style, custom_prompt, lazy_btn
    )


def render_basic_config(state: StateManager):
    """基础配置"""
    st.markdown("""
    <div class="config-card">
        <h4>📝 基础配置</h4>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        chapter_num = st.number_input(
            "章节号",
            min_value=1,
            max_value=9999,
            value=state.current_chapter
        )
        
        target_words = st.number_input(
            "目标字数",
            min_value=500,
            max_value=50000,
            value=7500,
            step=500
        )
        
        min_words = st.number_input(
            "最小字数",
            min_value=100,
            max_value=target_words,
            value=max(100, target_words - 1000),
            step=100
        )
    
    with col2:
        from utils.helpers import get_clawpanel_agents
        agents = get_clawpanel_agents()
        if agents:
            target_agent = st.selectbox(
                "写作风格",
                options=agents,
                index=0
            )
        else:
            target_agent = "default"
        
        chapter_title = st.text_input(
            "章节标题（可选）",
            placeholder="例如：第1章 觉醒",
            help="自定义章节标题，不填则自动生成"
        )
        
        custom_prompt = st.text_area(
            "自定义指令",
            height=100,
            placeholder="特殊要求可以在这里说明"
        )
    
    return chapter_num, target_words, min_words, target_agent, chapter_title, custom_prompt


def render_skills_config():
    """技能配置"""
    st.markdown("""
    <div class="config-card">
        <h4>🎯 技能配置 - 选择你需要的专业技能</h4>
        <p>每个技能都会影响生成质量，选择适合你小说的技能！</p>
    </div>
    """, unsafe_allow_html=True)
    
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
        
        selected_skills = []
        
        for skill_id in all_skills:
            skill_info = skill_descriptions.get(skill_id, {
                'name': skill_id,
                'desc': '自定义技能',
                'recommended': False
            })
            
            with st.container():
                st.markdown(f"""
                <div class="skill-item">
                    <div style="flex: 1;">
                        <div style="font-weight: 600; margin-bottom: 4px;">
                            {skill_info['name']}
                            {' ⭐ 推荐' if skill_info['recommended'] else ''}
                        </div>
                        <div style="font-size: 14px; color: #64748b;">{skill_info['desc']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                use_skill = st.checkbox(
                    f"启用 {skill_info['name']}",
                    value=skill_info['recommended'],
                    key=f"skill_{skill_id}"
                )
                
                if use_skill:
                    selected_skills.append(skill_id)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            enable_all_skills = st.checkbox(
                "🎯 启用所有技能（推荐）",
                value=True,
                help="一键启用所有专业技能"
            )
        
        with col2:
            custom_skill_path = st.text_input(
                "📁 自定义技能路径（可选）",
                placeholder="例如：/path/to/my/skills",
                help="加载自定义技能目录"
            )
        
        if enable_all_skills:
            selected_skills = all_skills
        
        st.info(f"已选择 {len(selected_skills)} 个技能")
        
        return selected_skills, enable_all_skills, custom_skill_path
        
    except Exception as e:
        st.error(f"技能加载失败: {e}")
        return [], True, ""


def render_agents_config():
    """智能体配置"""
    st.markdown("""
    <div class="config-card">
        <h4>🤖 智能体配置 - 多 Agent 协作模式</h4>
        <p>配置你的写作团队，不同智能体负责不同环节！</p>
    </div>
    """, unsafe_allow_html=True)
    
    enable_multi_agent = st.checkbox(
        "🤝 启用多智能体协作模式",
        value=True,
        help="多个智能体协作创作，质量更高"
    )
    
    if enable_multi_agent:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 核心智能体")
            
            enable_outliner = st.checkbox(
                "📋 大纲师",
                value=True,
                help="负责规划章节大纲和节奏"
            )
            
            enable_writer = st.checkbox(
                "✍️ 主笔",
                value=True,
                help="负责主要内容创作"
            )
            
            enable_editor = st.checkbox(
                "✏️ 编辑/校验师",
                value=True,
                help="负责校验和优化"
            )
        
        with col2:
            st.subheader("🔧 辅助智能体")
            
            enable_researcher = st.checkbox(
                "🔍 研究员",
                value=False,
                help="负责资料收集和研究"
            )
            
            enable_character_designer = st.checkbox(
                "🎭 人设师",
                value=False,
                help="负责人物设计和一致性检查"
            )
            
            enable_plot_architect = st.checkbox(
                "🏗️ 剧情架构师",
                value=False,
                help="负责剧情连贯性和伏笔设计"
            )
        
        st.markdown("---")
        
        st.subheader("⚙️ 协作参数")
        
        col3, col4 = st.columns(2)
        
        with col3:
            agent_rounds = st.slider(
                "协作轮次",
                min_value=1,
                max_value=5,
                value=2,
                help="智能体之间的协作轮次，越多越精细但越慢"
            )
            
            max_iterations = st.number_input(
                "最大迭代次数",
                min_value=1,
                max_value=10,
                value=3,
                help="每个智能体的最大迭代次数"
            )
        
        with col4:
            temperature = st.slider(
                "创造性（Temperature）",
                min_value=0.0,
                max_value=2.0,
                value=0.7,
                step=0.1,
                help="越高越有创意，越低越稳定"
            )
            
            top_p = st.slider(
                "Top-P 采样",
                min_value=0.1,
                max_value=1.0,
                value=0.9,
                step=0.05,
                help="核采样参数"
            )
        
        agent_config = {
            'enable_outliner': enable_outliner,
            'enable_writer': enable_writer,
            'enable_editor': enable_editor,
            'enable_researcher': enable_researcher,
            'enable_character_designer': enable_character_designer,
            'enable_plot_architect': enable_plot_architect,
            'agent_rounds': agent_rounds,
            'max_iterations': max_iterations,
            'temperature': temperature,
            'top_p': top_p
        }
    else:
        agent_config = {}
    
    return enable_multi_agent, agent_config


def render_advanced_config():
    """高级配置"""
    st.markdown("""
    <div class="config-card">
        <h4>🔧 高级配置 - 适合高级用户和 Agent 爱好者</h4>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎨 生成参数")
        
        temperature = st.slider(
            "Temperature（创造性）",
            min_value=0.0,
            max_value=2.0,
            value=0.7,
            step=0.1
        )
        
        top_p = st.slider(
            "Top-P",
            min_value=0.1,
            max_value=1.0,
            value=0.9,
            step=0.05
        )
        
        max_tokens = st.number_input(
            "Max Tokens",
            min_value=1000,
            max_value=100000,
            value=15000,
            step=1000
        )
        
        st.subheader("🔄 重试配置")
        
        max_retries = st.number_input(
            "最大重试次数",
            min_value=1,
            max_value=10,
            value=3
        )
        
        retry_delay = st.number_input(
            "重试延迟（秒）",
            min_value=1,
            max_value=60,
            value=5
        )
    
    with col2:
        st.subheader("🔌 功能开关")
        
        enable_openharness = st.checkbox(
            "🚀 OpenHarness 增强引擎（Beta）",
            value=False
        )
        
        enable_humanizer = st.checkbox(
            "🧹 Humanizer 二次去 AI 化",
            value=True
        )
        
        enable_undercover = st.checkbox(
            "🕵️ Undercover 模式",
            value=True
        )
        
        enable_mcp = st.checkbox(
            "🔗 MCP 工具调用",
            value=True
        )
        
        enable_xcrawl = st.checkbox(
            "🕸️ XCrawl 网络爬取",
            value=True
        )
        
        st.subheader("📁 输出配置")
        
        output_format = st.selectbox(
            "输出格式",
            options=["Markdown", "TXT", "HTML", "PDF"],
            index=0
        )
        
        save_raw_output = st.checkbox(
            "保存原始输出",
            value=True
        )
    
    advanced_config = {
        'temperature': temperature,
        'top_p': top_p,
        'max_tokens': max_tokens,
        'max_retries': max_retries,
        'retry_delay': retry_delay,
        'enable_openharness': enable_openharness,
        'enable_humanizer': enable_humanizer,
        'enable_undercover': enable_undercover,
        'enable_mcp': enable_mcp,
        'enable_xcrawl': enable_xcrawl,
        'output_format': output_format,
        'save_raw_output': save_raw_output
    }
    
    return advanced_config


def render_tools_config():
    """工具配置"""
    st.markdown("""
    <div class="config-card">
        <h4>🛠️ 工具配置 - 网文创作专属工具</h4>
        <p>启用专业的小说创作工具，提升质量！</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        enable_character_validator = st.checkbox(
            "🎭 人设一致性校验",
            value=True,
            help="检查人物设定是否一致，避免人设崩塌"
        )
        
        enable_plot_coherence = st.checkbox(
            "📖 剧情连贯性检测",
            value=True,
            help="检查剧情逻辑是否连贯，避免吃书"
        )
        
        enable_foreshadowing_detector = st.checkbox(
            "🎯 伏笔检测与管理",
            value=True,
            help="检测和管理伏笔，确保伏笔回收"
        )
    
    with col2:
        enable_sensitive_word_check = st.checkbox(
            "🔍 敏感词检测",
            value=True,
            help="检测敏感词，提高过审率"
        )
        
        enable_quality_score = st.checkbox(
            "⭐ 质量评分",
            value=True,
            help="对生成内容进行质量评分"
        )
        
        enable_auto_continue = st.checkbox(
            "🔄 自动连续生成",
            value=False,
            help="生成完一章后自动继续生成下一章"
        )
        
        if enable_auto_continue:
            max_chapters = st.number_input(
                "连续生成章节数",
                min_value=2,
                max_value=100,
                value=10
            )
        else:
            max_chapters = 1
    
    tools_config = {
        'enable_character_validator': enable_character_validator,
        'enable_plot_coherence': enable_plot_coherence,
        'enable_foreshadowing_detector': enable_foreshadowing_detector,
        'enable_sensitive_word_check': enable_sensitive_word_check,
        'enable_quality_score': enable_quality_score,
        'enable_auto_continue': enable_auto_continue,
        'max_chapters': max_chapters
    }
    
    return tools_config


def render_pipeline_config():
    """节点配置"""
    st.markdown("""
    <div class="config-card">
        <h4>🔄 节点配置 - DAG 管线节点</h4>
        <p>配置执行流程中的每个节点，高级用户可以自定义！</p>
    </div>
    """, unsafe_allow_html=True)
    
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
    
    enabled_nodes = []
    
    for node_id, node_name, default_enabled in nodes:
        enabled = st.checkbox(
            node_name,
            value=default_enabled,
            key=f"node_{node_id}"
        )
        if enabled:
            enabled_nodes.append(node_id)
    
    st.markdown("---")
    
    st.subheader("⚙️ 节点参数")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fail_fast = st.checkbox(
            "快速失败模式",
            value=True,
            help="任一节点失败立即停止"
        )
        
        continue_on_error = st.checkbox(
            "出错继续",
            value=False,
            help="非关键节点出错时继续执行"
        )
    
    with col2:
        timeout = st.number_input(
            "节点超时（秒）",
            min_value=60,
            max_value=3600,
            value=600
        )
        
        parallel_execution = st.checkbox(
            "并行执行（实验）",
            value=False,
            help="并行执行独立节点"
        )
    
    pipeline_config = {
        'enabled_nodes': enabled_nodes,
        'fail_fast': fail_fast,
        'continue_on_error': continue_on_error,
        'timeout': timeout,
        'parallel_execution': parallel_execution
    }
    
    return pipeline_config


def render_super_main_panel(state: StateManager):
    """超级主面板 - 集成所有配置"""
    render_super_header()
    
    active_tab = render_tab_selector()
    
    config = {}
    
    if active_tab == 'quick':
        (
            chapter_num, target_words, target_platform, genre,
            writing_style, custom_prompt, lazy_btn
        ) = render_quick_mode(state)
        
        config = {
            'mode': 'quick',
            'chapter_num': chapter_num,
            'target_words': target_words,
            'target_platform': target_platform,
            'genre': genre,
            'writing_style': writing_style,
            'custom_prompt': custom_prompt,
            'enable_skills': True,
            'enable_multi_agent': True,
            'enable_humanizer': True
        }
        
        return config, lazy_btn
    
    elif active_tab == 'basic':
        chapter_num, target_words, min_words, target_agent, chapter_title, custom_prompt = render_basic_config(state)
        
        config = {
            'mode': 'basic',
            'chapter_num': chapter_num,
            'target_words': target_words,
            'min_words': min_words,
            'target_agent': target_agent,
            'chapter_title': chapter_title,
            'custom_prompt': custom_prompt
        }
    
    elif active_tab == 'skills':
        selected_skills, enable_all_skills, custom_skill_path = render_skills_config()
        
        config = {
            'mode': 'skills',
            'selected_skills': selected_skills,
            'enable_all_skills': enable_all_skills,
            'custom_skill_path': custom_skill_path
        }
    
    elif active_tab == 'agents':
        enable_multi_agent, agent_config = render_agents_config()
        
        config = {
            'mode': 'agents',
            'enable_multi_agent': enable_multi_agent,
            'agent_config': agent_config
        }
    
    elif active_tab == 'advanced':
        advanced_config = render_advanced_config()
        
        config = {
            'mode': 'advanced',
            'advanced_config': advanced_config
        }
    
    elif active_tab == 'tools':
        tools_config = render_tools_config()
        
        config = {
            'mode': 'tools',
            'tools_config': tools_config
        }
    
    elif active_tab == 'pipeline':
        pipeline_config = render_pipeline_config()
        
        config = {
            'mode': 'pipeline',
            'pipeline_config': pipeline_config
        }
    
    st.markdown("---")
    
    col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])
    
    with col_btn1:
        lazy_btn = st.button(
            "🔥 一键躺平生成",
            type="primary",
            use_container_width=True
        )
    
    with col_btn2:
        if st.button("📋 导出配置", use_container_width=True):
            st.session_state.export_config = True
    
    with col_btn3:
        if st.button("📥 导入配置", use_container_width=True):
            st.session_state.import_config = True
    
    return config, lazy_btn
