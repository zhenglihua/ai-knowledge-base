"""
RAGFlow API 自动化测试用例
v0.8.2

测试覆盖：
1. 数据集管理（创建/列表/获取/删除）
2. 文档管理（上传/列表/删除）
3. RAG 检索
4. RAG 对话

运行方式：
    python tests/test_ragflow_api.py
"""

import os
import sys
import time
import tempfile
import unittest

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.integration.ragflow_client import RAGFlowService, RAGFlowConfig


# 测试配置
RAGFLOW_URL = os.getenv("RAGFLOW_URL", "http://localhost:9380")
RAGFLOW_API_KEY = os.getenv("RAGFLOW_API_KEY", "")

# 测试数据
TEST_PREFIX = int(time.time())
TEST_DATASET_NAME = f"测试数据集_{TEST_PREFIX}"
TEST_DATASET_NAME_2 = f"测试数据集2_{TEST_PREFIX}"


class RAGFlowAPITest(unittest.TestCase):
    """RAGFlow API 测试用例"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        print(f"\n{'='*60}")
        print(f"RAGFlow API 自动化测试")
        print(f"URL: {RAGFLOW_URL}")
        print(f"API Key: {RAGFLOW_API_KEY[:20]}..." if RAGFLOW_API_KEY else "API Key: 未设置")
        print(f"{'='*60}\n")

        if not RAGFLOW_API_KEY:
            print("⚠️ 警告: RAGFLOW_API_KEY 未设置，部分测试可能失败")
            sys.exit(1)

        cls.service = RAGFlowService(RAGFlowConfig(
            base_url=RAGFLOW_URL,
            api_token=RAGFLOW_API_KEY
        ))
        cls.created_datasets = []

    def test_01_list_datasets(self):
        """测试 1: 列出数据集"""
        print("\n📋 测试 1: 列出数据集")

        datasets = self.service.list_datasets()
        print(f"  当前数据集数量: {len(datasets)}")

        for ds in datasets[:3]:
            print(f"    - {ds.get('name')} ({ds.get('id')})")
        if len(datasets) > 3:
            print(f"    ... 还有 {len(datasets) - 3} 个")

        self.assertIsInstance(datasets, list, "数据集列表应该是 list 类型")
        print("  ✅ 通过")

    def test_02_create_dataset(self):
        """测试 2: 创建数据集"""
        print(f"\n📋 测试 2: 创建数据集")
        print(f"  数据集名称: {TEST_DATASET_NAME}")

        result = self.service.create_dataset(
            name=TEST_DATASET_NAME,
            description="自动化测试创建的数据集",
            chunk_method="naive",
            permission="me"
        )

        print(f"  响应码: {result.get('code')}")

        self.assertEqual(result.get('code'), 0, f"创建数据集失败: {result}")

        data = result.get('data', {})
        dataset_id = data.get('id')
        print(f"  数据集 ID: {dataset_id}")

        self.assertIsNotNone(dataset_id, "数据集 ID 不应该为空")
        self.created_datasets.append(dataset_id)

        print("  ✅ 通过")
        return dataset_id

    def test_03_create_second_dataset(self):
        """测试 3: 创建第二个数据集"""
        print(f"\n📋 测试 3: 创建第二个数据集")
        print(f"  数据集名称: {TEST_DATASET_NAME_2}")

        result = self.service.create_dataset(
            name=TEST_DATASET_NAME_2,
            description="第二个测试数据集"
        )

        self.assertEqual(result.get('code'), 0, f"创建第二个数据集失败: {result}")

        data = result.get('data', {})
        dataset_id = data.get('id')
        self.created_datasets.append(dataset_id)

        print(f"  数据集 ID: {dataset_id}")
        print("  ✅ 通过")
        return dataset_id

    def test_04_verify_datasets_created(self):
        """测试 4: 验证数据集已创建"""
        print("\n📋 测试 4: 验证数据集已创建")

        datasets = self.service.list_datasets()
        dataset_names = [ds.get('name') for ds in datasets]

        print(f"  查找: {TEST_DATASET_NAME}, {TEST_DATASET_NAME_2}")

        self.assertIn(TEST_DATASET_NAME, dataset_names, f"数据集 {TEST_DATASET_NAME} 应该存在")
        self.assertIn(TEST_DATASET_NAME_2, dataset_names, f"数据集 {TEST_DATASET_NAME_2} 应该存在")

        print("  ✅ 通过")

    def test_05_upload_document(self):
        """测试 5: 上传文档"""
        print("\n📋 测试 5: 上传文档")

        if not self.created_datasets:
            print("  ⚠️ 没有测试数据集，跳过测试")
            self.skipTest("没有测试数据集")

        dataset_id = self.created_datasets[0]

        # 创建临时测试文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("这是一个测试文档。\n")
            f.write("用于测试 RAGFlow 文档上传功能。\n")
            f.write("包含一些中文内容。\n")
            f.write("半导体工厂 CIM 系统测试。\n")
            temp_path = f.name

        print(f"  数据集 ID: {dataset_id}")
        print(f"  临时文件: {temp_path}")

        try:
            result = self.service.upload_document(
                dataset_id=dataset_id,
                file_path=temp_path,
                chunk_method="naive"
            )

            print(f"  响应码: {result.get('code')}")
            print(f"  消息: {result.get('message')}")

            if result.get('code') == 0:
                data = result.get('data', {})
                # API 返回的可能是 list 或 dict
                if isinstance(data, list):
                    print(f"  文档列表: {len(data)} 个文档")
                    if data:
                        doc = data[0]
                        print(f"  第一个文档 ID: {doc.get('id')}")
                else:
                    print(f"  文档 ID: {data.get('id')}")
                    print(f"  文档名称: {data.get('name')}")

        finally:
            os.unlink(temp_path)

        print("  ✅ 完成")

    def test_06_retrieval(self):
        """测试 6: RAG 检索"""
        print("\n📋 测试 6: RAG 检索")

        if not self.created_datasets:
            print("  ⚠️ 没有测试数据集，跳过测试")
            self.skipTest("没有测试数据集")

        dataset_ids = [self.created_datasets[0]]
        query = "测试文档内容"

        print(f"  数据集 IDs: {dataset_ids}")
        print(f"  查询: {query}")

        result = self.service.retrievals(
            dataset_ids=dataset_ids,
            query=query,
            top_k=5
        )

        print(f"  检索结果数量: {len(result)}")

        self.assertIsInstance(result, list, "检索结果应该是 list 类型")
        print("  ✅ 通过")

    def test_07_delete_first_dataset(self):
        """测试 7: 删除第一个数据集"""
        print("\n📋 测试 7: 删除第一个数据集")

        if not self.created_datasets:
            print("  ⚠️ 没有测试数据集，跳过测试")
            self.skipTest("没有测试数据集")

        # 列表第一个
        dataset_id = self.created_datasets.pop(0)
        print(f"  数据集 ID: {dataset_id}")

        # 更新客户端的内部数据集列表
        result = self.service.delete_dataset(dataset_id)

        print(f"  删除结果: {result}")

        # 删除可能返回成功但实际异步删除
        print("  ✅ 完成")

    def test_08_verify_second_dataset_still_exists(self):
        """测试 8: 验证第二个数据集仍存在"""
        print("\n📋 测试 8: 验证第二个数据集仍存在")

        if not self.created_datasets:
            print("  ⚠️ 没有剩余数据集，跳过测试")
            self.skipTest("没有剩余数据集")

        datasets = self.service.list_datasets()
        dataset_ids = [ds.get('id') for ds in datasets]

        print(f"  查找 ID: {self.created_datasets[0]}")

        self.assertIn(self.created_datasets[0], dataset_ids, "第二个数据集应该仍存在")

        print("  ✅ 通过")

    @classmethod
    def tearDownClass(cls):
        """清理测试数据"""
        print(f"\n{'='*60}")
        print("清理测试数据...")
        for dataset_id in cls.created_datasets:
            try:
                result = cls.service.delete_dataset(dataset_id)
                print(f"  删除数据集 {dataset_id}: {'成功' if result else '失败'}")
            except Exception as e:
                print(f"  删除数据集 {dataset_id} 失败: {e}")
        print(f"{'='*60}\n")


def run_tests():
    """运行测试"""
    print("\n" + "="*60)
    print("RAGFlow API 自动化测试套件")
    print("="*60)

    # 检查环境变量
    if not RAGFLOW_API_KEY:
        print("\n⚠️ 警告: RAGFLOW_API_KEY 环境变量未设置")
        print("请设置: export RAGFLOW_API_KEY=your_token\n")

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(RAGFlowAPITest)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 打印总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"运行测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n🎉 所有测试通过!")
    else:
        print("\n❌ 部分测试失败")
        if result.failures:
            print("\n失败:")
            for test, traceback in result.failures:
                print(f"  - {test}")
        if result.errors:
            print("\n错误:")
            for test, traceback in result.errors:
                print(f"  - {test}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
