import os
import re
from datetime import datetime
from typing import Optional, List, Callable
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from builtin_claude_core.file_lock import lock_manager

def sanitize_message(message: str) -> str:
    """
    清理日志消息，移除敏感信息
    
    Args:
        message: 原始消息
        
    Returns:
        清理后的消息
    """
    if not isinstance(message, str):
        return message
    
    # 过滤 API Key
    message = re.sub(r'sk-[a-zA-Z0-9_-]{20,}', '[REDACTED_API_KEY]', message)
    message = re.sub(r'(API[-_]?KEY|api[-_]?key)\s*[=:]\s*[^\s]+', r'\1=[REDACTED]', message, flags=re.IGNORECASE)
    
    # 过滤密码
    message = re.sub(r'(password|PASSWORD)\s*[=:]\s*[^\s]+', r'\1=[REDACTED]', message, flags=re.IGNORECASE)
    
    # 过滤 Token
    message = re.sub(r'(token|TOKEN)\s*[=:]\s*[^\s]+', r'\1=[REDACTED]', message, flags=re.IGNORECASE)
    
    # 过滤 Bearer Token
    message = re.sub(r'Bearer\s+[a-zA-Z0-9_.-]{20,}', 'Bearer [REDACTED]', message)
    
    return message

class Logger:
    """日志记录器"""
    
    def __init__(self, log_path: str = "system.log"):
        """初始化日志记录器
        
        Args:
            log_path: 日志文件路径
        """
        self.log_path = log_path
        self.log_display: List[str] = []
    
    def write(self, content: str, ui_callback: Optional[Callable] = None):
        """写入日志
        
        Args:
            content: 日志内容
            ui_callback: UI回调函数，用于更新界面
        """
        sanitized_content = sanitize_message(content)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {sanitized_content}"
        self.log_display.append(log_line)
        
        # 确保日志文件目录存在
        log_dir = os.path.dirname(self.log_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(log_line + "\n")
        
        if ui_callback:
            ui_callback("\n".join(self.log_display))
    
    def get_logs(self) -> List[str]:
        """获取所有日志
        
        Returns:
            日志列表
        """
        return self.log_display
    
    def clear(self):
        """清空日志"""
        self.log_display = []
    
    def load_from_file(self, max_lines: int = 25) -> List[str]:
        """从文件加载日志
        
        Args:
            max_lines: 最大加载行数
            
        Returns:
            日志列表
        """
        if os.path.exists(self.log_path):
            with lock_manager.with_lock(self.log_path):
                with open(self.log_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()[-max_lines:]
                    return [line.rstrip() for line in lines]
        return []
