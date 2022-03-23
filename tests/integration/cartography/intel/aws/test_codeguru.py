import cartography.intel.aws.codeguru
import tests.data.aws.codeguru

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'eu-west-1'
TEST_UPDATE_TAG = 123456789


def test_load_repository_associations(neo4j_session):
    data = tests.data.aws.codeguru.GET_REPOSITORY_ASSOCIATIONS
    cartography.intel.aws.codeguru.load_repository_associations(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "test-001",
        "test-002",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:CodeguruAssociation) RETURN r.owner;
        """,
    )
    actual_nodes = {n['r.owner'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_repository_associations_relationships(neo4j_session):
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: {aws_account_id}})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = {aws_update_tag}
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        aws_update_tag=TEST_UPDATE_TAG,
    )

    data = tests.data.aws.codeguru.GET_REPOSITORY_ASSOCIATIONS
    cartography.intel.aws.codeguru.load_repository_associations(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    expected = {
        (TEST_ACCOUNT_ID, 'test-001'),
        (TEST_ACCOUNT_ID, 'test-002'),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AWSAccount)-[:RESOURCE]->(n2:CodeguruAssociation) RETURN n1.id, n2.owner;
        """,
    )
    actual = {
        (r['n1.id'], r['n2.owner']) for r in result
    }

    assert actual == expected


def test_load_code_reviews(neo4j_session):
    data = tests.data.aws.codeguru.GET_CODE_REVIEWS
    cartography.intel.aws.codeguru.load_code_reviews(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "test-001",
        "test-002",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:CodeguruCodereview) RETURN r.owner;
        """,
    )
    actual_nodes = {n['r.owner'] for n in nodes}

    assert actual_nodes == expected_nodes

    data = tests.data.aws.codeguru.GET_RECOMMENDATIONS
    cartography.intel.aws.codeguru.load_recommendations(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "desc001",
        "desc002",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:CodeguruRecommendation) RETURN r.description;
        """,
    )
    actual_nodes = {n['r.description'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_codereviews_relationships(neo4j_session):

    data_association = tests.data.aws.codeguru.GET_REPOSITORY_ASSOCIATIONS
    cartography.intel.aws.codeguru.load_repository_associations(
        neo4j_session,
        data_association,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    data_codereview = tests.data.aws.codeguru.GET_CODE_REVIEWS
    cartography.intel.aws.codeguru.load_code_reviews(
        neo4j_session,
        data_codereview,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected = {
        ('AssociationId001', 'test-001'),
        ('AssociationId002', 'test-002'),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:CodeguruAssociation)-[:HAS_CODEREVIEW]->(n2:CodeguruCodereview) RETURN n1.associationid,n2.owner;
        """,
    )
    actual = {
        (r['n1.associationid'], r['n2.owner']) for r in result
    }

    assert actual == expected


def test_load_recommendations(neo4j_session):
    data = tests.data.aws.codeguru.GET_RECOMMENDATIONS
    cartography.intel.aws.codeguru.load_recommendations(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "desc001",
        "desc002",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:CodeguruRecommendation) RETURN r.description;
        """,
    )
    actual_nodes = {n['r.description'] for n in nodes}
    assert actual_nodes == expected_nodes


def test_load_recommendations_relationships(neo4j_session):
    data_codereview = tests.data.aws.codeguru.GET_CODE_REVIEWS
    cartography.intel.aws.codeguru.load_code_reviews(
        neo4j_session,
        data_codereview,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    data_recommendation = tests.data.aws.codeguru.GET_RECOMMENDATIONS
    cartography.intel.aws.codeguru.load_recommendations(
        neo4j_session,
        data_recommendation,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected = {
        ('test-001', 'desc001'),
        ('test-002', 'desc002'),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:CodeguruCodereview)-[:HAS_RECOMMENDATION]->(n2:CodeguruRecommendation) RETURN n1.owner,n2.description;
        """,
    )
    actual = {
        (r['n1.owner'], r['n2.description']) for r in result
    }

    assert actual == expected
