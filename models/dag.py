from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any

class NodeStatus(Enum):
    """DAG节点状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class DAGNode:
    """DAG节点数据模型"""
    node_id: str
    node_name: str
    description: str
    pre_nodes: list[str] = field(default_factory=list)
    status: NodeStatus = NodeStatus.IDLE
    result: Optional[Dict[str, Any]] = None
    error_msg: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

@dataclass
class DAGPipeline:
    """DAG管线数据模型"""
    pipeline_id: str
    nodes: Dict[str, DAGNode]
    create_time: datetime = field(default_factory=datetime.now)
    current_node: Optional[str] = None
    status: NodeStatus = NodeStatus.IDLE
