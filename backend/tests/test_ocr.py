"""
OCR模块测试用例
运行: pytest tests/test_ocr.py -v
"""
import pytest
import os
import sys
import tempfile
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ocr_service import OCRService, get_ocr_service

# 标记需要PaddleOCR的测试
pytestmark = [
    pytest.mark.skipif(
        not OCRService().is_available(),
        reason="PaddleOCR未安装或未初始化"
    )
]


class TestOCRService:
    """OCR服务单元测试"""
    
    @pytest.fixture
    def ocr_service(self):
        """OCR服务实例"""
        return OCRService()
    
    @pytest.fixture
    def test_image_path(self):
        """创建测试图片"""
        # 创建临时图片
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        # 尝试绘制文字（使用默认字体）
        try:
            font = ImageFont.truetype("/System/Library/Fonts/STHeiti Light.ttc", 24)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 24)
            except:
                font = ImageFont.load_default()
        
        # 绘制测试文字
        draw.text((10, 10), "设备型号: ABC-1234", fill='black', font=font)
        draw.text((10, 50), "压力: 10.5 MPa", fill='black', font=font)
        draw.text((10, 90), "温度: 85 C", fill='black', font=font)
        
        # 保存临时文件
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            img.save(tmp.name)
            return tmp.name
    
    def test_ocr_service_initialization(self, ocr_service):
        """测试OCR服务初始化"""
        assert ocr_service is not None
        # 在未安装PaddleOCR时可能不可用
        if ocr_service.is_available():
            assert ocr_service.ocr is not None
    
    def test_recognize_image(self, ocr_service, test_image_path):
        """测试单图片识别"""
        if not ocr_service.is_available():
            pytest.skip("PaddleOCR未安装")
        
        result = ocr_service.recognize_image(test_image_path)
        
        # 验证结果结构
        assert "success" in result
        assert result["success"] is True
        assert "text" in result
        assert "lines" in result
        assert "equipment_info" in result
        assert "parameters" in result
        
        # 清理
        os.unlink(test_image_path)
    
    def test_recognize_nonexistent_file(self, ocr_service):
        """测试识别不存在的文件"""
        result = ocr_service.recognize_image("/nonexistent/path/image.png")
        
        assert result["success"] is False
        assert "error" in result
        assert "文件不存在" in result["error"]
    
    def test_recognize_bytes(self, ocr_service, test_image_path):
        """测试从字节数据识别"""
        if not ocr_service.is_available():
            pytest.skip("PaddleOCR未安装")
        
        # 读取图片字节
        with open(test_image_path, 'rb') as f:
            image_bytes = f.read()
        
        result = ocr_service.recognize_bytes(image_bytes)
        
        # 验证结果
        assert "success" in result
        assert result["success"] is True
        assert "text" in result
        
        # 清理
        os.unlink(test_image_path)
    
    def test_extract_equipment_info(self, ocr_service):
        """测试设备信息提取"""
        test_text = """
        设备型号: ABC-1234
        备用型号: XYZ-5678
        设备名称: 高压泵
        型号: DEF-9999
        """
        
        equipment_info = ocr_service._extract_equipment_info(test_text)
        
        assert "model_numbers" in equipment_info
        assert "names" in equipment_info
        assert len(equipment_info["model_numbers"]) > 0
    
    def test_extract_parameters(self, ocr_service):
        """测试参数提取"""
        test_text = """
        压力: 10.5 MPa
        温度: 85 ℃
        流量: 100 m³/h
        功率: 50 kW
        电压: 380 V
        """
        
        parameters = ocr_service._extract_parameters(test_text)
        
        assert isinstance(parameters, list)
        assert len(parameters) > 0
        
        # 验证参数结构
        for param in parameters:
            assert "name" in param
            assert "value" in param
    
    def test_preprocess_image(self, ocr_service, test_image_path):
        """测试图片预处理"""
        if not ocr_service.is_available():
            pytest.skip("PaddleOCR未安装")
        
        output_path = test_image_path.replace('.png', '_processed.png')
        result_path = ocr_service.preprocess_image(test_image_path, output_path)
        
        # 验证输出文件存在
        assert os.path.exists(result_path)
        
        # 清理
        os.unlink(test_image_path)
        if os.path.exists(output_path):
            os.unlink(output_path)
    
    def test_batch_recognize(self, ocr_service, test_image_path):
        """测试批量识别"""
        if not ocr_service.is_available():
            pytest.skip("PaddleOCR未安装")
        
        # 创建第二张测试图片
        img2 = Image.new('RGB', (400, 200), color='white')
        img2.save(test_image_path.replace('.png', '_2.png'))
        
        image_paths = [
            test_image_path,
            test_image_path.replace('.png', '_2.png')
        ]
        
        results = ocr_service.batch_recognize(image_paths)
        
        assert len(results) == 2
        for result in results:
            assert "file_path" in result
            assert "success" in result
        
        # 清理
        for path in image_paths:
            if os.path.exists(path):
                os.unlink(path)
    
    def test_singleton(self):
        """测试单例模式"""
        service1 = get_ocr_service()
        service2 = get_ocr_service()
        
        assert service1 is service2


class TestOCRIntegration:
    """OCR集成测试 - 需要完整的FastAPI应用"""
    
    @pytest.fixture(scope="module")
    def client(self):
        """创建FastAPI测试客户端"""
        from fastapi.testclient import TestClient
        from main import app
        
        return TestClient(app)
    
    @pytest.fixture
    def test_image_file(self):
        """创建测试图片文件"""
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/System/Library/Fonts/STHeiti Light.ttc", 24)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 24)
            except:
                font = ImageFont.load_default()
        
        draw.text((10, 10), "型号: TEST-001", fill='black', font=font)
        draw.text((10, 50), "压力: 15.0 MPa", fill='black', font=font)
        
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        return img_buffer
    
    def test_ocr_status_endpoint(self, client):
        """测试OCR状态端点"""
        response = client.get("/api/ocr/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "available" in data
        assert "supported_formats" in data
        assert isinstance(data["supported_formats"], list)
    
    def test_ocr_recognize_endpoint(self, client, test_image_file):
        """测试OCR识别端点"""
        # 跳过如果PaddleOCR不可用
        ocr_service = OCRService()
        if not ocr_service.is_available():
            pytest.skip("PaddleOCR未安装")
        
        files = {
            "file": ("test.png", test_image_file, "image/png")
        }
        data = {
            "category": "测试文档",
            "tags": "测试,OCR"
        }
        
        response = client.post("/api/ocr/recognize", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["success"] is True
        assert "document_id" in result
        assert "text" in result
        assert "equipment_info" in result
        assert "parameters" in result
    
    def test_ocr_recognize_invalid_format(self, client):
        """测试OCR识别无效格式"""
        files = {
            "file": ("test.txt", BytesIO(b"not an image"), "text/plain")
        }
        
        response = client.post("/api/ocr/recognize", files=files)
        
        assert response.status_code == 400
        assert "不支持的图片格式" in response.json()["detail"]
    
    def test_ocr_batch_endpoint(self, client):
        """测试批量OCR端点"""
        ocr_service = OCRService()
        if not ocr_service.is_available():
            pytest.skip("PaddleOCR未安装")
        
        # 创建两个测试图片
        img1 = Image.new('RGB', (200, 100), color='white')
        img2 = Image.new('RGB', (200, 100), color='white')
        
        buffer1 = BytesIO()
        buffer2 = BytesIO()
        img1.save(buffer1, format='PNG')
        img2.save(buffer2, format='PNG')
        buffer1.seek(0)
        buffer2.seek(0)
        
        files = [
            ("files", ("test1.png", buffer1, "image/png")),
            ("files", ("test2.png", buffer2, "image/png"))
        ]
        
        response = client.post("/api/ocr/batch", files=files, data={"category": "测试"})
        
        assert response.status_code == 200
        result = response.json()
        
        assert "total" in result
        assert "success" in result
        assert "failed" in result
        assert "results" in result
        assert result["total"] == 2
    
    def test_ocr_base64_endpoint(self, client):
        """测试Base64图片识别端点"""
        ocr_service = OCRService()
        if not ocr_service.is_available():
            pytest.skip("PaddleOCR未安装")
        
        # 创建测试图片并转为base64
        img = Image.new('RGB', (200, 100), color='white')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        response = client.post(
            "/api/ocr/recognize/base64",
            data={
                "image_base64": img_base64,
                "category": "测试"
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
    
    def test_ocr_document_detail_endpoint(self, client, test_image_file):
        """测试OCR文档详情端点"""
        ocr_service = OCRService()
        if not ocr_service.is_available():
            pytest.skip("PaddleOCR未安装")
        
        # 先上传一个图片
        files = {
            "file": ("test.png", test_image_file, "image/png")
        }
        upload_response = client.post("/api/ocr/recognize", files=files, data={"category": "测试"})
        
        assert upload_response.status_code == 200
        doc_id = upload_response.json()["document_id"]
        
        # 获取文档详情
        response = client.get(f"/api/ocr/document/{doc_id}")
        
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == doc_id
        assert "content" in result
    
    def test_ocr_document_not_found(self, client):
        """测试获取不存在的OCR文档"""
        response = client.get("/api/ocr/document/nonexistent-id")
        
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])