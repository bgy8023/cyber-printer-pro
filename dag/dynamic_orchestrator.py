from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum
from models.dag import DAGPipeline, DAGNode, NodeStatus
from nodes.base import BaseNode
from utils.logger import Logger
from dag.pipeline import DAGExecutor

class TaskCategory(Enum):
    """任务分类枚举"""
    INITIALIZATION = "initialization"
    CONTENT_GENERATION = "content_generation"
    PROCESSING = "processing"
    PERSISTENCE = "persistence"
    FINALIZATION = "finalization"

class TaskRegistry:
    """任务注册表 - 支持动态注册和发现任务"""
    
    def __init__(self):
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._task_categories: Dict[TaskCategory, List[str]] = {
            category: [] for category in TaskCategory
        }
    
    def register_task(
        self,
        node_id: str,
        node_class: type,
        category: TaskCategory,
        required_context: Optional[List[str]] = None,
        provides_context: Optional[List[str]] = None,
        auto_discoverable: bool = True
    ):
        """注册任务
        
        Args:
            node_id: 节点ID
            node_class: 节点类
            category: 任务分类
            required_context: 所需的上下文键列表
            provides_context: 提供的上下文键列表
            auto_discoverable: 是否可被自动发现
        """
        self._tasks[node_id] = {
            "node_class": node_class,
            "category": category,
            "required_context": required_context or [],
            "provides_context": provides_context or [],
            "auto_discoverable": auto_discoverable
        }
        self._task_categories[category].append(node_id)
    
    def get_task(self, node_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        return self._tasks.get(node_id)
    
    def discover_tasks(self, context: Dict[str, Any]) -> List[str]:
        """根据当前上下文发现可执行的任务
        
        Args:
            context: 当前执行上下文
            
        Returns:
            可执行的任务ID列表
        """
        available_tasks = []
        for node_id, task_info in self._tasks.items():
            if not task_info["auto_discoverable"]:
                continue
            # 检查所需上下文是否都已满足
            required_context = task_info["required_context"]
            if all(key in context for key in required_context):
                available_tasks.append(node_id)
        return available_tasks
    
    def get_tasks_by_category(self, category: TaskCategory) -> List[str]:
        """按分类获取任务列表"""
        return self._task_categories.get(category, [])
    
    def list_all_tasks(self) -> List[str]:
        """列出所有已注册的任务"""
        return list(self._tasks.keys())

class OrchestratorStrategy(Enum):
    """调度策略枚举"""
    DYNAMIC = "dynamic"
    STATIC = "static"

class DynamicOrchestrator:
    """DeerFlow 2.0 单主脑动态任务调度器"""
    
    def __init__(self, logger: Logger):
        """初始化动态调度器
        
        Args:
            logger: 日志记录器
        """
        self.logger = logger
        self.registry = TaskRegistry()
        self.strategy = OrchestratorStrategy.DYNAMIC
        self._static_executor: Optional[DAGExecutor] = None
        self._registered_nodes: Dict[str, BaseNode] = {}
    
    def set_strategy(self, strategy: OrchestratorStrategy):
        """设置调度策略（支持向后兼容）
        
        Args:
            strategy: 调度策略
        """
        self.strategy = strategy
        if strategy == OrchestratorStrategy.STATIC:
            self.logger.write("🔄 [调度器] 切换到静态DAG模式（向后兼容）")
        else:
            self.logger.write("🔄 [调度器] 切换到DeerFlow 2.0动态模式")
    
    def register_node(self, node: BaseNode):
        """注册单个节点（用于静态模式）"""
        self._registered_nodes[node.node_id] = node
    
    def register_task(
        self,
        node_class: type,
        category: TaskCategory,
        required_context: Optional[List[str]] = None,
        provides_context: Optional[List[str]] = None,
        auto_discoverable: bool = True
    ):
        """注册任务（动态模式）
        
        Args:
            node_class: 节点类
            category: 任务分类
            required_context: 所需的上下文键
            provides_context: 提供的上下文键
            auto_discoverable: 是否可自动发现
        """
        # 创建实例获取node_id
        temp_instance = node_class()
        node_id = temp_instance.node_id
        
        self.registry.register_task(
            node_id=node_id,
            node_class=node_class,
            category=category,
            required_context=required_context,
            provides_context=provides_context,
            auto_discoverable=auto_discoverable
        )
        self.logger.write(f"📦 [调度器] 任务已注册: {temp_instance.node_name} ({node_id})")
    
    def analyze_user_intent(self, user_instruction: str, context: Dict[str, Any]) -> List[str]:
        """分析用户意图，识别需要的任务步骤
        
        Args:
            user_instruction: 用户指令
            context: 当前上下文
            
        Returns:
            推荐的任务ID列表
        """
        self.logger.write(f"🧠 [主脑] 正在分析用户指令: {user_instruction}")
        
        # 基于指令关键词和当前上下文分析
        instruction_lower = user_instruction.lower()
        
        # 发现可执行的任务
        available_tasks = self.registry.discover_tasks(context)
        
        # 根据指令和上下文智能排序和选择
        recommended_tasks = []
        
        # 总是从初始化类任务开始
        init_tasks = self.registry.get_tasks_by_category(TaskCategory.INITIALIZATION)
        for task_id in init_tasks:
            if task_id in available_tasks and task_id not in recommended_tasks:
                recommended_tasks.append(task_id)
        
        # 根据指令内容选择内容生成类任务
        if any(keyword in instruction_lower for keyword in ["生成", "写", "创作", "generate", "write"]):
            content_tasks = self.registry.get_tasks_by_category(TaskCategory.CONTENT_GENERATION)
            for task_id in content_tasks:
                if task_id in available_tasks and task_id not in recommended_tasks:
                    recommended_tasks.append(task_id)
        
        # 根据指令内容选择处理类任务
        if any(keyword in instruction_lower for keyword in ["处理", "优化", "润色", "process", "optimize"]):
            processing_tasks = self.registry.get_tasks_by_category(TaskCategory.PROCESSING)
            for task_id in processing_tasks:
                if task_id in available_tasks and task_id not in recommended_tasks:
                    recommended_tasks.append(task_id)
        
        # 根据指令内容选择持久化类任务
        if any(keyword in instruction_lower for keyword in ["保存", "归档", "notion", "github", "save", "archive"]):
            persistence_tasks = self.registry.get_tasks_by_category(TaskCategory.PERSISTENCE)
            for task_id in persistence_tasks:
                if task_id in available_tasks and task_id not in recommended_tasks:
                    recommended_tasks.append(task_id)
        
        # 最后添加结束类任务
        final_tasks = self.registry.get_tasks_by_category(TaskCategory.FINALIZATION)
        for task_id in final_tasks:
            if task_id in available_tasks and task_id not in recommended_tasks:
                recommended_tasks.append(task_id)
        
        self.logger.write(f"✅ [主脑] 分析完成，推荐执行 {len(recommended_tasks)} 个任务")
        for i, task_id in enumerate(recommended_tasks, 1):
            task_info = self.registry.get_task(task_id)
            if task_info:
                node = task_info["node_class"]()
                self.logger.write(f"   {i}. {node.node_name}")
        
        return recommended_tasks
    
    def create_dynamic_pipeline(self, pipeline_id: str, task_ids: List[str]) -> DAGPipeline:
        """创建动态DAG管线
        
        Args:
            pipeline_id: 管线ID
            task_ids: 任务ID列表
            
        Returns:
            DAG管线
        """
        nodes_dict = {}
        
        for i, task_id in enumerate(task_ids):
            task_info = self.registry.get_task(task_id)
            if not task_info:
                continue
            
            node = task_info["node_class"]()
            
            # 动态设置前置节点（前一个节点作为前置）
            pre_nodes = []
            if i > 0:
                pre_nodes = [task_ids[i-1]]
            
            nodes_dict[task_id] = DAGNode(
                node_id=node.node_id,
                node_name=node.node_name,
                description=node.description,
                pre_nodes=pre_nodes
            )
        
        return DAGPipeline(pipeline_id=pipeline_id, nodes=nodes_dict)
    
    def execute_dynamic(self, pipeline: DAGPipeline, context: Dict[str, Any]) -> bool:
        """动态执行管线
        
        Args:
            pipeline: DAG管线
            context: 执行上下文
            
        Returns:
            是否全部执行成功
        """
        self.logger.write("🚀 [调度器] 开始DeerFlow 2.0动态执行")
        
        executed_nodes = set()
        task_order = list(pipeline.nodes.keys())
        
        for node_id in task_order:
            if node_id in executed_nodes:
                continue
            
            task_info = self.registry.get_task(node_id)
            if not task_info:
                self.logger.write(f"⚠️ [调度器] 找不到任务: {node_id}")
                continue
            
            node = task_info["node_class"]()
            
            # 执行节点
            success = node.execute(pipeline, context, self.logger)
            executed_nodes.add(node_id)
            
            if not success:
                self.logger.write(f"❌ [调度器] 动态执行失败，节点：{node.node_name}")
                return False
            
            # 执行后检查是否有新的任务可以发现
            new_available = self.registry.discover_tasks(context)
            new_tasks = [t for t in new_available if t not in executed_nodes and t not in task_order]
            
            if new_tasks:
                self.logger.write(f"🔍 [调度器] 发现 {len(new_tasks)} 个新任务可执行")
        
        self.logger.write("✅ [调度器] DeerFlow 2.0动态执行完成")
        return True
    
    def execute_static(self, context: Dict[str, Any]) -> bool:
        """静态执行（向后兼容）
        
        Args:
            context: 执行上下文
            
        Returns:
            是否全部执行成功
        """
        if not self._static_executor:
            nodes = list(self._registered_nodes.values())
            self._static_executor = DAGExecutor(nodes, self.logger)
        
        pipeline = self._static_executor.create_pipeline("static_pipeline")
        return self._static_executor.execute(pipeline, context)
    
    def orchestrate(self, user_instruction: str, context: Dict[str, Any]) -> bool:
        """主脑调度入口
        
        Args:
            user_instruction: 用户指令
            context: 执行上下文
            
        Returns:
            是否执行成功
        """
        self.logger.write("🎯 [主脑] DeerFlow 2.0 单主脑动态调度器启动")
        
        if self.strategy == OrchestratorStrategy.STATIC:
            self.logger.write("📋 [主脑] 使用静态DAG模式（向后兼容）")
            return self.execute_static(context)
        
        # 动态模式
        # 1. 分析用户意图
        recommended_tasks = self.analyze_user_intent(user_instruction, context)
        
        if not recommended_tasks:
            self.logger.write("⚠️ [主脑] 未找到可执行的任务")
            return False
        
        # 2. 创建动态管线
        pipeline = self.create_dynamic_pipeline("dynamic_pipeline", recommended_tasks)
        
        # 3. 动态执行
        return self.execute_dynamic(pipeline, context)
    
    def get_registered_tasks_info(self) -> List[Dict[str, Any]]:
        """获取已注册任务的详细信息
        
        Returns:
            任务信息列表
        """
        info_list = []
        for task_id in self.registry.list_all_tasks():
            task_info = self.registry.get_task(task_id)
            if task_info:
                node = task_info["node_class"]()
                info_list.append({
                    "node_id": task_id,
                    "node_name": node.node_name,
                    "description": node.description,
                    "category": task_info["category"].value,
                    "required_context": task_info["required_context"],
                    "provides_context": task_info["provides_context"],
                    "auto_discoverable": task_info["auto_discoverable"]
                })
        return info_list
