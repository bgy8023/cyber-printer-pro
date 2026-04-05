from typing import Dict, Any, Optional, List
from models.dag import DAGPipeline
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from builtin_claude_core.file_lock import lock_manager

class StateManager:
    """应用状态管理器"""
    
    def __init__(self):
        """初始化状态管理器"""
        self.pipeline: Optional[DAGPipeline] = None
        self.current_chapter: int = 1
        self.preview_content: str = ""
        self.rollback_data: Dict[str, Any] = {}
        self.agents_list: list[str] = ["default"]
        self.log_display: List[str] = []
    
    def reset(self):
        """重置状态"""
        self.pipeline = None
        self.preview_content = ""
        self.rollback_data = {}
        self.log_display = []
    
    def load_current_chapter(self):
        """从文件加载当前章节号"""
        chapter_num_file = os.path.expanduser("~/OpenMars_Arch/current_chapter.txt")
        if os.path.exists(chapter_num_file):
            try:
                with lock_manager.with_lock(chapter_num_file):
                    with open(chapter_num_file, "r") as f:
                        self.current_chapter = int(f.read().strip())
            except:
                self.current_chapter = 1
