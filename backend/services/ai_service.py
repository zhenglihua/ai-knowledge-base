import os
from typing import Optional

# 尝试导入openai，失败则使用纯本地模式
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ openai未安装，使用纯本地AI模式")

class AIService:
    """AI服务 - 支持OpenAI API或本地模拟"""
    
    def __init__(self):
        if not OPENAI_AVAILABLE:
            self.use_openai = False
            return
        
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key:
            openai.api_key = self.api_key
            self.use_openai = True
        else:
            self.use_openai = False
    
    def generate_answer(self, query: str, context: str) -> str:
        """生成回答"""
        if self.use_openai:
            return self._generate_with_openai(query, context)
        else:
            return self._generate_local(query, context)
    
    def _generate_with_openai(self, query: str, context: str) -> str:
        """使用OpenAI API生成回答"""
        try:
            prompt = f"""基于以下参考文档回答问题：

参考文档：
{context}

用户问题：{query}

请根据参考文档内容给出准确、简洁的回答。如果文档中没有相关信息，请明确说明。"""
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个专业的半导体工厂知识库助手，基于提供的参考资料回答用户问题。回答要准确、专业、简洁。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            return self._generate_local(query, context)
    
    def _generate_local(self, query: str, context: str) -> str:
        """本地生成回答（模拟）"""
        # 简单的基于规则的回答生成
        if not context.strip():
            return "抱歉，知识库中暂无相关信息。请尝试上传更多文档或换个问题。"
        
        # 提取关键句子
        sentences = context.split('。')
        relevant = []
        query_keywords = set(query.lower().split())
        
        for sent in sentences[:5]:  # 取前5句
            if sent.strip():
                relevant.append(sent.strip())
        
        if relevant:
            answer = "根据知识库资料：\n\n"
            for i, sent in enumerate(relevant, 1):
                answer += f"{i}. {sent}\n\n"
            answer += "（注：当前使用本地模式，建议使用OpenAI API获取更智能的回答）"
            return answer
        else:
            return "抱歉，未能找到与问题直接相关的信息。"
