#!/usr/bin/env python3
"""
工业级 AI 项目管家 - 终极版
集成安全模块 + 8 个核心场景命令系统
"""
import streamlit as st
from datetime import datetime
import os
import json
import subprocess
from typing import Dict, Any, List
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

st.set_page_config(
    page_title="🤖 工业级 AI 项目管家",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
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

/* 卡片样式 */
.assistant-card {
    background: white;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 16px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 消息样式 */
.chat-message {
    padding: 16px;
    border-radius: 12px;
    margin-bottom: 12px;
}

.user-message {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.assistant-message {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
}

/* 分隔线 */
.section-divider {
    border: none;
    height: 1px;
    background: #e2e8f0;
    margin: 24px 0;
}

/* 工具按钮样式 */
.tool-btn {
    padding: 8px 16px;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
    background: white;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.2s;
}

.tool-btn:hover {
    background: #f1f5f9;
    border-color: #cbd5e1;
}

.tool-btn.active {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
}

/* 安全标签 */
.security-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: bold;
}

.security-safe {
    background: #10b981;
    color: white;
}

.security-warning {
    background: #f59e0b;
    color: white;
}

.security-danger {
    background: #ef4444;
    color: white;
}
</style>
""", unsafe_allow_html=True)

PROJECT_ROOT = Path(__file__).parent

from security_guard import (
    is_safe_path,
    mask_sensitive_info,
    create_backup,
    restore_backup,
    list_backups,
    safe_read_file,
    safe_write_file,
    safe_delete_file,
    get_security_status,
    get_mode,
    set_mode,
    is_unlimited_mode,
    execute_shell_command,
    PROJECT_ROOT as SG_PROJECT_ROOT
)

def init_session_state():
    """初始化 session_state"""
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    if 'current_chat_id' not in st.session_state:
        st.session_state.current_chat_id = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = {}
    if 'model_config' not in st.session_state:
        st.session_state.model_config = {
            'provider': 'DeepSeek',
            'model': 'deepseek-chat',
            'temperature': 0.7,
            'max_tokens': 15000
        }
    if 'generated_project' not in st.session_state:
        st.session_state.generated_project = None
    if 'current_dir' not in st.session_state:
        st.session_state.current_dir = str(PROJECT_ROOT)
    if 'selected_file' not in st.session_state:
        st.session_state.selected_file = None
    if 'file_content' not in st.session_state:
        st.session_state.file_content = None
    if 'active_tool' not in st.session_state:
        st.session_state.active_tool = 'chat'
    if 'show_unlimited_warning' not in st.session_state:
        st.session_state.show_unlimited_warning = False
    if 'system_prompt' not in st.session_state:
        st.session_state.system_prompt = """你是赛博印钞机 Pro 的工业级 AI 项目管家，一个功能强大、安全可靠的 AI 助手。

你的核心能力（8 个核心场景）：
1. 分析项目结构 & 代码审查 - 分析代码，找 bug，提优化建议
2. 自动修复代码 Bug - 扫描代码，定位问题，修复保存
3. Git 版本控制 & 自动提交 - 管理 Git 提交、推送、分支
4. 依赖管理 & 环境修复 - 检查、修复、升级依赖
5. 文档自动生成 & 更新 - 写 README、文档、注释
6. 调试 & 日志分析 - 看日志、找问题、定位崩溃
7. 测试 & 验证 - 写测试用例、运行测试、验证功能
8. 项目自动化 & 批量任务 - 批量生成、自动更新、定时任务

你的安全保障：
- 沙箱隔离：只能访问项目目录，不能碰系统文件
- 权限管控：敏感操作需要用户确认
- 敏感信息脱敏：API Key 等敏感信息自动脱敏
- 可还原：所有修改都有备份，随时可以还原

你的特点：
- 专业、友好、有帮助
- 理解项目上下文
- 提供具体可执行的建议
- 注意安全，不执行危险操作
- 详细解释你的思考过程

开始帮助用户吧！
"""
    if 'pending_operation' not in st.session_state:
        st.session_state.pending_operation = None

init_session_state()

def get_directory_tree(path: Path, max_depth: int = 3, current_depth: int = 0) -> List[Dict]:
    """获取目录树结构"""
    if current_depth >= max_depth:
        return []
    
    result = []
    try:
        for item in sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            if item.name.startswith('.') and item.name != '.env':
                continue
            
            safe, reason = is_safe_path(item)
            
            item_info = {
                'name': item.name,
                'path': str(item),
                'is_dir': item.is_dir(),
                'children': [],
                'safe': safe
            }
            
            if item.is_dir():
                item_info['children'] = get_directory_tree(item, max_depth, current_depth + 1)
            
            result.append(item_info)
    except Exception:
        pass
    
    return result

def render_file_tree(items: List[Dict], parent_key: str = ""):
    """渲染文件树"""
    for item in items:
        item_key = f"{parent_key}_{item['path']}"
        icon = "📁" if item['is_dir'] else "📄"
        
        safe_badge = "✅" if item.get('safe', True) else "⚠️"
        
        if st.button(
            f"{icon} {safe_badge} {item['name']}",
            key=item_key,
            use_container_width=True
        ):
            if item['is_dir']:
                st.session_state.current_dir = item['path']
                st.session_state.selected_file = None
            else:
                safe, reason = is_safe_path(Path(item['path']))
                if safe:
                    st.session_state.selected_file = item['path']
                    success, content, original = safe_read_file(Path(item['path']))
                    if success:
                        st.session_state.file_content = content
                    else:
                        st.session_state.file_content = f"[读取错误: {content}]"
                else:
                    st.error(f"安全限制: {reason}")
            st.rerun()

def save_current_chat():
    """保存当前对话到历史"""
    if st.session_state.chat_messages:
        st.session_state.chat_history[st.session_state.current_chat_id] = st.session_state.chat_messages.copy()

def build_context_info() -> str:
    """构建上下文信息"""
    context = []
    
    context.append("## 📁 项目信息")
    context.append(f"- 项目名称: {PROJECT_ROOT.name}")
    context.append(f"- 项目位置: {PROJECT_ROOT}")
    
    if st.session_state.selected_file:
        context.append(f"- 当前文件: {st.session_state.selected_file}")
    
    context.append("\n## 💬 对话历史")
    for i, msg in enumerate(st.session_state.chat_messages[-5:]):
        role = "用户" if msg["role"] == "user" else "助手"
        preview = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
        context.append(f"- [{role}]: {preview}")
    
    return "\n".join(context)

def run_git_command(cmd: List[str]) -> Tuple[bool, str]:
    """运行 Git 命令"""
    try:
        result = subprocess.run(
            ['git'] + cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)

def analyze_project_code() -> str:
    """场景一：分析项目结构 & 代码审查"""
    result = ["## 🔍 项目代码分析"]
    
    py_files = list(PROJECT_ROOT.glob("**/*.py"))
    result.append(f"\n### 📊 Python 文件统计: {len(py_files)} 个文件")
    
    important_files = [
        'web_panel_ultimate.py',
        'ai_assistant.py',
        'security_guard.py',
        'run_builtin_core.py'
    ]
    
    result.append("\n### 📁 重要文件检查:")
    for f in important_files:
        exists = (PROJECT_ROOT / f).exists()
        status = "✅" if exists else "❌"
        result.append(f"{status} {f}")
    
    result.append("\n### 💡 建议检查项:")
    result.append("- 检查 imports 是否正确")
    result.append("- 检查依赖是否完整")
    result.append("- 检查是否有明显的 bug")
    
    return "\n".join(result)

def handle_command(cmd: str) -> str:
    """处理命令 - 包含 8 个核心场景"""
    cmd = cmd.strip()
    
    if cmd == '/help' or cmd == '帮助':
        return """**🤖 工业级 AI 项目管家 - 完整命令**

**🎯 模式切换：**
- `/mode` - 查看当前模式和说明
- 在侧边栏切换安全/全能模式

**🔓 全能模式（仅全能模式可用）：**
- `/shell <command>` - 执行 Shell 命令
- `/pip <command>` - 执行 pip 命令（如 /pip install requests）
- `/git <command>` - 执行 Git 命令（如 /git status）

**🎯 8 个核心场景：**
1. `/scene analyze` - 分析项目结构 & 代码审查
2. `/scene bugfix` - 自动修复代码 Bug
3. `/scene git` - Git 版本控制 & 自动提交
4. `/scene deps` - 依赖管理 & 环境修复
5. `/scene docs` - 文档自动生成 & 更新
6. `/scene debug` - 调试 & 日志分析
7. `/scene test` - 测试 & 验证
8. `/scene auto` - 项目自动化 & 批量任务

**🔒 安全相关：**
- `/security status` - 查看安全状态
- `/security backups` - 查看备份列表
- `/security restore <file>` - 还原文件备份

**💬 基础命令：**
- `/help` 或 `帮助` - 显示此帮助
- `/clear` - 清空当前对话
- `/status` - 查看当前状态
- `/context` - 查看当前上下文

**📁 项目管理：**
- `/project info` - 查看项目信息
- `/project structure` - 查看项目结构
- `/project files` - 列出重要文件

**📚 小说管理：**
- `/novel list` - 列出已生成章节
- `/novel read <num>` - 读取章节内容
- `/novel settings` - 查看小说设定
- `/novel generate` - 生成新章节

**⚙️ 配置管理：**
- `/config show` - 显示当前配置

**📄 文件操作（安全）：**
- `/file view <path>` - 查看文件内容
- `/file list` - 列出当前目录文件
- `/file write <path> <content>` - 写入文件（需要确认）
- `/file delete <path>` - 删除文件（需要确认）
"""
    
    elif cmd == '/clear':
        st.session_state.chat_messages = []
        save_current_chat()
        return "✅ 对话已清空！"
    
    elif cmd == '/mode':
        current_mode = get_mode()
        is_unlimited = is_unlimited_mode()
        if is_unlimited:
            mode_info = """**🔓 全能模式**

当前模式：**全能模式**

✅ 可以执行任意 Shell 命令
✅ 可以读写任意文件（包括系统文件）
✅ 可以安装任意依赖
✅ 可以操作任意 Git 仓库

⚠️ **警告**：请谨慎使用！"""
        else:
            mode_info = """**🛡️ 安全模式**

当前模式：**安全模式**

✅ 只能访问项目目录
✅ 只能操作安全扩展名的文件
✅ 所有修改都会备份
✅ 敏感操作需要确认

**切换到全能模式**：在侧边栏点击「🔓 全能模式」"""
        return mode_info
    
    elif cmd.startswith('/shell'):
        parts = cmd.split(maxsplit=1)
        if len(parts) < 2:
            return "⚠️ 请指定要执行的命令，例如：`/shell ls -la`"
        
        shell_command = parts[1]
        success, stdout, stderr = execute_shell_command(shell_command)
        
        if success:
            result_parts = []
            result_parts.append("✅ **Shell 命令执行成功**")
            if stdout.strip():
                result_parts.append(f"\n**标准输出：**\n```\n{stdout}\n```")
            if stderr.strip():
                result_parts.append(f"\n**标准错误：**\n```\n{stderr}\n```")
            return "\n".join(result_parts)
        else:
            return f"❌ **Shell 命令执行失败**\n\n{stderr}"
    
    elif cmd.startswith('/pip'):
        parts = cmd.split(maxsplit=1)
        if len(parts) < 2:
            return "⚠️ 请指定 pip 命令，例如：`/pip install requests`"
        
        pip_command = f"pip {parts[1]}"
        success, stdout, stderr = execute_shell_command(pip_command)
        
        if success:
            result_parts = []
            result_parts.append("✅ **pip 命令执行成功**")
            if stdout.strip():
                result_parts.append(f"\n**输出：**\n```\n{stdout}\n```")
            if stderr.strip():
                result_parts.append(f"\n**警告/错误：**\n```\n{stderr}\n```")
            return "\n".join(result_parts)
        else:
            return f"❌ **pip 命令执行失败**\n\n{stderr}"
    
    elif cmd.startswith('/git'):
        parts = cmd.split(maxsplit=1)
        if len(parts) < 2:
            return "⚠️ 请指定 Git 命令，例如：`/git status`"
        
        git_command = f"git {parts[1]}"
        success, stdout, stderr = execute_shell_command(git_command)
        
        if success:
            result_parts = []
            result_parts.append("✅ **Git 命令执行成功**")
            if stdout.strip():
                result_parts.append(f"\n**输出：**\n```\n{stdout}\n```")
            if stderr.strip():
                result_parts.append(f"\n**警告/错误：**\n```\n{stderr}\n```")
            return "\n".join(result_parts)
        else:
            return f"❌ **Git 命令执行失败**\n\n{stderr}"
    
    elif cmd == '/status':
        msg_count = len(st.session_state.chat_messages)
        current_dir = st.session_state.current_dir
        security_status = get_security_status()
        current_mode = security_status['current_mode']
        return f"""**📊 当前状态：**
- 对话 ID：{st.session_state.current_chat_id}
- 消息数量：{msg_count}
- 模型：{st.session_state.model_config['model']}
- 提供商：{st.session_state.model_config['provider']}
- 当前目录：{current_dir}
- 当前模式：{current_mode}（{'全能' if security_status['is_unlimited'] else '安全'}）

**🔒 安全状态：**
- 备份目录：{security_status['backup_dir']}
- 备份数量：{security_status['backup_count']}
- 日志目录：{security_status['log_dir']}
"""
    
    elif cmd == '/context':
        return f"**🔍 当前上下文信息：**\n\n{build_context_info()}"
    
    elif cmd == '/security status':
        status = get_security_status()
        mode_label = "🔓 全能模式" if status['is_unlimited'] else "🛡️ 安全模式"
        return f"""**🔒 安全状态：**

- 当前模式：{mode_label}
- 项目根目录：{status['project_root']}
- 备份目录：{status['backup_dir']}
- 日志目录：{status['log_dir']}
- 备份数量：{status['backup_count']}

**安全扩展名白名单：**
{', '.join(status['safe_extensions'][:10])}...

**危险扩展名黑名单：**
{', '.join(status['dangerous_extensions'])}
"""
    
    elif cmd == '/security backups':
        backup_dir = SG_PROJECT_ROOT / ".ai_backups"
        if backup_dir.exists():
            backups = sorted(backup_dir.glob("*"), reverse=True)
            if backups:
                backup_list = "\n".join([f"- {b.name}" for b in backups[:20]])
                return f"""**💾 备份列表（最近 20 个）：**

{backup_list}

使用 `/security restore <文件名>` 还原
"""
            else:
                return "还没有备份"
        else:
            return "备份目录不存在"
    
    elif cmd.startswith('/security restore'):
        parts = cmd.split(maxsplit=2)
        if len(parts) < 3:
            return "⚠️ 请指定备份文件名，例如：`/security restore README.md.20240101_120000_123456`"
        
        backup_name = parts[2]
        backup_path = SG_PROJECT_ROOT / ".ai_backups" / backup_name
        
        if not backup_path.exists():
            return f"❌ 备份文件不存在：{backup_name}"
        
        try:
            original_name = backup_name.split('.')[0]
            if original_name.endswith('_md'):
                original_name = original_name.replace('_md', '.md')
            elif original_name.endswith('_py'):
                original_name = original_name.replace('_py', '.py')
            
            original_path = PROJECT_ROOT / original_name
            
            st.session_state.pending_operation = {
                'type': 'restore',
                'backup_path': str(backup_path),
                'original_path': str(original_path)
            }
            
            return f"""⚠️ **确认还原操作**

备份文件：{backup_name}
还原到：{original_path}

请在下方确认此操作！
"""
        except Exception as e:
            return f"❌ 解析失败：{str(e)}"
    
    elif cmd == '/scene analyze':
        return analyze_project_code()
    
    elif cmd == '/scene bugfix':
        return """**🔧 场景二：自动修复代码 Bug**

这个功能会：
1. 扫描项目中的 Python 文件
2. 分析常见问题（import 错误、类型问题等）
3. 定位具体问题点
4. 给出修复建议

**⚠️ 安全提示：**
- 所有修改都会自动备份
- 修改前需要你的确认
- 随时可以还原

使用 `/scene analyze` 先分析项目，然后告诉我你想修复什么！
"""
    
    elif cmd == '/scene git':
        success, output = run_git_command(['status'])
        git_info = output if success else f"Git 错误: {output}"
        
        return f"""**📦 场景三：Git 版本控制 & 自动提交**

**当前 Git 状态：**
```
{git_info}
```

**可用 Git 命令（通过自然语言）：**
- "查看 git 状态"
- "查看 git 日志"
- "提交修改"
- "推送到远程"

或者直接用命令：
- `/git status` - 查看状态
- `/git log` - 查看日志
"""
    
    elif cmd == '/scene deps':
        requirements_path = PROJECT_ROOT / 'requirements.txt'
        if requirements_path.exists():
            with open(requirements_path, 'r', encoding='utf-8') as f:
                requirements = f.read()
        else:
            requirements = "未找到 requirements.txt"
        
        return f"""**📦 场景四：依赖管理 & 环境修复**

**当前依赖：**
```
{requirements}
```

**可用功能：**
- 检查 import 语句
- 对比 requirements.txt
- 安装缺失依赖
- 修复环境问题

告诉我你需要做什么！
"""
    
    elif cmd == '/scene docs':
        return """**📝 场景五：文档自动生成 & 更新**

这个功能会：
1. 读取代码文件
2. 理解功能和逻辑
3. 生成 README、文档、注释
4. 保存到文件

**可用操作：**
- "生成 README"
- "给这个文件加注释"
- "更新文档"

告诉我你想生成什么文档！
"""
    
    elif cmd == '/scene debug':
        return """**🐛 场景六：调试 & 日志分析**

这个功能会：
1. 读取日志文件
2. 搜索错误关键词
3. 分析堆栈跟踪
4. 给出修复建议

**可用操作：**
- "分析最近的错误"
- "查看日志"
- "找崩溃原因"

告诉我你想调试什么！
"""
    
    elif cmd == '/scene test':
        return """**🧪 场景七：测试 & 验证**

这个功能会：
1. 分析代码逻辑
2. 写测试用例
3. 运行 pytest
4. 输出测试报告

**可用操作：**
- "给这个模块写测试"
- "运行测试"
- "验证功能"

告诉我你想测试什么！
"""
    
    elif cmd == '/scene auto':
        return """**⚡ 场景八：项目自动化 & 批量任务**

这个功能会：
1. 遍历目录
2. 批量处理文件
3. 保存结果

**可用操作：**
- "批量生成..."
- "自动更新..."
- "定时任务..."

告诉我你想做什么自动化任务！
"""
    
    elif cmd == '/project info':
        project_name = PROJECT_ROOT.name
        try:
            readme_path = PROJECT_ROOT / 'README.md'
            if readme_path.exists():
                with open(readme_path, 'r', encoding='utf-8') as f:
                    readme = f.read()
            else:
                readme = "未找到 README.md"
        except:
            readme = "未找到 README.md"
        
        return f"""**📁 项目信息：{project_name}**

**位置：** {PROJECT_ROOT}

**README 摘要：**
{readme[:800]}...

使用 `/project structure` 查看项目结构，或 `/scene analyze` 进行代码分析
"""
    
    elif cmd == '/project structure':
        tree = get_directory_tree(PROJECT_ROOT, max_depth=2)
        
        def print_tree(items, indent=0):
            result = ""
            for item in items:
                prefix = "  " * indent
                icon = "📁" if item['is_dir'] else "📄"
                safe_badge = "✅" if item.get('safe', True) else "⚠️"
                result += f"{prefix}{icon} {safe_badge} {item['name']}\n"
                if item['is_dir'] and item['children']:
                    result += print_tree(item['children'], indent + 1)
            return result
        
        structure = print_tree(tree)
        return f"""**🌳 项目结构：**

```
{structure}
```
"""
    
    elif cmd == '/project files':
        important_files = [
            'README.md',
            'requirements.txt',
            '.env',
            'web_panel_ultimate.py',
            'ai_assistant.py',
            'security_guard.py',
            'run_builtin_core.py'
        ]
        
        existing_files = []
        for f in important_files:
            if (PROJECT_ROOT / f).exists():
                existing_files.append(f"✅ {f}")
            else:
                existing_files.append(f"❌ {f}")
        
        return f"""**📋 重要文件：**

{chr(10).join(existing_files)}
"""
    
    elif cmd == '/novel list':
        from utils.helpers import get_resource_path
        output_dir = get_resource_path("output")
        
        if os.path.exists(output_dir):
            files = sorted([f for f in os.listdir(output_dir) if f.endswith('.md')], reverse=True)
            if files:
                file_list = "\n".join([f"- {f}" for f in files[:20]])
                return f"""**📚 已生成的章节（最近 20 个）：**

{file_list}

使用 `/novel read <num>` 读取具体章节
"""
            else:
                return "还没有生成任何章节"
        else:
            return "输出目录不存在"
    
    elif cmd.startswith('/novel read'):
        parts = cmd.split()
        if len(parts) < 3:
            return "⚠️ 请指定章节号，例如：`/novel read 1`"
        
        chapter_num = parts[2]
        from utils.helpers import get_resource_path
        output_dir = get_resource_path("output")
        
        if os.path.exists(output_dir):
            files = [f for f in os.listdir(output_dir) if f.endswith('.md') and chapter_num in f]
            if files:
                file_path = os.path.join(output_dir, files[0])
                success, content, original = safe_read_file(Path(file_path))
                if success:
                    st.session_state.generated_project = {
                        'name': files[0],
                        'files': {files[0]: content}
                    }
                    return f"✅ 已加载章节 {files[0]}，请在下方查看"
                else:
                    return f"❌ 读取失败：{content}"
            else:
                return f"❌ 未找到第 {chapter_num} 章"
        else:
            return "输出目录不存在"
    
    elif cmd == '/novel settings':
        settings_file = PROJECT_ROOT / 'novel_settings' / '连载设置.json'
        if settings_file.exists():
            success, content, original = safe_read_file(settings_file)
            if success:
                settings = json.loads(original)
                return f"""**📖 小说设定：**

```json
{json.dumps(settings, indent=2, ensure_ascii=False)}
```
"""
            else:
                return f"❌ 读取设定失败：{content}"
        else:
            return "未找到小说设定文件"
    
    elif cmd == '/novel generate':
        return """**✨ 小说生成向导**

让我帮你生成新章节！请告诉我：

1. **章节号**（例如：第 5 章）
2. **目标字数**（建议 7500 字）
3. **小说类型**（玄幻修仙/都市异能/...）
4. **特殊要求**（可选）

或者直接去 Web 面板点击"一键躺平生成"更方便！
"""
    
    elif cmd == '/config show':
        env_path = PROJECT_ROOT / '.env'
        if env_path.exists():
            success, content, original = safe_read_file(env_path)
            if success:
                return f"""**⚙️ 当前配置：**

```
{content}
```
"""
        else:
            return "未找到 .env 文件"
    
    elif cmd.startswith('/file view'):
        parts = cmd.split(maxsplit=2)
        if len(parts) < 3:
            return "⚠️ 请指定文件路径，例如：`/file view README.md`"
        
        file_path = parts[2]
        full_path = PROJECT_ROOT / file_path
        
        safe, reason = is_safe_path(full_path)
        if not safe:
            return f"❌ 安全限制：{reason}"
        
        if not full_path.exists():
            return f"❌ 文件不存在：{file_path}"
        
        success, content, original = safe_read_file(full_path)
        if success:
            st.session_state.generated_project = {
                'name': file_path,
                'files': {file_path: content}
            }
            return f"✅ 已加载文件 {file_path}，请在下方查看"
        else:
            return f"❌ 读取失败：{content}"
    
    elif cmd == '/file list':
        current_dir = Path(st.session_state.current_dir)
        items = []
        try:
            for item in sorted(current_dir.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                if item.name.startswith('.') and item.name != '.env':
                    continue
                safe, reason = is_safe_path(item)
                safe_badge = "✅" if safe else "⚠️"
                icon = "📁" if item.is_dir() else "📄"
                items.append(f"{icon} {safe_badge} {item.name}")
        except Exception as e:
            return f"❌ 列出文件失败：{str(e)}"
        
        return f"""**📂 当前目录：{current_dir}**

{chr(10).join(items)}
"""
    
    elif cmd.startswith('/file write'):
        return "⚠️ 写入文件功能需要通过安全确认，请用自然语言描述你想写什么内容到哪个文件，我会帮你准备好确认操作！"
    
    elif cmd.startswith('/file delete'):
        return "⚠️ 删除文件功能需要通过安全确认，请用自然语言描述你想删除哪个文件，我会帮你准备好确认操作！"
    
    return None

with st.sidebar:
    st.markdown("# 🤖 工业级 AI 项目管家")
    
    current_mode = get_mode()
    if current_mode == "safe":
        st.markdown("### 🛡️ 安全模式")
        st.success("安全模式：AI 只能访问项目目录")
    else:
        st.markdown("### 🔓 全能模式")
        st.warning("全能模式：AI 可以访问系统任意位置")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🛡️ 安全模式", use_container_width=True, type="primary" if current_mode == "safe" else "secondary"):
            set_mode("safe")
            st.rerun()
    with col2:
        if st.button("🔓 全能模式", use_container_width=True, type="primary" if current_mode == "unlimited" else "secondary"):
            if current_mode != "unlimited":
                st.session_state.show_unlimited_warning = True
                st.rerun()
            else:
                set_mode("safe")
                st.rerun()
    
    if st.session_state.get('show_unlimited_warning', False):
        st.warning("""
⚠️ **重要警告**

你即将切换到**全能模式**，这将：

- ✅ 允许 AI 执行任意 Shell 命令
- ✅ 允许 AI 读写任意文件（包括系统文件）
- ✅ 允许 AI 安装任意依赖
- ✅ 允许 AI 操作任意 Git 仓库

⚠️ **风险提示**：
- 它真的可以删除你的文件、修改系统配置
- 只在你信任的环境中使用
- 不要给不信任的人访问权限
""")
        col_confirm, col_cancel = st.columns(2)
        with col_confirm:
            if st.button("✅ 我确认开启全能模式", type="primary", use_container_width=True):
                set_mode("unlimited")
                st.session_state.show_unlimited_warning = False
                st.rerun()
        with col_cancel:
            if st.button("❌ 取消", use_container_width=True):
                st.session_state.show_unlimited_warning = False
                st.rerun()
    
    st.markdown("---")
    
    st.markdown("### 🎯 8 个核心场景")
    
    scenes = {
        'analyze': '🔍 代码分析',
        'bugfix': '🔧 Bug 修复',
        'git': '📦 Git 管理',
        'deps': '📦 依赖管理',
        'docs': '📝 文档生成',
        'debug': '🐛 调试分析',
        'test': '🧪 测试验证',
        'auto': '⚡ 自动化任务'
    }
    
    for scene_key, scene_label in scenes.items():
        if st.button(scene_label, key=f"scene_{scene_key}", use_container_width=True):
            cmd = f"/scene {scene_key}"
            response = handle_command(cmd)
            if response:
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": response
                })
                save_current_chat()
            st.rerun()
    
    st.markdown("---")
    
    st.markdown("### 💬 对话历史")
    
    chat_ids = list(st.session_state.chat_history.keys())
    if chat_ids:
        selected_chat = st.selectbox(
            "选择对话",
            ["-- 新建对话 --"] + chat_ids,
            key="chat_selector"
        )
        
        if selected_chat != "-- 新建对话 --" and selected_chat != st.session_state.current_chat_id:
            st.session_state.current_chat_id = selected_chat
            st.session_state.chat_messages = st.session_state.chat_history.get(selected_chat, [])
            st.rerun()
    
    if st.button("🆕 新建对话", use_container_width=True):
        st.session_state.current_chat_id = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        st.session_state.chat_messages = []
        st.rerun()
    
    st.markdown("---")
    
    st.markdown("### 📁 文件浏览器")
    
    current_dir = Path(st.session_state.current_dir)
    
    if current_dir != PROJECT_ROOT:
        if st.button("⬆️ 返回上级", use_container_width=True):
            st.session_state.current_dir = str(current_dir.parent)
            st.session_state.selected_file = None
            st.rerun()
    
    st.markdown(f"**当前目录：**\n`{current_dir.name}`")
    
    try:
        tree = get_directory_tree(current_dir, max_depth=1)
        render_file_tree(tree)
    except Exception as e:
        st.error(f"无法浏览目录：{str(e)}")
    
    st.markdown("---")
    
    st.markdown("### 🔒 安全状态")
    security_status = get_security_status()
    st.markdown(f"- 备份数量：**{security_status['backup_count']}**")
    if st.button("🛡️ 查看安全详情", use_container_width=True):
        response = handle_command('/security status')
        if response:
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": response
            })
            save_current_chat()
        st.rerun()
    
    st.markdown("---")
    
    st.markdown("### ⚙️ 模型配置")
    
    provider = st.selectbox(
        "LLM 提供商",
        ["DeepSeek", "OpenAI", "Anthropic", "自定义"],
        index=0
    )
    
    model = st.text_input("Model", value=st.session_state.model_config['model'])
    temperature = st.slider("Temperature", 0.0, 2.0, st.session_state.model_config['temperature'], 0.1)
    max_tokens = st.number_input("Max Tokens", 1000, 100000, st.session_state.model_config['max_tokens'], 1000)
    
    st.session_state.model_config.update({
        'provider': provider,
        'model': model,
        'temperature': temperature,
        'max_tokens': max_tokens
    })
    
    st.markdown("---")
    
    st.markdown("### 📖 快速命令")
    st.markdown("""
- `/help` - 完整帮助
- `/scene analyze` - 代码分析
- `/security status` - 安全状态
- `/project info` - 项目信息
- `/clear` - 清空对话
""")

st.title("🤖 工业级 AI 项目管家")
st.markdown("<p style='color: #64748b; margin-top: -8px; margin-bottom: 24px;'>8 个核心场景 · 工业级安全 · 深度项目集成</p>", unsafe_allow_html=True)

if st.session_state.pending_operation:
    op = st.session_state.pending_operation
    st.warning("⚠️ **待确认的操作**")
    
    if op['type'] == 'restore':
        st.info(f"还原操作：\n- 备份文件：{op['backup_path']}\n- 还原到：{op['original_path']}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ 确认执行", type="primary"):
                try:
                    success = restore_backup(Path(op['original_path']), Path(op['backup_path']))
                    if success:
                        st.success("✅ 还原成功！")
                        st.session_state.chat_messages.append({
                            "role": "assistant",
                            "content": f"✅ 文件已还原：{op['original_path']}"
                        })
                    else:
                        st.error("❌ 还原失败")
                except Exception as e:
                    st.error(f"❌ 还原失败：{str(e)}")
                st.session_state.pending_operation = None
                save_current_chat()
                st.rerun()
        with col2:
            if st.button("❌ 取消"):
                st.session_state.pending_operation = None
                st.rerun()
    
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

chat_container = st.container()

with chat_container:
    for msg in st.session_state.chat_messages:
        role = msg["role"]
        content = msg["content"]
        
        with st.chat_message(role):
            st.markdown(content)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

if prompt := st.chat_input("输入消息、命令或自然语言（/help 查看完整帮助）"):
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    
    with chat_container:
        with st.chat_message("user"):
            st.markdown(prompt)
    
    response = handle_command(prompt)
    
    if response:
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
        with chat_container:
            with st.chat_message("assistant"):
                st.markdown(response)
    else:
        try:
            from builtin_claude_core.llm_adapter import get_llm_adapter
            
            adapter = get_llm_adapter()
            
            context_info = build_context_info()
            
            enhanced_prompt = f"""当前上下文：
{context_info}

用户问题：{prompt}

请根据上下文信息，专业地回答用户的问题。如果需要更多信息，请礼貌地询问用户。
"""
            
            messages = []
            for msg in st.session_state.chat_messages[-8:]:
                messages.append({
                    "role": msg["role"],
                    "content": mask_sensitive_info(msg["content"])
                })
            
            with st.spinner("思考中..."):
                response_content = adapter.generate(
                    prompt=enhanced_prompt,
                    system_prompt=st.session_state.system_prompt,
                    temperature=st.session_state.model_config['temperature']
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
    
    save_current_chat()
    st.rerun()

if st.session_state.selected_file and st.session_state.file_content:
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    
    st.markdown(f"### 📄 {Path(st.session_state.selected_file).name}")
    st.caption(st.session_state.selected_file)
    
    file_ext = Path(st.session_state.selected_file).suffix.lower()
    if file_ext == '.md':
        st.markdown(st.session_state.file_content)
    else:
        language = 'python' if file_ext == '.py' else 'text'
        st.code(st.session_state.file_content, language=language)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "📥 下载文件",
            st.session_state.file_content,
            file_name=Path(st.session_state.selected_file).name
        )
    with col2:
        backups = list_backups(Path(st.session_state.selected_file))
        if backups:
            if st.button(f"↩️ 还原 ({len(backups)} 个备份)"):
                st.info(f"找到 {len(backups)} 个备份，使用 `/security restore <文件名>` 还原")
    with col3:
        if st.button("🗑️ 关闭文件"):
            st.session_state.selected_file = None
            st.session_state.file_content = None
            st.rerun()

if st.session_state.generated_project:
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    
    st.markdown("### 📁 生成的项目文件")
    
    project = st.session_state.generated_project
    files = project.get('files', {})
    
    if files:
        file_names = list(files.keys())
        selected_file = st.selectbox("选择文件", file_names)
        
        if selected_file:
            st.markdown(f"#### 📄 {selected_file}")
            file_ext = Path(selected_file).suffix.lower()
            if file_ext == '.md':
                st.markdown(files[selected_file])
            else:
                language = 'python' if file_ext == '.py' else 'text'
                st.code(files[selected_file], language=language)
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    f"📥 下载 {selected_file}",
                    files[selected_file],
                    file_name=selected_file
                )
            
            with col2:
                if st.button("🗑️ 清除项目"):
                    st.session_state.generated_project = None
                    st.rerun()

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; color: #94a3b8;'>
    <p>💡 提示：使用 /help 查看所有命令，或直接用自然语言和我交流！</p>
    <p>🔒 安全保障：所有操作都有备份，随时可以还原！</p>
</div>
""", unsafe_allow_html=True)
