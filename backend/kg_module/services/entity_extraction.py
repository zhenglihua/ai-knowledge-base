"""
实体抽取服务
从文档中提取设备、工艺、材料、参数等实体
结合基于规则的方法和NLP技术
"""
import re
import time
from typing import List, Dict, Optional, Tuple, Set, Any
from dataclasses import dataclass
from collections import defaultdict

from kg_module.models.entity import (
    EntityType, ExtractedEntity, ExtractionResult
)


@dataclass
class EntityPattern:
    """实体抽取模式"""
    patterns: List[str]                      # 正则表达式列表
    entity_type: EntityType                  # 实体类型
    priority: int = 1                        # 优先级（数字越小越优先）
    post_process: Optional[callable] = None  # 后处理函数


class EntityExtractor:
    """实体抽取器"""
    
    # 半导体工厂专用实体模式
    ENTITY_PATTERNS = {
        # 设备型号
        EntityType.EQUIPMENT: EntityPattern(
            patterns=[
                # AMAT 设备
                r'\b(AMAT|Applied Materials?)\s*[\-\s]?(Centura|Endura|Producer|Reflexion|Vantage)\s*[A-Z0-9]*\b',
                r'\b(AMAT)\s+[A-Z]?\d{3,4}\b',
                # ASML 光刻机
                r'\b(ASML)\s*(PAS|AT|XT|NXT|TWINSCAN)\s*[0-9]+\b',
                r'\b(ASML)\s+[A-Z]?\d{3,4}\b',
                # TEL (Tokyo Electron)
                r'\b(TEL|Tokyo Electron)\s*[\-\s]?(Alpha|Beta|Certas|Trias|Telius|Clean Track)\s*[A-Z0-9]*\b',
                r'\b(TEL)\s+[A-Z]?\d{3,4}\b',
                # Lam Research
                r'\b(Lam|Lam Research)\s*[\-\s]?(Versys|Kiyo|Flex|Altus|Vector)\s*[A-Z0-9]*\b',
                # KLA
                r'\b(KLA|KLA-Tencor)\s*[\-\s]?(Surfscan|eDR|eSL|SpectraShape)\s*[A-Z0-9]*\b',
                # Hitachi
                r'\b(Hitachi)\s*[\-\s]?(CG|SU|SE|RT)\s*\d{4,5}\b',
                # Nikon
                r'\b(Nikon)\s*[\-\s]?(NSR)\s*[A-Z]*\d+\b',
                # Canon
                r'\b(Canon)\s*[\-\s]?(FPA)\s*[A-Z]*\d+\b',
                # 通用设备名
                r'\b(光刻机|刻蚀机|沉积设备|扩散炉|离子注入机|CMP设备|清洗机|量测机|检测设备)\b',
                r'\b(Scanner|Stepper|Etcher|Deposition Tool|Implanter|CMP Tool|Cleaner)\b',
            ],
            entity_type=EntityType.EQUIPMENT,
            priority=1
        ),
        
        # 工艺/制程
        EntityType.PROCESS: EntityPattern(
            patterns=[
                # 工艺类型
                r'\b((?:干法|湿法)?刻蚀|Etch)\s*(?:工艺|制程|Recipe|Process)?\b',
                r'\b((?:化学气相|物理气相)?沉积|CVD|PVD|Deposition)\s*(?:工艺|制程)?\b',
                r'\b(光刻|Lithography|曝光)\s*(?:工艺|制程)?\b',
                r'\b(清洗|Clean|湿法处理)\s*(?:工艺|制程)?\b',
                r'\b(CMP|化学机械抛光)\s*(?:工艺|制程)?\b',
                r'\b(退火|Anneal)\s*(?:工艺|制程)?\b',
                r'\b(离子注入|Implantation)\s*(?:工艺|制程)?\b',
                r'\b(扩散|Diffusion)\s*(?:工艺|制程)?\b',
                r'\b(氧化|Oxidation)\s*(?:工艺|制程)?\b',
                # Recipe 名称
                r'\bRecipe\s*[\-_]?[A-Z0-9]+\b',
                r'\bProcess\s*[\-_]?[A-Z0-9]+\b',
                r'\b(工艺|制程)\s*(?:编号|代码|名称)?[:：]?\s*[A-Z0-9\-_]+\b',
            ],
            entity_type=EntityType.PROCESS,
            priority=1
        ),
        
        # 材料
        EntityType.MATERIAL: EntityPattern(
            patterns=[
                # 化学元素和化合物
                r'\b(Si|SiO2|SiN|Si3N4|SiON|Al|Cu|W|Ti|TiN|Ta|TaN|Co|Ni|Pt|Au|Ag)[\d\-]*\b',
                # 光刻胶
                r'\b(光刻胶|Photoresist|Resist)\s*[A-Z0-9\-]*\b',
                # 化学品
                r'\b(HF|HCl|H2SO4|HNO3|H3PO4|NH4OH|NaOH|KOH)\b',
                r'\b(氢氟酸|盐酸|硫酸|硝酸|磷酸|氨水|氢氧化钠|氢氧化钾)\b',
                # 气体
                r'\b(Ar|N2|O2|H2|He|Ne|Cl2|SF6|CF4|C4F8|NH3|SiH4|BCl3|WF6)\b',
                r'\b(氩气|氮气|氧气|氢气|氦气|氯气|六氟化硫)\b',
                # 衬底/晶圆
                r'\b(硅片|晶圆|Wafer)\s*[A-Z0-9\-]*\b',
            ],
            entity_type=EntityType.MATERIAL,
            priority=2
        ),
        
        # 工艺参数
        EntityType.PARAMETER: EntityPattern(
            patterns=[
                # 温度参数
                r'\b(温度|Temperature)[:：]?\s*(?:范围|设定值)?\s*\d+\s*[°℃℃K]\b',
                r'\b(?:温度|Temperature)\s*(?:范围|range)[:：]?\s*\d+\s*[-~]\s*\d+\s*[°℃℃K]\b',
                # 压力参数
                r'\b(压力|Pressure|真空度)[:：]?\s*\d+\.?\d*\s*(?:torr|Pa|mbar|atm)\b',
                # 流量参数
                r'\b(流量|Flow Rate|气体流量)[:：]?\s*\d+\.?\d*\s*(?:sccm|slm)\b',
                # 功率参数
                r'\b(功率|Power|RF Power|射频功率)[:：]?\s*\d+\.?\d*\s*[wW]\b',
                # 时间参数
                r'\b(时间|Time|Duration|处理时间)[:：]?\s*\d+\.?\d*\s*(?:s|sec|min|hr|hour)\b',
                # 转速
                r'\b(转速|RPM|Rotation Speed)[:：]?\s*\d+\s*rpm\b',
            ],
            entity_type=EntityType.PARAMETER,
            priority=2
        ),
        
        # 产品质量指标
        EntityType.QUALITY: EntityPattern(
            patterns=[
                r'\b(缺陷|Defect)\s*(?:密度|Density|数量|Count)?\b',
                r'\b(良率|Yield)\s*(?:目标|Target)?\b',
                r'\b(CD|Critical Dimension)\s*(?:均匀性|Uniformity)?\b',
                r'\b(Overlay|套刻精度|对准精度)\b',
                r'\b(薄膜厚度|Film Thickness)\s*(?:均匀性)?\b',
                r'\b(粗糙度|Roughness)\s*(?:Ra|Rq)?\b',
                r'\b(SPC|统计过程控制)\b',
                r'\b(CPK|过程能力指数)\b',
            ],
            entity_type=EntityType.QUALITY,
            priority=3
        ),
        
        # 产品
        EntityType.PRODUCT: EntityPattern(
            patterns=[
                r'\b(\d{2,3}nm)\s*(?:工艺|制程|技术节点)\b',
                r'\b(逻辑芯片|Logic|存储芯片|Memory|DRAM|NAND|Flash)\b',
                r'\b(CPU|GPU|SoC|ASIC|FPGA)\b',
                r'\b(晶圆|Wafer)\s*(?:直径|尺寸)?[:：]?\s*(?:8|12)\s*英寸\b',
            ],
            entity_type=EntityType.PRODUCT,
            priority=3
        ),
        
        # 部门/组织
        EntityType.DEPARTMENT: EntityPattern(
            patterns=[
                r'\b(工艺部|设备部|质量部|生产部|工程部|研发部|制造部)\b',
                r'\b(Process|Equipment|Quality|Production|Engineering)\s*(?:Department|Div)\b',
                r'\b(EE|PE|QE|ME|PIE|FA)\s*(?:部门|组|科)\b',
            ],
            entity_type=EntityType.DEPARTMENT,
            priority=4
        ),
        
        # 位置
        EntityType.LOCATION: EntityPattern(
            patterns=[
                r'\b(Fab|工厂)\s*[A-Z0-9]+\b',
                r'\b(车间|洁净室|Cleanroom)\s*[A-Z0-9]*\b',
                r'\b(Bay|Area|Zone)\s*[A-Z0-9]+\b',
            ],
            entity_type=EntityType.LOCATION,
            priority=4
        ),
    }
    
    def __init__(self):
        """初始化实体抽取器"""
        self._compile_patterns()
    
    def _compile_patterns(self):
        """编译正则表达式模式"""
        self.compiled_patterns = {}
        for entity_type, pattern_config in self.ENTITY_PATTERNS.items():
            self.compiled_patterns[entity_type] = [
                re.compile(p, re.IGNORECASE) for p in pattern_config.patterns
            ]
    
    def extract(
        self,
        text: str,
        doc_id: Optional[str] = None,
        min_confidence: float = 0.5
    ) -> ExtractionResult:
        """
        从文本中抽取实体
        
        Args:
            text: 输入文本
            doc_id: 文档ID
            min_confidence: 最小置信度阈值
            
        Returns:
            ExtractionResult: 抽取结果
        """
        start_time = time.time()
        entities = []
        seen_spans = set()  # 用于去重
        
        # 按优先级排序处理
        sorted_types = sorted(
            self.ENTITY_PATTERNS.items(),
            key=lambda x: x[1].priority
        )
        
        for entity_type, pattern_config in sorted_types:
            compiled_patterns = self.compiled_patterns.get(entity_type, [])
            
            for pattern in compiled_patterns:
                for match in pattern.finditer(text):
                    # 获取匹配位置和文本
                    start, end = match.span()
                    entity_text = match.group().strip()
                    
                    # 检查是否与已有实体重叠
                    span = (start, end)
                    if any(start <= s < end or start < e <= end for s, e in seen_spans):
                        # 高优先级覆盖低优先级
                        if pattern_config.priority <= 2:
                            continue
                    
                    # 清理实体文本
                    entity_text = self._clean_entity_text(entity_text, entity_type)
                    
                    # 计算置信度
                    confidence = self._calculate_confidence(
                        entity_text, entity_type, match
                    )
                    
                    if confidence >= min_confidence:
                        # 提取属性
                        properties = self._extract_properties(
                            entity_text, entity_type, text, start, end
                        )
                        
                        entity = ExtractedEntity(
                            text=entity_text,
                            type=entity_type,
                            start=start,
                            end=end,
                            confidence=confidence,
                            properties=properties
                        )
                        
                        entities.append(entity)
                        seen_spans.add(span)
        
        # 合并重叠实体（保留置信度高的）
        entities = self._merge_overlapping_entities(entities)
        
        processing_time = (time.time() - start_time) * 1000
        
        return ExtractionResult(
            doc_id=doc_id or "",
            entities=entities,
            processing_time_ms=processing_time
        )
    
    def _clean_entity_text(self, text: str, entity_type: EntityType) -> str:
        """清理实体文本"""
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text)
        # 移除标点
        text = text.strip(' ,.!?;:：，。！？；')
        return text
    
    def _calculate_confidence(
        self,
        entity_text: str,
        entity_type: EntityType,
        match
    ) -> float:
        """计算实体置信度"""
        confidence = 0.7  # 基础置信度
        
        # 长度因素（太短或太长降低置信度）
        length = len(entity_text)
        if 3 <= length <= 50:
            confidence += 0.1
        elif length < 2 or length > 100:
            confidence -= 0.2
        
        # 设备型号匹配度高
        if entity_type == EntityType.EQUIPMENT:
            if re.match(r'^[A-Z]+\s*[A-Z0-9\-]+$', entity_text, re.I):
                confidence += 0.15
        
        # 参数格式匹配
        if entity_type == EntityType.PARAMETER:
            if re.search(r'\d+\.?\d*\s*[a-zA-Z/]+$', entity_text):
                confidence += 0.15
        
        # 确保在0-1范围内
        return min(max(confidence, 0.0), 1.0)
    
    def _extract_properties(
        self,
        entity_text: str,
        entity_type: EntityType,
        full_text: str,
        start: int,
        end: int
    ) -> Dict[str, Any]:
        """提取实体属性"""
        properties = {}
        
        if entity_type == EntityType.PARAMETER:
            # 提取数值和单位
            value_match = re.search(r'(\d+\.?\d*)\s*([a-zA-Z/°℃℃]+)', entity_text)
            if value_match:
                properties['value'] = float(value_match.group(1))
                properties['unit'] = value_match.group(2)
        
        elif entity_type == EntityType.EQUIPMENT:
            # 提取厂商
            manufacturers = ['AMAT', 'ASML', 'TEL', 'Lam', 'KLA', 'Hitachi', 'Nikon', 'Canon']
            for mfr in manufacturers:
                if mfr.lower() in entity_text.lower():
                    properties['manufacturer'] = mfr
                    break
        
        elif entity_type == EntityType.MATERIAL:
            # 提取化学式
            formula_match = re.match(r'([A-Z][a-z]?\d*)+', entity_text)
            if formula_match:
                properties['formula'] = formula_match.group()
        
        # 提取上下文
        context_start = max(0, start - 50)
        context_end = min(len(full_text), end + 50)
        properties['context'] = full_text[context_start:context_end]
        
        return properties
    
    def _merge_overlapping_entities(
        self,
        entities: List[ExtractedEntity]
    ) -> List[ExtractedEntity]:
        """合并重叠的实体（保留置信度更高的）"""
        if not entities:
            return entities
        
        # 按开始位置排序
        entities = sorted(entities, key=lambda x: (x.start, -x.confidence))
        
        merged = []
        for entity in entities:
            # 检查是否与已合并实体重叠
            overlaps = False
            for existing in merged:
                if not (entity.end <= existing.start or entity.start >= existing.end):
                    # 有重叠，保留置信度高的
                    if entity.confidence > existing.confidence:
                        merged.remove(existing)
                        merged.append(entity)
                    overlaps = True
                    break
            
            if not overlaps:
                merged.append(entity)
        
        return sorted(merged, key=lambda x: x.start)
    
    def batch_extract(
        self,
        texts: List[Tuple[str, str]],  # [(doc_id, text), ...]
        min_confidence: float = 0.5
    ) -> List[ExtractionResult]:
        """
        批量抽取实体
        
        Args:
            texts: 文档ID和文本的列表
            min_confidence: 最小置信度阈值
            
        Returns:
            抽取结果列表
        """
        results = []
        for doc_id, text in texts:
            result = self.extract(text, doc_id, min_confidence)
            results.append(result)
        return results


# 全局抽取器实例
_extractor = None

def get_entity_extractor() -> EntityExtractor:
    """获取全局实体抽取器实例"""
    global _extractor
    if _extractor is None:
        _extractor = EntityExtractor()
    return _extractor


def extract_entities(
    text: str,
    doc_id: Optional[str] = None,
    min_confidence: float = 0.5
) -> ExtractionResult:
    """便捷的实体抽取函数"""
    return get_entity_extractor().extract(text, doc_id, min_confidence)