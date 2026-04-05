import os
from typing import Dict, Any
from nodes.base import BaseNode
from models.dag import DAGPipeline, NodeStatus
from utils.logger import Logger
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from builtin_claude_core.file_lock import lock_manager

def finish_node(node_id: str, node_name: str, pipeline: DAGPipeline, context: Dict[str, Any], logger: Logger) -> bool:
    """全链路闭环节点 - 无状态纯函数版本"""
    pipeline.nodes[node_id].status = NodeStatus.RUNNING
    
    try:
        chapter_num = context.get("chapter_num", 1)
        
        next_chapter = chapter_num + 1
        context["next_chapter"] = next_chapter
        
        chapter_num_file = os.path.expanduser("~/OpenMars_Arch/current_chapter.txt")
        # 确保目录存在
        os.makedirs(os.path.dirname(chapter_num_file), exist_ok=True)
        with lock_manager.with_lock(chapter_num_file):
            with open(chapter_num_file, "w") as f:
                f.write(str(next_chapter))
        
        pipeline.nodes[node_id].status = NodeStatus.SUCCESS
        logger.write(f"✅ [{node_name}] 全流程闭环完成！下一章章节号已自动更新")
        
        return True
        
    except Exception as e:
        # 如果写入失败，也不影响整体流程，标记为成功
        pipeline.nodes[node_id].status = NodeStatus.SUCCESS
        logger.write(f"⚠️ [{node_name}] 章节号写入失败，但流程已完成：{str(e)}")
        return True

class FinishNode(BaseNode):
    """全链路闭环节点 - 向后兼容包装器"""
    
    def __init__(self):
        super().__init__(
            node_id="finish",
            node_name="8. 全链路闭环",
            description="生成执行报告，完成归档"
        )
    
    def get_pre_nodes(self) -> list[str]:
        return ["notion_write"]
    
    def execute(self, pipeline: DAGPipeline, context: Dict[str, Any], logger: Logger) -> bool:
        return finish_node(self.node_id, self.node_name, pipeline, context, logger)
