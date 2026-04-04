import os
from datetime import datetime
from typing import Optional, List

class Logger:
    """日志记录器"""
    
    def __init__(self, log_path: str = "system.log"):
        """初始化日志记录器
        
        Args:
            log_path: 日志文件路径
        """
        self.log_path = log_path
        self.log_display: List[str] = []
    
    def write(self, content: str, ui_callback: Optional[callable] = None):
        """写入日志
        
        Args:
            content: 日志内容
            ui_callback: UI回调函数，用于更新界面
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {content}"
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
            with open(self.log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()[-max_lines:]
                return [line.rstrip() for line in lines]
        return []
