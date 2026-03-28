"""
AI 服务 - 基于统一 LLM 接口
v0.5.0
"""
from typing import Optional, List, Dict, Any
import json

from core.llm import get_llm_service, LLMService


class AIService:
    """
    AI 对话服务
    使用统一的 LLM 接口，支持 MiniMax/OpenAI/本地模型
    """

    def __init__(self):
        self._llm = get_llm_service()

    @property
    def llm_info(self) -> Dict[str, Any]:
        """获取 LLM 信息"""
        return self._llm.get_model_info()

    def generate_answer(
        self,
        query: str,
        context: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        生成回答

        Args:
            query: 用户问题
            context: 参考上下文/文档内容
            system_prompt: 自定义系统提示

        Returns:
            AI 生成的回答
        """
        return self._llm.generate(
            prompt=query,
            context=context,
            system_prompt=system_prompt
        )

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """
        对话接口

        Args:
            messages: 消息列表
                [
                    {"role": "system", "content": "你是一个..."},
                    {"role": "user", "content": "你好"},
                    ...
                ]

        Returns:
            AI 回复
        """
        return self._llm.chat(messages)

    def generate_with_context(
        self,
        query: str,
        contexts: List[str],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        基于多个上下文片段生成回答

        Args:
            query: 用户问题
            contexts: 上下文片段列表
            system_prompt: 自定义系统提示

        Returns:
            AI 生成的回答
        """
        # 合并上下文
        combined_context = "\n\n".join([f"[文档{i+1}]\n{c}" for i, c in enumerate(contexts)])

        return self.generate_answer(query, combined_context, system_prompt)

    def extract_key_info(
        self,
        text: str,
        extraction_type: str = "entities"
    ) -> Dict[str, Any]:
        """
        从文本中提取关键信息

        Args:
            text: 输入文本
            extraction_type: 提取类型 (entities/keywords/summary)

        Returns:
            提取结果
        """
        prompts = {
            "entities": f"""从以下文本中提取命名实体（人物、地点、组织、设备等）：

{text}

请以 JSON 格式输出：
{{"entities": ["实体1", "实体2", ...]}}""",

            "keywords": f"""从以下文本中提取关键词（5-10个）：

{text}

请以 JSON 格式输出：
{{"keywords": ["关键词1", "关键词2", ...]}}""",

            "summary": f"""简要总结以下文本的核心内容（100字以内）：

{text}

请输出总结："""
        }

        prompt = prompts.get(extraction_type, prompts["summary"])
        result = self._llm.generate(prompt)

        # 尝试解析 JSON
        if extraction_type in ["entities", "keywords"]:
            try:
                # 提取 JSON 部分
                if "{" in result and "}" in result:
                    json_str = result[result.index("{"):result.rindex("}")+1]
                    return json.loads(json_str)
            except:
                pass

        return {"result": result}

    def compare_documents(
        self,
        doc1: str,
        doc2: str,
        criteria: Optional[List[str]] = None
    ) -> str:
        """
        对比两份文档

        Args:
            doc1: 文档1
            doc2: 文档2
            criteria: 对比维度

        Returns:
            对比结果
        """
        criteria_text = "\n".join([f"- {c}" for c in criteria]) if criteria else "内容完整性、准确性、实用性"

        prompt = f"""对比以下两份文档，给出分析：

文档1：
{doc1}

文档2：
{doc2}

对比维度：
{criteria_text}

请给出详细的对比分析结果。"""

        return self._llm.generate(prompt)

    def suggest_related_questions(
        self,
        current_question: str,
        context: Optional[str] = None
    ) -> List[str]:
        """
        基于当前问题推荐相关问题

        Args:
            current_question: 当前问题
            context: 上下文

        Returns:
            推荐问题列表
        """
        prompt = f"""基于这个问题，推荐5个相关的问题（用户可能会接着问的）：

当前问题：{current_question}

请以 JSON 格式输出：
{{"related_questions": ["问题1", "问题2", "问题3", "问题4", "问题5"]}}"""

        result = self._llm.generate(prompt, context=context)

        try:
            if "{" in result and "}" in result:
                json_str = result[result.index("{"):result.rindex("}")+1]
                data = json.loads(json_str)
                return data.get("related_questions", [])
        except:
            pass

        return []


# ============== 便捷函数 ==============

# 全局单例
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """获取 AI 服务实例"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
