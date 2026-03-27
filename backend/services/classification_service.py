"""
文档智能分类和标签提取服务
基于规则 + NLP 的混合方案
"""
import re
import json
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from collections import Counter

@dataclass
class ClassificationResult:
    """分类结果"""
    category: str
    confidence: float
    reason: str

@dataclass
class TagResult:
    """标签提取结果"""
    tag: str
    tag_type: str  # equipment, process, parameter, material, etc.
    confidence: float

class DocumentClassifier:
    """文档分类器 - 半导体工厂专用"""
    
    # 预定义的分类及其关键词
    CATEGORIES = {
        "工艺文档": {
            "keywords": ["工艺", "制程", "recipe", "process", "etch", "deposition", "lithography", "cmp", "清洗", "扩散", "氧化", "离子注入", "退火", "光刻", "刻蚀", "薄膜", "沉积", "cmp", "化学机械抛光"],
            "equipment": ["光刻机", "刻蚀机", "沉积设备", "扩散炉", "离子注入机", "cmp设备"],
            "weight": 1.0
        },
        "设备文档": {
            "keywords": ["设备", "machine", "equipment", "tool", "chamber", "机台", "维护", "保养", "维修", "故障", "报警", "alarm", "parts", "备件", "manual", "手册", "规格书", "spec"],
            "equipment": ["am", " Centura", "Endura", "Producer", "DUV", "EUV", "scanner", "track"],
            "weight": 1.0
        },
        "CIM系统": {
            "keywords": ["cim", "mes", "eap", "rts", "api", "数据库", "database", "接口", "系统", "软件", "自动化", "integration", "pc", "workstation", "服务器", "server", "网络", "network", "report", "报表"],
            "equipment": ["oracle", "mysql", "sql server", "linux", "windows"],
            "weight": 1.0
        },
        "质量管控": {
            "keywords": ["质量", "quality", "缺陷", "defect", "检测", "inspection", "量测", "metrology", "spc", "cpk", "yield", "良率", "cp", "管制", "control", "chart", "规格", "spec", "limit"],
            "equipment": ["缺陷检测", "量测设备", "电性测试", "cp测试", "ft测试"],
            "weight": 1.0
        },
        "生产管理": {
            "keywords": ["生产", "production", "计划", "schedule", "lot", "wafer", "晶圆", "产能", "capacity", "效率", "efficiency", "排程", "dispatch", "派工", "wip", "在制品"],
            "equipment": [],
            "weight": 1.0
        },
        "安全环保": {
            "keywords": ["安全", "safety", "环保", "environment", "hse", "化学", "化学品", "chemical", "气体", "gas", "废料", "waste", "防护", "ppe", "事故", "accident"],
            "equipment": [],
            "weight": 1.0
        }
    }
    
    # 标签提取模式
    TAG_PATTERNS = {
        "equipment_model": {
            "patterns": [
                r'([A-Z][a-zA-Z]*\s*(?:Centura|Endura|Producer|Chamber|Tool))',
                r'(AMAT\s*[A-Z]?\d{3,4})',
                r'(ASML\s*[A-Z]?\d{3,4})',
                r'(TEL\s*[A-Z]?\d{3,4})',
                r'(Lam\s*\w+\s*\d{3,4})',
                r'(KLA\s*\w+\s*\d{3,4})',
                r'(Hitachi\s*[A-Z]+\d{3,4})',
                r'(Nikon\s*[A-Z]+\d{3,4})',
                r'(Canon\s*[A-Z]+\d{3,4})',
            ],
            "type": "equipment"
        },
        "process_name": {
            "patterns": [
                r'((?:蚀刻|etch|deposition|沉积|光刻|lithography|清洗|clean|cmp|退火|anneal|离子注入|implant)[\w\s]*工艺)',
                r'(recipe\s*[\w\-]+)',
                r'(process\s*[\w\-]+)',
            ],
            "type": "process"
        },
        "parameters": {
            "patterns": [
                r'(温度[:：]\s*(?:\d+\.?\d*)\s*[°℃℃])',
                r'(压力[:：]\s*(?:\d+\.?\d*)\s*(?:torr|pa|mbar|atm))',
                r'(流量[:：]\s*(?:\d+\.?\d*)\s*(?:sccm|slm))',
                r'(功率[:：]\s*(?:\d+\.?\d*)\s*[wW])',
                r'(时间[:：]\s*(?:\d+\.?\d*)\s*(?:s|sec|min|hr))',
            ],
            "type": "parameter"
        },
        "materials": {
            "patterns": [
                r'((?:Si|SiO2|SiN|Al|Cu|W|Ti|TiN|Ta|TaN|Co|Ni|Pt|Au|Ag)[\w\-\d]*)',
                r'(光刻胶|photoresist|resist)',
                r'(化学品|chemical)',
            ],
            "type": "material"
        }
    }
    
    def __init__(self):
        self._compile_patterns()
    
    def _compile_patterns(self):
        """编译正则表达式"""
        self.compiled_patterns = {}
        for tag_type, config in self.TAG_PATTERNS.items():
            self.compiled_patterns[tag_type] = [
                re.compile(p, re.IGNORECASE) for p in config["patterns"]
            ]
    
    def classify(self, content: str, title: str = "") -> ClassificationResult:
        """
        对文档进行分类
        
        Args:
            content: 文档内容
            title: 文档标题
            
        Returns:
            ClassificationResult: 分类结果
        """
        text = f"{title}\n{content}".lower()
        scores = {}
        
        for category, config in self.CATEGORIES.items():
            score = 0.0
            matched_keywords = []
            
            # 关键词匹配
            for keyword in config["keywords"]:
                count = text.count(keyword.lower())
                if count > 0:
                    score += count * config["weight"]
                    matched_keywords.append(keyword)
            
            # 标题加权（标题中出现关键词权重更高）
            title_lower = title.lower()
            for keyword in config["keywords"]:
                if keyword.lower() in title_lower:
                    score += 3 * config["weight"]
            
            # 设备型号匹配
            for equip in config.get("equipment", []):
                if equip.lower() in text:
                    score += 2 * config["weight"]
            
            scores[category] = {
                "score": score,
                "keywords": matched_keywords[:5]  # 最多显示5个关键词
            }
        
        # 找出得分最高的分类
        if scores:
            best_category = max(scores.items(), key=lambda x: x[1]["score"])
            category_name = best_category[0]
            category_score = best_category[1]["score"]
            keywords = best_category[1]["keywords"]
            
            # 计算置信度
            total_score = sum(s["score"] for s in scores.values())
            confidence = category_score / total_score if total_score > 0 else 0
            
            # 构建原因说明
            reason = f"匹配关键词: {', '.join(keywords)}" if keywords else "基于内容分析"
            
            # 如果置信度太低，归类为"其他"
            if confidence < 0.3:
                return ClassificationResult(
                    category="其他文档",
                    confidence=1.0 - confidence,
                    reason="未找到明确分类特征"
                )
            
            return ClassificationResult(
                category=category_name,
                confidence=confidence,
                reason=reason
            )
        
        return ClassificationResult(
            category="其他文档",
            confidence=0.5,
            reason="无法确定分类"
        )
    
    def extract_tags(self, content: str, title: str = "") -> List[TagResult]:
        """
        从文档中提取标签
        
        Args:
            content: 文档内容
            title: 文档标题
            
        Returns:
            List[TagResult]: 标签列表
        """
        text = f"{title}\n{content}"
        tags = []
        seen_tags = set()
        
        for tag_type, config in self.TAG_PATTERNS.items():
            patterns = self.compiled_patterns.get(tag_type, [])
            
            for pattern in patterns:
                matches = pattern.findall(text)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]
                    
                    tag = match.strip()
                    
                    # 去重和过滤
                    if tag and len(tag) > 1 and tag.lower() not in seen_tags:
                        seen_tags.add(tag.lower())
                        
                        # 计算置信度（基于出现频率和长度）
                        frequency = text.lower().count(tag.lower())
                        confidence = min(0.5 + frequency * 0.1, 0.95)
                        
                        tags.append(TagResult(
                            tag=tag,
                            tag_type=config["type"],
                            confidence=confidence
                        ))
        
        # 按置信度排序
        tags.sort(key=lambda x: x.confidence, reverse=True)
        
        # 返回前20个标签
        return tags[:20]
    
    def analyze_document(self, content: str, title: str = "") -> Dict:
        """
        完整分析文档 - 分类+标签
        
        Args:
            content: 文档内容
            title: 文档标题
            
        Returns:
            Dict: 包含分类和标签的分析结果
        """
        classification = self.classify(content, title)
        tags = self.extract_tags(content, title)
        
        return {
            "category": classification.category,
            "category_confidence": round(classification.confidence, 2),
            "category_reason": classification.reason,
            "tags": [
                {
                    "tag": t.tag,
                    "type": t.tag_type,
                    "confidence": round(t.confidence, 2)
                }
                for t in tags
            ],
            "tag_summary": {
                "equipment": [t.tag for t in tags if t.tag_type == "equipment"][:5],
                "process": [t.tag for t in tags if t.tag_type == "process"][:5],
                "parameter": [t.tag for t in tags if t.tag_type == "parameter"][:5],
                "material": [t.tag for t in tags if t.tag_type == "material"][:5],
            }
        }


# 预定义的预设分类和标签
PRESET_CATEGORIES = [
    {"id": "process", "name": "工艺文档", "color": "blue", "icon": "⚙️"},
    {"id": "equipment", "name": "设备文档", "color": "green", "icon": "🔧"},
    {"id": "cim", "name": "CIM系统", "color": "purple", "icon": "💻"},
    {"id": "quality", "name": "质量管控", "color": "orange", "icon": "📊"},
    {"id": "production", "name": "生产管理", "color": "cyan", "icon": "🏭"},
    {"id": "safety", "name": "安全环保", "color": "red", "icon": "🛡️"},
    {"id": "other", "name": "其他文档", "color": "default", "icon": "📄"},
]

PRESET_TAGS = {
    "equipment_model": ["AMAT", "ASML", "TEL", "Lam Research", "KLA", "Hitachi", "Nikon", "Canon"],
    "process": ["光刻", "刻蚀", "沉积", "清洗", "CMP", "退火", "离子注入", "扩散", "氧化"],
    "material": ["硅", "SiO2", "SiN", "铝", "铜", "钨", "光刻胶"],
}


# 全局分类器实例
_classifier = None

def get_classifier() -> DocumentClassifier:
    """获取全局分类器实例"""
    global _classifier
    if _classifier is None:
        _classifier = DocumentClassifier()
    return _classifier


def classify_document(content: str, title: str = "") -> ClassificationResult:
    """便捷的分类函数"""
    return get_classifier().classify(content, title)


def extract_document_tags(content: str, title: str = "") -> List[TagResult]:
    """便捷的标签提取函数"""
    return get_classifier().extract_tags(content, title)


def analyze_document(content: str, title: str = "") -> Dict:
    """便捷的完整分析函数"""
    return get_classifier().analyze_document(content, title)