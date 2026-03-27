#!/usr/bin/env python3
"""
AI知识库 MVP 简化功能测试
使用Python requests代替Playwright
"""
import requests
import json
import os
import sys
import time
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
TEST_FILE = "/Users/zheng/.openclaw/workspace/ai-knowledge-base/mvp/test_data/半导体工艺规范.txt"

# 测试结果存储
results = {
    "start_time": datetime.now().isoformat(),
    "tests": [],
    "passed": 0,
    "failed": 0
}

def log(message, level="INFO"):
    """打印日志"""
    prefix = {"INFO": "ℹ️", "PASS": "✅", "FAIL": "❌", "WARN": "⚠️"}.get(level, "ℹ️")
    print(f"{prefix} {message}")

def test_api(name, method, endpoint, **kwargs):
    """测试API端点"""
    url = f"{BASE_URL}{endpoint}"
    test_result = {
        "name": name,
        "endpoint": endpoint,
        "method": method,
        "status": "pending"
    }
    
    try:
        log(f"测试: {name} - {method} {endpoint}")
        response = requests.request(method, url, timeout=10, **kwargs)
        
        test_result["status_code"] = response.status_code
        test_result["response_time_ms"] = int(response.elapsed.total_seconds() * 1000)
        
        if response.status_code < 400:
            test_result["status"] = "passed"
            results["passed"] += 1
            log(f"通过 - HTTP {response.status_code} ({test_result['response_time_ms']}ms)", "PASS")
            try:
                test_result["response"] = response.json()
            except:
                test_result["response"] = response.text[:200]
        else:
            test_result["status"] = "failed"
            results["failed"] += 1
            log(f"失败 - HTTP {response.status_code}", "FAIL")
            test_result["error"] = response.text[:200]
            
    except Exception as e:
        test_result["status"] = "failed"
        results["failed"] += 1
        test_result["error"] = str(e)
        log(f"异常: {e}", "FAIL")
    
    results["tests"].append(test_result)
    return test_result

def run_tests():
    """运行所有测试"""
    log("="*60)
    log("AI知识库 MVP 功能测试")
    log(f"开始时间: {results['start_time']}")
    log("="*60)
    
    # ========== 1. 基础健康检查 ==========
    log("\n📋 1. 基础健康检查", "INFO")
    
    # 根端点
    test_api("根端点", "GET", "/")
    
    # 健康检查
    health = test_api("健康检查", "GET", "/api/health")
    
    # ========== 2. 文档管理API测试 ==========
    log("\n📄 2. 文档管理API", "INFO")
    
    # 获取文档列表
    docs = test_api("获取文档列表", "GET", "/api/documents")
    
    # 获取文档详情（如果有文档）
    if docs.get("response") and docs["response"].get("documents"):
        doc_id = docs["response"]["documents"][0]["id"]
        test_api(f"获取文档详情 (ID: {doc_id[:8]}...)", "GET", f"/api/documents/{doc_id}")
    
    # 文档上传测试
    if os.path.exists(TEST_FILE):
        log(f"使用测试文件: {TEST_FILE}")
        with open(TEST_FILE, "rb") as f:
            files = {"file": ("test_upload.txt", f, "text/plain")}
            data = {"category": "测试文档", "tags": "测试,上传"}
            upload = test_api("上传文档", "POST", "/api/documents/upload", files=files, data=data)
            
        # 如果上传成功，获取新文档ID
        if upload.get("status") == "passed" and upload.get("response"):
            new_doc_id = upload["response"].get("id")
            if new_doc_id:
                log(f"新文档ID: {new_doc_id[:8]}...")
    else:
        log(f"测试文件不存在: {TEST_FILE}", "WARN")
    
    # ========== 3. 搜索API测试 ==========
    log("\n🔍 3. 搜索API", "INFO")
    
    search_data = {"keyword": "半导体", "limit": 5}
    test_api("搜索文档", "POST", "/api/search", json=search_data)
    
    # ========== 4. AI问答API测试 ==========
    log("\n🤖 4. AI问答API", "INFO")
    
    chat_data = {"query": "什么是半导体？", "stream": False}
    chat_result = test_api("AI问答", "POST", "/api/chat", json=chat_data)
    
    # 对话历史测试（如果有对话ID）
    if chat_result.get("response") and chat_result["response"].get("conversation_id"):
        conv_id = chat_result["response"]["conversation_id"]
        log(f"对话ID: {conv_id[:8]}...")
    
    # ========== 5. 对话管理API测试 ==========
    log("\n💬 5. 对话管理API", "INFO")
    
    test_api("获取对话列表", "GET", "/api/conversations")
    
    # ========== 6. 统计API测试 ==========
    log("\n📊 6. 统计API", "INFO")
    
    test_api("获取仪表盘统计", "GET", "/api/stats/dashboard")
    test_api("获取搜索趋势", "GET", "/api/stats/search-trends")
    
    # ========== 7. 前端检查 ==========
    log("\n🌐 7. 前端页面检查", "INFO")
    try:
        frontend_resp = requests.get(FRONTEND_URL, timeout=5)
        frontend_test = {
            "name": "前端首页访问",
            "endpoint": FRONTEND_URL,
            "status": "passed" if frontend_resp.status_code == 200 else "failed",
            "status_code": frontend_resp.status_code
        }
        if frontend_test["status"] == "passed":
            results["passed"] += 1
            log(f"前端可访问 - HTTP {frontend_resp.status_code}", "PASS")
        else:
            results["failed"] += 1
            log(f"前端访问失败 - HTTP {frontend_resp.status_code}", "FAIL")
    except Exception as e:
        frontend_test = {
            "name": "前端首页访问",
            "status": "failed",
            "error": str(e)
        }
        results["failed"] += 1
        log(f"前端访问异常: {e}", "FAIL")
    
    results["tests"].append(frontend_test)

def generate_report():
    """生成测试报告"""
    results["end_time"] = datetime.now().isoformat()
    results["total"] = len(results["tests"])
    results["success_rate"] = f"{(results['passed'] / results['total'] * 100):.1f}%" if results["total"] > 0 else "0%"
    
    log("\n" + "="*60)
    log("测试报告")
    log("="*60)
    log(f"总测试数: {results['total']}")
    log(f"通过: {results['passed']}", "PASS")
    log(f"失败: {results['failed']}", "FAIL")
    log(f"成功率: {results['success_rate']}")
    
    # 失败的测试详情
    if results["failed"] > 0:
        log("\n失败的测试详情:", "FAIL")
        for test in results["tests"]:
            if test["status"] == "failed":
                log(f"  - {test['name']}: {test.get('error', '未知错误')}", "FAIL")
    
    # 保存报告到文件
    report_file = "/Users/zheng/.openclaw/workspace/ai-knowledge-base/mvp/test_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    log(f"\n详细报告已保存: {report_file}")
    
    return results

if __name__ == "__main__":
    run_tests()
    generate_report()
    
    # 返回码：0=全部通过, 1=有失败
    sys.exit(0 if results["failed"] == 0 else 1)
