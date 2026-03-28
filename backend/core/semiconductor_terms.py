"""
半导体行业术语词典
v0.3.0
支持术语扩展、同义词匹配、术语标准化
"""
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
import re


@dataclass
class TermEntry:
    """术语条目"""
    term: str  # 标准术语
    aliases: List[str]  # 别名/缩写
    category: str  # 分类
    description: str  # 描述
    english: str  # 英文


class SemiconductorTerms:
    """半导体术语词典"""

    # 工艺分类
    CATEGORY_PROCESS = "工艺"
    CATEGORY_EQUIPMENT = "设备"
    CATEGORY_MATERIAL = "材料"
    CATEGORY_PARAMETER = "参数"
    CATEGORY_QUALITY = "质量"
    CATEGORY_SAFETY = "安全"

    def __init__(self):
        self._terms: Dict[str, TermEntry] = {}
        self._alias_to_term: Dict[str, str] = {}  # 别名 -> 标准术语
        self._category_terms: Dict[str, Set[str]] = {}  # 分类 -> 术语集合
        self._build_dictionary()

    def _build_dictionary(self):
        """构建术语词典"""
        terms = [
            # 工艺相关
            TermEntry("光刻", ["Lithography", "曝光"], self.CATEGORY_PROCESS,
                     "通过光敏抗蚀剂和光线将图案转移到晶圆上的工艺",
                     "Photolithography"),
            TermEntry("刻蚀", ["Etching"], self.CATEGORY_PROCESS,
                     "移除晶圆上特定区域材料的工艺",
                     "Etching"),
            TermEntry("沉积", ["Deposition", "薄膜沉积"], self.CATEGORY_PROCESS,
                     "在晶圆表面形成薄膜的工艺",
                     "Film Deposition"),
            TermEntry("化学气相沉积", ["CVD", "Chemical Vapor Deposition"], self.CATEGORY_PROCESS,
                     "通过化学反应在衬底表面沉积薄膜",
                     "Chemical Vapor Deposition"),
            TermEntry("物理气相沉积", ["PVD", "Physical Vapor Deposition"], self.CATEGORY_PROCESS,
                     "通过物理过程沉积薄膜",
                     "Physical Vapor Deposition"),
            TermEntry("离子注入", ["Implant", "掺杂"], self.CATEGORY_PROCESS,
                     "将掺杂物离子加速注入晶圆",
                     "Ion Implantation"),
            TermEntry("化学机械平坦化", ["CMP", "研磨"], self.CATEGORY_PROCESS,
                     "结合化学腐蚀和机械研磨平整化晶圆表面",
                     "Chemical Mechanical Planarization"),
            TermEntry("扩散", ["Diffusion"], self.CATEGORY_PROCESS,
                     "高温下使掺杂物在晶圆中扩散",
                     "Thermal Diffusion"),
            TermEntry("氧化", ["Oxidation"], self.CATEGORY_PROCESS,
                     "在晶圆表面形成氧化层",
                     "Oxidation"),
            TermEntry("退火", ["Anneal", "热退火"], self.CATEGORY_PROCESS,
                     "通过加热恢复晶格结构或激活掺杂物",
                     "Annealing"),

            # 设备相关
            TermEntry("光刻机", ["Stepper", "曝光机", "Scanner"], self.CATEGORY_EQUIPMENT,
                     "用于光刻工艺的设备",
                     "Lithography Tool"),
            TermEntry("刻蚀机", ["Etcher", "干刻设备"], self.CATEGORY_EQUIPMENT,
                     "用于刻蚀工艺的设备",
                     "Etching Equipment"),
            TermEntry("沉积设备", ["Deposition Tool", "薄膜机"], self.CATEGORY_EQUIPMENT,
                     "用于薄膜沉积的设备",
                     "Deposition Equipment"),
            TermEntry("离子注入机", ["Implanter"], self.CATEGORY_EQUIPMENT,
                     "用于离子注入的设备",
                     "Ion Implanter"),
            TermEntry("CMP设备", ["CMP Tool", "研磨机"], self.CATEGORY_EQUIPMENT,
                     "用于化学机械平坦化的设备",
                     "CMP Equipment"),
            TermEntry("测量设备", ["Metrology", "量测机"], self.CATEGORY_EQUIPMENT,
                     "用于工艺测量和检测的设备",
                     "Metrology Tool"),
            TermEntry("缺陷检测设备", ["Inspection", "AOI"], self.CATEGORY_EQUIPMENT,
                     "用于缺陷检测的设备",
                     "Defect Inspection Tool"),

            # 参数相关
            TermEntry("温度", ["Temp", "Temperature"], self.CATEGORY_PARAMETER,
                     "工艺参数-温度",
                     "Temperature"),
            TermEntry("压力", ["Pressure", "压强"], self.CATEGORY_PARAMETER,
                     "工艺参数-压力",
                     "Pressure"),
            TermEntry("时间", ["Time", "Duration", "时长"], self.CATEGORY_PARAMETER,
                     "工艺参数-时间/持续时间",
                     "Duration"),
            TermEntry("流量", ["Flow", "Flow Rate"], self.CATEGORY_PARAMETER,
                     "工艺参数-气体/液体流量",
                     "Flow Rate"),
            TermEntry("功率", ["Power", "RF Power"], self.CATEGORY_PARAMETER,
                     "工艺参数-功率",
                     "Power"),
            TermEntry("电压", ["Voltage", "V"], self.CATEGORY_PARAMETER,
                     "工艺参数-电压",
                     "Voltage"),
            TermEntry("电流", ["Current", "A"], self.CATEGORY_PARAMETER,
                     "工艺参数-电流",
                     "Current"),
            TermEntry("厚度", ["Thickness", "Thick"], self.CATEGORY_PARAMETER,
                     "薄膜厚度参数",
                     "Film Thickness"),
            TermEntry("均匀性", ["Uniformity", "Uni"], self.CATEGORY_PARAMETER,
                     "薄膜或工艺的均匀性",
                     "Uniformity"),
            TermEntry("折射率", ["RI", "Index"], self.CATEGORY_PARAMETER,
                     "薄膜折射率",
                     "Refractive Index"),

            # 质量相关
            TermEntry("良率", ["Yield"], self.CATEGORY_QUALITY,
                     "合格品占总生产品的比例",
                     "Yield"),
            TermEntry("缺陷密度", ["Defect Density", "DD"], self.CATEGORY_QUALITY,
                     "单位面积缺陷数量",
                     "Defect Density"),
            TermEntry("CPK", ["Process Capability"], self.CATEGORY_QUALITY,
                     "过程能力指数",
                     "Process Capability Index"),
            TermEntry("良率工程师", ["YE", "Yield Engineer"], self.CATEGORY_QUALITY,
                     "负责良率提升的工程师",
                     "Yield Engineer"),
            TermEntry("工艺工程师", ["PE", "Process Engineer"], self.CATEGORY_QUALITY,
                     "负责工艺开发和优化的工程师",
                     "Process Engineer"),
            TermEntry("设备工程师", ["EE", "Equipment Engineer"], self.CATEGORY_QUALITY,
                     "负责设备维护的工程师",
                     "Equipment Engineer"),

            # 材料相关
            TermEntry("光刻胶", ["Photoresist", "PR", "抗蚀剂"], self.CATEGORY_MATERIAL,
                     "光敏材料，用于图案转移",
                     "Photoresist"),
            TermEntry("硅片", ["Wafer", "晶圆"], self.CATEGORY_MATERIAL,
                     "半导体制造的基础材料",
                     "Wafer"),
            TermEntry("二氧化硅", ["SiO2", "氧化硅"], self.CATEGORY_MATERIAL,
                     "常见的绝缘材料",
                     "Silicon Dioxide"),
            TermEntry("氮化硅", ["SiN", "Silicon Nitride"], self.CATEGORY_MATERIAL,
                     "常用的钝化材料",
                     "Silicon Nitride"),
            TermEntry("多晶硅", ["Poly-Si", "Polysilicon"], self.CATEGORY_MATERIAL,
                     "用于栅极和导线的材料",
                     "Polysilicon"),
        ]

        # 构建索引
        for term_entry in terms:
            self._add_term(term_entry)

    def _add_term(self, term_entry: TermEntry):
        """添加术语到词典"""
        # 主术语
        self._terms[term_entry.term] = term_entry

        # 别名索引
        for alias in term_entry.aliases:
            self._alias_to_term[alias.lower()] = term_entry.term
            self._alias_to_term[alias] = term_entry.term

        # 分类索引
        if term_entry.category not in self._category_terms:
            self._category_terms[term_entry.category] = set()
        self._category_terms[term_entry.category].add(term_entry.term)

    def normalize(self, text: str) -> str:
        """
        术语标准化
        将文本中的别名替换为标准术语

        Args:
            text: 输入文本

        Returns:
            标准化后的文本
        """
        result = text
        for alias, standard_term in self._alias_to_term.items():
            # 使用正则表达式进行单词边界匹配
            pattern = re.compile(r'\b' + re.escape(alias) + r'\b', re.IGNORECASE)
            result = pattern.sub(standard_term, result)
        return result

    def expand_query(self, query: str) -> List[str]:
        """
        扩展查询
        将查询词扩展为包含同义词的查询列表

        Args:
            query: 原始查询

        Returns:
            扩展后的查询列表
        """
        expanded = [query]
        query_lower = query.lower()

        # 检查是否有标准术语
        if query_lower in self._alias_to_term:
            standard_term = self._alias_to_term[query_lower]
            term_entry = self._terms[standard_term]
            # 添加所有别名
            expanded.extend(term_entry.aliases)
        elif query in self._terms:
            # 查询本身就是标准术语
            term_entry = self._terms[query]
            expanded.extend(term_entry.aliases)

        # 去重
        return list(set(expanded))

    def find_terms(self, text: str) -> List[Tuple[str, TermEntry]]:
        """
        在文本中查找术语

        Args:
            text: 输入文本

        Returns:
            [(匹配文本, 术语条目)] 列表
        """
        found = []
        for term, entry in self._terms.items():
            if term.lower() in text.lower():
                found.append((term, entry))
            else:
                # 检查别名
                for alias in entry.aliases:
                    if alias.lower() in text.lower():
                        found.append((alias, entry))
                        break

        return found

    def get_terms_by_category(self, category: str) -> List[TermEntry]:
        """获取指定分类的所有术语"""
        term_names = self._category_terms.get(category, set())
        return [self._terms[name] for name in term_names]

    def get_all_categories(self) -> List[str]:
        """获取所有分类"""
        return list(self._category_terms.keys())

    def search(self, keyword: str) -> List[TermEntry]:
        """
        搜索术语

        Args:
            keyword: 搜索关键词

        Returns:
            匹配的术语列表
        """
        keyword_lower = keyword.lower()
        results = []

        for term, entry in self._terms.items():
            if (keyword_lower in term.lower() or
                keyword_lower in entry.description.lower() or
                keyword_lower in entry.english.lower()):
                results.append(entry)
            else:
                # 检查别名
                for alias in entry.aliases:
                    if keyword_lower in alias.lower():
                        results.append(entry)
                        break

        return results


# 单例
semiconductor_terms = SemiconductorTerms()
