#!/usr/bin/env python3
"""
工业级 Web 面板 - 精简稳定版
OpenMars 工业级 AI 助手
"""
import streamlit as st
from datetime import datetime
from pathlib import Path
import sys
import os
import re

sys.path.insert(0, str(Path(__file__).parent))


def init_industrial_session():
    """初始化工业级会话状态"""
    if 'current_tab' not in st.session_state:
        st.session_state.current_tab = 'chat'
    if 'sidebar_collapsed' not in st.session_state:
        st.session_state.sidebar_collapsed = False
    if 'theme_mode' not in st.session_state:
        st.session_state.theme_mode = 'dark'
    
    if 'current_workspace' not in st.session_state:
        st.session_state.current_workspace = 'chat'
    
    if 'current_chapter' not in st.session_state:
        st.session_state.current_chapter = 1
    if 'target_words' not in st.session_state:
        st.session_state.target_words = 7500
    if 'selected_novel' not in st.session_state:
        st.session_state.selected_novel = "默认小说"
    
    if 'llm_config' not in st.session_state:
        from dotenv import load_dotenv
        load_dotenv()
        st.session_state.llm_config = {
            'provider': os.getenv('LLM_PROVIDER', 'OpenAI'),
            'api_key': os.getenv('LLM_API_KEY', ''),
            'api_base': os.getenv('API_BASE_URL', 'https://api.openai.com/v1'),
            'model': os.getenv('LLM_MODEL_NAME', 'gpt-4o'),
            'temperature': float(os.getenv('LLM_TEMPERATURE', '0.7')),
            'top_p': float(os.getenv('LLM_TOP_P', '0.9')),
            'max_tokens': int(os.getenv('LLM_MAX_TOKENS', '15000')),
            'max_retries': int(os.getenv('MAX_RETRY', '3'))
        }


def save_panel_settings():
    """保存所有面板设置到 JSON 文件"""
    import json
    import tempfile
    
    settings_file = Path("panel_settings.json")
    
    settings = {
        "llm_config": st.session_state.get("llm_config", {}),
        "current_workspace": st.session_state.get("current_workspace", "chat"),
        "theme_mode": st.session_state.get("theme_mode", "dark"),
        "current_chapter": st.session_state.get("current_chapter", 1),
        "target_words": st.session_state.get("target_words", 7500),
        "save_time": datetime.now().isoformat()
    }
    
    try:
        with tempfile.NamedTemporaryFile('w', dir=str(settings_file.parent), delete=False, encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
            temp_name = f.name
        
        os.replace(temp_name, str(settings_file))
        return True, f"设置已保存到 {settings_file}"
    except Exception as e:
        return False, f"保存失败：{str(e)}"


def load_panel_settings():
    """从 JSON 文件加载所有面板设置"""
    import json
    
    settings_file = Path("panel_settings.json")
    
    if not settings_file.exists():
        return False, "设置文件不存在"
    
    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        if "llm_config" in settings:
            st.session_state.llm_config = settings["llm_config"]
        if "current_workspace" in settings:
            st.session_state.current_workspace = settings["current_workspace"]
        if "theme_mode" in settings:
            st.session_state.theme_mode = settings["theme_mode"]
        if "current_chapter" in settings:
            st.session_state.current_chapter = settings["current_chapter"]
        if "target_words" in settings:
            st.session_state.target_words = settings["target_words"]
        
        return True, f"设置已从 {settings_file} 加载"
    except Exception as e:
        return False, f"加载失败：{str(e)}"


def apply_industrial_theme():
    """应用工业级主题"""
    st.markdown("""
    <style>
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            max-width: 100%;
        }
        
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
            border-right: 1px solid #334155;
        }
        
        [data-testid="stSidebar"] [data-testid="stMarkdown"] h1,
        [data-testid="stSidebar"] [data-testid="stMarkdown"] h2,
        [data-testid="stSidebar"] [data-testid="stMarkdown"] h3 {
            color: #f1f5f9 !important;
        }
        
        [data-testid="stSidebar"] label {
            color: #94a3b8 !important;
        }
        
        .stButton > button {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
        }
        
        .industrial-card {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            transition: all 0.2s ease;
        }
        
        .industrial-card:hover {
            border-color: #6366f1;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.1);
        }
        
        .workspace-btn {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            border: none;
            background: transparent;
            color: #94a3b8;
            cursor: pointer;
            width: 100%;
            text-align: left;
            font-size: 0.875rem;
            margin-bottom: 0.25rem;
            transition: all 0.2s ease;
        }
        
        .workspace-btn:hover {
            background: rgba(255, 255, 255, 0.1);
            color: white;
        }
        
        .workspace-btn.active {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
        }
        
        .metric-card {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 1.25rem;
            text-align: center;
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .metric-label {
            color: #94a3b8;
            font-size: 0.875rem;
            margin-top: 0.25rem;
        }
        
        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 500;
        }
        
        .status-online {
            background: rgba(34, 197, 94, 0.2);
            color: #22c55e;
        }
        
        .ultimate-card {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        }
        
        .generate-btn {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
            border: none;
            padding: 1rem 2rem;
            border-radius: 12px;
            font-size: 1.125rem;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        
        .generate-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #0f172a;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #334155;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #475569;
        }
    </style>
    """, unsafe_allow_html=True)


def render_sidebar():
    """渲染工业级侧边栏"""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🚀</div>
            <h1 style="margin: 0; font-size: 1.5rem;">OpenMars</h1>
            <p style="color: #94a3b8; margin: 0.5rem 0 0; font-size: 0.875rem;">工业级 AI 助手</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("""
            <div class="status-indicator status-online">
                <span>●</span>
                <span>在线</span>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style="color: #94a3b8; font-size: 0.8rem; text-align: right;">
                {datetime.now().strftime('%H:%M:%S')}
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        st.markdown("### 📂 工作区")
        
        workspaces = {
            'chat': {'icon': '💬', 'name': 'AI 助手', 'desc': '对话管理'},
            'quick': {'icon': '⚡', 'name': '快速模式', 'desc': '30秒上手'},
            'llm': {'icon': '🤖', 'name': '大模型配置', 'desc': 'API设置'},
            'history': {'icon': '📜', 'name': '历史记录', 'desc': '已生成章节'},
            'settings': {'icon': '🔧', 'name': '系统设置', 'desc': '高级选项'}
        }
        
        for ws_id, ws_info in workspaces.items():
            is_active = st.session_state.current_workspace == ws_id
            if st.button(
                f"{ws_info['icon']} {ws_info['name']}",
                key=f"ws_{ws_id}",
                use_container_width=True
            ):
                st.session_state.current_workspace = ws_id
                st.rerun()
        
        st.divider()
        
        st.markdown("### 📊 状态")
        
        output_dir = Path("output")
        file_count = 0
        if output_dir.exists():
            file_count = len([f for f in os.listdir(output_dir) if f.endswith('.md')])
        
        st.metric("当前章节", f"第 {st.session_state.current_chapter} 章")
        st.metric("已生成", f"{file_count} 章")
        
        st.divider()
        
        st.markdown("### 💾 面板设置")
        
        if st.button("💾 保存所有设置", type="primary", use_container_width=True):
            success, message = save_panel_settings()
            if success:
                st.success(message)
            else:
                st.error(message)
        
        if st.button("📂 加载所有设置", use_container_width=True):
            success, message = load_panel_settings()
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)


def render_chat_workspace():
    """渲染 AI 助手工作区"""
    st.markdown("### 💬 AI 助手 - 对话管理")
    
    chat_container = st.container()
    
    with chat_container:
        if 'chat_messages' not in st.session_state:
            st.session_state.chat_messages = []
        
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
    
    st.divider()
    
    if prompt := st.chat_input("输入消息或命令（/help 查看帮助）"):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
        
        def local_handle_command(cmd: str) -> str:
            cmd = cmd.strip()
            
            if cmd == '/help':
                return """**可用命令：**
- `/help` - 显示此帮助
- `/status` - 查看项目状态
- `/clear` - 清空对话历史
- `/novel list` - 列出小说章节
- `/novel info` - 查看小说信息
- `/config` - 查看当前配置
- `/novel generate` - 生成当前章节
- `/novel chapter N` - 设置章节号（如：/novel chapter 10）
- `/novel words N` - 设置目标字数（如：/novel words 10000）
"""
            elif cmd == '/status':
                output_dir = Path("output")
                file_count = 0
                if output_dir.exists():
                    file_count = len([f for f in os.listdir(output_dir) if f.endswith('.md')])
                
                return f"""**项目状态：**
- 当前章节：第 {st.session_state.current_chapter} 章
- 已生成：{file_count} 章
- 工作区：{st.session_state.current_workspace}
- 目标字数：{st.session_state.target_words} 字
- 小说：{st.session_state.selected_novel}
"""
            elif cmd.startswith('/novel chapter'):
                parts = cmd.split()
                if len(parts) == 3:
                    try:
                        chapter = int(parts[2])
                        st.session_state.current_chapter = chapter
                        return f"✅ 章节号已设置为：第 {chapter} 章"
                    except ValueError:
                        return "❌ 请输入有效的章节号（数字）"
                else:
                    return "❌ 用法：/novel chapter <章节号>"
            elif cmd.startswith('/novel words'):
                parts = cmd.split()
                if len(parts) == 3:
                    try:
                        words = int(parts[2])
                        st.session_state.target_words = words
                        return f"✅ 目标字数已设置为：{words} 字"
                    except ValueError:
                        return "❌ 请输入有效的字数（数字）"
                else:
                    return "❌ 用法：/novel words <目标字数>"
            elif cmd.startswith('/novel generate'):
                return f"""🚀 正在准备生成第 {st.session_state.current_chapter} 章...
请前往 ⚡ 快速模式 工作区点击生成按钮！
或者直接对我说："生成第 {st.session_state.current_chapter} 章"
"""
            elif cmd == '/clear':
                st.session_state.chat_messages = []
                return "✅ 对话历史已清空！"
            
            elif cmd.startswith('/novel list'):
                output_dir = Path("output")
                
                if output_dir.exists():
                    files = sorted([f for f in os.listdir(output_dir) if f.endswith('.md')], reverse=True)
                    if files:
                        file_list = "\n".join([f"- {f}" for f in files[:20]])
                        return f"**已生成的章节（最近 20 个）：**\n{file_list}"
                    else:
                        return "还没有生成任何章节"
                else:
                    return "输出目录不存在"
            
            elif cmd.startswith('/novel info'):
                return "**小说信息：**\n- 项目：OpenMars\n- 类型：玄幻修仙（默认）\n- 状态：运行中"
            
            elif cmd.startswith('/config'):
                env_path = ".env"
                config_info = "**当前配置：**\n"
                
                if os.path.exists(env_path):
                    with open(env_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                key, value = line.split('=', 1) if '=' in line else (line, '')
                                if 'KEY' in key or 'PASSWORD' in key:
                                    config_info += f"- {key}: ********\n"
                                else:
                                    config_info += f"- {key}: {value}\n"
                else:
                    config_info += "未找到 .env 文件"
                
                return config_info
            
            chapter_match = re.search(r'(?:生成|写|来)第\s*(\d+)\s*章', cmd)
            if chapter_match:
                chapter = int(chapter_match.group(1))
                st.session_state.current_chapter = chapter
                return f"""✅ 已设置为第 {chapter} 章！
请前往 ⚡ 快速模式 工作区点击生成按钮！"""
            
            words_match = re.search(r'(?:写|来|目标)\s*(\d+)\s*字', cmd)
            if words_match:
                words = int(words_match.group(1))
                st.session_state.target_words = words
                return f"✅ 目标字数已设置为：{words} 字"
            
            return None
        
        response = local_handle_command(prompt)
        
        if response:
            st.session_state.chat_messages.append({"role": "assistant", "content": response})
            with chat_container:
                with st.chat_message("assistant"):
                    st.markdown(response)
        else:
            try:
                from builtin_claude_core.llm_adapter import get_llm_adapter
                
                adapter = get_llm_adapter()
                
                messages = []
                for msg in st.session_state.chat_messages[-10:]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
                
                with st.spinner("思考中..."):
                    response_content = adapter.generate(
                        prompt=prompt,
                        system_prompt="你是OpenMars 的 AI 助手。你可以帮助用户管理项目、生成小说、查看状态等。回答要友好、专业、简洁。",
                        temperature=0.7
                    )
                
                st.session_state.chat_messages.append({"role": "assistant", "content": response_content})
                
                with chat_container:
                    with st.chat_message("assistant"):
                        st.markdown(response_content)
            
            except Exception as e:
                error_msg = f"抱歉，发生错误：{str(e)}"
                st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
                with chat_container:
                    with st.chat_message("assistant"):
                        st.error(error_msg)
        
        st.rerun()


def render_quick_workspace():
    """渲染快速模式工作区"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown('<div class="industrial-card">', unsafe_allow_html=True)
        st.markdown("### 👋 欢迎使用OpenMars")
        st.markdown("最简单的配置，小白也能轻松使用！")
        
        c1, c2 = st.columns(2)
        with c1:
            chapter_num = st.number_input("📖 章节号", min_value=1, max_value=9999, value=st.session_state.current_chapter)
            target_words = st.number_input("✍️ 目标字数", min_value=500, max_value=50000, value=st.session_state.target_words, step=500)
        
        with c2:
            target_platform = st.selectbox("📱 目标平台", ["番茄小说", "起点中文网", "晋江文学城", "纵横中文网", "飞卢小说网"])
            genre = st.selectbox("🎨 小说类型", ["玄幻修仙", "都市异能", "穿越重生", "科幻未来", "悬疑推理", "历史架空", "游戏竞技"])
        
        writing_style = st.selectbox("✒️ 写作风格", ["热血爽文", "轻松搞笑", "细腻情感", "严肃史诗", "快节奏"])
        custom_prompt = st.text_area("💡 自定义指令（可选）", height=80, placeholder="例如：写一个废土修仙打脸爽文，主角杀伐果断...")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="industrial-card">', unsafe_allow_html=True)
        st.markdown("### 🚀 一键生成")
        
        st.divider()
        
        lazy_btn = st.button("🔥 一键躺平生成", type="primary", use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="industrial-card">', unsafe_allow_html=True)
    st.markdown("### 📋 任务进度")
    
    if lazy_btn:
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()
            log_container = st.container()
            
            status_text.text("🚀 正在初始化生成环境...")
            progress_bar.progress(10)
            
            with log_container:
                st.markdown("#### 📝 实时日志")
                log_placeholder = st.empty()
            
            full_prompt = f"""
写一部{genre}小说，风格是{writing_style}，适合在{target_platform}发布。

{custom_prompt if custom_prompt else '请写出精彩的章节内容'}
""".strip()
            
            status_text.text("🤖 正在调用大模型生成内容...")
            progress_bar.progress(30)
            
            with log_container:
                log_placeholder.info(f"📖 章节：第 {chapter_num} 章")
                log_placeholder.info(f"✍️ 目标字数：{target_words} 字")
                log_placeholder.info(f"🎨 类型：{genre}")
                log_placeholder.info(f"✒️ 风格：{writing_style}")
            
            try:
                from cyber_printer_ultimate import generate_chapter_full
                
                status_text.text("⚡ 正在生成章节内容（这可能需要几分钟）...")
                progress_bar.progress(50)
                
                success, result_content = generate_chapter_full(
                    chapter_num=chapter_num,
                    target_words=target_words,
                    custom_prompt=full_prompt,
                    novel_name="默认小说"
                )
                
                if success:
                    status_text.text("✅ 生成成功！")
                    progress_bar.progress(100)
                    
                    with log_container:
                        log_placeholder.success(f"🎉 生成成功！实际字数：{len(result_content)} 字")
                    
                    st.markdown("#### 📄 生成结果")
                    st.text_area("章节内容", value=result_content, height=400)
                    
                    output_dir = Path("output")
                    output_dir.mkdir(exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_file = output_dir / f"第{chapter_num}章_{timestamp}.md"
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(result_content)
                    
                    st.success(f"✅ 文件已保存到：{output_file}")
                    
                    st.session_state.current_chapter = chapter_num + 1
                    
                else:
                    status_text.text("❌ 生成失败！")
                    progress_bar.progress(100)
                    
                    with log_container:
                        log_placeholder.error(f"❌ 生成失败：{result_content}")
                    
                    st.error(f"生成失败：{result_content}")
                    
            except ImportError as e:
                status_text.text("⚠️ 生成模块未找到，显示演示内容")
                progress_bar.progress(100)
                
                with log_container:
                    log_placeholder.warning(f"⚠️ 演示模式：{e}")
                
                st.markdown("#### 📄 演示内容")
                st.text_area("章节内容", value="这是演示内容，实际使用时请确保 cyber_printer_ultimate.py 存在且配置正确", height=200)
                
        except Exception as e:
            st.error(f"生成过程中发生错误：{e}")
            import traceback
            st.text(traceback.format_exc())
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_llm_workspace():
    """渲染大模型配置工作区（小白友好版）"""
    st.markdown('<div class="industrial-card">', unsafe_allow_html=True)
    st.markdown("### 🤖 大模型配置")
    
    config = st.session_state.llm_config
    
    provider_presets = {
        "🔮 DeepSeek（推荐）": {
            "api_base": "https://api.deepseek.com/v1",
            "models": ["deepseek-chat", "deepseek-coder"]
        },
        "🧠 OpenAI": {
            "api_base": "https://api.openai.com/v1",
            "models": ["gpt-4o", "gpt-4", "gpt-3.5-turbo"]
        },
        "🎯 豆包（ByteDance）": {
            "api_base": "https://ark.cn-beijing.volces.com/api/v3",
            "models": ["ep-20240603010101-xxxxx"]
        },
        "📚 智谱 AI": {
            "api_base": "https://open.bigmodel.cn/api/paas/v4",
            "models": ["glm-4", "glm-3-turbo"]
        },
        "🔧 自定义": {
            "api_base": "https://api.example.com/v1",
            "models": ["custom-model"]
        }
    }
    
    provider_display_names = list(provider_presets.keys())
    
    current_provider_display = "🔮 DeepSeek（推荐）"
    for display_name in provider_presets:
        if config['provider'].lower() in display_name.lower():
            current_provider_display = display_name
            break
    
    selected_provider = st.selectbox(
        "🎁 选择大模型服务商", 
        provider_display_names,
        index=provider_display_names.index(current_provider_display) if current_provider_display in provider_display_names else 0,
        help="选择你常用的服务商，我们会自动填好默认配置"
    )
    
    preset = provider_presets[selected_provider]
    
    st.markdown('<div style="background: #0f172a; border-radius: 8px; padding: 1rem; margin-bottom: 0.75rem;">', unsafe_allow_html=True)
    st.markdown("#### 🔑 API 密钥配置")
    
    api_key = st.text_input(
        "API Key（必填）", 
        type="password", 
        value=config['api_key'],
        placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxx"
    )
    
    auto_api_base = preset['api_base']
    if selected_provider == "🔧 自定义":
        api_base = st.text_input(
            "API Base URL", 
            value=config['api_base'] or auto_api_base,
            placeholder="https://api.example.com/v1"
        )
    else:
        api_base = auto_api_base
        st.info(f"✅ 已自动设置 API Base：{api_base}")
    
    available_models = preset['models']
    if selected_provider != "🔧 自定义" and config['model'] not in available_models:
        api_model = st.selectbox(
            "🤖 选择模型", 
            available_models,
            index=0
        )
    else:
        if selected_provider == "🔧 自定义":
            api_model = st.text_input(
                "模型名称", 
                value=config['model'] or "custom-model",
                placeholder="gpt-4, claude-3, etc."
            )
        else:
            api_model = st.selectbox(
                "🤖 选择模型", 
                available_models,
                index=available_models.index(config['model']) if config['model'] in available_models else 0
            )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div style="background: #0f172a; border-radius: 8px; padding: 1rem; margin-bottom: 0.75rem;">', unsafe_allow_html=True)
    st.markdown("#### ⚙️ 生成参数（新手推荐使用默认值）")
    
    param_presets = {
        "🎨 创意写作": {"temperature": 0.9, "top_p": 0.95, "desc": "适合小说、故事等创意内容"},
        "📝 平衡模式": {"temperature": 0.7, "top_p": 0.9, "desc": "适合大多数场景，推荐新手使用"},
        "🎯 精准回答": {"temperature": 0.3, "top_p": 0.8, "desc": "适合代码、问答等需要精确性的场景"}
    }
    
    preset_names = list(param_presets.keys())
    selected_preset = st.selectbox(
        "🎁 选择参数预设", 
        preset_names,
        index=1,
        help="选择一个预设，我们会自动填好推荐的参数"
    )
    
    preset = param_presets[selected_preset]
    
    col1, col2 = st.columns(2)
    with col1:
        temperature = st.slider(
            "🌡️ 创意程度 (Temperature)", 
            0.0, 2.0, 
            config['temperature'] if 'temperature' in config else preset['temperature'], 
            0.1,
            help="数值越大越有创意，数值越小越精确"
        )
        st.caption(f"💡 推荐值：{preset['temperature']}")
        
        top_p = st.slider(
            "📊 采样范围 (Top-P)", 
            0.1, 1.0, 
            config['top_p'] if 'top_p' in config else preset['top_p'], 
            0.05,
            help="控制模型选择词汇的范围"
        )
        st.caption(f"💡 推荐值：{preset['top_p']}")
    with col2:
        max_tokens = st.number_input(
            "✍️ 单次最大输出字数 (Max Tokens)", 
            min_value=1000, 
            max_value=100000, 
            value=config['max_tokens'] if 'max_tokens' in config else 15000, 
            step=1000,
            help="模型一次最多生成多少字"
        )
        st.caption("💡 推荐值：15000（约 10000 汉字）")
        
        max_retries = st.number_input(
            "🔄 失败重试次数", 
            min_value=1, 
            max_value=10, 
            value=config['max_retries'] if 'max_retries' in config else 3,
            help="生成失败时自动重试的次数"
        )
        st.caption("💡 推荐值：3")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div style="background: #0f172a; border-radius: 8px; padding: 1rem;">', unsafe_allow_html=True)
    st.markdown("#### 💾 保存配置")
    
    if st.button("💾 保存到 .env", type="primary", use_container_width=True):
        provider_name = selected_provider
        if "DeepSeek" in selected_provider:
            provider_name = "DeepSeek"
        elif "OpenAI" in selected_provider:
            provider_name = "OpenAI"
        elif "豆包" in selected_provider:
            provider_name = "ByteDance"
        elif "智谱" in selected_provider:
            provider_name = "Zhipu"
        else:
            provider_name = "Custom"
        
        st.session_state.llm_config.update({
            'provider': provider_name,
            'api_key': api_key,
            'api_base': api_base,
            'model': api_model,
            'temperature': temperature,
            'top_p': top_p,
            'max_tokens': max_tokens,
            'max_retries': max_retries
        })
        
        env_path = ".env"
        lines = []
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        
        new_lines = []
        found_keys = set()
        
        for line in lines:
            line = line.strip()
            updated = False
            if api_key:
                if line.startswith('OPENAI_API_KEY='):
                    new_lines.append(f'OPENAI_API_KEY={api_key}\n')
                    found_keys.add('OPENAI_API_KEY')
                    updated = True
                elif line.startswith('LLM_API_KEY='):
                    new_lines.append(f'LLM_API_KEY={api_key}\n')
                    found_keys.add('LLM_API_KEY')
                    updated = True
            if api_base and not updated:
                if line.startswith('OPENAI_API_BASE='):
                    new_lines.append(f'OPENAI_API_BASE={api_base}\n')
                    found_keys.add('OPENAI_API_BASE')
                    updated = True
                elif line.startswith('API_BASE_URL='):
                    new_lines.append(f'API_BASE_URL={api_base}\n')
                    found_keys.add('API_BASE_URL')
                    updated = True
            if api_model and not updated:
                if line.startswith('LLM_MODEL_NAME='):
                    new_lines.append(f'LLM_MODEL_NAME={api_model}\n')
                    found_keys.add('LLM_MODEL_NAME')
                    updated = True
                elif line.startswith('MODEL='):
                    new_lines.append(f'MODEL={api_model}\n')
                    found_keys.add('MODEL')
                    updated = True
            if temperature and not updated:
                if line.startswith('LLM_TEMPERATURE='):
                    new_lines.append(f'LLM_TEMPERATURE={temperature}\n')
                    found_keys.add('LLM_TEMPERATURE')
                    updated = True
            if max_tokens and not updated:
                if line.startswith('LLM_MAX_TOKENS='):
                    new_lines.append(f'LLM_MAX_TOKENS={max_tokens}\n')
                    found_keys.add('LLM_MAX_TOKENS')
                    updated = True
            if max_retries and not updated:
                if line.startswith('MAX_RETRY='):
                    new_lines.append(f'MAX_RETRY={max_retries}\n')
                    found_keys.add('MAX_RETRY')
                    updated = True
            if not updated:
                if line:
                    new_lines.append(line + '\n')
        
        if api_key and 'OPENAI_API_KEY' not in found_keys and 'LLM_API_KEY' not in found_keys:
            new_lines.append(f'LLM_API_KEY={api_key}\n')
        if api_base and 'OPENAI_API_BASE' not in found_keys and 'API_BASE_URL' not in found_keys:
            new_lines.append(f'API_BASE_URL={api_base}\n')
        if api_model and 'LLM_MODEL_NAME' not in found_keys and 'MODEL' not in found_keys:
            new_lines.append(f'LLM_MODEL_NAME={api_model}\n')
        if temperature and 'LLM_TEMPERATURE' not in found_keys:
            new_lines.append(f'LLM_TEMPERATURE={temperature}\n')
        if max_tokens and 'LLM_MAX_TOKENS' not in found_keys:
            new_lines.append(f'LLM_MAX_TOKENS={max_tokens}\n')
        if max_retries and 'MAX_RETRY' not in found_keys:
            new_lines.append(f'MAX_RETRY={max_retries}\n')
        
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        st.success("✅ 配置已保存到 .env 和 st.session_state！")
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def render_history_workspace():
    """渲染历史记录工作区"""
    st.markdown('<div class="industrial-card">', unsafe_allow_html=True)
    st.markdown("### 📜 历史记录")
    
    output_dir = Path("output")
    
    if output_dir.exists():
        files = sorted([f for f in os.listdir(output_dir) if f.endswith('.md')], reverse=True)
        if files:
            for file in files[:20]:
                file_path = os.path.join(output_dir, file)
                with st.expander(f"📄 {file}", expanded=False):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    st.markdown(content[:5000])
                    if len(content) > 5000:
                        st.info("内容已截断...")
        else:
            st.info("还没有生成任何章节")
    else:
        st.info("输出目录不存在")
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_settings_workspace():
    """渲染系统设置工作区"""
    st.markdown('<div class="industrial-card">', unsafe_allow_html=True)
    st.markdown("### 🔧 系统设置")
    
    st.markdown("#### 📊 系统信息")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Python 版本", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    with col2:
        st.metric("工作目录", str(Path.cwd()))
    
    st.divider()
    
    st.markdown("#### 🗂️ 项目文件")
    
    project_files = [
        "web_panel_industrial.py",
        "cyber_printer_ultimate.py",
        "builtin_claude_core/query_engine.py",
        "builtin_claude_core/memory_palace.py",
        "builtin_claude_core/llm_adapter.py",
        "builtin_claude_core/logger.py"
    ]
    
    for file in project_files:
        file_path = Path(file)
        if file_path.exists():
            size = file_path.stat().st_size
            st.write(f"✅ {file} ({size:,} bytes)")
        else:
            st.write(f"❌ {file} (不存在)")
    
    st.markdown('</div>', unsafe_allow_html=True)


def main():
    """主函数"""
    init_industrial_session()
    
    st.set_page_config(
        page_title="🚀 OpenMars - 工业级 AI 助手",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    apply_industrial_theme()
    render_sidebar()
    
    current_ws = st.session_state.current_workspace
    
    workspaces = {
        'chat': {'icon': '💬', 'name': 'AI 助手', 'desc': '对话管理'},
        'quick': {'icon': '⚡', 'name': '快速模式', 'desc': '30秒上手'},
        'llm': {'icon': '🤖', 'name': '大模型配置', 'desc': 'API设置'},
        'history': {'icon': '📜', 'name': '历史记录', 'desc': '已生成章节'},
        'settings': {'icon': '🔧', 'name': '系统设置', 'desc': '高级选项'}
    }
    
    st.title(f"{workspaces[current_ws]['icon']} {workspaces[current_ws]['name']}")
    st.markdown(f"<p style='color: #94a3b8; margin-top: -8px; margin-bottom: 24px;'>{workspaces[current_ws]['desc']}</p>", unsafe_allow_html=True)
    
    if current_ws == 'chat':
        render_chat_workspace()
    elif current_ws == 'quick':
        render_quick_workspace()
    elif current_ws == 'llm':
        render_llm_workspace()
    elif current_ws == 'history':
        render_history_workspace()
    elif current_ws == 'settings':
        render_settings_workspace()


if __name__ == "__main__":
    main()
