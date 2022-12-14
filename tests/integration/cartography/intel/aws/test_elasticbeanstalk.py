import cartography.intel.aws.elasticbeanstalk
import tests.data.aws.elasticbeanstalk

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'eu-west-1'
TEST_UPDATE_TAG = 123456789


def test_load_repository_associations(neo4j_session):
    data = tests.data.aws.elasticbeanstalk.GET_ELASTICBEANSTALK_APPLICATION
    cartography.intel.aws.elasticbeanstalk.load_elasticbeanstalk_applications(
        neo4j_session,
        data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_elasticbeanstalkapplication = {
        "arn:aws:elasticbeanstalk:us-east-1:000000000000:application/Scorekeep",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:ElasticBeanStalkApplication) RETURN r.arn;
        """,
    )

    actual_elasticbeanstalkapplication = {n['r.arn'] for n in nodes}

    assert expected_elasticbeanstalkapplication == actual_elasticbeanstalkapplication

    expected_elasticbeanstalkenvironment = {
        "arn:aws:elasticbeanstalk:us-east-1:000000000000:environment/Scorekeep/BETA",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:ElasticBeanStalkEnvironment) RETURN r.arn;
        """,
    )

    actual_elasticbeanstalkenvironment = {n['r.arn'] for n in nodes}

    assert expected_elasticbeanstalkenvironment == actual_elasticbeanstalkenvironment

    expected_elasticbeanstalversion = {
        "arn:aws:elasticbeanstalk:us-east-1:000000000000:applicationversion/Scorekeep/scorekeep-version-abcdefgh",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:ElasticBeanStalkVersion) RETURN r.arn;
        """,
    )

    actual_elasticbeanstalkversion = {n['r.arn'] for n in nodes}

    assert expected_elasticbeanstalversion == actual_elasticbeanstalkversion
