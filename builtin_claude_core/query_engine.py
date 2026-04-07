import os
import asyncio
# 【P0级修复 必须放在最顶部】工业级事件循环嵌套补丁，解决Streamlit容器冲突
import nest_asyncio
nest_asyncio.apply()

from dotenv import load_dotenv
from litellm import acompletion, RateLimitError
from .logger import logger

load_dotenv()

class AsyncQueryEngine:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
        self.model_name = os.getenv("LLM_MODEL_NAME", "deepseek-chat")
        self.max_retries = int(os.getenv("MAX_RETRY", "3"))
        # 【修复点1】正确的超时配置，适配DeepSeek异步SDK
        self.request_timeout = float(os.getenv("LLM_TIMEOUT", "120.0"))

    async def call_llm_async(self, user_prompt: str, system_prompt: str) -> str:
        for i in range(self.max_retries):
            try:
                # 【修复点2】异步调用用request_timeout，不是timeout，适配DeepSeek规范
                response = await acompletion(
                    model=self.model_name,
                    messages=[{"role": "system", "content": system_prompt},
                              {"role": "user", "content": user_prompt}],
                    api_key=self.api_key,
                    base_url=self.base_url,
                    temperature=0.7,
                    top_p=0.9,
                    request_timeout=self.request_timeout,
                    max_retries=0
                )
                return response.choices[0].message.content.strip()
            except RateLimitError:
                wait_time = 2 ** i
                logger.warning(f"⚠️  触发限流，等待{wait_time}秒后重试")
                await asyncio.sleep(wait_time)
            except Exception as e:
                if i == self.max_retries - 1:
                    logger.error(f"❌ LLM调用最终失败: {e}")
                    raise e
                wait_time = 1 * (i+1)
                logger.warning(f"⚠️  调用失败，等待{wait_time}秒后重试，错误: {e}")
                await asyncio.sleep(wait_time)

    async def parallel_coordinate_async(self, chapter_num: int, target_words: int, fixed_memory: str, dynamic_memory: str, custom_prompt: str):
        logger.info(f"⚡ 启动多智能体并行网络 | XML边界模式 | 章节: {chapter_num}")
        
        outline_prompt = f"<context>\n<static_worldview>\n{fixed_memory}\n</static_worldview>\n<recent_events>\n{dynamic_memory}\n</recent_events>\n</context>\n<user_request>\n{custom_prompt}\n</user_request>\n请基于<context>，为第{chapter_num}章生成剧情大纲。"
        review_prompt = f"<context>\n<static_worldview>\n{fixed_memory}\n</static_worldview>\n<recent_events>\n{dynamic_memory}\n</recent_events>\n</context>\n请分析<context>，列出第{chapter_num}章绝不能踩的人设崩塌、剧情矛盾毒点预警。"

        # 并行执行大纲和审查生成
        tasks = [
            self.call_llm_async(outline_prompt, "你是网文界白金大纲师，擅长设计节奏紧凑、爽点密集的章节结构。"),
            self.call_llm_async(review_prompt, "你是网文界金牌主编，专门排查人设崩塌、前后矛盾、逻辑漏洞的问题。")
        ]
        outline, review = await asyncio.gather(*tasks)
        
        final_prompt = f"<world_rules>\n{fixed_memory}\n</world_rules>\n<previous_chapters>\n{dynamic_memory}\n</previous_chapters>\n<chapter_outline>\n{outline}\n</chapter_outline>\n<strict_warnings>\n{review}\n</strict_warnings>\n请严格按照<chapter_outline>撰写正文，绝对避开<strict_warnings>中的毒点。字数逼近{target_words}字。只输出正文，不要标题、注释等额外内容。"
        
        final_content = await self.call_llm_async(final_prompt, "你是网文白金主笔，擅长写节奏紧凑、爽点密集、人物立体的爆款网文，严格遵守XML边界创作。")
        return {"outline": outline, "review": review, "content": final_content, "real_chars": len(final_content)}

    # 【修复点3】正确的同步-异步桥接，绝对不能用asyncio.run()
    def call_llm_sync(self, user_prompt: str, system_prompt: str = "你是专业助手") -> str:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.call_llm_async(user_prompt, system_prompt))

    def parallel_coordinate(self, chapter_num: int, target_words: int, fixed_memory: str, dynamic_memory: str, custom_prompt: str):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.parallel_coordinate_async(chapter_num, target_words, fixed_memory, dynamic_memory, custom_prompt))

def get_engine():
    return AsyncQueryEngine()
