# OCR识别模块使用说明

## 概述

OCR模块集成PaddleOCR引擎，支持识别图片中的文字，并自动提取设备型号、参数标签等信息，识别结果可存入向量数据库用于后续检索。

## 功能特性

- ✅ 支持多种图片格式：JPG, PNG, BMP, TIFF, GIF, WebP
- ✅ 自动提取设备型号、零件号
- ✅ 自动提取技术参数（压力、温度、流量等）
- ✅ 图片预处理优化（适合扫描件）
- ✅ 批量图片识别
- ✅ Base64图片识别
- ✅ OCR结果自动存入向量数据库

## 安装依赖

```bash
# 安装PaddleOCR（首次使用需要）
pip install paddleocr -i https://pypi.tuna.tsinghua.edu.cn/simple

# 可选：安装GPU版本以获得更快识别速度
# pip install paddlepaddle-gpu
```

## API端点

### 1. 获取OCR服务状态

**请求**：
```http
GET /api/ocr/status
```

**响应**：
```json
{
  "available": true,
  "supported_formats": ["jpg", "jpeg", "png", "bmp", "tiff", "tif", "gif", "webp"],
  "message": "OCR服务运行正常"
}
```

### 2. 单图片OCR识别

**请求**：
```http
POST /api/ocr/recognize
Content-Type: multipart/form-data

file: <图片文件>
category: 工艺文档
tags: 设备,参数表
preprocess: false
save_to_vector: true
```

**curl示例**：
```bash
curl -X POST "http://localhost:8000/api/ocr/recognize" \
  -F "file=@device_photo.jpg" \
  -F "category=设备文档" \
  -F "tags=泵,参数" \
  -F "preprocess=true"
```

**响应**：
```json
{
  "success": true,
  "document_id": "uuid-string",
  "text": "设备型号: ABC-1234\n压力: 10.5 MPa\n温度: 85℃",
  "lines": [
    {
      "text": "设备型号: ABC-1234",
      "confidence": 0.95,
      "box": [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    }
  ],
  "equipment_info": {
    "model_numbers": ["ABC-1234"],
    "names": ["高压泵"]
  },
  "parameters": [
    {"name": "压力", "value": "10.5 MPa"},
    {"name": "温度", "value": "85℃"}
  ]
}
```

### 3. Base64图片识别

**请求**：
```http
POST /api/ocr/recognize/base64
Content-Type: application/x-www-form-urlencoded

image_base64=data:image/jpeg;base64,/9j/4AAQ...
category=工艺文档
preprocess=false
```

**curl示例**：
```bash
curl -X POST "http://localhost:8000/api/ocr/recognize/base64" \
  -d "image_base64=$(base64 -i device.jpg)" \
  -d "category=设备文档"
```

### 4. 批量OCR识别

**请求**：
```http
POST /api/ocr/batch
Content-Type: multipart/form-data

files: <图片文件1>
files: <图片文件2>
category: 工艺文档
preprocess: false
```

**curl示例**：
```bash
curl -X POST "http://localhost:8000/api/ocr/batch" \
  -F "files=@photo1.jpg" \
  -F "files=@photo2.jpg" \
  -F "files=@drawing.png" \
  -F "category=设备档案"
```

**响应**：
```json
{
  "total": 3,
  "success": 2,
  "failed": 1,
  "results": [
    {
      "success": true,
      "document_id": "...",
      "text": "...",
      "equipment_info": {...},
      "parameters": [...]
    }
  ]
}
```

### 5. 获取OCR文档详情

**请求**：
```http
GET /api/ocr/document/{document_id}
```

**响应**：
```json
{
  "id": "uuid-string",
  "filename": "device_photo.jpg",
  "title": "设备型号: ABC-1234",
  "content": "## 识别文本\n设备型号: ABC-1234\n...",
  "category": "工艺文档",
  "tags": "设备,参数表",
  "file_type": "jpg",
  "created_at": "2024-01-15T10:30:00"
}
```

## 使用场景示例

### 场景1：识别设备铭牌照片

```python
import requests

# 上传设备铭牌照片
with open("pump_nameplate.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/ocr/recognize",
        files={"file": f},
        data={
            "category": "设备铭牌",
            "tags": "泵,高压泵",
            "preprocess": "true"  # 启用预处理提高识别率
        }
    )

result = response.json()
print(f"识别型号: {result['equipment_info']['model_numbers']}")
print(f"技术参数: {result['parameters']}")
```

### 场景2：批量处理工艺图纸

```python
import requests
from pathlib import Path

# 批量上传工艺图纸
files = []
for img_path in Path("drawings/").glob("*.jpg"):
    files.append(("files", open(img_path, "rb")))

response = requests.post(
    "http://localhost:8000/api/ocr/batch",
    files=files,
    data={"category": "工艺图纸", "preprocess": "true"}
)

results = response.json()
print(f"成功: {results['success']}, 失败: {results['failed']}")
```

### 场景3：移动端Base64上传

```javascript
// 移动端拍照后Base64上传
const reader = new FileReader();
reader.readAsDataURL(file);
reader.onload = () => {
    const base64Image = reader.result;
    
    fetch('/api/ocr/recognize/base64', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: `image_base64=${encodeURIComponent(base64Image)}&category=现场照片`
    })
    .then(r => r.json())
    .then(data => {
        console.log('识别结果:', data.text);
        console.log('设备信息:', data.equipment_info);
    });
};
```

## 支持的设备信息提取

### 自动识别的型号格式
- `ABC-1234` - 标准型号格式
- `ABC1234X` - 紧凑格式
- `AB-CD-1234` - 多级型号
- 标签："型号: XXX" 或 "Model: XXX"
- 零件号："PN: XXX" 或 "Part No: XXX"

### 自动识别的技术参数
- 物理参数：压力、温度、流量、功率、电压、电流、转速、尺寸、规格
- 数值+单位：如 `10.5 MPa`, `85℃`, `50 kW`
- 标签:值格式：如 `额定功率: 75kW`

## 数据结构说明

### OCR结果结构

```python
{
    "success": True,           # 识别是否成功
    "document_id": "uuid",     # 文档ID
    "text": "完整文本",         # 识别的完整文字
    "lines": [                 # 每行识别结果
        {
            "text": "行文本",
            "confidence": 0.95,  # 置信度 0-1
            "box": [[x,y], ...]  # 文字框坐标
        }
    ],
    "equipment_info": {        # 设备信息
        "model_numbers": [],   # 型号列表
        "names": []            # 设备名称列表
    },
    "parameters": [            # 参数列表
        {"name": "压力", "value": "10.5 MPa"}
    ]
}
```

### 向量库存储格式

OCR结果以结构化文本形式存入向量库：

```
## 识别文本
[识别的完整文字]

## 设备信息
型号: ABC-1234
设备名称: 高压泵

## 技术参数
- 压力: 10.5 MPa
- 温度: 85℃
- 功率: 50 kW
```

元数据包含：
- `source_type`: "ocr_image"
- `equipment_info`: 设备信息字典
- `parameters`: 参数列表

## 运行测试

```bash
# 安装测试依赖
pip install pytest pytest-asyncio httpx

# 运行OCR测试
cd backend
pytest tests/test_ocr.py -v

# 运行特定测试
pytest tests/test_ocr.py::TestOCRService::test_recognize_image -v
```

## 性能优化建议

1. **启用预处理**：扫描件建议开启 `preprocess=true`
2. **批量处理**：多张图片使用批量接口减少HTTP开销
3. **图片尺寸**：建议图片宽度不超过2000像素
4. **图片质量**：JPEG质量建议70-85%，平衡大小和清晰度

## 故障排查

### OCR引擎未初始化
```
错误: OCR引擎未初始化，请安装PaddleOCR
解决: pip install paddleocr
```

### 图片读取失败
```
错误: 无法读取图片文件
解决: 检查图片格式是否支持，图片是否损坏
```

### 识别结果为空
- 检查图片清晰度
- 尝试开启预处理 `preprocess=true`
- 检查文字方向（支持0/90/180/270度）

## 更新日志

### v1.0.0
- 初始版本发布
- 集成PaddleOCR中文识别
- 支持设备型号自动提取
- 支持技术参数自动提取
- 支持批量识别和Base64识别