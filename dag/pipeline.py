from typing import Dict, Any, List, Optional
from datetime import datetime
from models.dag import DAGPipeline, DAGNode, NodeStatus
from nodes.base import BaseNode
from utils.logger import Logger

class DAGExecutor:
    """DAG执行引擎"""
    
    def __init__(self, nodes: List[BaseNode], logger: Logger):
        """初始化执行引擎
        
        Args:
            nodes: 节点列表
            logger: 日志记录器
        """
        self.nodes = {node.node_id: node for node in nodes}
        self.logger = logger
        self.node_id_to_index = {node.node_id: i for i, node in enumerate(nodes)}
    
    def create_pipeline(self, pipeline_id: str) -> DAGPipeline:
        """创建DAG管线
        
        Args:
            pipeline_id: 管线ID
            
        Returns:
            DAG管线
        """
        nodes_dict = {}
        for node_id, node in self.nodes.items():
            nodes_dict[node_id] = DAGNode(
                node_id=node.node_id,
                node_name=node.node_name,
                description=node.description,
                pre_nodes=node.get_pre_nodes()
            )
        return DAGPipeline(pipeline_id=pipeline_id, nodes=nodes_dict)
    
    def execute(self, pipeline: DAGPipeline, context: Dict[str, Any]) -> bool:
        """执行DAG管线
        
        Args:
            pipeline: DAG管线
            context: 执行上下文
            
        Returns:
            是否全部执行成功
        """
        # 按照依赖顺序执行节点
        executed_nodes = set()
        
        while len(executed_nodes) < len(self.nodes):
            progress = False
            
            for node_id, node in self.nodes.items():
                if node_id in executed_nodes:
                    continue
                
                # 检查前置节点是否都已执行
                pre_nodes = node.get_pre_nodes()
                if all(pre_node in executed_nodes for pre_node in pre_nodes):
                    # 执行节点
                    success = node.execute(pipeline, context, self.logger)
                    executed_nodes.add(node_id)
                    progress = True
                    
                    if not success:
                        self.logger.write(f"❌ 管线执行失败，节点：{node.node_name}")
                        return False
            
            if not progress:
                self.logger.write("❌ 管线执行失败，存在循环依赖或未满足的前置条件")
                return False
        
        self.logger.write("✅ 管线执行完成")
        return True
    
    def get_nodes_ordered(self) -> List[BaseNode]:
        """获取按顺序排列的节点列表
        
        Returns:
            节点列表
        """
        return [node for _, node in sorted(self.nodes.items(), key=lambda x: self.node_id_to_index[x[0]])]
