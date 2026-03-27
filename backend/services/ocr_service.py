"""
OCR服务模块 - 基于PaddleOCR
支持设备图纸、工艺照片、扫描件的文字识别
"""
import os
import re
import cv2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import io

# PaddleOCR导入
try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    print("⚠️ PaddleOCR未安装，OCR功能将不可用")

class OCRService:
    """OCR服务 - 识别图片中的文字和设备信息"""
    
    # 设备型号正则表达式模式
    EQUIPMENT_PATTERNS = [
        r'[A-Z]{2,4}-\d{3,5}',           # 如: ABC-1234
        r'[A-Z]{2,4}\d{3,5}[A-Z]?',      # 如: ABC1234X
        r'[A-Z]{1,3}-[A-Z]{1,2}-\d{3,6}', # 如: AB-CD-1234
        r'型号[:：]\s*([A-Z0-9\-]+)',     # 型号: XXX
        r'Model[:：]\s*([A-Z0-9\-]+)',    # Model: XXX
        r'PN[:：]\s*([A-Z0-9\-]+)',       # 零件号
        r'Part\s*No[:：]\s*([A-Z0-9\-]+)', # Part No: XXX
    ]
    
    # 参数标签模式
    PARAMETER_PATTERNS = [
        r'([^:：\n]{2,20})[:：]\s*([^\n]+)',  # 标签: 值
        r'(压力|温度|流量|功率|电压|电流|转速|尺寸|规格)\s*[:：]\s*([0-9.]+\s*[A-Za-z%℃°]+)', # 物理参数
        r'([0-9.]+)\s*(MPa|bar|Pa|kPa|℃|°C|mm|cm|m|kW|W|V|A|Hz|rpm|kg|g)', # 数值+单位
    ]
    
    def __init__(self):
        self.ocr = None
        self._init_ocr()
    
    def _init_ocr(self):
        """初始化PaddleOCR引擎"""
        if not PADDLEOCR_AVAILABLE:
            return
        
        try:
            # 使用轻量级中文模型
            self.ocr = PaddleOCR(
                use_angle_cls=True,           # 方向分类器
                lang='ch',                    # 中文模型
                show_log=False,               # 不显示日志
                use_gpu=False                 # CPU运行
            )
            print("✅ PaddleOCR引擎初始化成功")
        except Exception as e:
            print(f"⚠️ PaddleOCR初始化失败: {e}")
            self.ocr = None
    
    def is_available(self) -> bool:
        """检查OCR服务是否可用"""
        return self.ocr is not None
    
    def recognize_image(self, image_path: str) -> Dict[str, Any]:
        """
        识别图片中的文字
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            OCR结果字典
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "OCR引擎未初始化，请安装PaddleOCR: pip install paddleocr"
            }
        
        try:
            # 验证文件
            if not os.path.exists(image_path):
                return {"success": False, "error": f"文件不存在: {image_path}"}
            
            # 读取图片
            img = cv2.imread(image_path)
            if img is None:
                return {"success": False, "error": "无法读取图片文件"}
            
            # 执行OCR识别
            result = self.ocr.ocr(image_path, cls=True)
            
            if not result or not result[0]:
                return {
                    "success": True,
                    "text": "",
                    "lines": [],
                    "equipment_info": {},
                    "parameters": []
                }
            
            # 解析结果
            lines = []
            full_text = []
            
            for line in result[0]:
                box = line[0]  # 文本框坐标
                text = line[1][0]  # 识别的文本
                confidence = line[1][1]  # 置信度
                
                lines.append({
                    "text": text,
                    "confidence": float(confidence),
                    "box": box
                })
                full_text.append(text)
            
            full_text_str = "\n".join(full_text)
            
            # 提取设备信息
            equipment_info = self._extract_equipment_info(full_text_str)
            
            # 提取参数
            parameters = self._extract_parameters(full_text_str)
            
            return {
                "success": True,
                "text": full_text_str,
                "lines": lines,
                "equipment_info": equipment_info,
                "parameters": parameters
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"OCR识别失败: {str(e)}"
            }
    
    def recognize_bytes(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        从字节数据识别图片文字
        
        Args:
            image_bytes: 图片二进制数据
            
        Returns:
            OCR结果字典
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "OCR引擎未初始化"
            }
        
        try:
            # 从字节数据创建临时文件
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                tmp.write(image_bytes)
                tmp_path = tmp.name
            
            # 执行识别
            result = self.recognize_image(tmp_path)
            
            # 清理临时文件
            os.unlink(tmp_path)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"处理图片数据失败: {str(e)}"
            }
    
    def _extract_equipment_info(self, text: str) -> Dict[str, Any]:
        """
        从文本中提取设备信息
        
        Args:
            text: OCR识别的完整文本
            
        Returns:
            设备信息字典
        """
        equipment_info = {
            "model_numbers": [],
            "part_numbers": [],
            "serial_numbers": [],
            "names": []
        }
        
        # 提取型号
        for pattern in self.EQUIPMENT_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                if isinstance(matches[0], tuple):
                    for match in matches:
                        if isinstance(match, tuple):
                            equipment_info["model_numbers"].extend([m for m in match if m])
                        else:
                            equipment_info["model_numbers"].append(match)
                else:
                    equipment_info["model_numbers"].extend(matches)
        
        # 去重
        equipment_info["model_numbers"] = list(set(equipment_info["model_numbers"]))
        
        # 提取设备名称（简单的启发式方法）
        name_keywords = ['设备', '机器', '装置', '系统', '泵', '阀', '电机', '控制器', '传感器']
        for keyword in name_keywords:
            pattern = f'([^\n]{{0,20}}{keyword}[^\n]{{0,20}})'
            matches = re.findall(pattern, text)
            equipment_info["names"].extend(matches)
        
        equipment_info["names"] = list(set(equipment_info["names"]))[:5]  # 最多保留5个
        
        return equipment_info
    
    def _extract_parameters(self, text: str) -> List[Dict[str, str]]:
        """
        从文本中提取参数标签和值
        
        Args:
            text: OCR识别的完整文本
            
        Returns:
            参数列表
        """
        parameters = []
        
        for pattern in self.PARAMETER_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    param_name = match[0].strip()
                    param_value = match[1].strip()
                    
                    # 过滤掉太短或太长的
                    if 1 <= len(param_name) <= 30 and len(param_value) <= 50:
                        parameters.append({
                            "name": param_name,
                            "value": param_value
                        })
        
        # 去重
        seen = set()
        unique_params = []
        for param in parameters:
            key = f"{param['name']}:{param['value']}"
            if key not in seen:
                seen.add(key)
                unique_params.append(param)
        
        return unique_params[:20]  # 最多返回20个参数
    
    def preprocess_image(self, image_path: str, output_path: Optional[str] = None) -> str:
        """
        预处理图片以提高OCR识别率
        
        Args:
            image_path: 原始图片路径
            output_path: 输出路径（可选）
            
        Returns:
            预处理后的图片路径
        """
        try:
            # 读取图片
            img = cv2.imread(image_path)
            if img is None:
                return image_path
            
            # 转换为灰度
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 自适应阈值处理（适合扫描件）
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # 降噪
            denoised = cv2.fastNlMeansDenoising(binary, None, 10, 7, 21)
            
            # 保存处理后的图片
            if output_path is None:
                base, ext = os.path.splitext(image_path)
                output_path = f"{base}_processed{ext}"
            
            cv2.imwrite(output_path, denoised)
            return output_path
            
        except Exception as e:
            print(f"图片预处理失败: {e}")
            return image_path
    
    def batch_recognize(self, image_paths: List[str]) -> List[Dict[str, Any]]:
        """
        批量识别多张图片
        
        Args:
            image_paths: 图片路径列表
            
        Returns:
            OCR结果列表
        """
        results = []
        for path in image_paths:
            result = self.recognize_image(path)
            result["file_path"] = path
            results.append(result)
        return results


# 单例实例
_ocr_service = None

def get_ocr_service() -> OCRService:
    """获取OCR服务单例"""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service