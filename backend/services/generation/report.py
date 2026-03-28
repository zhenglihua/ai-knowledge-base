"""
专业报告生成服务
v0.7.0
基于模板和文档内容自动生成专业报告
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ReportType(Enum):
    """报告类型枚举"""
    YIELD_ANALYSIS = "yield_analysis"      # 良率分析报告
    FAULT_ANALYSIS = "fault_analysis"      # 故障分析报告(8D)
    EQUIPMENT_EVAL = "equipment_eval"       # 设备评估报告
    CHANGE_IMPACT = "change_impact"        # 变更影响分析
    WEEKLY_SUMMARY = "weekly_summary"        # 周报
    TRAINING_MATERIAL = "training_material"  # 培训材料


@dataclass
class ReportTemplate:
    """报告模板"""
    type: ReportType
    name: str
    description: str
    sections: List[str]  # 章节列表


# 预置报告模板
REPORT_TEMPLATES = {
    ReportType.YIELD_ANALYSIS: ReportTemplate(
        type=ReportType.YIELD_ANALYSIS,
        name="良率分析报告",
        description="周/月度良率异常分析报告",
        sections=[
            "执行摘要",
            "数据概览",
            "良率趋势分析",
            "异常定位",
            "根因假设",
            "建议措施",
            "参考文档"
        ]
    ),
    ReportType.FAULT_ANALYSIS: ReportTemplate(
        type=ReportType.FAULT_ANALYSIS,
        name="故障分析报告(8D)",
        description="设备故障根因分析报告",
        sections=[
            "问题描述",
            "紧急响应措施",
            "根本原因分析",
            "短期措施",
            "长期措施",
            "效果验证",
            "预防措施"
        ]
    ),
    ReportType.EQUIPMENT_EVAL: ReportTemplate(
        type=ReportType.EQUIPMENT_EVAL,
        name="设备评估报告",
        description="设备选型对比评估报告",
        sections=[
            "评估背景",
            "设备规格对比",
            "产能对比",
            "维护成本分析",
            "供应商评估",
            "综合建议"
        ]
    ),
    ReportType.WEEKLY_SUMMARY: ReportTemplate(
        type=ReportType.WEEKLY_SUMMARY,
        name="周报",
        description="工作总结与下周计划",
        sections=[
            "本周工作总结",
            "关键指标达成",
            "问题与风险",
            "下周工作计划"
        ]
    ),
    ReportType.TRAINING_MATERIAL: ReportTemplate(
        type=ReportType.TRAINING_MATERIAL,
        name="培训材料",
        description="基于SOP的操作培训指南",
        sections=[
            "培训目标",
            "前置知识",
            "操作步骤",
            "注意事项",
            "异常处理",
            "考核要点"
        ]
    )
}


class ReportGenerator:
    """
    报告生成器
    基于模板和文档内容生成专业报告
    """

    def __init__(self, llm_service):
        self.llm = llm_service

    async def generate(
        self,
        report_type: ReportType,
        context: Dict[str, Any],
        template_override: Optional[Dict] = None
    ) -> str:
        """
        生成报告

        Args:
            report_type: 报告类型
            context: 上下文数据
                - documents: 相关文档列表
                - data: 结构化数据
                - metadata: 元数据(时间范围、批次等)
            template_override: 自定义模板(可选)

        Returns:
            Markdown 格式的报告内容
        """
        template = template_override or REPORT_TEMPLATES.get(report_type)

        if not template:
            raise ValueError(f"未知的报告类型: {report_type}")

        # 构建提示词
        prompt = self._build_prompt(template, context)

        # 调用 LLM 生成
        response = self.llm.generate(prompt)

        return response

    def _build_prompt(
        self,
        template: ReportTemplate,
        context: Dict[str, Any]
    ) -> str:
        """构建报告生成提示词"""
        documents = context.get("documents", [])
        metadata = context.get("metadata", {})
        data = context.get("data", {})

        # 构建文档摘要
        doc_summary = "\n\n".join([
            f"【文档{i+1}】{doc.get('title', '未命名')}\n{doc.get('content', '')[:500]}"
            for i, doc in enumerate(documents)
        ]) if documents else "无相关文档"

        sections_prompt = "\n".join([
            f"## {i+1}. {section}"
            for i, section in enumerate(template.sections)
        ])

        prompt = f"""你是一个专业的半导体行业报告撰写助手。请根据以下信息生成{template.name}。

报告类型: {template.name}
描述: {template.description}

【时间范围】
{metadata.get('time_range', '未指定')}

【相关数据】
{data if data else '无结构化数据'}

【参考文档】
{doc_summary}

请生成完整的{template.name}，格式如下:

{sections_prompt}

要求:
1. 内容专业、准确，符合半导体行业规范
2. 数据引用要标注来源
3. 分析要有深度，不要泛泛而谈
4. 建议措施要具体可执行
5. 使用 Markdown 格式输出"""

        return prompt

    def generate_outline(
        self,
        report_type: ReportType,
        topic: str
    ) -> List[str]:
        """
        生成报告大纲

        Args:
            report_type: 报告类型
            topic: 报告主题

        Returns:
            章节标题列表
        """
        template = REPORT_TEMPLATES.get(report_type)
        if not template:
            return []

        return template.sections


# 单例
_report_generator = None


def get_report_generator(llm_service) -> ReportGenerator:
    """获取报告生成器实例"""
    global _report_generator
    if _report_generator is None:
        _report_generator = ReportGenerator(llm_service)
    return _report_generator
