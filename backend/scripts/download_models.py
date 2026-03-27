#!/usr/bin/env python3
"""
模型下载脚本 - 使用ModelScope国内镜像
"""
import os
import sys
from modelscope import snapshot_download

MODELS = {
    "bge-base-zh": {
        "model_id": "AI-ModelScope/bge-base-zh-v1.5",
        "description": "智源BGE中文基础模型"
    },
    "bge-large-zh": {
        "model_id": "AI-ModelScope/bge-large-zh-v1.5",
        "description": "智源BGE中文大模型"
    },
    "gte-base-zh": {
        "model_id": "damo/nlp_gte_sentence-embedding_chinese-base",
        "description": "阿里GTE中文模型"
    },
    "text2vec-base": {
        "model_id": "AI-ModelScope/text2vec-base-chinese",
        "description": "text2vec中文模型"
    }
}

def download_model(model_name):
    """下载指定模型"""
    if model_name not in MODELS:
        print(f"❌ 不支持的模型: {model_name}")
        print(f"支持的模型: {', '.join(MODELS.keys())}")
        return False
    
    model_info = MODELS[model_name]
    model_id = model_info["model_id"]
    description = model_info["description"]
    
    print(f"📥 正在下载模型: {model_name}")
    print(f"   描述: {description}")
    print(f"   模型ID: {model_id}")
    
    try:
        local_path = snapshot_download(model_id, cache_dir="models")
        print(f"✅ 下载完成: {local_path}")
        return True
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("使用方法: python download_models.py [模型名称]")
        print("")
        print("支持的模型:")
        for name, info in MODELS.items():
            print(f"  - {name}: {info['description']}")
        print("")
        print("示例: python download_models.py bge-base-zh")
        return
    
    model_name = sys.argv[1]
    os.makedirs("models", exist_ok=True)
    
    success = download_model(model_name)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
