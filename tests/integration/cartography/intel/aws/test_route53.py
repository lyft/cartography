import cartography.intel.aws.route53
import cartography.util
import tests.data.aws.route53

TEST_UPDATE_TAG = 123456789
TEST_ZONE_ID = "TESTZONEID"
TEST_ZONE_NAME = "TESTZONENAME"
TEST_AWS_ACCOUNTID = "AWSID"
TEST_AWS_REGION = "us-east-1"


def _ensure_local_neo4j_has_test_route53_records(neo4j_session):
    cartography.intel.aws.route53.load_dns_details(
        neo4j_session, tests.data.aws.route53.GET_ZONES_SAMPLE_RESPONSE,
        TEST_AWS_ACCOUNTID, TEST_UPDATE_TAG,
    )
    cartography.intel.aws.route53.link_sub_zones(neo4j_session, TEST_UPDATE_TAG)


def _ensure_local_neo4j_has_test_ec2_records(neo4j_session):
    cartography.intel.aws.ec2.load_balancer_v2s.load_load_balancer_v2s(
        neo4j_session, tests.data.aws.ec2.load_balancers.LOAD_BALANCER_DATA,
        TEST_AWS_REGION, TEST_AWS_ACCOUNTID, TEST_UPDATE_TAG,
    )


def test_transform_and_load_ns(neo4j_session):
    # Test that NS records can be parsed and loaded
    data = tests.data.aws.route53.NS_RECORD
    parsed_data = cartography.intel.aws.route53.transform_ns_record_set(data, TEST_ZONE_ID)
    assert "ns-856.awsdns-43.net" in parsed_data["servers"]
    cartography.intel.aws.route53.load_ns_records(neo4j_session, [parsed_data], TEST_ZONE_NAME, TEST_UPDATE_TAG)


def test_transform_and_load_zones(neo4j_session):
    # Test that zones are being added by zone id
    data = tests.data.aws.route53.ZONE_RECORDS

    for zone in data:
        parsed_zone = cartography.intel.aws.route53.transform_zone(zone)
        cartography.intel.aws.route53.load_zone(neo4j_session, parsed_zone, TEST_AWS_ACCOUNTID, TEST_UPDATE_TAG)
    result = neo4j_session.run("MATCH (n:AWSDNSZone) RETURN count(n) as zonecount")
    for r in result:
        assert r["zonecount"] == 2


def test_transform_and_load_cname_records(neo4j_session):
    # Test that CNAME records are correctly transformed and loaded
    data = tests.data.aws.route53.CNAME_RECORD
    first_data = cartography.intel.aws.route53.transform_record_set(data, TEST_ZONE_ID, data['Name'][:-1])
    cartography.intel.aws.route53.load_cname_records(neo4j_session, first_data, TEST_UPDATE_TAG)

    second_data = cartography.intel.aws.route53.transform_record_set(data, TEST_ZONE_ID + "2", data['Name'][:-1])
    cartography.intel.aws.route53.load_cname_records(neo4j_session, second_data, TEST_UPDATE_TAG)
    result = neo4j_session.run("MATCH (n:AWSDNSRecord{name:'subdomain.lyft.com'}) return count(n) as recordcount")
    for r in result:
        assert r["recordcount"] == 2


def test_transform_and_load_ns_records(neo4j_session):
    # Test that NS records are correctly transformed and loaded
    data = tests.data.aws.route53.NS_RECORD
    first_data = [cartography.intel.aws.route53.transform_ns_record_set(data, TEST_ZONE_ID)]
    cartography.intel.aws.route53.load_ns_records(neo4j_session, first_data, TEST_ZONE_NAME, TEST_UPDATE_TAG)

    second_data = [cartography.intel.aws.route53.transform_ns_record_set(data, TEST_ZONE_ID + "2")]
    cartography.intel.aws.route53.load_ns_records(neo4j_session, second_data, TEST_ZONE_NAME, TEST_UPDATE_TAG)
    result = neo4j_session.run("MATCH (n:AWSDNSRecord{name:'testdomain.net'}) return count(n) as recordcount")
    for r in result:
        assert r["recordcount"] == 2


def test_load_dnspointsto_ec2_relationships(neo4j_session):
    """
    1. Load DNS and EC2 resources
    2. Ensure that the expected :DNS_POINTS_TO relationships have been created
    """
    # EC2 resources must be loaded first; it's the Route53 module that links DNS to EC2 resources.
    _ensure_local_neo4j_has_test_ec2_records(neo4j_session)
    _ensure_local_neo4j_has_test_route53_records(neo4j_session)

    # Verify that the expected DNS record points to the expected ELBv2
    result = neo4j_session.run(
        """
        MATCH (n:AWSDNSRecord{id:"/hostedzone/HOSTED_ZONE/elbv2.example.com/ALIAS"})
        -[:DNS_POINTS_TO]->(l:LoadBalancerV2{id:"myawesomeloadbalancer.amazonaws.com"})
        return n.name, l.name
        """,
    )
    expected = {("elbv2.example.com", "myawesomeloadbalancer")}
    actual = {(r['n.name'], r['l.name']) for r in result}
    assert actual == expected


def test_load_and_cleanup_dnspointsto_relationships(neo4j_session):
    """
    1. Load DNS resources
    2. Link them together
    3. Ensure that the expected :DNS_POINTS_TO relationships have been created
    4. Assume that these nodes are now stale and perform cleanup
    5. Ensure that the :DNS_POINTS_TO relationships have been deleted
    """
    _ensure_local_neo4j_has_test_route53_records(neo4j_session)
    # Now, have one DNS record point to another object.
    # This is to simulate having a DNS record pointing to a node that was synced in another module.
    neo4j_session.run(
        """
        MERGE (n1:AWSDNSRecord{id:"/hostedzone/HOSTED_ZONE/example.com/NS"})
        -[:DNS_POINTS_TO]->(:NewTestAsset{name:"hello"})
        """,
    )

    # Verify that the expected AWS DNS records point to each other
    result = neo4j_session.run(
        """
        MATCH (n1:AWSDNSRecord{id:"/hostedzone/HOSTED_ZONE/example.com/NS"})-[:DNS_POINTS_TO]->(n2:AWSDNSRecord)
        RETURN n1.name, n2.id
        """,
    )
    expected = {("example.com", "/hostedzone/HOSTED_ZONE/example.com/A")}
    actual = {(r['n1.name'], r['n2.id']) for r in result}
    assert actual == expected

    new_update_tag = 1337
    new_job_parameters = {
        "UPDATE_TAG": new_update_tag,
        "AWS_ID": TEST_AWS_ACCOUNTID,
    }
    # Run all cleanup jobs where DNS_POINTS_TO is mentioned in the AWS sync.
    cartography.intel.aws.route53.cleanup_route53(neo4j_session, TEST_AWS_ACCOUNTID, new_update_tag)
    cartography.intel.aws.elasticsearch.cleanup(
        neo4j_session, update_tag=new_update_tag, aws_account_id=TEST_AWS_ACCOUNTID,
    )
    cartography.util.run_cleanup_job('aws_account_dns_cleanup.json', neo4j_session, new_job_parameters)
    cartography.util.run_cleanup_job('aws_post_ingestion_dns_cleanup.json', neo4j_session, new_job_parameters)

    # Verify that the AWSDNSRecord-->AWSDNSRecord relationships don't exist anymore
    result = neo4j_session.run(
        """
        MATCH (n1:AWSDNSRecord{id:"/hostedzone/HOSTED_ZONE/example.com/NS"})-[:DNS_POINTS_TO]->(n2:AWSDNSRecord)
        RETURN count(n2) as recordcount
        """,
    )
    for r in result:
        assert r["recordcount"] == 0

    # Verify that the AWSDNSRecord-->NewTestAsset relationship still exists
    result = neo4j_session.run(
        """
        MATCH (n1:AWSDNSRecord{id:"/hostedzone/HOSTED_ZONE/example.com/NS"})-[:DNS_POINTS_TO]->(n2:NewTestAsset)
        RETURN n1.id, n2.name
        """,
    )
    actual = {(r['n1.id'], r['n2.name']) for r in result}
    expected = {("/hostedzone/HOSTED_ZONE/example.com/NS", "hello")}
    print(actual)
    print(expected)
    assert actual == expected
