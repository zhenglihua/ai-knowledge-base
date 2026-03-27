#!/bin/bash
# 演示数据上传脚本

API_BASE="http://localhost:8000/api"
DATA_DIR="test_data"

echo "📤 上传演示数据..."
echo ""

# 检查服务
if ! curl -s "$API_BASE/health" > /dev/null; then
    echo "❌ 后端服务未启动"
    exit 1
fi

# 上传文档
for file in $DATA_DIR/*.txt; do
    if [ -f "$file" ]; then
        echo "  上传: $(basename $file)"
        curl -s -X POST "$API_BASE/documents/upload" \
            -F "file=@$file" \
            -F "category=工艺文档" \> /dev/null
        echo "  ✅ 完成"
    fi
done

echo ""
echo "📊 当前文档数量:"
curl -s "$API_BASE/documents" | grep -o '"total":[0-9]*' | head -1
echo ""
echo "✅ 演示数据上传完成"
