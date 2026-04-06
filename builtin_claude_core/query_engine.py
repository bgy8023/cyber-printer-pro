import os
import asyncio
import nest_asyncio
import streamlit as st
from dotenv import load_dotenv
from litellm import acompletion, RateLimitError
from .logger import logger

# 开启事件循环嵌套，彻底解决 Streamlit 容器冲突
nest_asyncio.apply()
load_dotenv()

class AsyncQueryEngine:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        self.model_name = os.getenv("LLM_MODEL_NAME", "gpt-4o")
        self.max_retries = int(os.getenv("MAX_RETRY", "3"))
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "15000"))
        self.timeout = int(os.getenv("LLM_TIMEOUT", "300"))

    async def call_llm_async(self, user_prompt: str, system_prompt: str) -> str:
        for i in range(self.max_retries):
            try:
                response = await acompletion(
                    model=self.model_name,
                    messages=[{"role": "system", "content": system_prompt},
                              {"role": "user", "content": user_prompt}],
                    api_key=self.api_key,
                    base_url=self.base_url,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                return response.choices[0].message.content.strip()
            except RateLimitError:
                await asyncio.sleep(2 ** i)
            except Exception as e:
                if i == self.max_retries - 1: raise e
                await asyncio.sleep(1)

    async def parallel_coordinate_async(self, chapter_num: int, target_words: int, fixed_memory: str, dynamic_memory: str, custom_prompt: str):
        logger.info(f"⚡ 启动多智能体并行网络 | XML 边界模式 | 章节: {chapter_num}")
        
        # 并行阶段：大纲与排雷
        outline_prompt = f"<context>\n<static_worldview>\n{fixed_memory}\n</static_worldview>\n<recent_events>\n{dynamic_memory}\n</recent_events>\n</context>\n<user_request>\n{custom_prompt}\n</user_request>\n请基于 <context>，为第 {chapter_num} 章生成剧情大纲。"
        review_prompt = f"<context>\n<static_worldview>\n{fixed_memory}\n</static_worldview>\n<recent_events>\n{dynamic_memory}\n</recent_events>\n</context>\n请分析 <context>，列出第 {chapter_num} 章绝不能踩的毒点预警。"

        tasks = [
            self.call_llm_async(outline_prompt, "你是顶尖网文大纲师。"),
            self.call_llm_async(review_prompt, "你是网文金牌主编。")
        ]
        outline, review = await asyncio.gather(*tasks)
        
        # 终极融合阶段
        final_prompt = f"<world_rules>\n{fixed_memory}\n</world_rules>\n<previous_chapters>\n{dynamic_memory}\n</previous_chapters>\n<chapter_outline>\n{outline}\n</chapter_outline>\n<strict_warnings>\n{review}\n</strict_warnings>\n请严格按照 <chapter_outline> 撰写正文，绝对避开 <strict_warnings> 中的毒点。字数逼近 {target_words} 字。只输出正文。"
        
        final_content = await self.call_llm_async(final_prompt, "你是网文白金主笔。严格遵守 XML 边界创作。")
        return {"outline": outline, "review": review, "content": final_content, "real_chars": len(final_content)}

    def call_llm_sync(self, user_prompt: str, system_prompt: str = "你是专业助手", stream: bool = False) -> str:
        """
        Google级安全同步包装器，零冲突适配Streamlit容器
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.call_llm_async(user_prompt, system_prompt))

    def parallel_coordinate(self, chapter_num: int, target_words: int, fixed_memory: str, dynamic_memory: str, custom_prompt: str):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.parallel_coordinate_async(chapter_num, target_words, fixed_memory, dynamic_memory, custom_prompt))

@st.cache_resource
def get_engine():
    return AsyncQueryEngine()
