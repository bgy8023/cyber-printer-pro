import os
import time
import streamlit as st
from dotenv import load_dotenv
from litellm import completion
from .logger import logger

load_dotenv()

class AsyncQueryEngine:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        self.model_name = os.getenv("LLM_MODEL_NAME", "gpt-4o")
        self.max_retries = int(os.getenv("MAX_RETRY", "3"))
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "15000"))

    def call_llm_sync(self, user_prompt: str, system_prompt: str = "你是专业助手") -> str:
        """
        同步调用大模型，彻底避免异步事件循环问题
        """
        for i in range(self.max_retries):
            try:
                response = completion(
                    model=self.model_name,
                    messages=[{"role": "system", "content": system_prompt},
                              {"role": "user", "content": user_prompt}],
                    api_key=self.api_key,
                    base_url=self.base_url,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                if i == self.max_retries - 1:
                    raise e
                logger.warning(f"⚠️ 调用失败，重试 {i+1}/{self.max_retries}：{e}")
                time.sleep(2 ** i)

    def parallel_coordinate(self, chapter_num: int, target_words: int, fixed_memory: str, dynamic_memory: str, custom_prompt: str):
        """
        同步版本的多智能体协调，避免异步问题
        """
        logger.info(f"⚡ 启动多智能体网络 | XML 边界模式 | 章节: {chapter_num}")
        
        # 阶段 1：大纲生成
        outline_prompt = f"<context>\n<static_worldview>\n{fixed_memory}\n</static_worldview>\n<recent_events>\n{dynamic_memory}\n</recent_events>\n</context>\n<user_request>\n{custom_prompt}\n</user_request>\n请基于 <context>，为第 {chapter_num} 章生成剧情大纲。"
        logger.info("🤖 正在生成大纲...")
        outline = self.call_llm_sync(outline_prompt, "你是顶尖网文大纲师。")
        
        # 阶段 2：排雷预警
        review_prompt = f"<context>\n<static_worldview>\n{fixed_memory}\n</static_worldview>\n<recent_events>\n{dynamic_memory}\n</recent_events>\n</context>\n请分析 <context>，列出第 {chapter_num} 章绝不能踩的毒点预警。"
        logger.info("🔍 正在生成排雷预警...")
        review = self.call_llm_sync(review_prompt, "你是网文金牌主编。")
        
        # 阶段 3：终极融合
        final_prompt = f"<world_rules>\n{fixed_memory}\n</world_rules>\n<previous_chapters>\n{dynamic_memory}\n</previous_chapters>\n<chapter_outline>\n{outline}\n</chapter_outline>\n<strict_warnings>\n{review}\n</strict_warnings>\n请严格按照 <chapter_outline> 撰写正文，绝对避开 <strict_warnings> 中的毒点。字数逼近 {target_words} 字。只输出正文。"
        logger.info("✍️ 正在生成正文...")
        final_content = self.call_llm_sync(final_prompt, "你是网文白金主笔。严格遵守 XML 边界创作。")
        
        return {"outline": outline, "review": review, "content": final_content, "real_chars": len(final_content)}

    def call_llm_async(self, user_prompt: str, system_prompt: str) -> str:
        """保留异步接口，向后兼容"""
        return self.call_llm_sync(user_prompt, system_prompt)

    async def parallel_coordinate_async(self, chapter_num: int, target_words: int, fixed_memory: str, dynamic_memory: str, custom_prompt: str):
        """保留异步接口，向后兼容"""
        return self.parallel_coordinate(chapter_num, target_words, fixed_memory, dynamic_memory, custom_prompt)

@st.cache_resource
def get_engine():
    return AsyncQueryEngine()
