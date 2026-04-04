from typing import Dict, Any
from nodes.base import BaseNode
from models.dag import DAGPipeline, NodeStatus
from utils.logger import Logger
from utils.helpers import auto_update_plot_record

class UpdatePlotNode(BaseNode):
    """剧情记忆更新节点"""
    
    def __init__(self):
        super().__init__(
            node_id="update_plot",
            node_name="5. 剧情记忆更新",
            description="更新结构化记忆，防吃书"
        )
    
    def get_pre_nodes(self) -> list[str]:
        return ["humanizer_process"]
    
    def execute(self, pipeline: DAGPipeline, context: Dict[str, Any], logger: Logger) -> bool:
        """执行剧情记忆更新"""
        # 更新节点状态
        pipeline.nodes[self.node_id].status = NodeStatus.RUNNING
        
        try:
            # 获取参数
            chapter_content = context.get("final_content", "")
            chapter_num = context.get("chapter_num", 1)
            
            # 更新剧情备忘录
            auto_update_plot_record(chapter_content, chapter_num)
            
            # 更新节点状态为成功
            pipeline.nodes[self.node_id].status = NodeStatus.SUCCESS
            logger.write(f"✅ [{self.node_name}] 剧情记忆更新完成")
            
            return True
            
        except Exception as e:
            # 更新节点状态为失败
            pipeline.nodes[self.node_id].status = NodeStatus.FAILED
            pipeline.nodes[self.node_id].error_msg = str(e)
            logger.write(f"❌ [{self.node_name}] 剧情记忆更新失败：{str(e)}")
            return False
