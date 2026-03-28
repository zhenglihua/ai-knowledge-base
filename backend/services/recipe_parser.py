"""
Recipe 配方解析服务
v0.4.0
半导体工艺配方解析，提取关键参数
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import re
import json


@dataclass
class RecipeParameter:
    """配方参数"""
    name: str  # 参数名称
    value: str  # 参数值
    unit: str  # 单位
    category: str  # 分类（温度/时间/压力等）
    description: str  # 描述


@dataclass
class RecipeStep:
    """配方步骤"""
    step_number: int  # 步骤编号
    name: str  # 步骤名称
    parameters: List[RecipeParameter]  # 参数列表
    duration: Optional[str]  # 持续时间
    description: str  # 步骤描述


@dataclass
class Recipe:
    """完整配方"""
    recipe_id: str
    recipe_name: str
    equipment: str  # 设备型号
    product: str  # 产品/晶圆类型
    revision: str  # 版本号
    author: str  # 创建人
    created_date: str  # 创建日期
    steps: List[RecipeStep]  # 步骤列表
    raw_content: str  # 原始内容
    metadata: Dict[str, Any]  # 其他元数据


class RecipeParser:
    """
    Recipe 配方解析器
    支持半导体设备 Recipe 文件解析
    """

    # 常见设备品牌
    EQUIPMENT_PATTERNS = {
        "AMAT": r"Applied Materials|AMAT",
        "TEL": r"Tokyo Electron|TEL",
        "LAM": r"Lam Research|LAM",
        "ASML": r"ASML",
        " Nikon": r"Nikon",
        "Canon": r"Canon",
    }

    # 参数分类关键词
    PARAM_CATEGORIES = {
        "温度": [r"temp", r"温度", r"therm", r"heat"],
        "时间": [r"time", r"时间", r"duration", r"sec", r"min", r"ms"],
        "压力": [r"pressure", r"压力", r"press", r"torr", r"mT", r"pa"],
        "功率": [r"power", r"功率", r"rf", r"watt"],
        "流量": [r"flow", r"流量", r"sccm", r"slm"],
        "电压": [r"voltage", r"电压", r"volt", r"v"],
        "电流": [r"current", r"电流", r"amp"],
        "功率密度": [r"power density", r"功率密度"],
        "频率": [r"frequency", r"频率", r"hz", r"mhz"],
    }

    def __init__(self):
        self.recipe_patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict:
        """编译常用模式"""
        return {
            "step_header": re.compile(r"Step[\s_-]?(\d+)", re.IGNORECASE),
            "parameter": re.compile(r"(\w+)[\s=:]+([\d.]+)\s*(\w+)?"),
            "temperature": re.compile(r"(\d+\.?\d*)\s*(°?C|celsius)", re.IGNORECASE),
            "time": re.compile(r"(\d+\.?\d*)\s*(sec|min|ms|s|m)", re.IGNORECASE),
            "pressure": re.compile(r"(\d+\.?\d*)\s*(torr|mT|mbar|pa)", re.IGNORECASE),
            "flow": re.compile(r"(\d+\.?\d*)\s*(sccm|slm)", re.IGNORECASE),
        }

    def parse(self, content: str, file_name: str = "") -> Recipe:
        """
        解析 Recipe 文件

        Args:
            content: 文件内容
            file_name: 文件名

        Returns:
            Recipe 对象
        """
        # 检测设备类型
        equipment = self._detect_equipment(content)

        # 提取元数据
        metadata = self._extract_metadata(content, file_name)

        # 解析步骤
        steps = self._parse_steps(content)

        return Recipe(
            recipe_id=metadata.get("recipe_id", file_name),
            recipe_name=metadata.get("recipe_name", file_name),
            equipment=equipment,
            product=metadata.get("product", ""),
            revision=metadata.get("revision", ""),
            author=metadata.get("author", ""),
            created_date=metadata.get("date", ""),
            steps=steps,
            raw_content=content,
            metadata=metadata
        )

    def _detect_equipment(self, content: str) -> str:
        """检测设备类型"""
        for brand, pattern in self.EQUIPMENT_PATTERNS.items():
            if re.search(pattern, content):
                return brand
        return "Unknown"

    def _extract_metadata(self, content: str, file_name: str) -> Dict[str, str]:
        """提取元数据"""
        metadata = {}

        # 尝试从内容中提取
        patterns = {
            "recipe_id": r"Recipe[\s_-]?ID:?\s*(\S+)",
            "recipe_name": r"Reipe[\s_-]?Name:?\s*(.+?)(?:\n|$)",
            "product": r"Product:?\s*(.+?)(?:\n|$)",
            "revision": r"Rev[\.isio]:?\s*(\S+)",
            "author": r"Author:?\s*(\S+)",
            "date": r"Date:?\s*(\d{4}[-/]\d{2}[-/]\d{2})",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                metadata[key] = match.group(1).strip()

        if not metadata.get("recipe_name"):
            metadata["recipe_name"] = file_name

        return metadata

    def _parse_steps(self, content: str) -> List[RecipeStep]:
        """解析配方步骤"""
        steps = []
        lines = content.split("\n")

        current_step = None
        current_params = []

        for line in lines:
            line = line.strip()

            # 检测步骤头
            step_match = re.match(r"Step[\s_-]?(\d+)[\s:-]*(.*)", line, re.IGNORECASE)
            if step_match:
                # 保存之前的步骤
                if current_step is not None:
                    steps.append(RecipeStep(
                        step_number=current_step,
                        name=f"Step {current_step}",
                        parameters=current_params,
                        duration=self._extract_duration(current_params),
                        description=""
                    ))

                current_step = int(step_match.group(1))
                current_params = []
                continue

            # 解析参数行
            if line and "=" in line:
                param = self._parse_parameter_line(line)
                if param:
                    current_params.append(param)

        # 保存最后一个步骤
        if current_step is not None:
            steps.append(RecipeStep(
                step_number=current_step,
                name=f"Step {current_step}",
                parameters=current_params,
                duration=self._extract_duration(current_params),
                description=""
            ))

        return steps

    def _parse_parameter_line(self, line: str) -> Optional[RecipeParameter]:
        """解析参数行"""
        # 格式: NAME = VALUE UNIT 或 NAME: VALUE UNIT
        match = re.match(r"(\w+)[\s=:]+([\d.e+-]+)\s*(\w+)?", line)
        if match:
            name = match.group(1)
            value = match.group(2)
            unit = match.group(3) or ""

            # 分类参数
            category = self._categorize_parameter(name, value, unit)

            return RecipeParameter(
                name=name,
                value=value,
                unit=unit,
                category=category,
                description=""
            )

        # 另一种格式: NAME VALUE UNIT
        match = re.match(r"(\w+)\s+([\d.e+-]+)\s+(\w+)", line)
        if match:
            return RecipeParameter(
                name=match.group(1),
                value=match.group(2),
                unit=match.group(3),
                category=self._categorize_parameter(match.group(1), match.group(2), match.group(3)),
                description=""
            )

        return None

    def _categorize_parameter(self, name: str, value: str, unit: str) -> str:
        """分类参数"""
        name_lower = name.lower()
        unit_lower = unit.lower()

        # 根据单位判断
        if any(u in unit_lower for u in ["c", "°c"]):
            return "温度"
        if any(u in unit_lower for u in ["s", "sec", "min", "ms", "m"]):
            return "时间"
        if any(u in unit_lower for u in ["torr", "mt", "pa", "mbar"]):
            return "压力"
        if any(u in unit_lower for u in ["sccm", "slm"]):
            return "流量"
        if any(u in unit_lower for u in ["w", "kw", "watt"]):
            return "功率"
        if any(u in unit_lower for u in ["v", "volt"]):
            return "电压"
        if any(u in unit_lower for u in ["a", "amp"]):
            return "电流"

        # 根据名称判断
        for category, keywords in self.PARAM_CATEGORIES.items():
            if any(kw in name_lower for kw in keywords):
                return category

        return "其他"

    def _extract_duration(self, params: List[RecipeParameter]) -> Optional[str]:
        """提取持续时间"""
        for param in params:
            if param.category == "时间":
                return f"{param.value} {param.unit}"
        return None

    def to_dict(self, recipe: Recipe) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "recipe_id": recipe.recipe_id,
            "recipe_name": recipe.recipe_name,
            "equipment": recipe.equipment,
            "product": recipe.product,
            "revision": recipe.revision,
            "author": recipe.author,
            "created_date": recipe.created_date,
            "steps": [
                {
                    "step_number": step.step_number,
                    "name": step.name,
                    "parameters": [
                        {
                            "name": p.name,
                            "value": p.value,
                            "unit": p.unit,
                            "category": p.category
                        }
                        for p in step.parameters
                    ],
                    "duration": step.duration
                }
                for step in recipe.steps
            ],
            "metadata": recipe.metadata
        }


# 单例
recipe_parser = RecipeParser()
