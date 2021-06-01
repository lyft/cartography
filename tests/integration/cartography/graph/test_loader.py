from cartography.graph.loader import merge_nodes
from cartography.graph.loader import merge_relationships


TEST_UPDATE_TAG = 123456
TEST_NODE_DATA = [
    {
        'Id': 1337,
        'Name': 'Some-Asset',
        'Type': 'Some-Type',
        'Size': 'Big',
        'Encrypted': True,
    },
    {
        'Id': 1338,
        'Name': 'Some-Other-Asset',
        'Type': 'Some-Other-Type',
        'Size': 'Big',
        'Encrypted': True,
    },
    {
        'Id': 1339,
        'Name': 'Some-Other-Other-Asset',
        'Type': 'Some-Other-Other-Type',
        'Size': 'Tiny',
        'Encrypted': False,
    },
]
TEST_NODE_PROPERTY_MAP = {
    'id': 'Id',
    'name': 'Name',
    'type': 'Type',
    'size': 'Size',
    'encrypted': 'Encrypted',
}


def test_merge_nodes(neo4j_session):
    # Arrange
    # Act: add test nodes to the graph.
    merge_nodes(
        neo4j_session,
        'SomeNodeLabel',
        TEST_NODE_PROPERTY_MAP,
        TEST_NODE_DATA,
        TEST_UPDATE_TAG,
    )

    # Assert
    expected_nodes = {
        (1337, 'Some-Asset', True),
        (1338, 'Some-Other-Asset', True),
        (1339, 'Some-Other-Other-Asset', False),
    }
    nodes = neo4j_session.run("MATCH (s:SomeNodeLabel) return s.id, s.name, s.encrypted")
    actual_nodes = {(n['s.id'], n['s.name'], n['s.encrypted']) for n in nodes}
    assert actual_nodes == expected_nodes


def test_merge_relationships(neo4j_session):
    # Arrange: add 2 parent nodes to the graph, add test child nodes.
    neo4j_session.run("MERGE (p:ParentNode{id:101010, name:'Parent1'})")
    neo4j_session.run("MERGE (p:ParentNode{id:202020, name:'Parent2'})")
    merge_nodes(
        neo4j_session,
        'SomeNodeLabel',
        TEST_NODE_PROPERTY_MAP,
        TEST_NODE_DATA,
        TEST_UPDATE_TAG,
    )

    # Act: attach test nodes to the parent nodes
    relationship_mappings = [
        {'SomeNodeId': 1337, 'ParentId': 101010},
        {'SomeNodeId': 1338, 'ParentId': 101010},
        {'SomeNodeId': 1339, 'ParentId': 202020},
    ]
    merge_relationships(
        neo4j_session,
        'SomeNodeLabel', 'id', 'SomeNodeId',
        'ParentNode', 'id', 'ParentId',
        'PARENT',
        relationship_mappings,
        TEST_UPDATE_TAG,
    )

    # Assert
    # - (:SomeNodeLabel{id:1337})-[:PARENT]->(:ParentNode{id:101010})
    # - (:SomeNodeLabel{id:1338})-[:PARENT]->(:ParentNode{id:101010})
    # - (:SomeNodeLabel{id:1339})-[:PARENT]->(:ParentNode{id:202020})
    expected_nodes = {
        ('Some-Asset', 'Parent1'),
        ('Some-Other-Asset', 'Parent1'),
        ('Some-Other-Other-Asset', 'Parent2'),
    }
    nodes = neo4j_session.run("MATCH (s:SomeNodeLabel)-[:PARENT]->(p:ParentNode) return s.name, p.name")
    actual_nodes = {(n['s.name'], n['p.name']) for n in nodes}
    assert actual_nodes == expected_nodes


def test_merge_relationships_with_properties(neo4j_session):
    # Arrange: add 2 parent nodes to the graph, add test child nodes.
    neo4j_session.run("MERGE (p:ParentNode{id:101010, name:'Parent1'})")
    neo4j_session.run("MERGE (p:ParentNode{id:202020, name:'Parent2'})")
    merge_nodes(
        neo4j_session,
        'SomeNodeLabel',
        TEST_NODE_PROPERTY_MAP,
        TEST_NODE_DATA,
        TEST_UPDATE_TAG,
    )

    # Act: attach test nodes to the parent nodes by...
    relationship_mappings = [
        {'SomeNodeId': 1337, 'ParentId': 101010, 'RelAttrib': 'version1'},
        {'SomeNodeId': 1338, 'ParentId': 101010, 'RelAttrib': 'version2'},
        {'SomeNodeId': 1339, 'ParentId': 202020, 'RelAttrib': 'version1'},
    ]
    # setting the property map for relationship attributes.
    rel_property_map = {
        'rel_attrib': 'RelAttrib',
    }
    merge_relationships(
        neo4j_session,
        'SomeNodeLabel', 'id', 'SomeNodeId',
        'ParentNode', 'id', 'ParentId',
        'PARENT',
        relationship_mappings,
        TEST_UPDATE_TAG,
        rel_property_map,
    )

    # Assert
    # - (:SomeNodeLabel{id:1337})-[:PARENT{rel_attrib:'version1'}]->(:ParentNode{id:101010})
    # - (:SomeNodeLabel{id:1338})-[:PARENT{rel_attrib:'version2'}]->(:ParentNode{id:101010})
    # - (:SomeNodeLabel{id:1339})-[:PARENT{rel_attrib:'version1'}]->(:ParentNode{id:202020})
    expected = {
        ('Some-Asset', 'version1', 'Parent1'),
        ('Some-Other-Asset', 'version2', 'Parent1'),
        ('Some-Other-Other-Asset', 'version1', 'Parent2'),
    }
    items = neo4j_session.run("MATCH (s:SomeNodeLabel)-[r:PARENT]->(p:ParentNode) return s.name, r.rel_attrib, p.name")
    actual = {(n['s.name'], n['r.rel_attrib'], n['p.name']) for n in items}
    assert actual == expected
