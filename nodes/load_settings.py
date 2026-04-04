from typing import Dict, Any, Tuple
from nodes.base import BaseNode
from models.dag import DAGPipeline, NodeStatus
from utils.logger import Logger
from utils.helpers import get_lazy_prompt, get_mcp_servers

def load_settings_node(node_id: str, node_name: str, pipeline: DAGPipeline, context: Dict[str, Any], logger: Logger) -> bool:
    """结构化记忆加载节点 - 无状态纯函数版本"""
    pipeline.nodes[node_id].status = NodeStatus.RUNNING
    logger.write(f"🏛️ [{node_name}] 开始加载结构化记忆系统")
    
    try:
        chapter_num = context.get("chapter_num", 1)
        custom_prompt = context.get("custom_prompt", "")
        enable_mcp = context.get("enable_mcp", False)
        enable_xcrawl = context.get("enable_xcrawl", False)
        enable_undercover = context.get("enable_undercover", False)
        enable_multi_agent = context.get("enable_multi_agent", False)
        
        mcp_servers = get_mcp_servers() if enable_mcp else []
        
        final_prompt = custom_prompt if custom_prompt.strip() else get_lazy_prompt(
            enable_mcp, mcp_servers, enable_xcrawl, enable_undercover, enable_multi_agent
        )
        
        context["final_prompt"] = final_prompt
        context["mcp_servers"] = mcp_servers
        
        pipeline.nodes[node_id].status = NodeStatus.SUCCESS
        pipeline.nodes[node_id].result = {"final_prompt": final_prompt}
        logger.write(f"✅ [{node_name}] 结构化记忆加载完成")
        
        return True
        
    except Exception as e:
        pipeline.nodes[node_id].status = NodeStatus.FAILED
        pipeline.nodes[node_id].error_msg = str(e)
        logger.write(f"❌ [{node_name}] 记忆加载失败：{str(e)}")
        return False

class LoadSettingsNode(BaseNode):
    """结构化记忆加载节点 - 向后兼容包装器"""
    
    def __init__(self):
        super().__init__(
            node_id="load_settings",
            node_name="2. 结构化记忆加载",
            description="读取设定，生成结构化记忆"
        )
    
    def get_pre_nodes(self) -> list[str]:
        return ["init_check"]
    
    def execute(self, pipeline: DAGPipeline, context: Dict[str, Any], logger: Logger) -> bool:
        return load_settings_node(self.node_id, self.node_name, pipeline, context, logger)
