from unittest.mock import Mock

import cartography.intel.gandi.organization
import tests.data.gandi.organization
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789
COMMON_JOB_PARAMETERS = {"UPDATE_TAG": TEST_UPDATE_TAG}


def test_load_gandi_organization(neo4j_session):
    """
    Ensure that organization actually get loaded
    """
    gandi_api = Mock(
        get_organizations=Mock(return_value=tests.data.gandi.organization.GANDI_ORGANIZATIONS),
    )

    # Act
    cartography.intel.gandi.organization.sync(
        neo4j_session,
        gandi_api,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMETERS,
    )

    # Assert organization exists
    expected_nodes = {
        ('1aeab22b-1c3e-4829-a64f-a51d52014073', 'LyftOSS'),
    }
    assert check_nodes(neo4j_session, 'GandiOrganization', ['id', 'name']) == expected_nodes
