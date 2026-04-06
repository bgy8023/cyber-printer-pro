# OpenMars 核心模块导出
__version__ = "2.3.0"

# 核心推理引擎
from .query_engine import ClaudeQueryEngine, AsyncQueryEngine, get_session_engine

# 记忆系统
from .memory_palace_simple import SimpleMemoryPalace, get_memory_palace
from .memory_palace import MemoryPalace

# 一致性校验器
from .consistency_checker import HardRuleConsistencyChecker, ConsistencyCheckResult
from .consistency_agent import ConsistencyAgent

# LLM 适配器
from .llm_adapter import LLMAdapter, get_llm_adapter, reset_llm_adapter

# 文件锁
from .file_lock import FileLockManager, lock_manager

# 配置管理
from .config_manager import ConfigManager

# 性能监控
from .metrics import MetricsCollector, GenerationMetrics

# Coordinator 协调器
from .coordinator import Coordinator

# AutoDream 梦游巩固
from .autodream import AutoDream, get_autodream

# Kairos 守护进程
from .kairos_daemon import KairosDaemon

# 日志
from .logger import logger

# 全部导出
__all__ = [
    "ClaudeQueryEngine",
    "AsyncQueryEngine",
    "get_session_engine",
    "SimpleMemoryPalace",
    "get_memory_palace",
    "MemoryPalace",
    "HardRuleConsistencyChecker",
    "ConsistencyCheckResult",
    "ConsistencyAgent",
    "LLMAdapter",
    "get_llm_adapter",
    "reset_llm_adapter",
    "FileLockManager",
    "lock_manager",
    "ConfigManager",
    "MetricsCollector",
    "GenerationMetrics",
    "Coordinator",
    "AutoDream",
    "get_autodream",
    "KairosDaemon",
    "logger",
]
