"""
OCR API路由 - 图片文字识别接口
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
import uuid
import os
import json
from datetime import datetime

from models.database import get_db, Document, UserActivity
from services.ocr_service import get_ocr_service, OCRService
from services.vector_store import VectorStore

router = APIRouter(prefix="/api/ocr", tags=["OCR识别"])

# 数据模型
class OCRRequest(BaseModel):
    document_id: Optional[str] = None
    preprocess: bool = False
    save_to_vector_store: bool = True

class OCRResponse(BaseModel):
    success: bool
    document_id: Optional[str] = None
    text: str = ""
    lines: List[dict] = []
    equipment_info: dict = {}
    parameters: List[dict] = []
    error: Optional[str] = None

class BatchOCRResponse(BaseModel):
    total: int
    success: int
    failed: int
    results: List[OCRResponse]

# 支持的图片格式
SUPPORTED_IMAGE_TYPES = ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif', 'gif', 'webp']

@router.post("/recognize", response_model=OCRResponse)
async def recognize_image(
    file: UploadFile = File(...),
    category: str = Form("工艺文档"),
    tags: str = Form(""),
    preprocess: bool = Form(False),
    save_to_vector: bool = Form(True),
    db: Session = Depends(get_db)
):
    """
    上传图片并执行OCR识别
    
    - **file**: 图片文件 (jpg, png, bmp等)
    - **category**: 文档分类
    - **tags**: 标签
    - **preprocess**: 是否预处理图片
    - **save_to_vector**: 是否保存到向量库
    """
    ocr_service = get_ocr_service()
    
    # 检查OCR引擎
    if not ocr_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="OCR引擎未初始化，请安装PaddleOCR: pip install paddleocr"
        )
    
    # 验证文件类型
    ext = file.filename.split('.')[-1].lower()
    if ext not in SUPPORTED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的图片格式: {ext}。支持的格式: {', '.join(SUPPORTED_IMAGE_TYPES)}"
        )
    
    try:
        # 生成文档ID
        doc_id = str(uuid.uuid4())
        
        # 保存上传的文件
        file_path = f"uploads/ocr_{doc_id}_{file.filename}"
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 预处理（如果需要）
        if preprocess:
            file_path = ocr_service.preprocess_image(file_path)
        
        # 执行OCR识别
        result = ocr_service.recognize_image(file_path)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "OCR识别失败"))
        
        # 构建结构化内容
        structured_content = build_structured_content(result)
        
        # 保存到数据库
        doc = Document(
            id=doc_id,
            filename=file.filename,
            title=extract_title(result) or file.filename,
            content=structured_content,
            category=category,
            tags=tags,
            file_path=file_path,
            file_size=len(content),
            file_type=ext,
            status='active'
        )
        db.add(doc)
        
        # 保存到向量库
        if save_to_vector:
            vector_store = VectorStore()
            vector_store.add_document(doc_id, structured_content, {
                "title": doc.title,
                "category": category,
                "tags": tags,
                "source_type": "ocr_image",
                "equipment_info": result.get("equipment_info", {}),
                "parameters": result.get("parameters", [])
            })
        
        # 记录活动
        activity = UserActivity(
            user_id="anonymous",
            activity_type="upload",
            details=json.dumps({
                "doc_id": doc_id,
                "filename": file.filename,
                "type": "ocr_image",
                "text_length": len(result.get("text", ""))
            })
        )
        db.add(activity)
        db.commit()
        
        return OCRResponse(
            success=True,
            document_id=doc_id,
            text=result.get("text", ""),
            lines=result.get("lines", []),
            equipment_info=result.get("equipment_info", {}),
            parameters=result.get("parameters", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")

@router.post("/recognize/base64")
async def recognize_base64(
    image_base64: str = Form(...),
    category: str = Form("工艺文档"),
    preprocess: bool = Form(False),
    db: Session = Depends(get_db)
):
    """
    接收Base64编码的图片并执行OCR识别
    
    - **image_base64**: Base64编码的图片数据
    - **category**: 文档分类
    - **preprocess**: 是否预处理图片
    """
    import base64
    
    ocr_service = get_ocr_service()
    
    if not ocr_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="OCR引擎未初始化"
        )
    
    try:
        # 解码Base64
        try:
            # 移除可能存在的data URL前缀
            if ',' in image_base64:
                image_base64 = image_base64.split(',')[1]
            image_bytes = base64.b64decode(image_base64)
        except Exception:
            raise HTTPException(status_code=400, detail="无效的Base64数据")
        
        # 执行OCR
        result = ocr_service.recognize_bytes(image_bytes)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "OCR识别失败"))
        
        # 保存到数据库
        doc_id = str(uuid.uuid4())
        structured_content = build_structured_content(result)
        
        doc = Document(
            id=doc_id,
            filename=f"ocr_base64_{doc_id}.jpg",
            title=extract_title(result) or "OCR识别结果",
            content=structured_content,
            category=category,
            file_path="",
            file_size=len(image_bytes),
            file_type="jpg",
            status='active'
        )
        db.add(doc)
        
        # 保存到向量库
        vector_store = VectorStore()
        vector_store.add_document(doc_id, structured_content, {
            "title": doc.title,
            "category": category,
            "source_type": "ocr_base64"
        })
        
        # 记录活动
        activity = UserActivity(
            user_id="anonymous",
            activity_type="upload",
            details=json.dumps({
                "doc_id": doc_id,
                "type": "ocr_base64",
                "text_length": len(result.get("text", ""))
            })
        )
        db.add(activity)
        db.commit()
        
        return OCRResponse(
            success=True,
            document_id=doc_id,
            text=result.get("text", ""),
            lines=result.get("lines", []),
            equipment_info=result.get("equipment_info", {}),
            parameters=result.get("parameters", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")

@router.post("/batch", response_model=BatchOCRResponse)
async def batch_recognize(
    files: List[UploadFile] = File(...),
    category: str = Form("工艺文档"),
    preprocess: bool = Form(False),
    db: Session = Depends(get_db)
):
    """
    批量OCR识别多张图片
    
    - **files**: 图片文件列表
    - **category**: 文档分类
    - **preprocess**: 是否预处理图片
    """
    ocr_service = get_ocr_service()
    
    if not ocr_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="OCR引擎未初始化"
        )
    
    results = []
    success_count = 0
    failed_count = 0
    
    for file in files:
        ext = file.filename.split('.')[-1].lower()
        if ext not in SUPPORTED_IMAGE_TYPES:
            results.append(OCRResponse(
                success=False,
                error=f"不支持的格式: {ext}"
            ))
            failed_count += 1
            continue
        
        try:
            doc_id = str(uuid.uuid4())
            file_path = f"uploads/ocr_{doc_id}_{file.filename}"
            
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            if preprocess:
                file_path = ocr_service.preprocess_image(file_path)
            
            result = ocr_service.recognize_image(file_path)
            
            if result["success"]:
                structured_content = build_structured_content(result)
                
                # 保存到数据库
                doc = Document(
                    id=doc_id,
                    filename=file.filename,
                    title=extract_title(result) or file.filename,
                    content=structured_content,
                    category=category,
                    file_path=file_path,
                    file_size=len(content),
                    file_type=ext,
                    status='active'
                )
                db.add(doc)
                
                # 保存到向量库
                vector_store = VectorStore()
                vector_store.add_document(doc_id, structured_content, {
                    "title": doc.title,
                    "category": category,
                    "source_type": "ocr_image"
                })
                
                results.append(OCRResponse(
                    success=True,
                    document_id=doc_id,
                    text=result.get("text", ""),
                    lines=result.get("lines", []),
                    equipment_info=result.get("equipment_info", {}),
                    parameters=result.get("parameters", [])
                ))
                success_count += 1
            else:
                results.append(OCRResponse(
                    success=False,
                    error=result.get("error", "识别失败")
                ))
                failed_count += 1
                
        except Exception as e:
            results.append(OCRResponse(
                success=False,
                error=str(e)
            ))
            failed_count += 1
    
    # 记录批量活动
    activity = UserActivity(
        user_id="anonymous",
        activity_type="upload",
        details=json.dumps({
            "type": "ocr_batch",
            "total": len(files),
            "success": success_count,
            "failed": failed_count
        })
    )
    db.add(activity)
    db.commit()
    
    return BatchOCRResponse(
        total=len(files),
        success=success_count,
        failed=failed_count,
        results=results
    )

@router.get("/status")
async def ocr_status():
    """获取OCR引擎状态"""
    ocr_service = get_ocr_service()
    return {
        "available": ocr_service.is_available(),
        "supported_formats": SUPPORTED_IMAGE_TYPES,
        "message": "OCR服务运行正常" if ocr_service.is_available() else "OCR引擎未初始化"
    }

@router.get("/document/{doc_id}")
async def get_ocr_document(doc_id: str, db: Session = Depends(get_db)):
    """获取OCR文档详情"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    return {
        "id": doc.id,
        "filename": doc.filename,
        "title": doc.title,
        "content": doc.content,
        "category": doc.category,
        "tags": doc.tags,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "created_at": doc.created_at.isoformat()
    }

# 辅助函数
def extract_title(ocr_result: dict) -> Optional[str]:
    """从OCR结果中提取标题"""
    lines = ocr_result.get("lines", [])
    if not lines:
        return None
    
    # 找第一行较长且置信度高的文本作为标题
    for line in lines[:3]:  # 只看前3行
        text = line.get("text", "").strip()
        confidence = line.get("confidence", 0)
        if len(text) >= 3 and len(text) <= 50 and confidence > 0.8:
            return text
    
    return None

def build_structured_content(ocr_result: dict) -> str:
    """构建结构化的OCR内容"""
    sections = []
    
    # 识别文本
    text = ocr_result.get("text", "").strip()
    if text:
        sections.append("## 识别文本\n" + text)
    
    # 设备信息
    equipment = ocr_result.get("equipment_info", {})
    if equipment.get("model_numbers") or equipment.get("names"):
        sections.append("## 设备信息")
        if equipment.get("model_numbers"):
            sections.append("型号: " + ", ".join(equipment["model_numbers"]))
        if equipment.get("names"):
            sections.append("设备名称: " + ", ".join(equipment["names"]))
    
    # 参数
    parameters = ocr_result.get("parameters", [])
    if parameters:
        sections.append("## 技术参数")
        for param in parameters[:10]:  # 最多10个
            sections.append(f"- {param['name']}: {param['value']}")
    
    return "\n\n".join(sections)