# 文档OCR识别模块

## 完成内容

### 1. 核心服务 (`services/ocr_service.py`)
- **OCRService类**: 基于PaddleOCR的文字识别服务
- **设备信息提取**: 自动识别型号、零件号、设备名称
- **参数标签提取**: 自动提取压力、温度、流量等技术参数
- **图片预处理**: 自适应阈值、降噪优化（适合扫描件）
- **批量识别**: 支持多张图片批量处理
- **单例模式**: `get_ocr_service()` 获取服务实例

### 2. API路由 (`api/ocr.py`)
| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/ocr/status` | GET | 获取OCR服务状态 |
| `/api/ocr/recognize` | POST | 上传图片并OCR识别 |
| `/api/ocr/recognize/base64` | POST | Base64图片识别 |
| `/api/ocr/batch` | POST | 批量图片识别 |
| `/api/ocr/document/{id}` | GET | 获取OCR文档详情 |

### 3. 测试用例 (`tests/test_ocr.py`)
- 单元测试: OCR服务初始化、图片识别、信息提取
- 集成测试: API端点测试、错误处理测试
- 测试覆盖率: 核心功能和API端点

### 4. 使用文档 (`docs/OCR_USAGE.md`)
- API详细说明和curl示例
- 使用场景示例代码（Python/JavaScript）
- 故障排查指南

### 5. 依赖更新 (`requirements.txt`)
```
paddleocr>=2.7.0
opencv-python>=4.8.0
pillow>=10.0.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
httpx>=0.25.0
```

## 项目结构

```
backend/
├── main.py                    # 已更新：注册OCR路由
├── services/
│   ├── ocr_service.py         # 新增：OCR核心服务
│   └── vector_store.py        # 现有：向量存储
├── api/
│   ├── __init__.py
│   ├── ocr.py                 # 新增：OCR API路由
│   ├── conversations.py
│   └── stats.py
├── models/
│   └── database.py            # 现有：复用Document模型
├── tests/
│   └── test_ocr.py            # 新增：OCR测试
├── docs/
│   └── OCR_USAGE.md           # 新增：使用文档
└── requirements.txt           # 已更新：添加OCR依赖
```

## API使用示例

### 单图片识别
```bash
curl -X POST "http://localhost:8000/api/ocr/recognize" \
  -F "file=@device_photo.jpg" \
  -F "category=设备文档" \
  -F "preprocess=true"
```

### 响应示例
```json
{
  "success": true,
  "document_id": "uuid",
  "text": "设备型号: ABC-1234\n压力: 10.5 MPa",
  "lines": [{"text": "...", "confidence": 0.95}],
  "equipment_info": {
    "model_numbers": ["ABC-1234"],
    "names": ["高压泵"]
  },
  "parameters": [
    {"name": "压力", "value": "10.5 MPa"}
  ]
}
```

### 批量识别
```bash
curl -X POST "http://localhost:8000/api/ocr/batch" \
  -F "files=@1.jpg" -F "files=@2.jpg" \
  -F "category=工艺图纸"
```

## 数据流向

```
上传图片 → OCR识别 → 提取设备信息/参数 → 结构化文本 → 向量库存储
```

## 快速开始

1. **安装依赖**
```bash
pip install paddleocr opencv-python pillow
```

2. **启动服务**
```bash
cd backend
uvicorn main:app --reload
```

3. **测试OCR**
```bash
curl http://localhost:8000/api/ocr/status
```

## 运行测试

```bash
pytest tests/test_ocr.py -v
```

## 技术特点

- ✅ FastAPI异步处理
- ✅ PaddleOCR中文识别优化
- ✅ 设备型号/参数自动提取（正则匹配）
- ✅ 扫描件预处理优化
- ✅ 自动存入向量库支持RAG检索
- ✅ 完善的错误处理和测试覆盖