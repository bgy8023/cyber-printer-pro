from typing import Callable, Dict, Any
from enum import Enum
from .logger import logger

class SimpleHookType(Enum):
    PRE_GENERATE = "pre_generate"
    POST_FINISH = "post_finish"

class SimpleHookManager:
    """简化版钩子管理器，单例模式"""
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.hooks: Dict[SimpleHookType, list[Callable]] = {t: [] for t in SimpleHookType}
        return cls._instance

    def register(self, hook_type: SimpleHookType, func: Callable):
        """注册钩子函数"""
        self.hooks[hook_type].append(func)
        logger.info(f"✅ 已注册{hook_type.value}钩子：{func.__name__}")

    def trigger(self, hook_type: SimpleHookType, context: Dict[str, Any]) -> Dict[str, Any]:
        """触发指定类型的钩子，返回处理后的上下文"""
        for hook_func in self.hooks[hook_type]:
            try:
                logger.info(f"🚀 执行{hook_type.value}钩子：{hook_func.__name__}")
                context = hook_func(context)
            except Exception as e:
                logger.error(f"❌ 钩子{hook_func.__name__}执行失败：{str(e)}", exc_info=True)
        return context

def example_pre_generate_hook(context: Dict[str, Any]) -> Dict[str, Any]:
    """生成前钩子示例：自动添加时间戳"""
    import time
    context["generate_timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"🕐 生成时间戳：{context['generate_timestamp']}")
    return context

def example_post_finish_hook(context: Dict[str, Any]) -> Dict[str, Any]:
    """生成后钩子示例：自动打印完成信息"""
    chapter_num = context.get("chapter_num", 0)
    word_count = context.get("word_count", 0)
    logger.info(f"🎉 第{chapter_num}章生成完成，字数：{word_count}")
    return context

hook_manager = SimpleHookManager()
