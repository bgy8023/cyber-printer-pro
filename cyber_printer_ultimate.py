import os
import requests
import threading
import time
from builtin_claude_core.query_engine import get_engine
from builtin_claude_core.memory_palace import SQLiteMemoryPalace as SimpleMemoryPalace
from builtin_claude_core.logger import logger

# 全局互斥锁，确保同一时间只允许一个生成任务执行
generate_global_lock = threading.Lock()

# 检查是否使用免费模型（智谱 GLM-4-Flash）
def is_free_model():
    model_name = os.getenv('LLM_MODEL_NAME', '').lower()
    base_url = os.getenv('LLM_BASE_URL', '').lower()
    return 'glm-4-flash' in model_name or 'bigmodel.cn' in base_url

def send_mobile_alert(title, content, is_error=False):
    webhook_url = os.getenv("WEBHOOK_URL")
    if not webhook_url:
        return
        
    try:
        icon = "🚨" if is_error else "🎉"
        full_title = f"{icon}{title}"
        full_content = f"【赛博印钞机Pro】{content}"
        
        if "bark" in webhook_url.lower():
            requests.get(f"{webhook_url}/{full_title}/{full_content}", timeout=5)
        elif "ftqq" in webhook_url.lower() or "sct" in webhook_url.lower():
            requests.post(webhook_url, data={"title": full_title, "desp": full_content}, timeout=5)
        else:
            requests.post(webhook_url, json={"title": full_title, "content": full_content}, timeout=5)
        
        logger.info(f"📱 告警已推送：{title}")
    except Exception as e:
        logger.warning(f"⚠️  告警推送失败: {e}")
        pass

# 加在 cyber_printer_ultimate.py 里，生成函数改造
def generate_chapter_full(chapter_num, target_words, custom_prompt, novel_name="默认小说"):
    # 免费模型风控保护：严格串行执行，防限流
    if is_free_model():
        logger.info("使用免费模型，启用严格串行执行保护")
        # 尝试获取锁，5秒内获取不到直接拒绝新任务
        if not generate_global_lock.acquire(blocking=True, timeout=5):
            logger.warning("检测到免费模型并发生成，已拒绝新任务")
            return False, "⚠️  免费模型限流保护：当前有任务正在执行，请稍后再试"
    else:
        # 付费模型：常规锁保护
        logger.info("使用付费模型，启用常规并发保护")
        if not generate_global_lock.acquire(blocking=False):
            logger.warning("检测到并发生成，已拒绝新任务")
            return False, "当前有任务正在执行，请稍后再试"

    # 无论哪种模型，统一在 finally 里释放锁
    try:
        # 免费模型额外加 2 秒延迟，确保不触发 30 并发上限
        if is_free_model():
            time.sleep(2)

        # 你的生成逻辑，一行不改
        logger.info(f"🚀 开始生成 | 小说：{novel_name} | 章节：{chapter_num}")
        send_mobile_alert(f"开始生成第{chapter_num}章", f"目标字数：{target_words} | 小说：{novel_name}")
        
        memory = SimpleMemoryPalace(novel_name)
        fixed_mem = memory.get_fixed_prompt()
        dynamic_mem = memory.get_dynamic_prompt()
        
        engine = get_engine()
        result = engine.parallel_coordinate(chapter_num, target_words, fixed_mem, dynamic_mem, custom_prompt)
        
        if result and result.get("content"):
            summary = result["content"][:150] + "..." if len(result["content"]) > 150 else result["content"]
            memory.safe_update(chapter_num, summary, result["real_chars"], result["content"])
            send_mobile_alert(
                f"第{chapter_num}章生成完毕", 
                f"实际字数：{result['real_chars']} | 目标：{target_words} | 小说：{novel_name}"
            )
            return True, result["content"]
            
        send_mobile_alert(
            f"第{chapter_num}章生成异常", 
            "大模型返回内容为空", 
            is_error=True
        )
        return False, "大模型返回内容为空"
        
    except Exception as e:
        logger.error(f"生成失败: {e}", exc_info=True)
        error_msg = str(e)[:200]
        send_mobile_alert(
            f"流水线严重崩溃", 
            f"第{chapter_num}章 | {error_msg}", 
            is_error=True
        )
        return False, str(e)
    finally:
        # 免费模型执行完成后再加 2 秒延迟
        if is_free_model():
            time.sleep(2)
        # 无论成功失败，都释放全局互斥锁
        generate_global_lock.release()
        logger.info(f"🔓 生成任务完成，释放全局互斥锁 | 小说：{novel_name} | 章节：{chapter_num}")