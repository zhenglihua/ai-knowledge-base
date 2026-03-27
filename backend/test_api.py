#!/usr/bin/env python3
"""
AI知识库MVP - 测试脚本
测试文档解析、向量存储和RAG流程
"""
import os
import sys
import uuid

# 添加backend到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.document_parser import DocumentParser
from services.document_parser_v2 import DocumentParser as EnhancedParser, DocumentChunker
from services.vector_store import VectorStore
from services.ai_service import AIService
from services.rag_service import EnhancedVectorStore, EnhancedRAGService

def test_document_parser():
    """测试文档解析器"""
    print("\n" + "="*50)
    print("📄 测试文档解析器")
    print("="*50)
    
    parser = DocumentParser()
    
    # 创建测试文件
    test_dir = "test_files"
    os.makedirs(test_dir, exist_ok=True)
    
    # 测试TXT文件
    txt_content = """半导体制造工艺简介

半导体制造是一个复杂的过程，涉及多个步骤：

1. 晶圆制备：将硅锭切割成薄片
2. 氧化：在硅片表面形成氧化层
3. 光刻：使用光刻胶和掩膜版进行图案转移
4. 刻蚀：去除 unwanted 的材料
5. 掺杂：引入杂质改变硅的导电性
6. 金属化：添加导电层
7. 测试和封装

这些步骤需要严格控制温度、压力和化学环境。"""
    
    txt_path = f"{test_dir}/test_process.txt"
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(txt_content)
    
    result = parser.parse(txt_path, "test_process.txt")
    print(f"✅ TXT解析成功 - 内容长度: {len(result)} 字符")
    print(f"   预览: {result[:100]}...")
    
    # 测试增强版解析器
    print("\n--- 测试增强版解析器 ---")
    enhanced_parser = EnhancedParser()
    result2 = enhanced_parser.parse(txt_path, "test_process.txt")
    print(f"✅ 增强解析成功 - 字符数: {result2['metadata']['char_count']}")
    print(f"   行数: {result2['metadata']['line_count']}")
    
    # 测试分块器
    chunker = DocumentChunker(chunk_size=200, chunk_overlap=20)
    chunks = chunker.chunk_text(result)
    print(f"✅ 文本分块成功 - 生成 {len(chunks)} 个块")
    for i, chunk in enumerate(chunks[:3]):
        print(f"   块{i+1}: {chunk['char_count']} 字符")
    
    return True

def test_vector_store():
    """测试向量存储"""
    print("\n" + "="*50)
    print("🔍 测试向量存储")
    print("="*50)
    
    # 使用增强版向量存储
    store = EnhancedVectorStore()
    
    # 添加测试文档
    doc1_id = str(uuid.uuid4())
    doc1_content = """半导体制造工艺 - 光刻技术

光刻是半导体制造中最关键的步骤之一。它使用紫外光通过掩膜版将电路图案转移到硅片上。

关键参数：
- 波长：193nm（深紫外）或13.5nm（极紫外）
- 分辨率：决定最小特征尺寸
- 焦深：影响工艺窗口

光刻胶的选择也很重要，分为正胶和负胶两种。"""
    
    doc2_id = str(uuid.uuid4())
    doc2_content = """半导体制造工艺 - 刻蚀技术

刻蚀是将光刻定义的图案转移到硅片中的过程。主要有两种刻蚀方法：

1. 湿法刻蚀：使用化学溶液
   - 优点：选择性好，成本低
   - 缺点：各向同性，不适合精细图案

2. 干法刻蚀：使用等离子体
   - 优点：各向异性，适合精细图案
   - 缺点：选择性较差

刻蚀速率、选择性和均匀性是关键指标。"""
    
    # 添加文档
    chunks1 = store.add_document(doc1_id, doc1_content, {
        'title': '光刻技术文档',
        'category': '制造工艺'
    })
    print(f"✅ 文档1添加成功 - 分成 {chunks1} 个块")
    
    chunks2 = store.add_document(doc2_id, doc2_content, {
        'title': '刻蚀技术文档',
        'category': '制造工艺'
    })
    print(f"✅ 文档2添加成功 - 分成 {chunks2} 个块")
    
    # 测试搜索
    print("\n--- 测试语义搜索 ---")
    query = "什么是光刻胶？"
    results = store.search(query, top_k=3)
    print(f"✅ 搜索完成 - 找到 {len(results)} 个相关片段")
    for i, r in enumerate(results):
        print(f"   排名{i+1}: 相似度 {r.score:.4f} - {r.content[:50]}...")
    
    # 测试重排序搜索
    print("\n--- 测试重排序搜索 ---")
    results_rerank = store.search_with_rerank("刻蚀方法有哪些？", top_k=3)
    print(f"✅ 重排序搜索完成")
    for i, r in enumerate(results_rerank):
        print(f"   排名{i+1}: 得分 {r.score:.4f} - {r.content[:50]}...")
    
    # 显示统计
    stats = store.get_stats()
    print(f"\n✅ 存储统计: {stats['total_documents']} 文档, {stats['total_chunks']} 块")
    
    return store

def test_rag_service(store):
    """测试RAG服务"""
    print("\n" + "="*50)
    print("🤖 测试RAG问答服务")
    print("="*50)
    
    # 初始化RAG服务
    ai_service = AIService()
    rag = EnhancedRAGService(store, ai_service)
    
    # 测试检索
    print("\n--- 测试文档检索 ---")
    query = "刻蚀有哪些类型？"
    context = rag.retrieve(query, top_k=3)
    print(f"✅ 检索完成 - 从 {context.total_docs} 个文档找到 {context.total_chunks} 个片段")
    
    # 测试回答生成
    print("\n--- 测试回答生成 ---")
    result = rag.generate_answer(query, context)
    print(f"✅ 回答生成完成")
    print(f"   问题: {result['query']}")
    print(f"   回答: {result['answer'][:200]}...")
    print(f"   引用来源: {len(result['sources'])} 个")
    
    # 测试对话模式
    print("\n--- 测试对话模式 ---")
    chat_result = rag.chat("它们各有什么优缺点？", [
        {'query': query, 'answer': result['answer'][:100]}
    ])
    print(f"✅ 对话完成")
    print(f"   回答: {chat_result['answer'][:200]}...")
    
    return rag

def test_api_endpoints():
    """测试API端点"""
    print("\n" + "="*50)
    print("🌐 测试API端点")
    print("="*50)
    
    import requests
    
    base_url = "http://localhost:8000"
    
    try:
        # 测试健康检查
        resp = requests.get(f"{base_url}/api/health", timeout=5)
        print(f"✅ 健康检查: {resp.json()}")
        
        # 测试文档列表
        resp = requests.get(f"{base_url}/api/documents", timeout=5)
        data = resp.json()
        print(f"✅ 文档列表: 共 {data.get('total', 0)} 个文档")
        
        # 测试搜索
        resp = requests.post(
            f"{base_url}/api/search",
            json={"keyword": "半导体", "limit": 5},
            timeout=5
        )
        data = resp.json()
        print(f"✅ 搜索测试: 找到 {data.get('total', 0)} 个结果")
        
        # 测试聊天
        resp = requests.post(
            f"{base_url}/api/chat",
            json={"query": "什么是半导体制造？"},
            timeout=10
        )
        data = resp.json()
        print(f"✅ 聊天测试: 回答长度 {len(data.get('answer', ''))} 字符")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("⚠️ API服务未启动，跳过API测试")
        print("   请先运行: python main.py")
        return False
    except Exception as e:
        print(f"⚠️ API测试出错: {e}")
        return False

def main():
    """主测试函数"""
    print("\n" + "🚀 "*20)
    print("  AI知识库MVP - 功能测试")
    print("🚀 "*20)
    
    try:
        # 测试文档解析
        test_document_parser()
        
        # 测试向量存储
        store = test_vector_store()
        
        # 测试RAG服务
        rag = test_rag_service(store)
        
        # 测试API端点（如果服务在运行）
        test_api_endpoints()
        
        print("\n" + "="*50)
        print("✅ 所有测试完成！")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
