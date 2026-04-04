from typing import Dict, Any
from nodes.base import BaseNode
from models.dag import DAGPipeline, NodeStatus
from utils.logger import Logger
from utils.helpers import auto_update_plot_record

def update_plot_node(node_id: str, node_name: str, pipeline: DAGPipeline, context: Dict[str, Any], logger: Logger) -> bool:
    """剧情记忆更新节点 - 无状态纯函数版本"""
    pipeline.nodes[node_id].status = NodeStatus.RUNNING
    
    try:
        chapter_content = context.get("final_content", "")
        chapter_num = context.get("chapter_num", 1)
        
        auto_update_plot_record(chapter_content, chapter_num)
        
        pipeline.nodes[node_id].status = NodeStatus.SUCCESS
        logger.write(f"✅ [{node_name}] 剧情记忆更新完成")
        
        return True
        
    except Exception as e:
        pipeline.nodes[node_id].status = NodeStatus.FAILED
        pipeline.nodes[node_id].error_msg = str(e)
        logger.write(f"❌ [{node_name}] 剧情记忆更新失败：{str(e)}")
        return False

class UpdatePlotNode(BaseNode):
    """剧情记忆更新节点 - 向后兼容包装器"""
    
    def __init__(self):
        super().__init__(
            node_id="update_plot",
            node_name="5. 剧情记忆更新",
            description="更新结构化记忆，防吃书"
        )
    
    def get_pre_nodes(self) -> list[str]:
        return ["humanizer_process"]
    
    def execute(self, pipeline: DAGPipeline, context: Dict[str, Any], logger: Logger) -> bool:
        return update_plot_node(self.node_id, self.node_name, pipeline, context, logger)
