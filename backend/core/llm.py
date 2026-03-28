"""
统一 LLM 接口
v0.5.0
支持 Qwen, MiniMax, OpenAI, OpenRouter, 本地模型
"""
import os
import json
import requests
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

from core.llm_config import llm_config_manager, LLMConfig

load_dotenv()


class LLMError(Exception):
    """LLM 调用异常"""
    pass


class LLMService:
    """
    统一 LLM 服务
    支持多种 Provider: Qwen, MiniMax, OpenAI, OpenRouter, 本地模型
    """

    def __init__(self):
        self.config = llm_config_manager.config
        self._session = requests.Session()
        self._init_client()

    def _init_client(self):
        """初始化客户端"""
        if not self.config.api_key and self.config.provider != "local":
            print(f"⚠️ {self.config.provider} API Key 未配置，将使用模拟模式")
            return

        self._session.headers.update({
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        })

    @property
    def is_available(self) -> bool:
        """检查 LLM 是否可用"""
        return bool(self.config.api_key)

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        生成回答

        Args:
            prompt: 用户输入
            system_prompt: 系统提示（可选）
            context: 上下文/参考资料
            **kwargs: 其他参数（temperature, max_tokens 等）

        Returns:
            生成的文本
        """
        if not self.is_available:
            return self._generate_fallback(prompt, context)

        # 构建消息
        messages = self._build_messages(prompt, system_prompt, context)

        try:
            # 根据 provider 调用不同的 API
            if self.config.provider == "qwen":
                return self._generate_qwen(messages, **kwargs)
            else:
                return self._generate_openai(messages, **kwargs)
        except Exception as e:
            print(f"LLM 调用失败: {e}")
            return self._generate_fallback(prompt, context)

    def _generate_openai(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """使用 OpenAI 兼容 API"""
        url = f"{self.config.base_url}/chat/completions"
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
        }

        response = self._session.post(url, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()

        return data["choices"][0]["message"]["content"]

    def _generate_qwen(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """使用 Qwen/阿里云 API"""
        url = f"{self.config.base_url}/services/aigc/text-generation/generation"
        payload = {
            "model": self.config.model,
            "input": {"messages": messages},
            "parameters": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "result_format": "message",
            }
        }

        response = self._session.post(url, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()

        # 解析 Qwen 返回格式: {"output": {"choices": [{"message": {"content": "..."}}]}}
        return data["output"]["choices"][0]["message"]["content"]

    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """将消息列表转换为纯文本"""
        result = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                result.append(f"系统: {content}")
            elif role == "user":
                result.append(f"用户: {content}")
            elif role == "assistant":
                result.append(f"助手: {content}")
        return "\n\n".join(result)

    def _build_messages(
        self,
        prompt: str,
        system_prompt: Optional[str],
        context: Optional[str]
    ) -> List[Dict[str, str]]:
        """构建消息列表"""
        messages = []

        # 系统消息
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        elif self.config.system_prompt:
            messages.append({"role": "system", "content": self.config.system_prompt})

        # 上下文（如果有）
        if context:
            context_prompt = f"""基于以下参考文档回答问题：

参考文档：
{context}

请根据参考文档内容给出准确、简洁的回答。如果文档中没有相关信息，请明确说明。"""
            messages.append({"role": "user", "content": context_prompt})

        # 用户问题
        messages.append({"role": "user", "content": prompt})

        return messages

    def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        对话接口（直接传递消息列表）

        Args:
            messages: 消息列表 [{"role": "user/assistant/system", "content": "..."}]
            **kwargs: 其他参数

        Returns:
            生成的文本
        """
        if not self.is_available:
            return "LLM 服务暂不可用，请检查配置。"

        call_kwargs = {
            "model": self.config.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
        }

        try:
            response = self._client.chat.completions.create(**call_kwargs)
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM 调用失败: {e}")
            return f"抱歉，发生了错误: {str(e)}"

    def _generate_fallback(self, prompt: str, context: Optional[str] = None) -> str:
        """降级模式（无可用 API 时）"""
        if context:
            # 基于上下文的简单回复
            sentences = context.split('。')
            relevant = [s.strip() for s in sentences[:5] if s.strip()]

            if relevant:
                answer = "根据知识库资料：\n\n"
                for i, sent in enumerate(relevant, 1):
                    answer += f"{i}. {sent}。\n\n"
                answer += f"\n（当前使用本地模式，如需更智能的回答请配置 {self.config.provider} API）"
                return answer

        return "抱歉，知识库中暂无相关信息。请尝试上传更多文档或换个问题。"

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "provider": self.config.provider,
            "model": self.config.model,
            "available": self.is_available,
            "base_url": self.config.base_url,
        }


# ============== 便捷函数 ==============

# 全局单例
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """获取 LLM 服务实例"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


def generate_with_llm(prompt: str, context: Optional[str] = None) -> str:
    """快捷函数：使用 LLM 生成回答"""
    return get_llm_service().generate(prompt, context=context)


def chat_with_llm(messages: List[Dict[str, str]]) -> str:
    """快捷函数：使用 LLM 对话"""
    return get_llm_service().chat(messages)
