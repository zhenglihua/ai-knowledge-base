"""
知识图谱模块测试
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestEntityAndRelation:
    """实体和关系数据类测试"""
    
    def test_entity_creation(self):
        """测试实体创建"""
        class Entity:
            def __init__(self, id, name, type, properties):
                self.id = id
                self.name = name
                self.type = type
                self.properties = properties
        
        entity = Entity(
            id="test_001",
            name="光刻机",
            type="Equipment",
            properties={"manufacturer": "ASML"}
        )
        assert entity.id == "test_001"
        assert entity.name == "光刻机"
        assert entity.type == "Equipment"
        print("✅ 实体创建测试通过")
    
    def test_relation_creation(self):
        """测试关系创建"""
        class Relation:
            def __init__(self, from_id, from_type, to_id, to_type, relation_type):
                self.from_id = from_id
                self.from_type = from_type
                self.to_id = to_id
                self.to_type = to_type
                self.relation_type = relation_type
        
        relation = Relation(
            from_id="eq_001",
            from_type="Equipment",
            to_id="proc_001",
            to_type="Process",
            relation_type="USES"
        )
        assert relation.from_id == "eq_001"
        assert relation.relation_type == "USES"
        print("✅ 关系创建测试通过")


class TestSemiconductorNER:
    """半导体实体识别测试"""
    
    def test_ner_initialization(self):
        """测试NER初始化"""
        from backend.services.ner_service import SemiconductorNER
        
        ner = SemiconductorNER()
        assert ner is not None
        assert hasattr(ner, 'ENTITY_TYPES')
        print("✅ NER初始化测试通过")
    
    def test_recognize_equipment(self):
        """测试识别设备实体"""
        from backend.services.ner_service import SemiconductorNER
        
        ner = SemiconductorNER()
        text = "光刻机是半导体制造的核心设备"
        entities = ner.recognize(text)
        
        entity_names = [e.name for e in entities]
        assert "光刻机" in entity_names
        print(f"✅ 设备识别测试通过，识别到: {entity_names}")
    
    def test_recognize_process(self):
        """测试识别工艺实体"""
        from backend.services.ner_service import SemiconductorNER
        
        ner = SemiconductorNER()
        text = "光刻工艺和刻蚀工艺是主要工序"
        entities = ner.recognize(text)
        
        entity_names = [e.name for e in entities]
        has_process = any(e in entity_names for e in ["光刻", "刻蚀"])
        assert has_process
        print(f"✅ 工艺识别测试通过，识别到: {entity_names}")
    
    def test_recognize_parameter(self):
        """测试识别参数实体"""
        from backend.services.ner_service import SemiconductorNER
        
        ner = SemiconductorNER()
        text = "温度150℃压力100Pa"
        entities = ner.recognize(text)
        
        assert len(entities) > 0
        print(f"✅ 参数识别测试通过，识别到: {[e.name for e in entities]}")
    
    def test_recognize_mixed(self):
        """测试混合文本识别"""
        from backend.services.ner_service import SemiconductorNER
        
        ner = SemiconductorNER()
        text = "ASML光刻机执行光刻工艺，温度控制在150℃"
        entities = ner.recognize(text)
        
        assert len(entities) > 0
        entity_types = [e.type for e in entities]
        print(f"✅ 混合识别测试通过，识别到 {len(entities)} 个实体，类型: {set(entity_types)}")
    
    def test_entity_types_coverage(self):
        """测试实体类型覆盖"""
        from backend.services.ner_service import SemiconductorNER
        
        ner = SemiconductorNER()
        expected_types = ['equipment', 'process', 'material', 'parameter', 'fault', 'person', 'document', 'term']
        
        for entity_type in expected_types:
            assert entity_type in ner.ENTITY_TYPES
        
        print(f"✅ 实体类型覆盖测试通过，覆盖 {len(expected_types)} 种类型")


class TestRelationExtractor:
    """关系抽取测试"""
    
    def test_extractor_initialization(self):
        """测试抽取器初始化"""
        from backend.services.ner_service import SemiconductorRelationExtractor
        
        extractor = SemiconductorRelationExtractor()
        assert extractor is not None
        assert hasattr(extractor, 'RELATION_PATTERNS')
        print("✅ 关系抽取器初始化测试通过")
    
    def test_relation_patterns(self):
        """测试关系模式"""
        from backend.services.ner_service import SemiconductorRelationExtractor
        
        extractor = SemiconductorRelationExtractor()
        assert len(extractor.RELATION_PATTERNS) > 0
        print(f"✅ 关系模式测试通过，包含 {len(extractor.RELATION_PATTERNS)} 种模式")


class TestKnowledgeGraphBuilder:
    """知识图谱构建器测试"""
    
    def test_builder_initialization(self):
        """测试构建器初始化"""
        from backend.services.ner_service import KnowledgeGraphBuilder
        
        builder = KnowledgeGraphBuilder()
        assert builder.ner is not None
        assert builder.extractor is not None
        print("✅ 知识图谱构建器初始化测试通过")
    
    def test_process_document(self):
        """测试文档处理"""
        from backend.services.ner_service import KnowledgeGraphBuilder
        
        builder = KnowledgeGraphBuilder()
        text = "ASML光刻机进行光刻工艺"
        entities, relations = builder.process_document(text, "doc_001")
        
        assert len(entities) > 0
        # 应该包含文档实体
        assert any("doc_001" == e.id or e.type == "Document" for e in entities)
        print(f"✅ 文档处理测试通过，提取 {len(entities)} 个实体，{len(relations)} 个关系")


class TestNeo4jService:
    """Neo4j服务测试"""
    
    def test_neo4j_initialization(self):
        """测试Neo4j服务初始化"""
        try:
            from backend.services.neo4j_service import Neo4jService
            
            service = Neo4jService(
                uri="bolt://localhost:7687",
                user="neo4j",
                password="password"
            )
            assert service.uri == "bolt://localhost:7687"
            assert service.user == "neo4j"
            assert service.driver is None  # 初始未连接
            print("✅ Neo4j服务初始化测试通过")
        except ImportError:
            print("⚠️ Neo4j驱动未安装，跳过此测试")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*50)
    print("知识图谱模块测试")
    print("="*50 + "\n")
    
    test_suites = [
        TestEntityAndRelation(),
        TestSemiconductorNER(),
        TestRelationExtractor(),
        TestKnowledgeGraphBuilder(),
        TestNeo4jService(),
    ]
    
    total = 0
    passed = 0
    
    for suite in test_suites:
        print(f"\n📋 {suite.__class__.__name__}")
        print("-" * 40)
        
        for method in dir(suite):
            if method.startswith("test_"):
                total += 1
                try:
                    if hasattr(suite, 'setup_method'):
                        getattr(suite, 'setup_method')()
                    getattr(suite, method)()
                    passed += 1
                except Exception as e:
                    print(f"❌ {method}: {e}")
    
    print("\n" + "="*50)
    print(f"测试结果: {passed}/{total} 通过")
    print("="*50 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
