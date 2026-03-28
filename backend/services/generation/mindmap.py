"""
思维导图生成服务
v0.7.0
基于文档内容生成可视化的概念关系图
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json


@dataclass
class MindMapNode:
    """思维导图节点"""
    id: str
    text: str
    children: List["MindMapNode"]
    metadata: Dict[str, Any]


@dataclass
class MindMapEdge:
    """思维导图边/关系"""
    source: str
    target: str
    label: str


class MindMapGenerator:
    """
    思维导图生成器
    基于 LLM 从文档内容中提取概念和关系
    """

    def __init__(self, llm_service):
        self.llm = llm_service

    async def generate(
        self,
        document_text: str,
        max_nodes: int = 20,
        topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成思维导图

        Args:
            document_text: 文档内容
            max_nodes: 最大节点数
            topic: 主题（可选）

        Returns:
            {
                "nodes": [{"id": "...", "text": "...", "children": [...]}],
                "edges": [{"source": "...", "target": "...", "label": "..."}],
                "format": "tree" | "graph"
            }
        """
        # 构建提示词
        prompt = self._build_prompt(document_text, max_nodes, topic)

        # 调用 LLM 生成
        response = self.llm.generate(prompt)

        # 解析响应
        return self._parse_response(response)

    def _build_prompt(
        self,
        document_text: str,
        max_nodes: int,
        topic: Optional[str]
    ) -> str:
        """构建提示词"""
        topic_hint = f"聚焦主题: {topic}" if topic else ""

        return f"""你是一个专业的知识梳理助手。请根据以下文档内容，生成一个结构化的思维导图。

{topic_hint}

文档内容:
{document_text[:3000]}

请以 JSON 格式输出思维导图结构:
{{
    "format": "tree",  // 或 "graph"
    "center": "核心主题",
    "nodes": [
        {{
            "id": "node_1",
            "text": "主概念1",
            "level": 0,
            "children": [
                {{"id": "node_1_1", "text": "子概念1.1", "level": 1}},
                {{"id": "node_1_2", "text": "子概念1.2", "level": 1}}
            ]
        }}
    ],
    "edges": [
        {{"source": "node_1", "target": "node_2", "label": "相关"}}
    ]
}}

要求:
1. 节点数量不超过 {max_nodes} 个
2. 概念之间要有逻辑关系
3. 使用有意义的短句作为节点文本
4. 只输出 JSON，不要其他内容"""

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """解析 LLM 响应"""
        try:
            # 提取 JSON
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end]
            elif "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
            else:
                return self._default_structure()

            data = json.loads(json_str)
            return data
        except:
            return self._default_structure()

    def _default_structure(self) -> Dict[str, Any]:
        """默认结构"""
        return {
            "format": "tree",
            "center": "文档主题",
            "nodes": [
                {
                    "id": "root",
                    "text": "文档主题",
                    "level": 0,
                    "children": []
                }
            ],
            "edges": []
        }

    def to_html(self, mindmap_data: Dict[str, Any]) -> str:
        """
        转换为可交互的 HTML 思维导图

        Args:
            mindmap_data: generate() 返回的数据

        Returns:
            HTML 字符串
        """
        nodes_json = json.dumps(mindmap_data.get("nodes", []), ensure_ascii=False)
        edges_json = json.dumps(mindmap_data.get("edges", []), ensure_ascii=False)

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>思维导图</title>
    <script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
    <style>
        body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }}
        svg {{ width: 100vw; height: 100vh; }}
        .node circle {{ fill: #4A90E2; stroke: #fff; stroke-width: 2px; cursor: pointer; }}
        .node text {{ font-size: 12px; fill: #333; }}
        .link {{ stroke: #999; stroke-width: 1.5px; fill: none; }}
    </style>
</head>
<body>
    <svg id="mindmap"></svg>
    <script>
        const nodes = {nodes_json};
        const edges = {edges_json};
        // 简化的力导向图实现
        const svg = d3.select("#mindmap");
        // ... (完整实现见 static/mindmap.html)
    </script>
</body>
</html>"""


# 单例
_mindmap_generator = None


def get_mindmap_generator(llm_service) -> MindMapGenerator:
    """获取思维导图生成器实例"""
    global _mindmap_generator
    if _mindmap_generator is None:
        _mindmap_generator = MindMapGenerator(llm_service)
    return _mindmap_generator
