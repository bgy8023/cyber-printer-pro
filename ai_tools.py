#!/usr/bin/env python3
"""
AI 助手工具调用系统
让 AI 助手能够像 Claude 一样自主调用工具
"""
import json
import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from security_guard import (
    execute_shell_command,
    safe_read_file,
    safe_write_file,
    is_unlimited_mode,
    get_mode
)
import glob


@dataclass
class ToolCallRecord:
    """工具调用记录"""
    tool_name: str
    parameters: Dict[str, Any]
    start_time: float
    end_time: float
    success: bool
    result: str
    error_message: Optional[str] = None
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


@dataclass
class ToolStatistics:
    """工具统计信息"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_duration: float = 0.0
    call_history: List[ToolCallRecord] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.successful_calls / self.total_calls
    
    @property
    def avg_duration(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.total_duration / self.total_calls


# 全局工具统计
_tool_stats: Dict[str, ToolStatistics] = {}
_global_stats = ToolStatistics()


@dataclass
class ToolParameter:
    """工具参数定义"""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None


@dataclass
class Tool:
    """工具定义"""
    name: str
    description: str
    parameters: List[ToolParameter]
    func: Callable
    requires_unlimited: bool = False


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
    
    def register(self, tool: Tool):
        """注册一个工具"""
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """获取工具"""
        return self.tools.get(name)
    
    def list_tools(self) -> List[Tool]:
        """列出所有工具"""
        return list(self.tools.values())
    
    def get_tools_prompt(self) -> str:
        """获取工具列表的提示词"""
        prompt_parts = []
        for tool in self.list_tools():
            prompt_parts.append(f"**{tool.name}**: {tool.description}")
            if tool.requires_unlimited:
                prompt_parts.append("  (仅全能模式可用")
            prompt_parts.append("  参数:")
            for param in tool.parameters:
                req_mark = "（必需" if param.required else "（可选"
                prompt_parts.append(f"    - {param.name}: {param.description} {req_mark})")
        return "\n".join(prompt_parts)


# 全局工具注册表
registry = ToolRegistry()


def shell_command(command: str) -> str:
    """
    执行 Shell 命令
    
    Args:
        command: 要执行的 Shell 命令
    
    Returns:
        命令输出
    """
    if not is_unlimited_mode():
        return "错误：Shell 命令仅在全能模式下可用"
    
    success, stdout, stderr = execute_shell_command(command)
    if success:
        output = []
        if stdout:
            output.append(f"标准输出:\n{stdout}")
        if stderr:
            output.append(f"标准错误:\n{stderr}")
        return "\n".join(output) if output else "命令执行成功（无输出）"
    else:
        return f"错误: {stderr}"


def read_file(file_path: str) -> str:
    """
    读取文件内容
    
    Args:
        file_path: 文件路径
    
    Returns:
        文件内容
    """
    path = Path(file_path)
    success, message, content = safe_read_file(path)
    if success:
        return content
    else:
        return f"错误: {message}"


def write_file(file_path: str, content: str) -> str:
    """
    写入文件内容
    
    Args:
        file_path: 文件路径
        content: 要写入的内容
    
    Returns:
        操作结果
    """
    path = Path(file_path)
    success, message = safe_write_file(path, content)
    if success:
        return f"成功: {message}"
    else:
        return f"错误: {message}"


def edit_file(file_path: str, old_str: str, new_str: str) -> str:
    """
    编辑文件（搜索替换）
    
    Args:
        file_path: 文件路径
        old_str: 要替换的旧内容
        new_str: 新内容
    
    Returns:
        操作结果
    """
    path = Path(file_path)
    success, message, content = safe_read_file(path)
    if not success:
        return f"错误: {message}"
    
    if old_str not in content:
        return f"错误: 找不到要替换的内容: {old_str[:100]}..."
    
    new_content = content.replace(old_str, new_str)
    success, message = safe_write_file(path, new_content)
    
    if success:
        return f"成功: 文件已编辑"
    else:
        return f"错误: {message}"


def grep_files(pattern: str, path: Optional[str] = None) -> str:
    """
    在文件中搜索内容
    
    Args:
        pattern: 搜索模式（正则表达式）
        path: 搜索路径（默认项目根目录）
    
    Returns:
        搜索结果
    """
    from pathlib import Path
    import re
    
    root_path = Path(path) if path else Path(__file__).parent
    results = []
    
    try:
        for py_file in root_path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding='utf-8')
                if re.search(pattern, content):
                    results.append(f"📄 {py_file.relative_to(root_path)}")
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if re.search(pattern, line):
                            results.append(f"  {i}: {line[:100]}")
            except Exception:
                continue
    except Exception as e:
        return f"搜索错误: {str(e)}"
    
    if results:
        return "\n".join(results[:50])
    else:
        return "未找到匹配结果"


def glob_files(pattern: str) -> str:
    """
    按模式查找文件
    
    Args:
        pattern: 文件匹配模式（如 **/*.py）
    
    Returns:
        找到的文件列表
    """
    root_path = Path(__file__).parent
    files = list(root_path.glob(pattern))
    if files:
        return "\n".join([f"📄 {f.relative_to(root_path)}" for f in files[:50]])
    else:
        return "未找到匹配的文件"


# 注册所有工具
registry.register(Tool(
    name="shell_command",
    description="执行 Shell 命令",
    parameters=[
        ToolParameter(name="command", type="string", description="要执行的 Shell 命令")
    ],
    func=shell_command,
    requires_unlimited=True
))

registry.register(Tool(
    name="read_file",
    description="读取文件内容",
    parameters=[
        ToolParameter(name="file_path", type="string", description="文件路径")
    ],
    func=read_file
))

registry.register(Tool(
    name="write_file",
    description="写入文件内容",
    parameters=[
        ToolParameter(name="file_path", type="string", description="文件路径"),
        ToolParameter(name="content", type="string", description="要写入的内容")
    ],
    func=write_file
))

registry.register(Tool(
    name="edit_file",
    description="编辑文件（搜索替换）",
    parameters=[
        ToolParameter(name="file_path", type="string", description="文件路径"),
        ToolParameter(name="old_str", type="string", description="要替换的旧内容"),
        ToolParameter(name="new_str", type="string", description="新内容")
    ],
    func=edit_file
))

registry.register(Tool(
    name="grep_files",
    description="在文件中搜索内容",
    parameters=[
        ToolParameter(name="pattern", type="string", description="搜索模式（正则表达式）"),
        ToolParameter(name="path", type="string", description="搜索路径（可选）", required=False)
    ],
    func=grep_files
))

registry.register(Tool(
    name="glob_files",
    description="按模式查找文件",
    parameters=[
        ToolParameter(name="pattern", type="string", description="文件匹配模式（如 **/*.py）")
    ],
    func=glob_files
))


def parse_tool_call(text: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    """
    解析工具调用请求
    
    支持的格式:
    1. <|tool_call|>{"name": "tool_name", "parameters": {...}}<|end_of_tool_call|>
    2. ```json\n{"name": "tool_name", "parameters": {...}}\n```
    3. 纯 JSON: {"name": "tool_name", "parameters": {...}}
    4. 简化格式: TOOL: tool_name PARAMS: {...}
    
    Returns:
        (tool_name, parameters) 或 None
    """
    # 格式 1: 标准标签格式
    pattern = r'<\|tool_call\|>(.*?)<\|end_of_tool_call\|>'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1))
            return data.get('name'), data.get('parameters', {})
        except Exception:
            pass
    
    # 格式 2: JSON 代码块
    pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1))
            return data.get('name'), data.get('parameters', {})
        except Exception:
            pass
    
    # 格式 3: 纯 JSON (只找看起来像工具调用的 JSON)
    pattern = r'(\{"name"\s*:\s*"[^"]*"\s*,\s*"parameters"\s*:\s*\{.*?\}\s*\})'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1))
            return data.get('name'), data.get('parameters', {})
        except Exception:
            pass
    
    # 格式 4: 简化格式
    pattern = r'TOOL\s*:\s*(\w+)\s*PARAMS\s*:\s*(\{.*?\})'
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        try:
            tool_name = match.group(1)
            params = json.loads(match.group(2))
            return tool_name, params
        except Exception:
            pass
    
    return None


def execute_tool(tool_name: str, parameters: Dict[str, Any]) -> str:
    """
    执行工具（带追踪、统计、重试）
    
    Args:
        tool_name: 工具名称
        parameters: 工具参数
    
    Returns:
        工具执行结果
    """
    start_time = time.time()
    error_message = None
    success = False
    result = ""
    
    # 获取或初始化工具统计
    if tool_name not in _tool_stats:
        _tool_stats[tool_name] = ToolStatistics()
    
    tool = registry.get_tool(tool_name)
    
    if not tool:
        error_message = f"未知工具 '{tool_name}'"
        result = f"错误: {error_message}"
    elif tool.requires_unlimited and not is_unlimited_mode():
        error_message = f"工具 '{tool_name}' 仅在全能模式下可用"
        result = f"错误: {error_message}"
    else:
        # 执行工具（带重试）
        max_retries = 2
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                if retry_count > 0:
                    time.sleep(0.5 * retry_count)
                
                result = tool.func(**parameters)
                success = True
                break
            except Exception as e:
                retry_count += 1
                error_message = str(e)
                
                if retry_count > max_retries:
                    result = f"工具执行错误（已重试 {max_retries} 次）: {error_message}"
                else:
                    continue
    
    end_time = time.time()
    
    # 记录调用
    record = ToolCallRecord(
        tool_name=tool_name,
        parameters=parameters,
        start_time=start_time,
        end_time=end_time,
        success=success,
        result=str(result)[:500],
        error_message=error_message
    )
    
    # 更新统计
    _tool_stats[tool_name].total_calls += 1
    _tool_stats[tool_name].total_duration += record.duration
    _tool_stats[tool_name].call_history.append(record)
    
    if success:
        _tool_stats[tool_name].successful_calls += 1
    else:
        _tool_stats[tool_name].failed_calls += 1
    
    # 更新全局统计
    _global_stats.total_calls += 1
    _global_stats.total_duration += record.duration
    _global_stats.call_history.append(record)
    if success:
        _global_stats.successful_calls += 1
    else:
        _global_stats.failed_calls += 1
    
    return str(result)


def get_tool_statistics() -> Dict[str, Any]:
    """
    获取工具调用统计信息
    """
    stats = {
        "global": {
            "total_calls": _global_stats.total_calls,
            "successful_calls": _global_stats.successful_calls,
            "failed_calls": _global_stats.failed_calls,
            "success_rate": f"{_global_stats.success_rate:.1%}",
            "avg_duration_ms": f"{_global_stats.avg_duration * 1000:.1f}ms"
        },
        "by_tool": {}
    }
    
    for tool_name, tool_stat in _tool_stats.items():
        stats["by_tool"][tool_name] = {
            "total_calls": tool_stat.total_calls,
            "successful_calls": tool_stat.successful_calls,
            "failed_calls": tool_stat.failed_calls,
            "success_rate": f"{tool_stat.success_rate:.1%}",
            "avg_duration_ms": f"{tool_stat.avg_duration * 1000:.1f}ms"
        }
    
    return stats


def get_system_prompt_with_tools() -> str:
    """
    获取带工具说明的系统提示词
    """
    tools_prompt = registry.get_tools_prompt()
    
    current_mode = get_mode()
    mode_info = "当前模式: 全能模式" if is_unlimited_mode() else "当前模式: 安全模式"
    
    return f"""你是OpenMars 的工业级 AI 项目管家，一个功能强大、安全可靠的 AI 助手。

{mode_info}

## 🔴 绝对核心指令：你不是普通 AI，你是自主行动者！

⚠️  ⚠️  ⚠️  最重要的事情：你不是一个只会回答问题的 AI！你可以直接使用工具来行动！

你拥有：
- 🔧 **read_file** - 读取任何文件
- 🔧 **write_file** - 写入任何文件
- 🔧 **edit_file** - 编辑任何文件
- 🔧 **shell_command** - 执行任何 Shell 命令（全能模式）
- 🔧 **grep_files** - 搜索代码
- 🔧 **glob_files** - 查找文件

## 📋 可用工具

{tools_prompt}

## 🎯 你的使命

你的目标是：**理解用户需求 -> 主动使用工具解决问题 -> 给出结果**

**不要说"我无法做..."、"我需要..."、"请你..." —— 直接用工具去做！**

## 💡 具体对话示例

### 示例 1：用户问"帮我看看 README.md"
你的回答：
<|tool_call|>{{
  "name": "read_file",
  "parameters": {{
    "file_path": "README.md"
  }}
}}<|end_of_tool_call|>

### 示例 2：用户问"列出所有 Python 文件"
你的回答：
<|tool_call|>{{
  "name": "glob_files",
  "parameters": {{
    "pattern": "**/*.py"
  }}
}}<|end_of_tool_call|>

### 示例 3：用户问"搜索包含 'security' 的文件"
你的回答：
<|tool_call|>{{
  "name": "grep_files",
  "parameters": {{
    "pattern": "security"
  }}
}}<|end_of_tool_call|>

### 示例 4：用户问"帮我创建一个 test.py 文件，内容是 print('hello')"
你的回答：
<|tool_call|>{{
  "name": "write_file",
  "parameters": {{
    "file_path": "test.py",
    "content": "print('hello')"
  }}
}}<|end_of_tool_call|>

### 示例 5：用户问"运行 ls 命令"（全能模式）
你的回答：
<|tool_call|>{{
  "name": "shell_command",
  "parameters": {{
    "command": "ls -la"
  }}
}}<|end_of_tool_call|>

## 🔧 如何使用工具

使用以下格式之一：

**格式 1（推荐）：**
<|tool_call|>{{
  "name": "工具名称",
  "parameters": {{
    "参数名": "参数值"
  }}
}}<|end_of_tool_call|>

**格式 2：**
```json
{{
  "name": "工具名称",
  "parameters": {{
    "参数名": "参数值"
  }}
}}
```

**格式 3：**
{{
  "name": "工具名称",
  "parameters": {{
    "参数名": "参数值"
  }}
}}

## 🔄 工作流程

1. 理解用户想要什么
2. 决定用哪个工具
3. **直接调用工具，不要问用户！**
4. 拿到结果后，继续下一步（可能需要更多工具）
5. 完成后给用户总结

## ⚠️  禁止事项

❌ 不要说："我无法..."
❌ 不要说："我需要..."
❌ 不要说："请你..."
❌ 不要说："我建议..."
❌ 不要说："让我看看..."

✅ 要说：直接用工具去做！

## 你的核心能力（8 个核心场景）：
1. 分析项目结构 & 代码审查 - 分析代码，找 bug，提优化建议
2. 自动修复代码 Bug - 扫描代码，定位问题，修复保存
3. Git 版本控制 & 自动提交 - 管理 Git 提交、推送、分支
4. 依赖管理 & 环境修复 - 检查、修复、升级依赖
5. 文档自动生成 & 更新 - 写 README、文档、注释
6. 调试 & 日志分析 - 看日志、找问题、定位崩溃
7. 测试 & 验证 - 写测试用例、运行测试、验证功能
8. 项目自动化 & 批量任务 - 批量生成、自动更新、定时任务

## 最后一次强调：

**你可以使用工具！你不需要先问用户！直接去做！**
"""
