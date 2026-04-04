from typing import Dict, Any, Tuple
from nodes.base import BaseNode
from models.dag import DAGPipeline, NodeStatus
from utils.logger import Logger
from utils.helpers import get_lazy_prompt, get_mcp_servers

class LoadSettingsNode(BaseNode):
    """结构化记忆加载节点"""
    
    def __init__(self):
        super().__init__(
            node_id="load_settings",
            node_name="2. 结构化记忆加载",
            description="读取设定，生成结构化记忆"
        )
    
    def get_pre_nodes(self) -> list[str]:
        return ["init_check"]
    
    def execute(self, pipeline: DAGPipeline, context: Dict[str, Any], logger: Logger) -> bool:
        """执行结构化记忆加载"""
        # 更新节点状态
        pipeline.nodes[self.node_id].status = NodeStatus.RUNNING
        logger.write(f"🏛️ [{self.node_name}] 开始加载结构化记忆系统")
        
        try:
            # 获取参数
            chapter_num = context.get("chapter_num", 1)
            custom_prompt = context.get("custom_prompt", "")
            enable_mcp = context.get("enable_mcp", False)
            enable_xcrawl = context.get("enable_xcrawl", False)
            enable_undercover = context.get("enable_undercover", False)
            enable_multi_agent = context.get("enable_multi_agent", False)
            
            # 获取MCP服务器列表
            mcp_servers = get_mcp_servers() if enable_mcp else []
            
            # 生成最终Prompt
            final_prompt = custom_prompt if custom_prompt.strip() else get_lazy_prompt(
                enable_mcp, mcp_servers, enable_xcrawl, enable_undercover, enable_multi_agent
            )
            
            # 保存到上下文
            context["final_prompt"] = final_prompt
            context["mcp_servers"] = mcp_servers
            
            # 更新节点状态为成功
            pipeline.nodes[self.node_id].status = NodeStatus.SUCCESS
            pipeline.nodes[self.node_id].result = {"final_prompt": final_prompt}
            logger.write(f"✅ [{self.node_name}] 结构化记忆加载完成")
            
            return True
            
        except Exception as e:
            # 更新节点状态为失败
            pipeline.nodes[self.node_id].status = NodeStatus.FAILED
            pipeline.nodes[self.node_id].error_msg = str(e)
            logger.write(f"❌ [{self.node_name}] 记忆加载失败：{str(e)}")
            return False
