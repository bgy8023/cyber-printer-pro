import os
import time
from dotenv import load_dotenv
from .logger import logger

load_dotenv()

class SyncQueryEngine:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
        self.model_name = os.getenv("LLM_MODEL_NAME", "deepseek-chat")
        self.max_retries = int(os.getenv("MAX_RETRY", "3"))

    def call_llm_sync(self, user_prompt: str, system_prompt: str = "你是专业助手") -> str:
        # 使用同步客户端，彻底避免异步上下文问题
        import openai
        client = openai.OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        for i in range(self.max_retries):
            try:
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    top_p=0.9
                )
                return response.choices[0].message.content.strip()
            except openai.RateLimitError:
                wait_time = 2 ** i
                logger.warning(f"⚠️  触发限流，等待{wait_time}秒后重试")
                time.sleep(wait_time)
            except Exception as e:
                if i == self.max_retries - 1:
                    logger.error(f"❌ LLM调用最终失败: {e}")
                    raise e
                wait_time = 1 * (i+1)
                logger.warning(f"⚠️  调用失败，等待{wait_time}秒后重试，错误: {e}")
                time.sleep(wait_time)

    def parallel_coordinate(self, chapter_num: int, target_words: int, fixed_memory: str, dynamic_memory: str, custom_prompt: str):
        logger.info(f"⚡ 启动多智能体并行网络 | XML边界模式 | 章节: {chapter_num}")
        
        outline_prompt = f"<context>\n<static_worldview>\n{fixed_memory}\n</static_worldview>\n<recent_events>\n{dynamic_memory}\n</recent_events>\n</context>\n<user_request>\n{custom_prompt}\n</user_request>\n请基于<context>，为第{chapter_num}章生成剧情大纲。"
        review_prompt = f"<context>\n<static_worldview>\n{fixed_memory}\n</static_worldview>\n<recent_events>\n{dynamic_memory}\n</recent_events>\n</context>\n请分析<context>，列出第{chapter_num}章绝不能踩的人设崩塌、剧情矛盾毒点预警。"

        # 同步执行（虽然慢一点，但 100% 稳定）
        outline = self.call_llm_sync(outline_prompt, "你是网文界白金大纲师，擅长设计节奏紧凑、爽点密集的章节结构。")
        review = self.call_llm_sync(review_prompt, "你是网文界金牌主编，专门排查人设崩塌、前后矛盾、逻辑漏洞的问题。")
        
        final_prompt = f"<world_rules>\n{fixed_memory}\n</world_rules>\n<previous_chapters>\n{dynamic_memory}\n</previous_chapters>\n<chapter_outline>\n{outline}\n</chapter_outline>\n<strict_warnings>\n{review}\n</strict_warnings>\n请严格按照<chapter_outline>撰写正文，绝对避开<strict_warnings>中的毒点。字数逼近{target_words}字。只输出正文，不要标题、注释等额外内容。"
        
        final_content = self.call_llm_sync(final_prompt, "你是网文白金主笔，擅长写节奏紧凑、爽点密集、人物立体的爆款网文，严格遵守XML边界创作。")
        return {"outline": outline, "review": review, "content": final_content, "real_chars": len(final_content)}

    # 保留异步方法，但内部调用同步方法
    async def call_llm_async(self, user_prompt: str, system_prompt: str) -> str:
        return self.call_llm_sync(user_prompt, system_prompt)

    async def parallel_coordinate_async(self, chapter_num: int, target_words: int, fixed_memory: str, dynamic_memory: str, custom_prompt: str):
        return self.parallel_coordinate(chapter_num, target_words, fixed_memory, dynamic_memory, custom_prompt)

def get_engine():
    return SyncQueryEngine()
