import cartography.intel.gcp.dataflow
import cartography.intel.gcp.bigtable
import cartography.intel.gcp.bigquery
import cartography.intel.gcp.pubsub
import cartography.intel.gcp.spanner

import tests.data.gcp.dataflow
import tests.data.gcp.bigtable
import tests.data.gcp.bigquery
import tests.data.gcp.pubsub
import tests.data.gcp.spanner

TEST_PROJECT_ID = 'project-123'
TEST_UPDATE_TAG = 123456789


def test_dataflow_jobs(neo4j_session):
    data = tests.data.gcp.dataflow.TEST_DATAFLOW_JOBS
    cartography.intel.gcp.dataflow.load_dataflow_jobs(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )
    expected_nodes = {
        'job1'
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPDataFlowJob) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_dataflow_job_bigtable_relation(neo4j_session):
    data = tests.data.gcp.bigtable.BIGTABLE_TABLE
    cartography.intel.gcp.bigtable.load_bigtable_tables(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )
    data = tests.data.gcp.dataflow.TEST_DATAFLOW_JOBS
    cartography.intel.gcp.dataflow.load_dataflow_jobs(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )
    expected_nodes = {
        ('job1', 'table123'), ('job1', 'table456')
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:GCPDataFlowJob)-[:REFERENCES]->(m:GCPBigtableTable) RETURN n.id,m.id;
        """,
    )

    actual_nodes = {(n['n.id'], n['m.id']) for n in nodes}

    assert actual_nodes == expected_nodes


def test_dataflow_job_bigquery_relation(neo4j_session):
    data = tests.data.gcp.bigquery.TEST_TABLE
    cartography.intel.gcp.bigquery.load_bigquery_tables(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )
    data = tests.data.gcp.dataflow.TEST_DATAFLOW_JOBS
    cartography.intel.gcp.dataflow.load_dataflow_jobs(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )
    expected_nodes = {
        ('job1', 'table2'), ('job1', 'table1')
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:GCPDataFlowJob)-[:REFERENCES]->(m:GCPBigqueryTable) RETURN n.id,m.id;
        """,
    )

    actual_nodes = {(n['n.id'], n['m.id']) for n in nodes}

    assert actual_nodes == expected_nodes


def test_dataflow_job_pubsub_relation(neo4j_session):
    data = tests.data.gcp.pubsub.TEST_TOPICS
    cartography.intel.gcp.pubsub.load_pubsub_topics(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )
    data = tests.data.gcp.pubsub.TEST_SUBCRIPTIONS
    cartography.intel.gcp.pubsub.load_pubsub_subscriptions(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )
    data = tests.data.gcp.dataflow.TEST_DATAFLOW_JOBS
    cartography.intel.gcp.dataflow.load_dataflow_jobs(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )
    expected_nodes = {
        (
            'projects/project123/subscriptions/sub123',
            'job1',
            'projects/project123/topic/topic123'
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (o:GCPPubsubSubscription)<-[:REFERENCES]-(n:GCPDataFlowJob)-[:REFERENCES]->(m:GCPPubsubTopic) RETURN o.id,n.id,m.id;
        """,
    )

    actual_nodes = {(n['o.id'], n['n.id'], n['m.id']) for n in nodes}

    assert actual_nodes == expected_nodes


def test_dataflow_job_spanner_relation(neo4j_session):
    data = tests.data.gcp.spanner.TEST_INSTANCE_DATABASE
    cartography.intel.gcp.spanner.load_spanner_instances_databases(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )
    data = tests.data.gcp.dataflow.TEST_DATAFLOW_JOBS
    cartography.intel.gcp.dataflow.load_dataflow_jobs(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )
    expected_nodes = {
        ('job1',
         'projects/project-123/instances/instance1/databases/database1'),
        ('job1',
         'projects/project-123/instances/instance1/databases/database2'),
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:GCPDataFlowJob)-[:REFERENCES]->(m:GCPSpannerInstanceDatabase) RETURN n.id,m.id;
        """,
    )

    actual_nodes = {(n['n.id'], n['m.id']) for n in nodes}

    assert actual_nodes == expected_nodes
