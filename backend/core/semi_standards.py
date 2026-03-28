"""
SEMI 标准文档库
v0.4.0
半导体行业 SEMI 标准查询和匹配
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class SEMIStandard:
    """SEMI 标准条目"""
    code: str  # 标准编号，如 SEMI E10
    name: str  # 标准名称
    version: str  # 版本
    category: str  # 分类
    description: str  # 描述
    keywords: List[str]  # 关键词


class SEMIStandardLibrary:
    """
    SEMI 标准知识库
    收录常用 SEMI 标准供查询和匹配
    """

    # 标准分类
    CATEGORY_EQUIPMENT = "设备"
    CATEGORY_COMMUNICATION = "通信"
    CATEGORY_SAFETY = "安全"
    CATEGORY_MATERIAL = "材料"
    CATEGORY_PROCESS = "工艺"
    CATEGORY_METROLOGY = "测量"
    CATEGORY_FACTORY = "工厂"

    def __init__(self):
        self._standards: Dict[str, SEMIStandard] = {}
        self._standards_by_category: Dict[str, List[SEMIStandard]] = {}
        self._build_library()

    def _build_library(self):
        """构建标准库"""
        standards = [
            # Equipment Automation Standards
            SEMIStandard(
                code="SEMI E10",
                name="Specification for Definition of Equipment Performance",
                version="0709",
                category=self.CATEGORY_EQUIPMENT,
                description="设备性能指标定义规范，包含设备可用率、产能等关键指标",
                keywords=["availability", "uptime", "throughput", "mtbf", "mttf", "mttr", "设备效率", "可用率"]
            ),
            SEMIStandard(
                code="SEMI E37",
                name="High-Speed SECS Message Service (HSMS)",
                version="0318",
                category=self.CATEGORY_COMMUNICATION,
                description="高速 SECS 消息服务协议，用于设备与主机通信",
                keywords=["HSMS", "SECS", "GEM", "通信", "协议", "TCP/IP"]
            ),
            SEMIStandard(
                code="SEMI E30",
                name="GEM Standard - Generic Model for Communications",
                version="0318",
                category=self.CATEGORY_COMMUNICATION,
                description="通用设备模型标准，定义设备通信和控制接口",
                keywords=["GEM", "SECS-II", "equipment", "host", "通信", "控制"]
            ),
            SEMIStandard(
                code="SEMI E84",
                name="Specification for Mechanical Handlers",
                version="0709",
                category=self.CATEGORY_EQUIPMENT,
                description="机械手传输规范，定义晶圆传送接口",
                keywords=["handler", "loader", "unloader", "CSM", "HOB", "机械手"]
            ),
            SEMIStandard(
                code="SEMI E87",
                name="Specification for Carrier Management",
                version="0710",
                category=self.CATEGORY_EQUIPMENT,
                description="载具管理规范，定义 FOUP 和 CAS 的接口",
                keywords=["FOUP", "carrier", "CAS", "LPI", "载具", "晶圆传送"]
            ),
            SEMIStandard(
                code="SEMI E90",
                name="Specification for Substrate Tracking",
                version="0709",
                category=self.CATEGORY_EQUIPMENT,
                description="基片追踪规范，定义晶圆在设备内的追踪协议",
                keywords=["tracking", "substrate", "lot", "batch", "追踪", "晶圆追踪"]
            ),

            # Safety Standards
            SEMIStandard(
                code="SEMI S1",
                name="Safety Guideline for Equipment Design",
                version="0314",
                category=self.CATEGORY_SAFETY,
                description="设备设计安全指南，涵盖电气、机械、热、化学安全",
                keywords=["safety", "electrical", "mechanical", "thermal", "安全", "设计"]
            ),
            SEMIStandard(
                code="SEMI S2",
                name="Environmental Safety and Health Guidelines",
                version="0318",
                category=self.CATEGORY_SAFETY,
                description="环境安全与健康指南，设备环境安全评估标准",
                keywords=["ESH", "safety", "environment", "health", "环境安全", "健康"]
            ),
            SEMIStandard(
                code="SEMI S10",
                name="Safety Risk Assessment",
                version="0218",
                category=self.CATEGORY_SAFETY,
                description="安全风险评估标准，定义风险评估流程",
                keywords=["risk", "assessment", "hazard", "风险评估", "危害"]
            ),

            # Materials Standards
            SEMIStandard(
                code="SEMI F19",
                name="Specification for Polished Monocrystalline Silicon Wafers",
                version="0218",
                category=self.CATEGORY_MATERIAL,
                description="抛光单晶硅片规范，定义硅片尺寸、表面质量等",
                keywords=["wafer", "silicon", "diameter", "thickness", "硅片", "抛光"]
            ),
            SEMIStandard(
                code="SEMI M1",
                name="Specification for Monocrystalline Silicon",
                version="0318",
                category=self.CATEGORY_MATERIAL,
                description="单晶硅材料规范，定义硅材料纯度、掺杂等",
                keywords=["silicon", "monocrystalline", "doping", "材料", "硅"]
            ),

            # Process Standards
            SEMIStandard(
                code="SEMI C3",
                name="Rules for Bare Silicon Wafer Handling",
                version="0712",
                category=self.CATEGORY_PROCESS,
                description="裸硅片操作规范，定义晶圆操作的环境和方式",
                keywords=["handling", "cleanroom", "wafer", "操作", "洁净室"]
            ),
            SEMIStandard(
                code="SEMI E44",
                name="Guide for Equipment Data Acquisition",
                version="0218",
                category=self.CATEGORY_PROCESS,
                description="设备数据采集指南，定义设备数据采集格式",
                keywords=["data", "acquisition", "DAS", "data collection", "数据采集"]
            ),

            # Metrology Standards
            SEMIStandard(
                code="SEMI E89",
                name="Guide for Measurement System Analysis",
                version="0617",
                category=self.CATEGORY_METROLOGY,
                description="测量系统分析指南，定义测量系统的验证方法",
                keywords=["MSA", "measurement", "calibration", "measurement system", "测量"]
            ),

            # Factory Standards
            SEMIStandard(
                code="SEMI E58",
                name="Guide for Real Time Fault Tracking",
                version="0617",
                category=self.CATEGORY_FACTORY,
                description="实时故障追踪指南，定义故障分类和追踪协议",
                keywords=["fault", "tracking", "alarm", "故障", "追踪"]
            ),
            SEMIStandard(
                code="SEMI E116",
                name="Standard for Equipment Performance Tracking",
                version="0617",
                category=self.CATEGORY_FACTORY,
                description="设备性能追踪标准，定义设备数据采集和报告格式",
                keywords=["performance", "tracking", "PMP", "equipment log", "性能追踪"]
            ),
        ]

        # 构建索引
        for standard in standards:
            self._standards[standard.code] = standard

            if standard.category not in self._standards_by_category:
                self._standards_by_category[standard.category] = []
            self._standards_by_category[standard.category].append(standard)

    def search(self, keyword: str) -> List[SEMIStandard]:
        """
        搜索标准

        Args:
            keyword: 搜索关键词

        Returns:
            匹配的标准列表
        """
        keyword_lower = keyword.lower()
        results = []

        for standard in self._standards.values():
            # 匹配标准编号
            if keyword_lower in standard.code.lower():
                results.append(standard)
                continue

            # 匹配名称
            if keyword_lower in standard.name.lower():
                results.append(standard)
                continue

            # 匹配关键词
            for kw in standard.keywords:
                if keyword_lower in kw.lower():
                    results.append(standard)
                    break

        return results

    def get_by_code(self, code: str) -> Optional[SEMIStandard]:
        """根据编号获取标准"""
        return self._standards.get(code.upper())

    def get_by_category(self, category: str) -> List[SEMIStandard]:
        """获取指定分类的所有标准"""
        return self._standards_by_category.get(category, [])

    def get_all_categories(self) -> List[str]:
        """获取所有分类"""
        return list(self._standards_by_category.keys())

    def match_document(self, document_text: str) -> List[Tuple[SEMIStandard, float]]:
        """
        文档匹配标准

        Args:
            document_text: 文档文本

        Returns:
            [(标准, 相似度得分)] 列表
        """
        doc_lower = document_text.lower()
        matches = []

        for standard in self._standards.values():
            score = 0.0

            # 检查编号出现次数
            code_parts = standard.code.split()
            for part in code_parts:
                if part.lower() in doc_lower:
                    score += 2.0

            # 检查关键词匹配
            for kw in standard.keywords:
                if kw.lower() in doc_lower:
                    score += 1.0

            if score > 0:
                matches.append((standard, score))

        # 按分数排序
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches

    def get_related_standards(self, standard_code: str) -> List[SEMIStandard]:
        """
        获取相关标准

        根据同一分类的其他标准
        """
        standard = self.get_by_code(standard_code)
        if not standard:
            return []

        category_standards = self.get_by_category(standard.category)
        return [s for s in category_standards if s.code != standard_code]


# 单例
semi_standard_library = SEMIStandardLibrary()
