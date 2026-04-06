from builtin_claude_core.query_engine import get_engine
from builtin_claude_core.memory_palace_simple import SimpleMemoryPalace
from builtin_claude_core.logger import logger

def generate_chapter_full(chapter_num, target_words, custom_prompt, novel_name="默认小说"):
    try:
        memory = SimpleMemoryPalace(novel_name)
        fixed_mem = memory.get_fixed_prompt()
        dynamic_mem = memory.get_dynamic_prompt()
        
        engine = get_engine()
        result = engine.parallel_coordinate(chapter_num, target_words, fixed_mem, dynamic_mem, custom_prompt)
        
        if result and result.get("content"):
            memory.safe_update(chapter_num, result["content"][:150] + "...", result["real_chars"])
            return True, result["content"]
        return False, "大模型返回内容为空"
    except Exception as e:
        logger.error(f"生成失败: {e}", exc_info=True)
        return False, str(e)
