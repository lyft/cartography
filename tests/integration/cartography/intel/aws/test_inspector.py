from cartography.intel.aws.inspector import load_inspector_findings
from cartography.intel.aws.inspector import load_inspector_packages
from cartography.intel.aws.inspector import transform_inspector_findings
from tests.data.aws.inspector import LIST_FINDINGS_EC2_PACKAGE
from tests.data.aws.inspector import LIST_FINDINGS_NETWORK

TEST_UPDATE_TAG = 123456


def test_load_inspector_findings(neo4j_session):
    # Add some fake accounts
    neo4j_session.run(
        """
        MERGE (:AWSAccount{id: '123456789012'})
        MERGE (:AWSAccount{id: '123456789011'})
        """,
    )

    # Add some fake findings
    neo4j_session.run(
        """
        MERGE (:AWSInspectorFinding{id: 'arn:aws:test123', awsaccount: "123456789011"})
        MERGE (:AWSInspectorFinding{id: 'arn:aws:test456', awsaccount: "123456789012"})
        """,
    )

    # Ensure the findings are loaded
    actual = (
        neo4j_session.run(
            "MATCH(:AWSInspectorFinding) RETURN count(*) as count",
        )
        .single()
        .value()
    )
    expected = 2
    assert actual == expected

    # Add some fake instances
    neo4j_session.run(
        """
        MERGE (:EC2Instance{id: 'i-instanceid', instanceid: 'i-instanceid', awsaccount: "123456789011"})
        MERGE (:EC2Instance{id: 'i-88503981029833100', instanceid: 'i-88503981029833100', awsaccount: "123456789012"})
        """,
    )

    # Ensure the instances are loaded
    actual = (
        neo4j_session.run(
            "MATCH(:EC2Instance) RETURN count(*) as count",
        )
        .single()
        .value()
    )
    expected = 2
    assert actual == expected

    # Transform the mock data
    transformed_network_findings, _ = transform_inspector_findings(
        LIST_FINDINGS_NETWORK
    )
    (
        transformed_ec2_findings,
        transformed_package_findings,
    ) = transform_inspector_findings(LIST_FINDINGS_EC2_PACKAGE)

    # Load the mock data
    load_inspector_findings(
        neo4j_session, transformed_network_findings, "us-west-2", TEST_UPDATE_TAG
    )
    load_inspector_findings(
        neo4j_session, transformed_ec2_findings, "us-west-2", TEST_UPDATE_TAG
    )
    load_inspector_packages(
        neo4j_session, transformed_package_findings, "us-west-2", TEST_UPDATE_TAG
    )

    # Check Findings
    nodes = neo4j_session.run(
        "MATCH (a:AWSInspectorFinding) return a.instanceid",
    )
    actual_nodes = {(n["a.instanceid"]) for n in nodes}
    expected_nodes = {
        "i-instanceid",
        "i-88503981029833100",
    }
    assert actual_nodes == set(expected_nodes)

    # Check Packages
    nodes = neo4j_session.run(
        "MATCH (a:AWSInspectorPackage) return a.id",
    )
    actual_nodes = {(n["a.id"]) for n in nodes}
    expected_nodes = {
        "kernel|X86_64|4.9.17|6.29.amzn1|0",
        "kernel-tools|X86_64|4.9.17|6.29.amzn1|0",
    }
    assert actual_nodes == set(expected_nodes)

    # Check Finding:Package relationship
    nodes = neo4j_session.run(
        """MATCH (:AWSInspectorFinding)-[:AFFECTS]->(a:AWSInspectorPackage)
        RETURN a.id""",
    )
    actual_nodes = {(n["a.id"]) for n in nodes}
    expected_nodes = [
        "kernel-tools|X86_64|4.9.17|6.29.amzn1|0",
        "kernel|X86_64|4.9.17|6.29.amzn1|0",
    ]
    assert actual_nodes == set(expected_nodes)

    # Check Finding:AWSAccount relationship
    nodes = neo4j_session.run(
        """MATCH (a:AWSAccount)-[:RESOURCE]->(:AWSInspectorFinding)
        RETURN a.id""",
    )
    actual_nodes = {(n["a.id"]) for n in nodes}

    expected_nodes = [
        "123456789011",
        "123456789012",
    ]
    assert actual_nodes == set(expected_nodes)

    # Check Package:AWSAccount relationship
    nodes = neo4j_session.run(
        """MATCH (a:AWSAccount)-[:RESOURCE]->(:AWSInspectorPackage)
        RETURN a.id""",
    )
    actual_nodes = {(n["a.id"]) for n in nodes}
    expected_nodes = [
        "123456789012",
        "123456789012",
    ]
    assert actual_nodes == set(expected_nodes)

    # Check Instance:Finding relationship
    nodes = neo4j_session.run(
        """MATCH (:EC2Instance)<-[:PRESENT_ON]-(a:AWSInspectorFinding)
        RETURN a.id""",
    )
    actual_nodes = {(n["a.id"]) for n in nodes}
    expected_nodes = [
        "arn:aws:test123",
        "arn:aws:test456",
    ]
    assert actual_nodes == set(expected_nodes)
