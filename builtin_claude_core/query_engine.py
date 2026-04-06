import os
import streamlit as st
from dotenv import load_dotenv
from litellm import completion, RateLimitError
from .logger import logger
import time

load_dotenv()

class AsyncQueryEngine:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        self.model_name = os.getenv("LLM_MODEL_NAME", "gpt-4o")
        self.max_retries = int(os.getenv("MAX_RETRY", "3"))

    def call_llm_sync(self, user_prompt: str, system_prompt: str) -> str:
        for i in range(self.max_retries):
            try:
                response = completion(
                    model=self.model_name,
                    messages=[{"role": "system", "content": system_prompt},
                              {"role": "user", "content": user_prompt}],
                    api_key=self.api_key,
                    base_url=self.base_url,
                    temperature=0.7
                )
                return response.choices[0].message.content.strip()
            except RateLimitError:
                time.sleep(2 ** i)
            except Exception as e:
                if i == self.max_retries - 1:
                    raise e
                time.sleep(1)

    def parallel_coordinate(self, chapter_num: int, target_words: int, fixed_memory: str, dynamic_memory: str, custom_prompt: str):
        logger.info(f"⚡ 启动单智能体生成 | 章节: {chapter_num}")
        
        outline_prompt = f"<context>\n<static_worldview>\n{fixed_memory}\n</static_worldview>\n<recent_events>\n{dynamic_memory}\n</recent_events>\n</context>\n<user_request>\n{custom_prompt}\n</user_request>\n请基于<context>，为第{chapter_num}章生成剧情大纲。"
        review_prompt = f"<context>\n<static_worldview>\n{fixed_memory}\n</static_worldview>\n<recent_events>\n{dynamic_memory}\n</recent_events>\n</context>\n请分析<context>，列出第{chapter_num}章绝不能踩的人设崩塌、剧情矛盾毒点预警。"

        outline = self.call_llm_sync(outline_prompt, "你是网文界白金大纲师，擅长设计节奏紧凑、爽点密集的章节结构。")
        review = self.call_llm_sync(review_prompt, "你是网文界金牌主编，专门排查人设崩塌、前后矛盾、逻辑漏洞的问题。")
        
        final_prompt = f"<world_rules>\n{fixed_memory}\n</world_rules>\n<previous_chapters>\n{dynamic_memory}\n</previous_chapters>\n<chapter_outline>\n{outline}\n</chapter_outline>\n<strict_warnings>\n{review}\n</strict_warnings>\n请严格按照<chapter_outline>撰写正文，绝对避开<strict_warnings>中的毒点。字数逼近{target_words}字。只输出正文，不要标题、注释等额外内容。"
        
        final_content = self.call_llm_sync(final_prompt, "你是网文白金主笔，擅长写节奏紧凑、爽点密集、人物立体的爆款网文，严格遵守XML边界创作。")
        return {"outline": outline, "review": review, "content": final_content, "real_chars": len(final_content)}

@st.cache_resource
def get_engine():
    return AsyncQueryEngine()
