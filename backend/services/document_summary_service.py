"""
文档摘要服务 - 自动生成文档摘要卡片
使用 LLM 从文档内容中提取结构化摘要信息
"""
import re
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

from services.document_parser import DocumentParser
from services.ai_service import get_ai_service


@dataclass
class SummaryCard:
    """文档摘要卡片"""
    doc_id: str
    filename: str
    summary: str                          # 总体摘要（150字以内）
    sections: List[str]                  # 主要章节
    key_parameters: List[Dict]            # 关键工艺参数
    key_equipment: List[str]              # 关键设备
    safety_notes: List[str]               # 安全注意事项
    tables_found: int                     # 发现的表格数量
    word_count: int                      # 文档字数
    tags: List[str]                      # 文档标签

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DocumentSummaryService:
    """文档摘要服务"""

    def __init__(self):
        self._parser = DocumentParser()
        self._ai = None  # 延迟初始化

    def _get_ai(self):
        if self._ai is None:
            self._ai = get_ai_service()
        return self._ai

    def generate_summary(self, file_path: str, filename: str, doc_id: str = "") -> SummaryCard:
        """
        生成文档摘要卡片
        
        步骤：
        1. 解析文档（提取文本和表格）
        2. 提取关键工艺参数
        3. 使用 LLM 生成结构化摘要
        """
        # 1. 解析文档
        parsed = self._parser.parse_with_tables(file_path, filename)
        text = parsed.get('text', '')
        tables = parsed.get('tables', [])
        
        # 2. 提取工艺参数
        params = self._parser.extract_params(file_path, filename)
        
        # 3. 提取设备信息
        equipment_keywords = [
            '光刻机', '刻蚀机', 'CVD', 'PVD', 'LPCVD', 'PECVD', 'APCVD',
            '离子注入机', 'CMP', '抛光机', '扩散炉', '炉管', 'RTA', 'RTP',
            '溅射机', '蒸发机', '清洗机', '探针台', 'ATE', '切割机',
            '贴片机', '键合机', '塑封压机', '探针', '步进机', '扫描机',
            'Nikon', 'Canon', 'ASML', 'Applied Materials', 'TEL', 'Lam Research'
        ]
        equipment = []
        found_eq = set()
        for eq in equipment_keywords:
            if eq in text and eq not in found_eq:
                equipment.append(eq)
                found_eq.add(eq)
        
        # 4. 提取安全注意事项
        safety_keywords = ['安全', '注意事项', '警示', '警告', '危险', '有毒', '腐蚀', '烫伤', '爆炸', '自燃']
        safety_notes = []
        for line in text.split('\n'):
            line = line.strip()
            if any(kw in line for kw in safety_keywords) and len(line) > 10:
                # 清理并截取
                note = re.sub(r'^[#\d\.、]+', '', line).strip()
                if note and len(note) < 200:
                    safety_notes.append(note)
        
        # 5. 提取章节
        sections = []
        for line in text.split('\n'):
            match = re.match(r'^#+\s+(.+?)\s*$', line.strip())
            if match:
                sections.append(match.group(1))
        
        # 6. 生成标签
        tags = self._generate_tags(text, filename, sections, equipment)
        
        # 7. 使用 LLM 生成摘要
        summary = self._generate_summary_text(text, filename, sections, tables)
        
        return SummaryCard(
            doc_id=doc_id or filename,
            filename=filename,
            summary=summary,
            sections=sections[:10],  # 最多10个章节
            key_parameters=params[:20],  # 最多20个参数
            key_equipment=equipment[:10],  # 最多10个设备
            safety_notes=safety_notes[:5],  # 最多5条安全注意
            tables_found=len(tables),
            word_count=len(text),
            tags=tags[:8]  # 最多8个标签
        )

    def _generate_summary_text(
        self, text: str, filename: str, sections: List[str], tables: List[Dict]
    ) -> str:
        """使用 LLM 生成文档摘要"""
        try:
            ai = self._get_ai()
            
            # 取前2000字符作为摘要上下文
            context = text[:3000] if text else ""
            
            # 构建摘要 prompt
            prompt = f"""你是一个专业的半导体工艺文档分析助手。请为以下文档生成一个简明摘要。

文档名称：{filename}
主要章节：{'、'.join(sections[:8])}
表格数量：{len(tables)}

文档内容摘要：
{context[:2000]}

请按以下JSON格式输出摘要（只输出JSON，不要其他内容）：
{{
    "brief_summary": "100-150字的中文摘要，说明文档的核心内容和目的",
    "main_topics": ["主题1", "主题2", "主题3"],
    "difficulty_level": "基础/进阶/高级",
    "target_audience": "目标读者"
}}"""
            
            result = ai.generate_answer(prompt)
            
            # 解析 JSON
            try:
                if "{" in result and "}" in result:
                    json_str = result[result.index("{"):result.rindex("}")+1]
                    data = json.loads(json_str)
                    brief = data.get('brief_summary', '')
                    if brief:
                        return brief
            except:
                pass
            
            # 如果 JSON 解析失败，尝试返回 LLM 的原始回复
            if result and len(result) > 10:
                return result[:300]
                
        except Exception as e:
            pass
        
        # Fallback: 生成简单的摘要
        return self._generate_fallback_summary(text, sections, filename)

    def _generate_fallback_summary(self, text: str, sections: List[str], filename: str) -> str:
        """当 LLM 不可用时的简单摘要"""
        # 找第一段文字作为摘要
        paras = [p.strip() for p in text.split('\n') if len(p.strip()) > 50]
        
        if paras:
            first_para = paras[0][:200]
            return f"本文档为{filename}，包含{'、'.join(sections[:3])}等核心内容。"
        
        return f"本文档为{filename}，共{len(sections)}个章节，涉及半导体工艺相关内容。"

    def _generate_tags(self, text: str, filename: str, sections: List[str], equipment: List[str]) -> List[str]:
        """自动生成文档标签"""
        tags = set()
        
        # 从文件名推断标签
        name_tags = {
            '光刻': '光刻工艺', '刻蚀': '刻蚀工艺', '沉积': '薄膜沉积',
            '离子': '离子注入', 'CMP': '化学机械抛光', '抛光': '化学机械抛光',
            '扩散': '扩散退火', '退火': '扩散退火', '金属化': '金属化工艺',
            '清洗': '清洗干燥', '干燥': '清洗干燥', '封装': '封装测试', '测试': '封装测试'
        }
        for kw, tag in name_tags.items():
            if kw in filename:
                tags.add(tag)
        
        # 从章节内容推断标签
        section_text = ' '.join(sections)
        tech_tags = {
            '参数': '工艺参数', '设备': '设备维护', '问题': '故障处理',
            '安全': '安全规范', '工艺': '工艺流程', '检测': '质量检测',
            '标准': '质量标准', '维护': '设备维护'
        }
        for kw, tag in tech_tags.items():
            if kw in section_text:
                tags.add(tag)
        
        # 从设备推断标签
        if equipment:
            tags.add('设备相关')
        
        return list(tags)

    def generate_batch_summary(self, file_paths: List[Dict[str, str]]) -> List[SummaryCard]:
        """
        批量生成摘要
        
        Args:
            file_paths: [{"path": "...", "filename": "...", "doc_id": "..."}]
        """
        results = []
        for fp in file_paths:
            try:
                card = self.generate_summary(
                    file_path=fp['path'],
                    filename=fp['filename'],
                    doc_id=fp.get('doc_id', '')
                )
                results.append(card)
            except Exception as e:
                print(f"生成摘要失败 {fp['filename']}: {e}")
        return results


# 全局单例
_summary_service: Optional[DocumentSummaryService] = None


def get_summary_service() -> DocumentSummaryService:
    global _summary_service
    if _summary_service is None:
        _summary_service = DocumentSummaryService()
    return _summary_service
