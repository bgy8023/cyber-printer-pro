# builtin_claude_core/query_engine.py
# 工业级异步多模型引擎，基于LiteLLM实现，全会话隔离，非阻塞无死穴
import os
import asyncio
from dotenv import load_dotenv
from litellm import acompletion, RateLimitError, APIConnectionError, APIError
from .logger import logger

# 加载环境变量
load_dotenv()

class AsyncQueryEngine:
    """
    异步推理引擎，每个用户会话独立实例，彻底解决并发阻塞问题
    支持100+大模型，全兼容OpenAI格式，内置企业级重试策略
    """
    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model_name: str = None,
        timeout: int = None,
        temperature: float = None,
        max_retries: int = None
    ):
        # 从环境变量加载默认配置，支持实例级覆盖（会话隔离）
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        self.model_name = model_name or os.getenv("LLM_MODEL_NAME", "gpt-4o")
        self.timeout = timeout or int(os.getenv("LLM_TIMEOUT", "300"))
        self.temperature = temperature or float(os.getenv("LLM_TEMPERATURE", "0.7"))
        self.max_retries = max_retries or int(os.getenv("MAX_RETRY", "3"))

        # 校验配置有效性
        self._validate_config()
        logger.info(f"✅ 异步引擎初始化完成 | 模型：{self.model_name} | 会话ID：{id(self)}")

    def _validate_config(self):
        """配置合法性校验，提前拦截无效配置"""
        if not self.api_key or self.api_key == "你的大模型_API_Key":
            raise ValueError("无效的LLM_API_KEY，请检查环境变量配置")
        if not self.base_url:
            raise ValueError("LLM_BASE_URL不能为空")
        if not self.model_name:
            raise ValueError("LLM_MODEL_NAME不能为空")

    async def call_llm_async(
        self,
        user_prompt: str,
        system_prompt: str = "你是专业的网络小说创作专家，擅长写节奏快、爽点足、代入感强的网文",
        stream: bool = False
    ) -> str:
        """
        异步LLM调用，非阻塞，不会影响其他用户会话
        内置指数退避重试，自动处理限流、超时、网络波动
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        for retry_count in range(self.max_retries):
            try:
                logger.info(f"🚀 异步LLM调用 | 会话ID：{id(self)} | 第{retry_count+1}次尝试")
                response = await acompletion(
                    model=self.model_name,
                    messages=messages,
                    api_key=self.api_key,
                    base_url=self.base_url,
                    temperature=self.temperature,
                    timeout=self.timeout,
                    stream=stream,
                    num_retries=0  # 关闭内置重试，自定义指数退避
                )

                if stream:
                    return response

                content = response.choices[0].message.content.strip()
                if not content:
                    raise Exception("LLM返回内容为空")

                logger.info(f"✅ 异步LLM调用完成 | 会话ID：{id(self)} | 内容长度：{len(content)}")
                return content

            except RateLimitError as e:
                wait_time = 2 ** retry_count
                logger.warning(f"⚠️  触发限流 | 会话ID：{id(self)} | 等待{wait_time}秒后重试：{str(e)}")
                await asyncio.sleep(wait_time)  # 异步sleep，绝不阻塞其他会话

            except APIConnectionError as e:
                wait_time = 2 ** retry_count
                logger.warning(f"⚠️  接口连接失败 | 会话ID：{id(self)} | 等待{wait_time}秒后重试：{str(e)}")
                await asyncio.sleep(wait_time)

            except APIError as e:
                logger.error(f"❌ 接口调用错误 | 会话ID：{id(self)} | 错误：{str(e)}", exc_info=True)
                if retry_count == self.max_retries - 1:
                    raise Exception(f"LLM调用失败：{str(e)}")
                await asyncio.sleep(2 ** retry_count)

            except Exception as e:
                logger.error(f"❌ 未知错误 | 会话ID：{id(self)} | 错误：{str(e)}", exc_info=True)
                if retry_count == self.max_retries - 1:
                    raise Exception(f"LLM调用失败，已达最大重试次数：{str(e)}")
                await asyncio.sleep(2 ** retry_count)

        raise Exception("LLM调用失败，已耗尽所有重试次数")

# ------------------------------
# Streamlit 会话级隔离工厂函数
# ------------------------------
import streamlit as st

@st.cache_resource(ttl=3600, show_spinner="正在初始化创作引擎...")
def get_session_engine(
    session_id: str,
    api_key: str = None,
    base_url: str = None,
    model_name: str = None
) -> AsyncQueryEngine:
    """
    Streamlit 会话级引擎实例，每个用户独立实例，完全隔离
    ttl=3600：1小时无操作自动销毁，释放资源
    """
    return AsyncQueryEngine(
        api_key=api_key,
        base_url=base_url,
        model_name=model_name
    )
