from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Dict, Any, Optional
import os
from .logger import logger

class Coordinator:
    """
    【DeerFlow 2.0 动态并行调度器】
    - 从固定4线程改为动态并行度
    - 根据任务需求自动调整
    - 支持任务优先级和依赖关系
    """
    def __init__(self, max_workers: Optional[int] = None):
        """
        初始化协调器
        
        Args:
            max_workers: 最大并行数，None则自动计算
        """
        if max_workers is None:
            max_workers = self._calculate_optimal_workers()
        
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        logger.info(f"🤖 Coordinator 初始化完成，动态并行度：{max_workers}")
    
    def _calculate_optimal_workers(self) -> int:
        """
        计算最优并行数
        - 根据CPU核心数和任务类型自动调整
        - DeerFlow理念：够用就行，不浪费资源
        """
        import multiprocessing
        cpu_count = multiprocessing.cpu_count()
        
        try:
            env_workers = os.getenv("COORDINATOR_MAX_WORKERS")
            if env_workers:
                return int(env_workers)
        except (ValueError, TypeError):
            pass
        
        optimal = min(cpu_count, 8)
        logger.info(f"🔧 自动计算最优并行度：CPU {cpu_count}核 → 使用 {optimal} 线程")
        return optimal
    
    def parallel_design(
        self, 
        outline: str, 
        context: str,
        task_config: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        【DeerFlow 2.0 动态并行设计】
        - 支持自定义任务配置
        - 根据任务复杂度自动调整并行度
        - 支持优先级和依赖关系
        
        Args:
            outline: 章节大纲
            context: 上下文信息
            task_config: 自定义任务配置，None则使用默认配置
        
        Returns:
            合并后的设计结果
        """
        logger.info("🤖 Coordinator 开始动态并行设计（DeerFlow 2.0）...")
        
        if task_config is None:
            task_config = self._get_default_tasks(outline, context)
        
        results = self._execute_tasks_dynamically(task_config)
        
        summary = self._merge_results(results, task_config)
        
        logger.info("✅ Coordinator 动态并行设计完成")
        return summary
    
    def _get_default_tasks(self, outline: str, context: str) -> List[Dict[str, Any]]:
        """获取默认任务配置"""
        return [
            {
                "id": "cool_points",
                "title": "爽点设计",
                "prompt": f"设计3个强爽点，大纲：{outline}",
                "priority": 1,
                "depends_on": []
            },
            {
                "id": "hook",
                "title": "开头钩子",
                "prompt": f"设计抓眼球开头，大纲：{outline}",
                "priority": 1,
                "depends_on": []
            },
            {
                "id": "rhythm",
                "title": "节奏规划",
                "prompt": "设计松紧节奏，7500字",
                "priority": 2,
                "depends_on": ["cool_points"]
            },
            {
                "id": "dialogue",
                "title": "人物对话风格",
                "prompt": f"强化对话自然度，上下文：{context}",
                "priority": 2,
                "depends_on": ["hook"]
            }
        ]
    
    def _execute_tasks_dynamically(self, task_config: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        动态执行任务
        - 按优先级排序
        - 处理依赖关系
        - 动态调整并行度
        """
        results = {}
        completed_tasks = set()
        
        sorted_tasks = sorted(task_config, key=lambda x: x["priority"])
        
        while len(completed_tasks) < len(sorted_tasks):
            ready_tasks = [
                task for task in sorted_tasks
                if task["id"] not in completed_tasks
                and all(dep in completed_tasks for dep in task["depends_on"])
            ]
            
            if not ready_tasks:
                logger.warning("⚠️ 没有可执行的任务，检查依赖关系")
                break
            
            current_workers = min(len(ready_tasks), self.max_workers)
            logger.info(f"📊 本轮执行 {len(ready_tasks)} 个任务，使用 {current_workers} 线程")
            
            futures = {}
            for task in ready_tasks[:current_workers]:
                future = self.executor.submit(
                    self._run_task,
                    task["title"],
                    task["prompt"]
                )
                futures[future] = task["id"]
            
            for future in as_completed(futures):
                task_id = futures[future]
                try:
                    result = future.result()
                    results[task_id] = result
                    completed_tasks.add(task_id)
                    logger.info(f"✅ 任务完成：{task_id}")
                except Exception as e:
                    logger.error(f"❌ 任务失败：{task_id}，错误：{str(e)}", exc_info=True)
                    results[task_id] = f"任务执行失败：{str(e)}"
                    completed_tasks.add(task_id)
        
        return results
    
    def _merge_results(self, results: Dict[str, str], task_config: List[Dict[str, Any]]) -> str:
        """合并执行结果"""
        parts = []
        for task in task_config:
            task_id = task["id"]
            title = task["title"]
            result = results.get(task_id, "任务未执行")
            parts.append(f"【{title}】\n{result}")
        
        return "\n".join(parts)
    
    def _run_task(self, title: str, prompt: str) -> str:
        """执行单个任务（占位实现）"""
        logger.info(f"🚀 执行任务：{title}")
        return f"{title} 已完成（DeerFlow 2.0 动态并行生成）"
    
    def shutdown(self, wait: bool = True):
        """关闭协调器，释放资源"""
        logger.info("🔌 正在关闭 Coordinator...")
        self.executor.shutdown(wait=wait)
        logger.info("✅ Coordinator 已关闭")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown(wait=True)
        return False
