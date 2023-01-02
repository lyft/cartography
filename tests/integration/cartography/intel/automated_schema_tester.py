def build_tester_queries(node_schema: CartographyNodeSchema) -> List[str]:
    return []


def test_all_nodes(neo4j_session):
    # Get all schemas from the models folder

    queries = build_tester_queries()

    #for query in queries: