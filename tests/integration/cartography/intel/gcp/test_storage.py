import cartography.intel.gcp.storage
import tests.data.gcp.storage


TEST_UPDATE_TAG = 123456789


def test_transform_and_load_storage_buckets(neo4j_session):
    """
    Test that we can correctly transform and load GCP Storage Buckets to Neo4j.
    """
    bucket_res = tests.data.gcp.storage.STORAGE_RESPONSE
    bucket_list = cartography.intel.gcp.storage.transform_gcp_buckets(bucket_res)
    cartography.intel.gcp.storage.load_gcp_buckets(neo4j_session, bucket_list, TEST_UPDATE_TAG)

    query = """
    MATCH(bucket:GCPBucket{id:{BucketId}})
    RETURN bucket.id, bucket.project_number, bucket.kind
    """
    expected_id = 'bucket_name'
    expected_project_num = 9999
    expected_kind = 'storage#bucket'
    nodes = neo4j_session.run(
        query,
        BucketId=expected_id,
    )
    actual_nodes = {(n['bucket.id'], n['bucket.project_number'], n['bucket.kind']) for n in nodes}
    expected_nodes = {
        (expected_id, expected_project_num, expected_kind),
    }
    assert actual_nodes == expected_nodes
