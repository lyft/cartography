import cartography.intel.aws.route53
import tests.data.aws.route53

TEST_UPDATE_TAG = 123456789
TEST_ZONE_ID = "TESTZONEID"
TEST_ZONE_NAME = "TESTZONENAME"
TEST_AWS_ACCOUNTID = "AWSID"


def test_cname(neo4j_session):
    # test that cnames can be parsed and loaded
    data = tests.data.aws.route53.CNAME_RECORD
    parsed_data = cartography.intel.aws.route53.parse_record_set(data, TEST_ZONE_ID)
    cartography.intel.aws.route53.load_cname_records(neo4j_session, parsed_data, TEST_UPDATE_TAG)


def test_ns(neo4j_session):
    # test that ns records can be parsed and loaded
    data = tests.data.aws.route53.NS_RECORD
    parsed_data = [cartography.intel.aws.route53.parse_ns_record_set(data, TEST_ZONE_ID)]
    cartography.intel.aws.route53.load_ns_records(neo4j_session, parsed_data, TEST_ZONE_NAME, TEST_UPDATE_TAG)


def test_zone(neo4j_session):
    # testtest that zone are being added by zone id
    data = tests.data.aws.route53.ZONE_RECORDS

    for zone in data:
        parsed_zone = cartography.intel.aws.route53.parse_zone(zone)
        cartography.intel.aws.route53.load_zone(neo4j_session, parsed_zone, TEST_AWS_ACCOUNTID, TEST_UPDATE_TAG)
    result = neo4j_session.run("MATCH (n:AWSDNSZone) RETURN count(n) as zonecount")
    for r in result:
        assert r["zonecount"] == 2
