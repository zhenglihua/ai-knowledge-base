"""
AGI 内容生成 API
v0.7.0
思维导图、报告生成、PPT生成
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json

from services.generation import (
    get_mindmap_generator,
    get_report_generator,
    get_pptx_generator,
    ReportType
)
from core.llm import get_llm_service


router = APIRouter(prefix="/api/generation", tags=["AGI内容生成"])


# ========== 思维导图 ==========

class MindMapRequest(BaseModel):
    """思维导图请求"""
    document_id: Optional[str] = None
    document_text: Optional[str] = None
    topic: Optional[str] = None
    max_nodes: int = 20


class MindMapResponse(BaseModel):
    """思维导图响应"""
    success: bool
    data: Dict[str, Any]
    message: str


@router.post("/mindmap", response_model=MindMapResponse)
async def generate_mindmap(request: MindMapRequest):
    """
    生成思维导图

    基于文档内容生成可视化的概念关系图
    """
    try:
        # 获取文档内容
        if request.document_id:
            # TODO: 从数据库获取文档
            document_text = "示例文档内容..."
        elif request.document_text:
            document_text = request.document_text
        else:
            raise HTTPException(status_code=400, detail="需要提供 document_id 或 document_text")

        # 生成思维导图
        llm = get_llm_service()
        generator = get_mindmap_generator(llm)

        result = await generator.generate(
            document_text=document_text,
            max_nodes=request.max_nodes,
            topic=request.topic
        )

        return MindMapResponse(
            success=True,
            data=result,
            message="思维导图生成成功"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mindmap/templates")
async def get_mindmap_templates():
    """获取思维导图模板"""
    templates = [
        {"id": "tree", "name": "树形结构", "description": "适合展示层级关系"},
        {"id": "graph", "name": "网状结构", "description": "适合展示概念关联"},
        {"id": "flowchart", "name": "流程图", "description": "适合展示工艺流程"},
    ]
    return {"templates": templates}


# ========== 报告生成 ==========

class ReportRequest(BaseModel):
    """报告生成请求"""
    report_type: str  # yield_analysis, fault_analysis, equipment_eval 等
    context: Dict[str, Any]  # documents, metadata, data


class ReportResponse(BaseModel):
    """报告响应"""
    success: bool
    content: str  # Markdown 格式
    outline: List[str]  # 报告大纲


@router.post("/report", response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    """
    生成专业报告

    支持: 良率分析报告、故障分析报告(8D)、设备评估报告等
    """
    try:
        # 解析报告类型
        try:
            report_type = ReportType(request.report_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的报告类型: {request.report_type}"
            )

        # 生成报告
        llm = get_llm_service()
        generator = get_report_generator(llm)

        content = await generator.generate(
            report_type=report_type,
            context=request.context
        )

        # 生成大纲
        outline = generator.generate_outline(
            report_type=report_type,
            topic=request.context.get("metadata", {}).get("topic", "")
        )

        return ReportResponse(
            success=True,
            content=content,
            outline=outline
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/templates")
async def get_report_templates():
    """获取支持的报告模板"""
    templates = [
        {
            "type": "yield_analysis",
            "name": "良率分析报告",
            "description": "周/月度良率异常分析"
        },
        {
            "type": "fault_analysis",
            "name": "故障分析报告(8D)",
            "description": "设备故障根因分析"
        },
        {
            "type": "equipment_eval",
            "name": "设备评估报告",
            "description": "设备选型对比评估"
        },
        {
            "type": "change_impact",
            "name": "变更影响分析",
            "description": "工艺变更风险评估"
        },
        {
            "type": "weekly_summary",
            "name": "周报",
            "description": "工作总结与下周计划"
        },
        {
            "type": "training_material",
            "name": "培训材料",
            "description": "基于SOP的操作指南"
        }
    ]
    return {"templates": templates}


# ========== PPT 生成 ==========

class SlideInput(BaseModel):
    """幻灯片输入"""
    title: str
    bullets: List[str]
    content: Optional[str] = None


class PPTRequest(BaseModel):
    """PPT生成请求"""
    title: str
    slides: List[SlideInput]
    theme: str = "professional"


class PPTResponse(BaseModel):
    """PPT响应"""
    success: bool
    file_path: str
    download_url: str
    message: str


@router.post("/pptx", response_model=PPTResponse)
async def generate_pptx(request: PPTRequest):
    """
    生成 PPT 文件

    将报告内容转换为 PowerPoint 演示文稿
    """
    try:
        from services.generation import PPTXGenerator, SlideContent

        generator = get_pptx_generator()

        # 转换幻灯片
        slides = [
            SlideContent(
                title=s.title,
                bullets=s.bullets,
                content=s.content
            )
            for s in request.slides
        ]

        # 生成 PPT
        file_path = await generator.generate(
            title=request.title,
            slides=slides,
            theme=request.theme
        )

        return PPTResponse(
            success=True,
            file_path=file_path,
            download_url=f"/api/generation/download/{file_path.split('/')[-1]}",
            message="PPT生成成功"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pptx/templates")
async def get_pptx_templates():
    """获取 PPT 主题模板"""
    templates = [
        {"id": "professional", "name": "专业蓝", "description": "科技蓝色调，适合商务演示"},
        {"id": "tech", "name": "科技感", "description": "深色背景，适合技术分享"},
        {"id": "simple", "name": "简约白", "description": "简洁清晰，适合培训材料"},
    ]
    return {"templates": templates}


# ========== 批量内容生成 ==========

class BatchGenerateRequest(BaseModel):
    """批量生成请求"""
    document_id: str
    generate_mindmap: bool = True
    generate_summary: bool = True
    generate_report: bool = False
    report_type: Optional[str] = None


class BatchGenerateResponse(BaseModel):
    """批量生成响应"""
    success: bool
    mindmap: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    report: Optional[str] = None
    message: str


@router.post("/batch", response_model=BatchGenerateResponse)
async def batch_generate(request: BatchGenerateRequest):
    """
    批量内容生成

    一次调用生成多种内容: 思维导图 + 摘要 + 报告
    """
    try:
        llm = get_llm_service()
        result = {
            "success": True,
            "mindmap": None,
            "summary": None,
            "report": None,
            "message": ""
        }

        # TODO: 从数据库获取文档内容
        document_text = "文档内容..."

        # 生成思维导图
        if request.generate_mindmap:
            try:
                generator = get_mindmap_generator(llm)
                mindmap = await generator.generate(document_text)
                result["mindmap"] = mindmap
            except Exception as e:
                result["mindmap"] = {"error": str(e)}

        # 生成摘要
        if request.generate_summary:
            try:
                prompt = f"请简要总结以下文档的核心内容（200字以内）：\n\n{document_text[:2000]}"
                summary = llm.generate(prompt)
                result["summary"] = summary
            except Exception as e:
                result["summary"] = f"生成失败: {e}"

        # 生成报告
        if request.generate_report and request.report_type:
            try:
                report_gen = get_report_generator(llm)
                report_type = ReportType(request.report_type)
                context = {
                    "documents": [{"title": "文档", "content": document_text}],
                    "metadata": {},
                    "data": {}
                }
                report = await report_gen.generate(report_type, context)
                result["report"] = report
            except Exception as e:
                result["report"] = f"生成失败: {e}"

        return BatchGenerateResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
