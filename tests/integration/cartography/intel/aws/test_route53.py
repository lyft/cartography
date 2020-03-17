import cartography.intel.aws.route53
import tests.data.aws.route53

TEST_UPDATE_TAG = 123456789
TEST_ZONE_ID = "TESTZONEID"
TEST_ZONE_NAME = "TESTZONENAME"
TEST_AWS_ACCOUNTID = "AWSID"


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
