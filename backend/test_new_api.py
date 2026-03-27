#!/usr/bin/env python3
"""
新功能API测试脚本
测试对话历史、流式响应、数据统计API
"""
import requests
import json
import sys
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """测试健康检查"""
    print("\n=== 测试健康检查 ===")
    resp = requests.get(f"{BASE_URL}/api/health")
    print(f"状态: {resp.status_code}")
    print(f"响应: {json.dumps(resp.json(), indent=2, ensure_ascii=False)}")
    return resp.status_code == 200

def test_conversations():
    """测试对话历史API"""
    print("\n=== 测试对话历史API ===")
    
    # 1. 创建对话
    print("\n1. 创建对话")
    resp = requests.post(
        f"{BASE_URL}/api/conversations",
        json={"title": "测试对话", "user_id": "test_user"}
    )
    print(f"创建对话: {resp.status_code}")
    conv_data = resp.json()
    conv_id = conv_data.get("id")
    print(f"对话ID: {conv_id}")
    
    # 2. 获取对话列表
    print("\n2. 获取对话列表")
    resp = requests.get(f"{BASE_URL}/api/conversations?user_id=test_user")
    print(f"对话列表: {resp.status_code}")
    print(f"响应: {json.dumps(resp.json(), indent=2, ensure_ascii=False)[:500]}...")
    
    # 3. 添加消息
    print("\n3. 添加消息")
    resp = requests.post(
        f"{BASE_URL}/api/conversations/{conv_id}/messages",
        json={"role": "user", "content": "什么是半导体？"}
    )
    print(f"添加消息: {resp.status_code}")
    
    # 4. 获取对话详情
    print("\n4. 获取对话详情")
    resp = requests.get(f"{BASE_URL}/api/conversations/{conv_id}")
    print(f"对话详情: {resp.status_code}")
    print(f"消息数: {len(resp.json().get('messages', []))}")
    
    return conv_id

def test_chat_with_history(conv_id=None):
    """测试带历史记录的AI问答"""
    print("\n=== 测试AI问答（带历史） ===")
    
    payload = {"query": "什么是光刻技术？"}
    if conv_id:
        payload["conversation_id"] = conv_id
    
    resp = requests.post(f"{BASE_URL}/api/chat", json=payload)
    print(f"状态: {resp.status_code}")
    
    data = resp.json()
    print(f"回答: {data.get('answer', '')[:200]}...")
    print(f"对话ID: {data.get('conversation_id')}")
    print(f"延迟: {data.get('latency_ms')}ms")
    print(f"来源: {len(data.get('sources', []))} 个")
    
    return data.get('conversation_id')

def test_stream_chat():
    """测试流式响应"""
    print("\n=== 测试流式响应 ===")
    
    payload = {"query": "简述半导体制造流程"}
    
    try:
        resp = requests.post(
            f"{BASE_URL}/api/chat/stream",
            json=payload,
            stream=True,
            headers={"Accept": "text/event-stream"}
        )
        
        print("接收流式数据:")
        full_text = ""
        for line in resp.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])
                        if data.get('type') == 'content':
                            text = data.get('text', '')
                            full_text += text
                            print(text, end='', flush=True)
                        elif data.get('type') == 'end':
                            print(f"\n[流式响应完成]")
                    except json.JSONDecodeError:
                        pass
        
        print(f"\n完整回答长度: {len(full_text)} 字符")
        return True
    except Exception as e:
        print(f"流式响应错误: {e}")
        return False

def test_stats():
    """测试数据统计API"""
    print("\n=== 测试数据统计API ===")
    
    # 1. 仪表盘数据
    print("\n1. 仪表盘统计")
    resp = requests.get(f"{BASE_URL}/api/stats/dashboard")
    print(f"状态: {resp.status_code}")
    print(f"响应: {json.dumps(resp.json(), indent=2, ensure_ascii=False)[:800]}...")
    
    # 2. 文档统计
    print("\n2. 文档统计")
    resp = requests.get(f"{BASE_URL}/api/stats/documents?days=30")
    print(f"状态: {resp.status_code}")
    data = resp.json()
    print(f"总文档数: {data.get('summary', {}).get('total')}")
    print(f"文件类型: {len(data.get('file_types', []))} 种")
    
    # 3. 问答统计
    print("\n3. 问答统计")
    resp = requests.get(f"{BASE_URL}/api/stats/chats?days=30")
    print(f"状态: {resp.status_code}")
    data = resp.json()
    print(f"总问题数: {data.get('summary', {}).get('total_questions')}")
    print(f"平均延迟: {data.get('avg_latency_ms')}ms")
    
    # 4. 用户活跃度
    print("\n4. 用户活跃度")
    resp = requests.get(f"{BASE_URL}/api/stats/users?days=30")
    print(f"状态: {resp.status_code}")
    data = resp.json()
    print(f"活跃用户数: {data.get('summary', {}).get('unique_users')}")
    
    return True

def test_document_management():
    """测试文档管理API"""
    print("\n=== 测试文档管理API ===")
    
    # 获取文档列表
    resp = requests.get(f"{BASE_URL}/api/documents?limit=5")
    print(f"文档列表: {resp.status_code}")
    data = resp.json()
    print(f"总文档数: {data.get('total')}")
    
    if data.get('documents'):
        doc_id = data['documents'][0]['id']
        
        # 获取文档详情
        resp = requests.get(f"{BASE_URL}/api/documents/{doc_id}")
        print(f"文档详情: {resp.status_code}")
        print(f"标题: {resp.json().get('title')}")
    
    return True

def main():
    print("🚀 AI知识库API测试脚本")
    print("=" * 50)
    
    try:
        # 检查服务是否运行
        if not test_health():
            print("❌ 服务未运行，请先启动: python main.py")
            sys.exit(1)
        
        # 测试对话历史
        conv_id = test_conversations()
        
        # 测试AI问答
        new_conv_id = test_chat_with_history(conv_id)
        
        # 测试流式响应
        test_stream_chat()
        
        # 测试数据统计
        test_stats()
        
        # 测试文档管理
        test_document_management()
        
        print("\n" + "=" * 50)
        print("✅ 所有测试完成！")
        print("=" * 50)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到服务")
        print("请确保服务已启动: python main.py")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()