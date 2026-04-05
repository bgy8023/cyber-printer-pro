from typing import Callable, Dict, Any, Optional
from enum import Enum
from .logger import logger
import asyncio
import time


class HookType(Enum):
    """18种生命周期钩子类型"""
    # 初始化阶段
    ON_INIT = "on_init"
    ON_LOAD = "on_load"
    ON_READY = "on_ready"
    
    # 大纲阶段
    PRE_OUTLINE = "pre_outline"
    POST_OUTLINE = "post_outline"
    ON_OUTLINE_ERROR = "on_outline_error"
    
    # 写作阶段
    PRE_WRITE = "pre_write"
    ON_WRITE_PROGRESS = "on_write_progress"
    POST_WRITE = "post_write"
    ON_WRITE_ERROR = "on_write_error"
    
    # 审核阶段
    PRE_REVIEW = "pre_review"
    POST_REVIEW = "post_review"
    ON_REVIEW_ERROR = "on_review_error"
    
    # 润色阶段
    PRE_POLISH = "pre_polish"
    POST_POLISH = "post_polish"
    ON_POLISH_ERROR = "on_polish_error"
    
    # 完成阶段
    PRE_FINISH = "pre_finish"
    POST_FINISH = "post_finish"
    ON_FINISH_ERROR = "on_finish_error"
    
    # 记忆阶段
    PRE_MEMORY_SAVE = "pre_memory_save"
    POST_MEMORY_SAVE = "post_memory_save"
    PRE_MEMORY_LOAD = "pre_memory_load"
    POST_MEMORY_LOAD = "post_memory_load"
    
    # 缓存阶段
    PRE_CACHE_GET = "pre_cache_get"
    POST_CACHE_GET = "post_cache_get"
    PRE_CACHE_SET = "pre_cache_set"
    POST_CACHE_SET = "post_cache_set"


class HookManager:
    """增强版钩子管理器，单例模式"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.hooks: Dict[HookType, list[Callable]] = {t: [] for t in HookType}
            cls._instance.hook_stats: Dict[HookType, int] = {t: 0 for t in HookType}
        return cls._instance
    
    def register(self, hook_type: HookType, func: Callable):
        """注册钩子函数"""
        self.hooks[hook_type].append(func)
        logger.info(f"✅ 已注册{hook_type.value}钩子：{func.__name__}")
    
    def register_multiple(self, hook_types: list[HookType], func: Callable):
        """批量注册钩子函数到多个类型"""
        for hook_type in hook_types:
            self.register(hook_type, func)
    
    def unregister(self, hook_type: HookType, func: Callable):
        """注销钩子函数"""
        if func in self.hooks[hook_type]:
            self.hooks[hook_type].remove(func)
            logger.info(f"🗑️  已注销{hook_type.value}钩子：{func.__name__}")
    
    def trigger(self, hook_type: HookType, context: Dict[str, Any]) -> Dict[str, Any]:
        """触发指定类型的钩子，返回处理后的上下文"""
        self.hook_stats[hook_type] += 1
        
        for hook_func in self.hooks[hook_type]:
            try:
                logger.info(f"🚀 执行{hook_type.value}钩子：{hook_func.__name__}")
                result = hook_func(context)
                if isinstance(result, dict):
                    context = result
            except Exception as e:
                logger.error(f"❌ 钩子{hook_func.__name__}执行失败：{str(e)}", exc_info=True)
        
        return context
    
    async def trigger_async(self, hook_type: HookType, context: Dict[str, Any]) -> Dict[str, Any]:
        """异步触发指定类型的钩子"""
        self.hook_stats[hook_type] += 1
        
        for hook_func in self.hooks[hook_type]:
            try:
                logger.info(f"🚀 执行{hook_type.value}异步钩子：{hook_func.__name__}")
                if asyncio.iscoroutinefunction(hook_func):
                    result = await hook_func(context)
                else:
                    result = hook_func(context)
                
                if isinstance(result, dict):
                    context = result
            except Exception as e:
                logger.error(f"❌ 异步钩子{hook_func.__name__}执行失败：{str(e)}", exc_info=True)
        
        return context
    
    def get_stats(self) -> Dict[str, int]:
        """获取钩子执行统计"""
        return {t.value: count for t, count in self.hook_stats.items()}
    
    def reset_stats(self):
        """重置统计信息"""
        for t in HookType:
            self.hook_stats[t] = 0
        logger.info("📊 钩子统计已重置")
    
    def clear_hooks(self, hook_type: Optional[HookType] = None):
        """清空钩子"""
        if hook_type:
            self.hooks[hook_type] = []
            logger.info(f"🧹 已清空{hook_type.value}钩子")
        else:
            for t in HookType:
                self.hooks[t] = []
            logger.info("🧹 已清空所有钩子")


# 示例钩子函数
def example_on_init_hook(context: Dict[str, Any]) -> Dict[str, Any]:
    """初始化钩子示例：记录启动时间"""
    context["init_timestamp"] = time.time()
    logger.info(f"🕐 系统初始化时间：{context['init_timestamp']}")
    return context


def example_pre_write_hook(context: Dict[str, Any]) -> Dict[str, Any]:
    """写作前钩子示例：添加章节元数据"""
    chapter_num = context.get("chapter_num", 0)
    context["write_start_time"] = time.time()
    logger.info(f"✍️  准备撰写第{chapter_num}章")
    return context


def example_post_write_hook(context: Dict[str, Any]) -> Dict[str, Any]:
    """写作后钩子示例：计算写作时间"""
    if "write_start_time" in context:
        write_time = time.time() - context["write_start_time"]
        context["write_duration"] = write_time
        word_count = len(context.get("content", ""))
        logger.info(f"✅ 写作完成 | 耗时：{write_time:.2f}秒 | 字数：{word_count}")
    return context


def example_pre_cache_get_hook(context: Dict[str, Any]) -> Dict[str, Any]:
    """缓存获取前钩子示例：记录缓存请求"""
    cache_key = context.get("cache_key", "unknown")
    logger.info(f"🔍 查询缓存：{cache_key}")
    return context


def example_post_cache_get_hook(context: Dict[str, Any]) -> Dict[str, Any]:
    """缓存获取后钩子示例：记录缓存命中"""
    cache_hit = context.get("cache_hit", False)
    if cache_hit:
        logger.info("✅ 缓存命中")
    else:
        logger.info("❌ 缓存未命中")
    return context


def example_pre_memory_save_hook(context: Dict[str, Any]) -> Dict[str, Any]:
    """记忆保存前钩子示例：添加保存时间"""
    context["save_timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"💾 准备保存记忆：{context['save_timestamp']}")
    return context


def example_post_finish_hook(context: Dict[str, Any]) -> Dict[str, Any]:
    """完成后钩子示例：打印完成信息"""
    chapter_num = context.get("chapter_num", 0)
    word_count = context.get("word_count", 0)
    logger.info(f"🎉 第{chapter_num}章生成完成，字数：{word_count}")
    return context


# 全局钩子管理器
hook_manager = HookManager()

