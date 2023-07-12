import cartography.intel.gcp.sql
import tests.data.gcp.sql
import tests.data.gcp.compute
import cartography.intel.gcp.compute
from cartography.util import run_analysis_job

TEST_WORKSPACE_ID = '1223344'
TEST_PROJECT_NUMBER = '000000000000'
TEST_UPDATE_TAG = 123456789

common_job_parameters = {
    "UPDATE_TAG": TEST_UPDATE_TAG,
    "WORKSPACE_ID": '1223344',
    "GCP_PROJECT_ID": TEST_PROJECT_NUMBER 
,
}

def cloudanix_workspace_to_gcp_project(neo4j_session):
    query = """
    MERGE (w:CloudanixWorkspace{id: $WorkspaceId})
    MERGE (project:GCPProject{id: $ProjectId})
    MERGE (w)-[:OWNER]->(project)
    """
    nodes = neo4j_session.run(
        query,
        WorkspaceId=TEST_WORKSPACE_ID,
        ProjectId=TEST_PROJECT_NUMBER,
    )


def test_load_sql_instances(neo4j_session):
    data = tests.data.gcp.sql.CLOUD_SQL_INSTANCES
    cartography.intel.gcp.sql.load_sql_instances(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "instance123",
        "instance456",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPSQLInstance) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_sql_users(neo4j_session):
    data = tests.data.gcp.sql.CLOUD_SQL_USERS
    cartography.intel.gcp.sql.load_sql_users(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "user123",
        "user456",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPSQLUser) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_sql_databases(neo4j_session):
    data = tests.data.gcp.sql.CLOUD_SQL_DATABASES
    cartography.intel.gcp.sql.load_sql_databases(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "database-123",
        "database-456",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPSQLDatabase) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_sql_instance_relationships(neo4j_session):
    # Create Test GCP Project
    neo4j_session.run(
        """
        MERGE (gcp:GCPProject{id: $PROJECT_NUMBER})
        ON CREATE SET gcp.firstseen = timestamp()
        SET gcp.lastupdated = $UPDATE_TAG
        """,
        PROJECT_NUMBER=TEST_PROJECT_NUMBER,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Load SQL Instances
    data = tests.data.gcp.sql.CLOUD_SQL_INSTANCES
    cartography.intel.gcp.sql.load_sql_instances(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected = {
        (TEST_PROJECT_NUMBER, "instance123"),
        (TEST_PROJECT_NUMBER, "instance456"),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPProject)-[:RESOURCE]->(n2:GCPSQLInstance) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_public_ip_address(neo4j_session):
    # Load test SQL Instances
    data = tests.data.gcp.sql.CLOUD_SQL_INSTANCES
    cartography.intel.gcp.sql.load_sql_instances(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    
    for inst in data:
        cartography.intel.gcp.sql.load_public_ip_address(
            neo4j_session,
            inst,
            TEST_PROJECT_NUMBER,
            TEST_UPDATE_TAG,
            )

        expected = {
            ('instance123', '103.34.34.1'),
            ('instance456', '104.34.34.1')
            }
    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPSQLInstance)-[r:MEMBER_OF_PUBLIC_IP_ADDRESS]->(n2:GCPPublicIpAddress) RETURN n1.id, n2.ipAddress;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.ipAddress']) for r in result
    }
    assert actual == expected


def test_load_sql_instances_vpc_network(neo4j_session):
    # Load test SQL Instances
    data = tests.data.gcp.sql.CLOUD_SQL_INSTANCES
    cartography.intel.gcp.sql.load_sql_instances(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )
 # vpc 
    vpc_res = tests.data.gcp.compute.VPC_RESPONSE
    vpc_list = cartography.intel.gcp.compute.transform_gcp_vpcs(vpc_res)
    
    cartography.intel.gcp.compute.load_gcp_vpcs(neo4j_session, vpc_list, TEST_UPDATE_TAG)
    for insta in data:
        cartography.intel.gcp.sql.load_sql_instances_vpc_network(neo4j_session, insta,TEST_PROJECT_NUMBER, TEST_UPDATE_TAG)
    expected = {
        ('instance123', 'projects/project-abc/global/networks/default'),
        ('instance456', 'projects/project-abc/global/networks/default'),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPSQLInstance)-[:VPC_NETWORK]->(n2:GCPVpc) RETURN n1.id, n2.id;
        """,
    )
   
    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }
    assert actual == expected


def test_sql_user_relationship(neo4j_session):
    # Load test SQL Instances
    data = tests.data.gcp.sql.CLOUD_SQL_INSTANCES
    cartography.intel.gcp.sql.load_sql_instances(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    # Load test SQL Users
    data = tests.data.gcp.sql.CLOUD_SQL_USERS
    cartography.intel.gcp.sql.load_sql_users(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected = {
        ('instance123', 'user123'),
        ('instance456', 'user456'),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPSQLInstance)-[:USED_BY]->(n2:GCPSQLUser) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected

def test_sql_instance_public_facing(neo4j_session):

    test_load_sql_instances(neo4j_session)
    test_sql_instance_relationships(neo4j_session)
    cloudanix_workspace_to_gcp_project(neo4j_session)

    run_analysis_job('gcp_sql_instance_analysis.json',neo4j_session,common_job_parameters)

    query1 = """
    MATCH (i:GCPSQLInstance)<-[:RESOURCE]-(:GCPProject{id: $GCP_PROJECT_ID})<-[:OWNER]-(:CloudanixWorkspace{id: $WORKSPACE_ID}) \nWHERE i.exposed_internet = true
    RETURN i.name
    """

    objects = neo4j_session.run(query1, GCP_PROJECT_ID=TEST_PROJECT_NUMBER, WORKSPACE_ID=TEST_WORKSPACE_ID)

    actual_nodes = {
        (
            o['i.name'],

        ) for o in objects
        
    }

    expected_nodes = {
        (
            'sqlinstance123',
        )
    }
    assert actual_nodes == expected_nodes