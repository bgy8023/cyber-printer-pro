from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from models.dag import DAGPipeline, NodeStatus
from utils.logger import Logger

class BaseNode(ABC):
    """DAG节点基类"""
    
    def __init__(self, node_id: str, node_name: str, description: str):
        """初始化节点
        
        Args:
            node_id: 节点ID
            node_name: 节点名称
            description: 节点描述
        """
        self.node_id = node_id
        self.node_name = node_name
        self.description = description
    
    @abstractmethod
    def execute(self, pipeline: DAGPipeline, context: Dict[str, Any], logger: Logger) -> bool:
        """执行节点逻辑
        
        Args:
            pipeline: DAG管线
            context: 执行上下文
            logger: 日志记录器
            
        Returns:
            是否执行成功
        """
        pass
    
    def get_pre_nodes(self) -> List[str]:
        """获取前置节点列表
        
        Returns:
            前置节点ID列表
        """
        return []
