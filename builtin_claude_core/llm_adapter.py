# llm_adapter.py - 统一 LLM 适配器
# 支持多种后端：OpenAI、Anthropic Claude、本地模型等
import os
import json
import time
import asyncio
from typing import Dict, Any, Optional, Iterator
from abc import ABC, abstractmethod
from .logger import logger


class BaseLLMProvider(ABC):
    """LLM 提供者抽象基类"""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        pass
    
    @abstractmethod
    def generate_stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """流式生成文本"""
        pass
    
    @abstractmethod
    async def async_generate(self, prompt: str, **kwargs) -> str:
        """异步生成文本"""
        pass
    
    @abstractmethod
    async def async_generate_stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """异步流式生成文本"""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API 提供者"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None, model: str = "gpt-4"):
        self.api_key = api_key
        self.base_url = base_url or "https://api.openai.com/v1"
        self.model = model
        self._client = None
        
    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            except ImportError:
                logger.error("❌ 未安装 openai 包，请运行: pip install openai")
                raise
        return self._client
    
    def generate(self, prompt: str, **kwargs) -> str:
        client = self._get_client()
        max_retries = kwargs.get('max_retries', 3)
        
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=kwargs.get('temperature', 0.7),
                    max_tokens=kwargs.get('max_tokens', 4000),
                    timeout=kwargs.get('timeout', 120)
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"⚠️ OpenAI API 调用失败 (尝试 {attempt+1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise
        
        return ""
    
    def generate_stream(self, prompt: str, **kwargs) -> Iterator[str]:
        client = self._get_client()
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 4000),
                stream=True
            )
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"❌ OpenAI 流式生成失败: {str(e)}")
            raise
    
    async def async_generate(self, prompt: str, **kwargs) -> str:
        client = self._get_client()
        max_retries = kwargs.get('max_retries', 3)
        
        for attempt in range(max_retries):
            try:
                response = await asyncio.to_thread(
                    client.chat.completions.create,
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=kwargs.get('temperature', 0.7),
                    max_tokens=kwargs.get('max_tokens', 4000),
                    timeout=kwargs.get('timeout', 120)
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"⚠️ OpenAI 异步调用失败 (尝试 {attempt+1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise
        
        return ""
    
    async def async_generate_stream(self, prompt: str, **kwargs) -> Iterator[str]:
        client = self._get_client()
        try:
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 4000),
                stream=True
            )
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"❌ OpenAI 异步流式生成失败: {str(e)}")
            raise


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API 提供者"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None, model: str = "claude-3-sonnet-20240229"):
        self.api_key = api_key
        self.base_url = base_url or "https://api.anthropic.com"
        self.model = model
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            try:
                from anthropic import Anthropic
                self._client = Anthropic(api_key=self.api_key, base_url=self.base_url)
            except ImportError:
                logger.error("❌ 未安装 anthropic 包，请运行: pip install anthropic")
                raise
        return self._client
    
    def generate(self, prompt: str, **kwargs) -> str:
        client = self._get_client()
        max_retries = kwargs.get('max_retries', 3)
        
        for attempt in range(max_retries):
            try:
                response = client.messages.create(
                    model=self.model,
                    max_tokens=kwargs.get('max_tokens', 4000),
                    temperature=kwargs.get('temperature', 0.7),
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            except Exception as e:
                logger.warning(f"⚠️ Claude API 调用失败 (尝试 {attempt+1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise
        
        return ""
    
    def generate_stream(self, prompt: str, **kwargs) -> Iterator[str]:
        client = self._get_client()
        try:
            with client.messages.stream(
                model=self.model,
                max_tokens=kwargs.get('max_tokens', 4000),
                temperature=kwargs.get('temperature', 0.7),
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for text in stream.text_stream:
                    yield text
        except Exception as e:
            logger.error(f"❌ Claude 流式生成失败: {str(e)}")
            raise
    
    async def async_generate(self, prompt: str, **kwargs) -> str:
        client = self._get_client()
        max_retries = kwargs.get('max_retries', 3)
        
        for attempt in range(max_retries):
            try:
                response = await asyncio.to_thread(
                    client.messages.create,
                    model=self.model,
                    max_tokens=kwargs.get('max_tokens', 4000),
                    temperature=kwargs.get('temperature', 0.7),
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            except Exception as e:
                logger.warning(f"⚠️ Claude 异步调用失败 (尝试 {attempt+1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise
        
        return ""
    
    async def async_generate_stream(self, prompt: str, **kwargs) -> Iterator[str]:
        client = self._get_client()
        try:
            with client.messages.stream(
                model=self.model,
                max_tokens=kwargs.get('max_tokens', 4000),
                temperature=kwargs.get('temperature', 0.7),
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for text in stream.text_stream:
                    yield text
        except Exception as e:
            logger.error(f"❌ Claude 异步流式生成失败: {str(e)}")
            raise


class OllamaProvider(BaseLLMProvider):
    """本地 Ollama 模型提供者"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2"):
        self.base_url = base_url
        self.model = model
    
    def generate(self, prompt: str, **kwargs) -> str:
        import requests
        max_retries = kwargs.get('max_retries', 3)
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": kwargs.get('temperature', 0.7),
                            "num_predict": kwargs.get('max_tokens', 4000)
                        }
                    },
                    timeout=kwargs.get('timeout', 300)
                )
                response.raise_for_status()
                return response.json().get("response", "")
            except Exception as e:
                logger.warning(f"⚠️ Ollama 调用失败 (尝试 {attempt+1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise
        
        return ""
    
    def generate_stream(self, prompt: str, **kwargs) -> Iterator[str]:
        import requests
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": True,
                    "options": {
                        "temperature": kwargs.get('temperature', 0.7),
                        "num_predict": kwargs.get('max_tokens', 4000)
                    }
                },
                stream=True,
                timeout=kwargs.get('timeout', 300)
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if "response" in data:
                        yield data["response"]
        except Exception as e:
            logger.error(f"❌ Ollama 流式生成失败: {str(e)}")
            raise
    
    async def async_generate(self, prompt: str, **kwargs) -> str:
        import aiohttp
        max_retries = kwargs.get('max_retries', 3)
        
        for attempt in range(max_retries):
            try:
                timeout = aiohttp.ClientTimeout(total=kwargs.get('timeout', 300))
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(
                        f"{self.base_url}/api/generate",
                        json={
                            "model": self.model,
                            "prompt": prompt,
                            "stream": False,
                            "options": {
                                "temperature": kwargs.get('temperature', 0.7),
                                "num_predict": kwargs.get('max_tokens', 4000)
                            }
                        }
                    ) as response:
                        response.raise_for_status()
                        data = await response.json()
                        return data.get("response", "")
            except Exception as e:
                logger.warning(f"⚠️ Ollama 异步调用失败 (尝试 {attempt+1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise
        
        return ""
    
    async def async_generate_stream(self, prompt: str, **kwargs) -> Iterator[str]:
        import aiohttp
        try:
            timeout = aiohttp.ClientTimeout(total=kwargs.get('timeout', 300))
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": True,
                        "options": {
                            "temperature": kwargs.get('temperature', 0.7),
                            "num_predict": kwargs.get('max_tokens', 4000)
                        }
                    }
                ) as response:
                    response.raise_for_status()
                    async for line in response.content:
                        if line:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
        except Exception as e:
            logger.error(f"❌ Ollama 异步流式生成失败: {str(e)}")
            raise


class LLMAdapter:
    """
    统一 LLM 适配器
    根据配置自动选择合适的 LLM 提供者
    
    环境变量配置优先级（从高到低）：
    - API_BASE_URL > LLM_BASE_URL > 提供者特定的 BASE_URL > 默认值
    - LLM_API_KEY > 提供者特定的 API_KEY
    - LLM_MODEL_NAME > 提供者特定的 MODEL
    
    支持通过 .env 配置切换中转池：
    - 设置 API_BASE_URL 为你的中转池地址即可
    - 例如：API_BASE_URL=https://api.你的中转池.com/v1
    """
    
    PROVIDERS = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "ollama": OllamaProvider,
    }
    
    def __init__(self, provider_type: Optional[str] = None, **kwargs):
        """
        初始化 LLM 适配器
        
        Args:
            provider_type: 提供者类型 (openai/anthropic/ollama)，None 则从环境变量读取
            **kwargs: 传递给提供者的参数
        """
        if provider_type is None:
            provider_type = os.getenv("LLM_PROVIDER", "openai").lower()
        
        self.provider_type = provider_type
        self.provider = self._create_provider(provider_type, **kwargs)
        logger.info(f"✅ LLM 适配器初始化完成，使用提供者: {provider_type}")
    
    def _create_provider(self, provider_type: str, **kwargs) -> BaseLLMProvider:
        """创建 LLM 提供者实例"""
        if provider_type not in self.PROVIDERS:
            raise ValueError(f"不支持的 LLM 提供者: {provider_type}，支持的类型: {list(self.PROVIDERS.keys())}")
        
        provider_class = self.PROVIDERS[provider_type]
        
        # 根据提供者类型自动读取环境变量
        if provider_type == "openai":
            # 按优先级获取 API key: kwargs > LLM_API_KEY > OPENAI_API_KEY
            api_key = kwargs.get("api_key") or os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("使用 OpenAI 需要提供 api_key 或设置 LLM_API_KEY/OPENAI_API_KEY 环境变量")
            # 按优先级获取 base_url: kwargs > API_BASE_URL > LLM_BASE_URL > OPENAI_BASE_URL > 默认值
            base_url = kwargs.get("base_url") or os.getenv("API_BASE_URL") or os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL")
            # 按优先级获取 model: kwargs > LLM_MODEL_NAME > OPENAI_MODEL
            model = kwargs.get("model") or os.getenv("LLM_MODEL_NAME") or os.getenv("OPENAI_MODEL", "gpt-4")
            return OpenAIProvider(
                api_key=api_key,
                base_url=base_url,
                model=model
            )
        
        elif provider_type == "anthropic":
            # 按优先级获取 API key: kwargs > LLM_API_KEY > ANTHROPIC_API_KEY
            api_key = kwargs.get("api_key") or os.getenv("LLM_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("使用 Anthropic 需要提供 api_key 或设置 LLM_API_KEY/ANTHROPIC_API_KEY 环境变量")
            # 按优先级获取 base_url: kwargs > API_BASE_URL > LLM_BASE_URL > ANTHROPIC_BASE_URL > 默认值
            base_url = kwargs.get("base_url") or os.getenv("API_BASE_URL") or os.getenv("LLM_BASE_URL") or os.getenv("ANTHROPIC_BASE_URL")
            # 按优先级获取 model: kwargs > LLM_MODEL_NAME > ANTHROPIC_MODEL
            model = kwargs.get("model") or os.getenv("LLM_MODEL_NAME") or os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
            return AnthropicProvider(
                api_key=api_key,
                base_url=base_url,
                model=model
            )
        
        elif provider_type == "ollama":
            # 按优先级获取 base_url: kwargs > API_BASE_URL > LLM_BASE_URL > OLLAMA_BASE_URL > 默认值
            base_url = kwargs.get("base_url") or os.getenv("API_BASE_URL") or os.getenv("LLM_BASE_URL") or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            # 按优先级获取 model: kwargs > LLM_MODEL_NAME > OLLAMA_MODEL
            model = kwargs.get("model") or os.getenv("LLM_MODEL_NAME") or os.getenv("OLLAMA_MODEL", "llama2")
            return OllamaProvider(
                base_url=base_url,
                model=model
            )
        
        else:
            raise ValueError(f"未实现的提供者类型: {provider_type}")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        生成文本
        
        Args:
            prompt: 提示词
            **kwargs: 生成参数 (temperature, max_tokens, timeout, max_retries)
        
        Returns:
            生成的文本
        """
        return self.provider.generate(prompt, **kwargs)
    
    def generate_stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """
        流式生成文本
        
        Args:
            prompt: 提示词
            **kwargs: 生成参数
        
        Yields:
            生成的文本片段
        """
        yield from self.provider.generate_stream(prompt, **kwargs)
    
    async def async_generate(self, prompt: str, **kwargs) -> str:
        """
        异步生成文本
        
        Args:
            prompt: 提示词
            **kwargs: 生成参数 (temperature, max_tokens, timeout, max_retries)
        
        Returns:
            生成的文本
        """
        return await self.provider.async_generate(prompt, **kwargs)
    
    async def async_generate_stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """
        异步流式生成文本
        
        Args:
            prompt: 提示词
            **kwargs: 生成参数
        
        Yields:
            生成的文本片段
        """
        async for chunk in self.provider.async_generate_stream(prompt, **kwargs):
            yield chunk
    
    def switch_provider(self, provider_type: str, **kwargs):
        """切换 LLM 提供者"""
        logger.info(f"🔄 切换 LLM 提供者: {self.provider_type} -> {provider_type}")
        self.provider_type = provider_type
        self.provider = self._create_provider(provider_type, **kwargs)


# 全局单例
_llm_adapter: Optional[LLMAdapter] = None


def get_llm_adapter(provider_type: Optional[str] = None, **kwargs) -> LLMAdapter:
    """获取全局 LLM 适配器实例"""
    global _llm_adapter
    if _llm_adapter is None:
        _llm_adapter = LLMAdapter(provider_type=provider_type, **kwargs)
    return _llm_adapter


def reset_llm_adapter():
    """重置全局适配器（用于测试或切换配置）"""
    global _llm_adapter
    _llm_adapter = None
    logger.info("🔄 LLM 适配器已重置")
