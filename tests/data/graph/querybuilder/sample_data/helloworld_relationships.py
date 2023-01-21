MERGE_SUB_RESOURCE_QUERY = """
MERGE (s:SubResource{id: "sub-resource-id"})
ON CREATE SET s.lastupdated = 1
"""


MERGE_HELLO_ASSET_QUERY = """
MERGE (h:HelloAsset{id: "the-helloasset-id-1"})
ON CREATE SET h.lastupdated = 1
"""


MERGE_WORLD_ASSET_QUERY = """
MERGE (w:WorldAsset{id: "the-worldasset-id-1"})
ON CREATE SET w.lastupdated = 1
"""


# This dataset shows an InterestingNode attached to a WorldAsset but no other relationships.
INTERESTING_NODE_WITH_PARTIAL_RELS = [
    {
        'Id': 'interesting-node-id',
        'property1': 'b',
        'property2': 'c',
        'AnotherField': 'd',
        'YetAnotherRelField': 'e',
        'world_asset_id': 'the-worldasset-id-1',
    },
]

# This dataset shows an InterestingNode attached to a HelloAsset and a WorldAsset.
INTERESTING_NODE_WITH_ALL_RELS = [
    {
        'Id': 'interesting-node-id',
        'property1': 'b',
        'property2': 'c',
        'AnotherField': 'd',
        'YetAnotherRelField': 'e',
        'world_asset_id': 'the-worldasset-id-1',
        'hello_asset_id': 'the-helloasset_id-1',
    },
]
