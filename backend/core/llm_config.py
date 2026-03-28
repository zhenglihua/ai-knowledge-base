"""
LLM 配置管理
v0.5.0
支持 MiniMax、OpenAI、本地模型统一配置
"""
import os
from typing import Literal, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: str  # 提供商: minimax / openai / local
    model: str  # 模型名称
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.3
    system_prompt: str = "你是一个专业的AI助手，请基于提供的参考资料准确回答用户问题。"


class LLMConfigManager:
    """LLM 配置管理器"""

    # Provider 常量
    PROVIDER_MINIMAX = "minimax"
    PROVIDER_OPENAI = "openai"
    PROVIDER_OPENROUTER = "openrouter"
    PROVIDER_QWEN = "qwen"
    PROVIDER_OLLAMA = "ollama"
    PROVIDER_LOCAL = "local"

    # 支持的模型
    MODELS = {
        # MiniMax
        "minimax": {
            "default": "MiniMax-M2",
            "supported": ["MiniMax-M2", "abab6-chat"],
        },
        # OpenAI
        "openai": {
            "default": "gpt-3.5-turbo",
            "supported": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
        },
        # 本地模型
        "local": {
            "default": "llama3",
            "supported": ["llama3", "llama2", "chatglm3", "qwen2", "mixtral"],
        }
    }

    # API 端点
    BASE_URLS = {
        "minimax": "https://api.minimax.chat/v1",
        "openai": "https://api.openai.com/v1",
        "openrouter": "https://openrouter.ai/api/v1",
        "qwen": "https://dashscope.aliyuncs.com/api/v1",
        "ollama": "http://localhost:11434/v1",
        "local": "http://localhost:11434/v1",  # Ollama 默认
    }

    def __init__(self):
        self._config: Optional[LLMConfig] = None
        self._load_config()

    def _load_config(self):
        """从环境变量加载配置"""
        # 确定 provider
        provider = os.getenv("LLM_PROVIDER", "").lower()

        # 如果没指定，尝试自动检测
        if not provider:
            provider = self._auto_detect_provider()

        # 获取对应的配置
        if provider == self.PROVIDER_MINIMAX:
            self._config = self._get_minimax_config()
        elif provider == self.PROVIDER_OPENAI:
            self._config = self._get_openai_config()
        elif provider == self.PROVIDER_OPENROUTER:
            self._config = self._get_openrouter_config()
        elif provider == self.PROVIDER_QWEN:
            self._config = self._get_qwen_config()
        elif provider == self.PROVIDER_OLLAMA:
            self._config = self._get_ollama_config()
        elif provider == self.PROVIDER_LOCAL:
            self._config = self._get_local_config()
        else:
            # 默认使用 Ollama
            self._config = self._get_ollama_config()

    def _auto_detect_provider(self) -> str:
        """自动检测可用的 Provider"""
        # 优先级: Ollama > Qwen > OpenRouter > MiniMax > OpenAI > 本地
        if os.getenv("OLLAMA_API_KEY") or os.getenv("OLLAMA_HOST"):
            return self.PROVIDER_OLLAMA
        if os.getenv("QWEN_API_KEY"):
            return self.PROVIDER_QWEN
        if os.getenv("OPENROUTER_API_KEY"):
            return self.PROVIDER_OPENROUTER
        if os.getenv("MINIMAX_API_KEY"):
            return self.PROVIDER_MINIMAX
        if os.getenv("OPENAI_API_KEY"):
            return self.PROVIDER_OPENAI
        if os.getenv("LOCAL_MODEL_ENDPOINT"):
            return self.PROVIDER_LOCAL
        return self.PROVIDER_OLLAMA  # 默认

    def _get_minimax_config(self) -> LLMConfig:
        """MiniMax 配置"""
        api_key = os.getenv("MINIMAX_API_KEY", "")
        model = os.getenv("MINIMAX_MODEL", "MiniMax-M2")
        base_url = os.getenv("MINIMAX_API_BASE") or self.BASE_URLS["minimax"]

        return LLMConfig(
            provider=self.PROVIDER_MINIMAX,
            model=model,
            api_key=api_key,
            base_url=base_url,
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1000")),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
            system_prompt=os.getenv("LLM_SYSTEM_PROMPT",
                "你是一个专业的半导体工厂知识库助手，基于提供的参考资料回答用户问题。回答要准确、专业、简洁。")
        )

    def _get_openai_config(self) -> LLMConfig:
        """OpenAI 配置"""
        api_key = os.getenv("OPENAI_API_KEY", "")
        model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

        return LLMConfig(
            provider=self.PROVIDER_OPENAI,
            model=model,
            api_key=api_key,
            base_url=self.BASE_URLS["openai"],
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1000")),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
            system_prompt=os.getenv("LLM_SYSTEM_PROMPT",
                "你是一个专业的AI助手，请基于提供的参考资料准确回答用户问题。")
        )

    def _get_openrouter_config(self) -> LLMConfig:
        """OpenRouter 配置"""
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        base_url = os.getenv("OPENROUTER_API_BASE") or self.BASE_URLS["openrouter"]

        return LLMConfig(
            provider=self.PROVIDER_OPENROUTER,
            model=model,
            api_key=api_key,
            base_url=base_url,
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1000")),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
            system_prompt=os.getenv("LLM_SYSTEM_PROMPT",
                "你是一个专业的AI助手，请基于提供的参考资料准确回答用户问题。")
        )

    def _get_qwen_config(self) -> LLMConfig:
        """通义千问配置"""
        api_key = os.getenv("QWEN_API_KEY", "")
        model = os.getenv("QWEN_MODEL", "qwen-turbo")
        base_url = os.getenv("QWEN_API_BASE") or self.BASE_URLS["qwen"]

        return LLMConfig(
            provider=self.PROVIDER_QWEN,
            model=model,
            api_key=api_key,
            base_url=base_url,
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1000")),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
            system_prompt=os.getenv("LLM_SYSTEM_PROMPT",
                "你是一个专业的半导体工厂知识库助手，基于提供的参考资料回答用户问题。回答要准确、专业、简洁。")
        )

    def _get_ollama_config(self) -> LLMConfig:
        """Ollama 本地模型配置"""
        model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        base_url = os.getenv("OLLAMA_HOST") or self.BASE_URLS["ollama"]

        return LLMConfig(
            provider=self.PROVIDER_OLLAMA,
            model=model,
            api_key="",  # Ollama 不需要 API Key
            base_url=base_url,
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000")),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
            system_prompt=os.getenv("LLM_SYSTEM_PROMPT",
                "你是一个专业的半导体工厂知识库助手，基于提供的参考资料回答用户问题。回答要准确、专业、简洁。")
        )

    def _get_local_config(self) -> LLMConfig:
        """本地模型配置"""
        endpoint = os.getenv("LOCAL_MODEL_ENDPOINT", "http://localhost:11434/v1")
        model = os.getenv("LOCAL_MODEL_NAME", "llama3")

        return LLMConfig(
            provider=self.PROVIDER_LOCAL,
            model=model,
            api_key=os.getenv("LOCAL_MODEL_API_KEY", ""),  # 本地通常不需要
            base_url=endpoint,
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000")),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
            system_prompt=os.getenv("LLM_SYSTEM_PROMPT",
                "你是一个专业的AI助手，请基于提供的参考资料准确回答用户问题。")
        )

    @property
    def config(self) -> LLMConfig:
        """获取当前配置"""
        return self._config

    def get_provider_display_name(self) -> str:
        """获取 Provider 显示名称"""
        names = {
            self.PROVIDER_MINIMAX: "MiniMax",
            self.PROVIDER_OPENAI: "OpenAI",
            self.PROVIDER_OPENROUTER: "OpenRouter",
            self.PROVIDER_QWEN: "通义千问",
            self.PROVIDER_OLLAMA: "Ollama (本地)",
            self.PROVIDER_LOCAL: "本地模型"
        }
        return names.get(self._config.provider, self._config.provider)

    def is_available(self) -> bool:
        """检查 LLM 是否可用"""
        return bool(self._config.api_key) or self._config.provider == self.PROVIDER_LOCAL

    def switch_provider(self, provider: str, **kwargs):
        """切换 Provider"""
        if provider == self.PROVIDER_MINIMAX:
            self._config = self._get_minimax_config()
            if kwargs.get("api_key"):
                self._config.api_key = kwargs["api_key"]
        elif provider == self.PROVIDER_OPENAI:
            self._config = self._get_openai_config()
            if kwargs.get("api_key"):
                self._config.api_key = kwargs["api_key"]
        elif provider == self.PROVIDER_OPENROUTER:
            self._config = self._get_openrouter_config()
            if kwargs.get("api_key"):
                self._config.api_key = kwargs["api_key"]
            if kwargs.get("model"):
                self._config.model = kwargs["model"]
        elif provider == self.PROVIDER_QWEN:
            self._config = self._get_qwen_config()
            if kwargs.get("api_key"):
                self._config.api_key = kwargs["api_key"]
            if kwargs.get("model"):
                self._config.model = kwargs["model"]
        elif provider == self.PROVIDER_OLLAMA:
            self._config = self._get_ollama_config()
            if kwargs.get("endpoint"):
                self._config.base_url = kwargs["endpoint"]
            if kwargs.get("model"):
                self._config.model = kwargs["model"]
        elif provider == self.PROVIDER_LOCAL:
            self._config = self._get_local_config()
            if kwargs.get("endpoint"):
                self._config.base_url = kwargs["endpoint"]
            if kwargs.get("model"):
                self._config.model = kwargs["model"]

    def get_status(self) -> dict:
        """获取 LLM 状态"""
        return {
            "provider": self._config.provider,
            "provider_name": self.get_provider_display_name(),
            "model": self._config.model,
            "available": self.is_available(),
            "base_url": self._config.base_url,
        }


# 全局单例
llm_config_manager = LLMConfigManager()
