#!/usr/bin/env python3
"""
DeerFlow 2.0 动态调度器使用示例
演示如何注册任务、设置策略和执行调度
"""

from typing import Dict, Any
from utils.logger import Logger
from dag.dynamic_orchestrator import (
    DynamicOrchestrator,
    TaskCategory,
    OrchestratorStrategy
)
from nodes.init_check import InitCheckNode
from nodes.load_settings import LoadSettingsNode
from nodes.generate_content import GenerateContentNode
from nodes.humanizer_process import HumanizerProcessNode
from nodes.update_plot import UpdatePlotNode
from nodes.notion_write import NotionWriteNode
from nodes.github_archive import GitHubArchiveNode
from nodes.finish import FinishNode

def main():
    """示例主函数"""
    logger = Logger("orchestrator_example.log")
    logger.write("=" * 60)
    logger.write("🦌 DeerFlow 2.0 动态调度器示例")
    logger.write("=" * 60)
    
    # 创建调度器实例
    orchestrator = DynamicOrchestrator(logger)
    
    # 注册任务（动态模式）
    logger.write("\n📦 正在注册任务...")
    
    # 初始化类任务
    orchestrator.register_task(
        node_class=InitCheckNode,
        category=TaskCategory.INITIALIZATION,
        required_context=[],
        provides_context=["notion_token", "notion_db_id", "github_token", "github_repo"]
    )
    
    orchestrator.register_task(
        node_class=LoadSettingsNode,
        category=TaskCategory.INITIALIZATION,
        required_context=["notion_token", "notion_db_id", "github_token", "github_repo"],
        provides_context=["chapter_num", "chapter_title", "final_prompt", "target_words", "target_agent"]
    )
    
    # 内容生成类任务
    orchestrator.register_task(
        node_class=GenerateContentNode,
        category=TaskCategory.CONTENT_GENERATION,
        required_context=["chapter_num", "chapter_title", "final_prompt", "target_words", "target_agent"],
        provides_context=["raw_content", "real_chars"]
    )
    
    # 处理类任务
    orchestrator.register_task(
        node_class=HumanizerProcessNode,
        category=TaskCategory.PROCESSING,
        required_context=["raw_content"],
        provides_context=["humanized_content"]
    )
    
    orchestrator.register_task(
        node_class=UpdatePlotNode,
        category=TaskCategory.PROCESSING,
        required_context=["chapter_num"],
        provides_context=["plot_updated"]
    )
    
    # 持久化类任务
    orchestrator.register_task(
        node_class=NotionWriteNode,
        category=TaskCategory.PERSISTENCE,
        required_context=["raw_content", "chapter_num"],
        provides_context=["notion_saved"]
    )
    
    orchestrator.register_task(
        node_class=GitHubArchiveNode,
        category=TaskCategory.PERSISTENCE,
        required_context=["raw_content", "chapter_num", "github_token", "github_repo"],
        provides_context=["github_archived"]
    )
    
    # 结束类任务
    orchestrator.register_task(
        node_class=FinishNode,
        category=TaskCategory.FINALIZATION,
        required_context=["notion_saved"],
        provides_context=["next_chapter"]
    )
    
    # 查看已注册的任务信息
    logger.write("\n📋 已注册任务列表:")
    tasks_info = orchestrator.get_registered_tasks_info()
    for task in tasks_info:
        logger.write(f"  - {task['node_name']} ({task['node_id']})")
        logger.write(f"    分类: {task['category']}")
        logger.write(f"    所需上下文: {task['required_context']}")
        logger.write(f"    提供上下文: {task['provides_context']}")
    
    # 演示动态模式
    logger.write("\n" + "=" * 60)
    logger.write("🚀 演示 1: DeerFlow 2.0 动态模式")
    logger.write("=" * 60)
    
    orchestrator.set_strategy(OrchestratorStrategy.DYNAMIC)
    
    # 模拟用户指令
    user_instruction = "生成第5章内容，保存到Notion并归档到GitHub"
    context: Dict[str, Any] = {
        "target_agent": "default",
        "enable_multi_agent": True,
        "enable_humanizer": True,
        "enable_mcp": False
    }
    
    # 执行调度
    logger.write(f"\n📝 用户指令: {user_instruction}")
    success = orchestrator.orchestrate(user_instruction, context)
    
    if success:
        logger.write("\n✅ 动态调度执行成功！")
    else:
        logger.write("\n❌ 动态调度执行失败")
    
    # 演示静态模式（向后兼容）
    logger.write("\n" + "=" * 60)
    logger.write("📋 演示 2: 静态DAG模式（向后兼容）")
    logger.write("=" * 60)
    
    orchestrator.set_strategy(OrchestratorStrategy.STATIC)
    
    # 注册节点（用于静态模式）
    nodes = [
        InitCheckNode(),
        LoadSettingsNode(),
        GenerateContentNode(),
        HumanizerProcessNode(),
        UpdatePlotNode(),
        NotionWriteNode(),
        GitHubArchiveNode(),
        FinishNode()
    ]
    for node in nodes:
        orchestrator.register_node(node)
    
    # 执行静态模式
    logger.write("\n📋 正在执行静态DAG模式...")
    success_static = orchestrator.orchestrate("静态模式执行", context)
    
    if success_static:
        logger.write("\n✅ 静态模式执行成功！")
    else:
        logger.write("\n❌ 静态模式执行失败")
    
    logger.write("\n" + "=" * 60)
    logger.write("🎯 示例执行完成")
    logger.write("=" * 60)

if __name__ == "__main__":
    main()
