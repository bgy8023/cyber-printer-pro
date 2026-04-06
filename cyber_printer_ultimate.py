import os
import requests
from builtin_claude_core.query_engine import get_engine
from builtin_claude_core.memory_palace import SQLiteMemoryPalace as SimpleMemoryPalace
from builtin_claude_core.logger import logger

def send_mobile_alert(title, content, is_error=False):
    """
    全平台兼容轻量级告警推送
    在.env中配置WEBHOOK_URL即可启用
    支持：Bark(iOS)/Server酱/飞书/钉钉自定义机器人
    """
    webhook_url = os.getenv("WEBHOOK_URL")
    if not webhook_url:
        return
        
    try:
        icon = "🚨" if is_error else "🎉"
        full_title = f"{icon}{title}"
        full_content = f"【OpenMars】{content}"
        
        # Bark iOS 极客首选
        if "bark" in webhook_url.lower():
            requests.get(f"{webhook_url}/{full_title}/{full_content}", timeout=5)
        # Server酱 全平台通用
        elif "ftqq" in webhook_url.lower() or "sct" in webhook_url.lower():
            requests.post(webhook_url, data={"title": full_title, "desp": full_content}, timeout=5)
        # 飞书/钉钉 自定义机器人
        else:
            requests.post(webhook_url, json={"title": full_title, "content": full_content}, timeout=5)
        
        logger.info(f"📱 告警已推送：{title}")
    except Exception as e:
        logger.warning(f"⚠️ 告警推送失败（不影响主流程）: {e}")
        pass

def generate_chapter_full(chapter_num, target_words, custom_prompt, novel_name="默认小说"):
    try:
        logger.info(f"🚀 开始生成 | 小说：{novel_name} | 章节：{chapter_num}")
        # 启动告警（可选）
        send_mobile_alert(f"开始生成第{chapter_num}章", f"目标字数：{target_words} | 小说：{novel_name}")
        
        memory = SimpleMemoryPalace(novel_name)
        fixed_mem = memory.get_fixed_prompt()
        dynamic_mem = memory.get_dynamic_prompt()
        
        engine = get_engine()
        result = engine.parallel_coordinate(chapter_num, target_words, fixed_mem, dynamic_mem, custom_prompt)
        
        if result and result.get("content"):
            summary = result["content"][:150] + "..." if len(result["content"]) > 150 else result["content"]
            memory.safe_update(chapter_num, summary, result["real_chars"], result["content"])
            # 成功告警
            send_mobile_alert(
                f"第{chapter_num}章生成完毕",
                f"实际字数：{result['real_chars']} | 目标：{target_words} | 小说：{novel_name}"
            )
            return True, result["content"]
            
        # 内容为空告警
        send_mobile_alert(
            f"第{chapter_num}章生成异常",
            "大模型返回内容为空",
            is_error=True
        )
        return False, "大模型返回内容为空"
        
    except Exception as e:
        logger.error(f"生成失败: {e}", exc_info=True)
        # 严重崩溃告警
        error_msg = str(e)[:200]
        send_mobile_alert(
            f"流水线严重崩溃",
            f"第{chapter_num}章 | {error_msg}",
            is_error=True
        )
        return False, str(e)
