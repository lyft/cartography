from unittest.mock import Mock

from cartography.intel.duo.api_host import sync_duo_api_host
from cartography.intel.duo.endpoints import sync_duo_endpoints
from cartography.intel.duo.groups import sync_duo_groups
from cartography.intel.duo.users import sync_duo_users
from tests.data.duo.endpoints import GET_ENDPOINTS_RESPONSE
from tests.data.duo.groups import GET_GROUPS_RESPONSE
from tests.data.duo.users import GET_USERS_RESPONSE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_API_HOSTNAME = 'https://api-1234.duo.com'
COMMON_JOB_PARAMETERS = {
    'DUO_API_HOSTNAME': TEST_API_HOSTNAME,
    'UPDATE_TAG': TEST_UPDATE_TAG,
}


def test_sync_duo_users(neo4j_session):
    # Arrange
    mock_client = Mock(
        get_users=Mock(return_value=GET_USERS_RESPONSE),
        get_groups=Mock(return_value=GET_GROUPS_RESPONSE),
        get_endpoints=Mock(return_value=GET_ENDPOINTS_RESPONSE),
    )

    # Act
    sync_duo_api_host(neo4j_session, COMMON_JOB_PARAMETERS)
    sync_duo_endpoints(mock_client, neo4j_session, COMMON_JOB_PARAMETERS)
    sync_duo_groups(mock_client, neo4j_session, COMMON_JOB_PARAMETERS)
    neo4j_session.run(
        'UNWIND $data as item MERGE (h:Human{email: item.email})',
        data=GET_USERS_RESPONSE,
    )
    sync_duo_users(mock_client, neo4j_session, COMMON_JOB_PARAMETERS)

    # Assert
    assert check_nodes(
        neo4j_session,
        'DuoUser',
        ['id', 'user_id', 'username', 'email'],
    ) == {
        ('userid1', 'userid1', 'username1', 'email1@example.com'),
        ('userid2', 'userid2', 'username2', 'email2@example.com'),
        ('userid3', 'userid3', 'username3', 'email3@example.com'),
        ('userid4', 'userid4', 'username4', 'email4@example.com'),
    }

    assert check_rels(
        neo4j_session,
        'DuoApiHost', 'id',
        'DuoUser', 'id',
        'RESOURCE',
        rel_direction_right=True,
    ) == {
        (TEST_API_HOSTNAME, 'userid1'),
        (TEST_API_HOSTNAME, 'userid2'),
        (TEST_API_HOSTNAME, 'userid3'),
        (TEST_API_HOSTNAME, 'userid4'),
    }

    assert check_rels(
        neo4j_session,
        'DuoUser', 'id',
        'DuoEndpoint', 'id',
        'ENDPOINT_DUO',
        rel_direction_right=True,
    ) == {
        ('userid1', 'epkey1'),
        ('userid2', 'epkey2'),
        ('userid3', 'epkey3'),
        ('userid4', 'epkey4'),
    }

    assert check_rels(
        neo4j_session,
        'DuoGroup', 'id',
        'DuoUser', 'id',
        'GROUP_DUO',
        rel_direction_right=True,
    ) == {
        ('groupid1', 'userid1'),
        ('groupid2', 'userid1'),
        ('groupid2', 'userid2'),
        ('groupid3', 'userid3'),
        ('groupid4', 'userid4'),
    }

    assert check_rels(
        neo4j_session,
        'Human', 'email',
        'DuoUser', 'email',
        'IDENTITY_DUO',
        rel_direction_right=True,
    ) == {
        ('email1@example.com', 'email1@example.com'),
        ('email2@example.com', 'email2@example.com'),
        ('email3@example.com', 'email3@example.com'),
        ('email4@example.com', 'email4@example.com'),
    }
