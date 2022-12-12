MERGE_SUB_RESOURCE_QUERY = """
MERGE (s:SubResource{id: "sub-resource-id"})
ON CREATE SET s.lastupdated = 1
"""

MERGE_WORLD_ASSET_QUERY = """
MERGE (w:WorldAsset{id: "the-worldasset-id-1"})
ON CREATE SET w.lastupdated = 1
"""


# This dataset shows an InterestingNode attached to a WorldAsset but no other relationships.
INTERESTING_NODE_WITH_PARTIAL_RELATIONSHIPS = [
    {
        'Id': 'interesting-node-id',
        'property1': 'b',
        'property2': 'c',
        'AnotherField': 'd',
        'YetAnotherRelField': 'e',
        'world_asset_id': 'the-worldasset-id-1'
    }
]