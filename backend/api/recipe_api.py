"""
Recipe 配方管理 API
v0.4.0
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json

from services.recipe_parser import recipe_parser
from core.semi_standards import semi_standard_library


router = APIRouter(prefix="/api/recipe", tags=["Recipe配方"])


class RecipeResponse(BaseModel):
    """配方响应"""
    recipe_id: str
    recipe_name: str
    equipment: str
    product: str
    revision: str
    author: str
    created_date: str
    steps: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class SEMIStandardResponse(BaseModel):
    """SEMI标准响应"""
    code: str
    name: str
    version: str
    category: str
    description: str
    keywords: List[str]


@router.post("/parse", response_model=RecipeResponse)
async def parse_recipe(file: UploadFile = File(...)):
    """
    解析 Recipe 配方文件

    支持上传 Recipe 文件，自动提取参数和步骤
    """
    try:
        content = await file.read()
        text = content.decode("utf-8", errors="ignore")

        recipe = recipe_parser.parse(text, file.filename)
        return recipe_parser.to_dict(recipe)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recipe解析失败: {str(e)}")


@router.post("/parse/text")
async def parse_recipe_text(content: str, file_name: str = "manual_input"):
    """
    解析 Recipe 配方文本（直接传入文本）

    用于测试或剪贴板粘贴场景
    """
    try:
        recipe = recipe_parser.parse(content, file_name)
        return recipe_parser.to_dict(recipe)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recipe解析失败: {str(e)}")


@router.get("/search")
async def search_recipe(keyword: str):
    """
    搜索配方

    根据设备型号、产品类型等搜索配方
    """
    # TODO: 实现配方数据库搜索
    return {
        "results": [],
        "total": 0,
        "message": "配方搜索功能开发中"
    }


@router.get("/standards/search")
async def search_semi_standards(keyword: str) -> Dict[str, Any]:
    """
    搜索 SEMI 标准

    根据关键词搜索匹配的 SEMI 标准
    """
    results = semi_standard_library.search(keyword)

    return {
        "standards": [
            {
                "code": s.code,
                "name": s.name,
                "version": s.version,
                "category": s.category,
                "description": s.description,
                "keywords": s.keywords
            }
            for s in results
        ],
        "total": len(results)
    }


@router.get("/standards/{code}")
async def get_semi_standard(code: str) -> Dict[str, Any]:
    """
    获取 SEMI 标准详情
    """
    standard = semi_standard_library.get_by_code(code)
    if not standard:
        raise HTTPException(status_code=404, detail=f"SEMI标准 {code} 未找到")

    return {
        "code": standard.code,
        "name": standard.name,
        "version": standard.version,
        "category": standard.category,
        "description": standard.description,
        "keywords": standard.keywords
    }


@router.get("/standards/categories")
async def get_semi_standard_categories() -> Dict[str, Any]:
    """
    获取 SEMI 标准分类
    """
    categories = semi_standard_library.get_all_categories()

    category_info = {
        "设备": "Equipment Standards",
        "通信": "Communication Standards",
        "安全": "Safety Standards",
        "材料": "Material Standards",
        "工艺": "Process Standards",
        "测量": "Metrology Standards",
        "工厂": "Factory Standards"
    }

    return {
        "categories": [
            {
                "id": cat,
                "name": category_info.get(cat, cat),
                "description": f"SEMI {cat} 相关标准"
            }
            for cat in categories
        ]
    }


@router.get("/standards/category/{category}")
async def get_semi_standards_by_category(category: str) -> Dict[str, Any]:
    """
    获取指定分类的 SEMI 标准
    """
    standards = semi_standard_library.get_by_category(category)

    return {
        "category": category,
        "standards": [
            {
                "code": s.code,
                "name": s.name,
                "version": s.version,
                "description": s.description
            }
            for s in standards
        ],
        "total": len(standards)
    }


@router.post("/standards/match")
async def match_document_standards(content: str) -> Dict[str, Any]:
    """
    文档匹配 SEMI 标准

    分析文档内容，匹配相关的 SEMI 标准
    """
    matches = semi_standard_library.match_document(content)

    return {
        "matches": [
            {
                "code": s.code,
                "name": s.name,
                "category": s.category,
                "score": score
            }
            for s, score in matches[:10]
        ],
        "total": len(matches)
    }
