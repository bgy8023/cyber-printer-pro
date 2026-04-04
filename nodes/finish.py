import os
from typing import Dict, Any
from nodes.base import BaseNode
from models.dag import DAGPipeline, NodeStatus
from utils.logger import Logger

class FinishNode(BaseNode):
    """全链路闭环节点"""
    
    def __init__(self):
        super().__init__(
            node_id="finish",
            node_name="8. 全链路闭环",
            description="生成执行报告，完成归档"
        )
    
    def get_pre_nodes(self) -> list[str]:
        return ["notion_write"]
    
    def execute(self, pipeline: DAGPipeline, context: Dict[str, Any], logger: Logger) -> bool:
        """执行全链路闭环"""
        # 更新节点状态
        pipeline.nodes[self.node_id].status = NodeStatus.RUNNING
        
        try:
            # 获取章节号
            chapter_num = context.get("chapter_num", 1)
            
            # 更新章节号（+1）
            next_chapter = chapter_num + 1
            context["next_chapter"] = next_chapter
            
            # 保存章节号到文件
            chapter_num_file = os.path.expanduser("~/OpenClaw_Arch/current_chapter.txt")
            with open(chapter_num_file, "w") as f:
                f.write(str(next_chapter))
            
            # 更新节点状态为成功
            pipeline.nodes[self.node_id].status = NodeStatus.SUCCESS
            logger.write(f"✅ [{self.node_name}] 全流程闭环完成！下一章章节号已自动更新")
            
            return True
            
        except Exception as e:
            # 更新节点状态为失败
            pipeline.nodes[self.node_id].status = NodeStatus.FAILED
            pipeline.nodes[self.node_id].error_msg = str(e)
            logger.write(f"❌ [{self.node_name}] 全链路闭环失败：{str(e)}")
            return False
