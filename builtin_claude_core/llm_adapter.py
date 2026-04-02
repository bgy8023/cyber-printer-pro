# llm_adapter.py - 统一 LLM 适配器
# 支持多种后端：OpenAI、Anthropic Claude、本地模型等
import os
import json
import time
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


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API 提供者"""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        self.api_key = api_key
        self.model = model
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            try:
                from anthropic import Anthropic
                self._client = Anthropic(api_key=self.api_key)
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


class LLMAdapter:
    """
    统一 LLM 适配器
    根据配置自动选择合适的 LLM 提供者
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
            api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("使用 OpenAI 需要提供 api_key 或设置 OPENAI_API_KEY 环境变量")
            return OpenAIProvider(
                api_key=api_key,
                base_url=kwargs.get("base_url") or os.getenv("OPENAI_BASE_URL"),
                model=kwargs.get("model") or os.getenv("LLM_MODEL_NAME") or os.getenv("OPENAI_MODEL", "gpt-4")
            )
        
        elif provider_type == "anthropic":
            api_key = kwargs.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("使用 Anthropic 需要提供 api_key 或设置 ANTHROPIC_API_KEY 环境变量")
            return AnthropicProvider(
                api_key=api_key,
                model=kwargs.get("model") or os.getenv("LLM_MODEL_NAME") or os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
            )
        
        elif provider_type == "ollama":
            return OllamaProvider(
                base_url=kwargs.get("base_url") or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                model=kwargs.get("model") or os.getenv("LLM_MODEL_NAME") or os.getenv("OLLAMA_MODEL", "llama2")
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
