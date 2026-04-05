#!/usr/bin/env python3
"""
工业级安全保障模块
- 沙箱隔离：AI 只能访问项目目录（安全模式）
- 敏感信息脱敏：API Key、密码等自动脱敏
- 权限管控：拦截敏感操作（安全模式）
- 可还原：文件修改前自动备份
- 模式切换：安全模式/全能模式
"""
import os
import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple
import json
import sys

PROJECT_ROOT = Path(__file__).parent
BACKUP_DIR = PROJECT_ROOT / ".ai_backups"
LOG_DIR = PROJECT_ROOT / ".ai_logs"
MODE_CONFIG_PATH = PROJECT_ROOT / ".ai_mode_config.json"

SENSITIVE_PATTERNS = [
    (r'(?i)api[_-]?key\s*[=:]\s*["\']?([a-zA-Z0-9\-_]{16,})["\']?', 'API_KEY'),
    (r'(?i)password\s*[=:]\s*["\']?([^\s"\']{4,})["\']?', 'PASSWORD'),
    (r'(?i)token\s*[=:]\s*["\']?([a-zA-Z0-9\-_]{16,})["\']?', 'TOKEN'),
    (r'(?i)secret\s*[=:]\s*["\']?([a-zA-Z0-9\-_]{16,})["\']?', 'SECRET'),
    (r'sk-[a-zA-Z0-9]{20,}', 'OPENAI_KEY'),
    (r'anthropic_[a-zA-Z0-9]{30,}', 'ANTHROPIC_KEY'),
]

_current_mode = "safe"


def get_mode() -> str:
    """获取当前模式"""
    return _current_mode


def set_mode(mode: str) -> bool:
    """
    设置模式
    mode: 'safe' 或 'unlimited'
    """
    global _current_mode
    if mode not in ['safe', 'unlimited']:
        return False
    _current_mode = mode
    try:
        with open(MODE_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump({'mode': mode}, f)
        _log_action("MODE_CHANGE", f"切换到 {mode} 模式")
        return True
    except Exception as e:
        print(f"保存模式配置失败: {e}")
        return False


def is_unlimited_mode() -> bool:
    """检查是否是全能模式"""
    return _current_mode == "unlimited"


def _load_mode():
    """加载模式配置"""
    global _current_mode
    if MODE_CONFIG_PATH.exists():
        try:
            with open(MODE_CONFIG_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'mode' in data and data['mode'] in ['safe', 'unlimited']:
                    _current_mode = data['mode']
        except Exception as e:
            pass


SAFE_EXTENSIONS = {
    '.py', '.md', '.txt', '.json', '.yaml', '.yml', 
    '.html', '.css', '.js', '.jsx', '.ts', '.tsx',
    '.sh', '.bat', '.ps1', '.env', '.gitignore'
}

DANGEROUS_EXTENSIONS = {
    '.exe', '.dll', '.so', '.dylib', '.bin', 
    '.pyd', '.pyc', '.pyo'
}

DANGEROUS_PATHS = [
    '/etc', '/bin', '/sbin', '/usr/bin', '/usr/sbin',
    '/System', '/Applications', '/Library',
    'C:\\Windows', 'C:\\Program Files'
]


def init_security():
    """初始化安全模块"""
    BACKUP_DIR.mkdir(exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)
    _load_mode()


def is_safe_path(file_path: Path) -> Tuple[bool, str]:
    """
    检查路径是否安全
    返回 (是否安全, 原因)
    """
    if is_unlimited_mode():
        return True, "全能模式"
    
    file_path = file_path.resolve()
    
    try:
        file_path.relative_to(PROJECT_ROOT.resolve())
    except ValueError:
        return False, f"路径不在项目目录内: {file_path}"
    
    for dangerous in DANGEROUS_PATHS:
        if str(file_path).startswith(dangerous):
            return False, f"访问危险系统路径: {file_path}"
    
    if file_path.suffix in DANGEROUS_EXTENSIONS:
        return False, f"危险文件类型: {file_path.suffix}"
    
    return True, "安全"


def mask_sensitive_info(text: str) -> str:
    """
    脱敏敏感信息
    """
    result = text
    for pattern, label in SENSITIVE_PATTERNS:
        result = re.sub(pattern, lambda m: f"{label}=********", result)
    return result


def create_backup(file_path: Path) -> Optional[Path]:
    """
    创建文件备份
    返回备份文件路径
    """
    if not file_path.exists():
        return None
    
    safe, reason = is_safe_path(file_path)
    if not safe:
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    relative_path = file_path.relative_to(PROJECT_ROOT)
    backup_path = BACKUP_DIR / f"{relative_path.as_posix().replace('/', '_')}.{timestamp}"
    
    shutil.copy2(file_path, backup_path)
    _log_action("BACKUP", f"{file_path} -> {backup_path}")
    
    return backup_path


def restore_backup(file_path: Path, backup_path: Optional[Path] = None) -> bool:
    """
    从备份还原文件
    如果没有指定 backup_path，使用最新备份
    """
    safe, reason = is_safe_path(file_path)
    if not safe:
        return False
    
    if backup_path is None:
        relative_path = file_path.relative_to(PROJECT_ROOT)
        pattern = f"{relative_path.as_posix().replace('/', '_')}.*"
        backups = sorted(BACKUP_DIR.glob(pattern), reverse=True)
        if not backups:
            return False
        backup_path = backups[0]
    
    if not backup_path.exists():
        return False
    
    shutil.copy2(backup_path, file_path)
    _log_action("RESTORE", f"{backup_path} -> {file_path}")
    return True


def list_backups(file_path: Path) -> List[Path]:
    """列出文件的所有备份"""
    try:
        relative_path = file_path.relative_to(PROJECT_ROOT)
        pattern = f"{relative_path.as_posix().replace('/', '_')}.*"
        return sorted(BACKUP_DIR.glob(pattern), reverse=True)
    except:
        return []


def safe_read_file(file_path: Path, max_size: int = 1024 * 1024) -> Tuple[bool, str, str]:
    """
    安全读取文件
    返回 (成功, 内容/错误, 原始内容)
    """
    safe, reason = is_safe_path(file_path)
    if not safe:
        return False, reason, ""
    
    if not file_path.exists():
        return False, f"文件不存在: {file_path}", ""
    
    if file_path.stat().st_size > max_size:
        return False, f"文件过大: {file_path.stat().st_size} bytes", ""
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            original = f.read()
        masked = mask_sensitive_info(original)
        _log_action("READ", str(file_path))
        return True, masked, original
    except Exception as e:
        return False, f"读取失败: {str(e)}", ""


def safe_write_file(file_path: Path, content: str, create_backup: bool = True) -> Tuple[bool, str]:
    """
    安全写入文件
    返回 (成功, 消息)
    """
    safe, reason = is_safe_path(file_path)
    if not safe:
        return False, reason
    
    if not is_unlimited_mode() and file_path.suffix not in SAFE_EXTENSIONS:
        return False, f"不允许的文件类型: {file_path.suffix}"
    
    backup_path = None
    if create_backup and file_path.exists():
        backup_path = create_backup(file_path)
    
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        _log_action("WRITE", str(file_path))
        return True, f"写入成功 (备份: {backup_path})"
    except Exception as e:
        if backup_path:
            restore_backup(file_path, backup_path)
        return False, f"写入失败: {str(e)}"


def safe_delete_file(file_path: Path, create_backup: bool = True) -> Tuple[bool, str]:
    """
    安全删除文件
    返回 (成功, 消息)
    """
    safe, reason = is_safe_path(file_path)
    if not safe:
        return False, reason
    
    if not file_path.exists():
        return False, f"文件不存在: {file_path}"
    
    backup_path = None
    if create_backup:
        backup_path = create_backup(file_path)
    
    try:
        file_path.unlink()
        _log_action("DELETE", str(file_path))
        return True, f"删除成功 (备份: {backup_path})"
    except Exception as e:
        if backup_path:
            restore_backup(file_path, backup_path)
        return False, f"删除失败: {str(e)}"


def _log_action(action: str, detail: str):
    """记录安全操作日志"""
    log_file = LOG_DIR / f"security_{datetime.now().strftime('%Y%m%d')}.log"
    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "action": action,
        "detail": mask_sensitive_info(detail)
    }
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


def execute_shell_command(command: str, cwd: Optional[Path] = None, timeout: int = 300) -> Tuple[bool, str, str]:
    """
    执行 Shell 命令（仅在全能模式下可用）
    返回 (成功, 标准输出, 标准错误)
    """
    if not is_unlimited_mode():
        return False, "", "仅在全能模式下允许执行 Shell 命令"
    
    log_security_event("shell_execute", {
        "command": mask_sensitive_info(command),
        "cwd": str(cwd) if cwd else None
    })
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(cwd) if cwd else str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return True, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"命令执行超时（{timeout}秒）"
    except Exception as e:
        return False, "", f"命令执行失败: {str(e)}"

def get_security_status() -> dict:
    """获取安全状态"""
    return {
        "project_root": str(PROJECT_ROOT),
        "backup_dir": str(BACKUP_DIR),
        "log_dir": str(LOG_DIR),
        "safe_extensions": list(SAFE_EXTENSIONS),
        "dangerous_extensions": list(DANGEROUS_EXTENSIONS),
        "backup_count": len(list(BACKUP_DIR.glob("*"))),
        "current_mode": _current_mode,
        "is_unlimited": is_unlimited_mode()
    }


init_security()
