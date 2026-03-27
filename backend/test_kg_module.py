"""
知识图谱模块测试脚本
"""
import sys
sys.path.insert(0, '/Users/zheng/.openclaw/workspace/ai-knowledge-base/mvp/backend')

def test_entity_extraction():
    """测试实体抽取"""
    print("=" * 50)
    print("测试实体抽取服务")
    print("=" * 50)
    
    from kg_module.services.entity_extraction import extract_entities
    
    test_text = """
    ASML TWINSCAN NXT光刻机使用ArF准分子激光光源，波长为193nm。
    刻蚀工艺Recipe-001需要在温度：120°C，压力：10mTorr的条件下进行。
    该设备使用CF4和SiO2作为刻蚀材料，流量分别为50sccm和30sccm。
    AMAT Centura Producer用于PVD沉积工艺，功率设置为2000W。
    TEL Alpha刻蚀机支持干法刻蚀工艺。
    薄膜厚度均匀性是关键的质量指标。
    """
    
    result = extract_entities(test_text, doc_id="test_doc_001")
    
    print(f"处理时间: {result.processing_time_ms:.2f}ms")
    print(f"抽取实体数: {len(result.entities)}")
    print("\n抽取的实体:")
    for entity in result.entities:
        print(f"  - [{entity.type.value}] {entity.text} (置信度: {entity.confidence:.2f})")
        if entity.properties:
            print(f"    属性: {entity.properties}")
    
    return result


def test_relation_extraction(entities):
    """测试关系抽取"""
    print("\n" + "=" * 50)
    print("测试关系抽取服务")
    print("=" * 50)
    
    from kg_module.services.relation_extraction import extract_relations
    
    test_text = """
    ASML TWINSCAN NXT光刻机使用ArF准分子激光光源，波长为193nm。
    刻蚀工艺需要在温度：120°C，压力：10mTorr的条件下进行。
    AMAT Centura设备用于PVD沉积工艺。
    """
    
    relations = extract_relations(test_text, entities)
    
    print(f"抽取关系数: {len(relations)}")
    print("\n抽取的关系:")
    for rel in relations:
        print(f"  - [{rel.type.value}] {rel.head_text} -> {rel.tail_text} (置信度: {rel.confidence:.2f})")
    
    return relations


def test_knowledge_graph_store():
    """测试知识图谱存储"""
    print("\n" + "=" * 50)
    print("测试知识图谱存储")
    print("=" * 50)
    
    from kg_module.models.graph_store import get_graph_store
    from kg_module.models.entity import Entity, EntityType, Relation, RelationType
    
    store = get_graph_store(storage_path="data/test_knowledge_graph.pkl")
    
    # 添加测试实体
    entity1 = Entity.create(
        name="ASML NXT 2000i",
        entity_type=EntityType.EQUIPMENT,
        description="高端浸没式光刻机",
        properties={"wavelength": "193nm", "manufacturer": "ASML"}
    )
    
    entity2 = Entity.create(
        name="ArF准分子激光",
        entity_type=EntityType.MATERIAL,
        description="深紫外光源",
        properties={"wavelength": "193nm"}
    )
    
    entity3 = Entity.create(
        name="光刻工艺",
        entity_type=EntityType.PROCESS,
        description="半导体光刻制程"
    )
    
    # 添加到图谱
    stored_e1 = store.add_entity(entity1)
    stored_e2 = store.add_entity(entity2)
    stored_e3 = store.add_entity(entity3)
    
    print(f"添加实体: {stored_e1.name} ({stored_e1.id})")
    print(f"添加实体: {stored_e2.name} ({stored_e2.id})")
    print(f"添加实体: {stored_e3.name} ({stored_e3.id})")
    
    # 添加关系
    rel1 = Relation.create(
        relation_type=RelationType.USES,
        source_id=stored_e1.id,
        target_id=stored_e2.id,
        description="光刻机使用ArF光源"
    )
    
    rel2 = Relation.create(
        relation_type=RelationType.HAS_PROCESS,
        source_id=stored_e1.id,
        target_id=stored_e3.id,
        description="设备包含光刻工艺"
    )
    
    store.add_relation(rel1)
    store.add_relation(rel2)
    
    print(f"添加关系: {rel1.type.value} ({rel1.id})")
    print(f"添加关系: {rel2.type.value} ({rel2.id})")
    
    # 测试搜索
    print("\n搜索实体 'ASML':")
    results = store.search_entities("ASML")
    for e in results:
        print(f"  - {e.name}")
    
    # 测试邻居
    print(f"\n获取 '{stored_e1.name}' 的邻居:")
    neighbors = store.get_neighbors(stored_e1.id)
    for n in neighbors:
        print(f"  - {n['entity']['name']} (通过 {n['relation']['type']})")
    
    # 获取统计
    stats = store.get_statistics()
    print(f"\n图谱统计: {stats}")
    
    # 保存
    store.save()
    print("\n图谱已保存")
    
    return store


def test_recommendation():
    """测试推荐服务"""
    print("\n" + "=" * 50)
    print("测试智能推荐服务")
    print("=" * 50)
    
    from kg_module.services.recommendation import get_recommender
    
    recommender = get_recommender()
    
    # 测试关键词推荐
    keywords = ["光刻机", "刻蚀"]
    results = recommender.recommend_by_keywords(keywords, limit=3)
    
    print(f"关键词 {keywords} 的推荐结果:")
    for r in results:
        print(f"  - 文档: {r['doc_id']}, 分数: {r['score']}")
    
    # 测试热门实体
    trending = recommender.get_trending_entities(limit=5)
    print(f"\n热门实体:")
    for t in trending:
        print(f"  - {t['entity']['name']} ({t['doc_count']}个文档)")


def test_api_endpoints():
    """测试API端点"""
    print("\n" + "=" * 50)
    print("测试API端点")
    print("=" * 50)
    
    import httpx
    
    base_url = "http://localhost:8000"
    
    # 测试实体抽取API
    print("\n测试 POST /api/kg/extract/entities")
    try:
        response = httpx.post(
            f"{base_url}/api/kg/extract/entities",
            json={
                "text": "ASML光刻机使用ArF激光光源，温度设置为120°C。",
                "min_confidence": 0.5
            }
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功! 抽取 {len(data['entities'])} 个实体")
        else:
            print(f"❌ 失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 错误: {e}")
    
    # 测试图谱统计API
    print("\n测试 GET /api/kg/statistics")
    try:
        response = httpx.get(f"{base_url}/api/kg/statistics")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功! 实体数: {data.get('entity_count', 0)}, 关系数: {data.get('relation_count', 0)}")
        else:
            print(f"❌ 失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 错误: {e}")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("知识图谱模块测试")
    print("=" * 60)
    
    try:
        # 1. 测试实体抽取
        entity_result = test_entity_extraction()
        
        # 2. 测试关系抽取
        relations = test_relation_extraction(entity_result.entities)
        
        # 3. 测试图谱存储
        store = test_knowledge_graph_store()
        
        # 4. 测试推荐服务
        test_recommendation()
        
        # 5. 测试API端点（需要服务器运行）
        # test_api_endpoints()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()