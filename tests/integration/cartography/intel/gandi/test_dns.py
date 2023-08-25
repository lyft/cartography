from unittest.mock import Mock

import cartography.intel.gandi.organization
import cartography.intel.gandi.zones
import tests.data.gandi.organization
import tests.data.gandi.zones
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
COMMON_JOB_PARAMETERS = {"UPDATE_TAG": TEST_UPDATE_TAG}


def test_load_gandi_zones(neo4j_session):
    """
    Ensure that zones actually get loaded
    """
    gandi_api = Mock(
        get_organizations=Mock(return_value=tests.data.gandi.organization.GANDI_ORGANIZATIONS),
        get_domains=Mock(return_value=tests.data.gandi.zones.GANDI_DNS_ZONES),
    )

    # Act
    cartography.intel.gandi.organization.sync(
        neo4j_session,
        gandi_api,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMETERS,
    )
    cartography.intel.gandi.zones.sync(
        neo4j_session,
        gandi_api,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMETERS,
    )

    # Assert zones exists
    expected_nodes = {
        ('3c31bfaa-3ba9-4f10-b468-404762ffa6a0', 'lyft.com', 'com', '1aeab22b-1c3e-4829-a64f-a51d52014073'),
    }
    assert check_nodes(neo4j_session, 'GandiDNSZone', ['id', 'name', 'tld', 'organization_id']) == expected_nodes

    # Asserts records exists
    expected_nodes = {
        ('e1c458121cc75d19801a5fc261267446', None, 'NS', 'lyft.com'),
        ('09ca0af5ae3a005d87fd617c734006cc', None, 'NS', 'lyft.com'),
        ('71b0716bcebab7d820f34417a7c8e017', '_DMARC', 'CNAME', 'lyft.com'),
        ('32b136cf5f96c5240362292782772fa1', '@', 'A', 'lyft.com'),
        ('31c058a2af95ce4a763113adc7af8a65', '@', 'TXT', 'lyft.com'),
        ('aadda9b146e8ac211703fe758eea7579', None, 'NS', 'lyft.com'),
    }
    assert check_nodes(neo4j_session, 'GandiDNSRecord', ['id', 'name', 'type', 'registered_domain']) == expected_nodes

    # Asserts ips exists
    expected_nodes = {
        ('1.1.1.1',),
    }
    assert check_nodes(neo4j_session, 'Ip', ['ip']) == expected_nodes

    # Asserts zones are linked to organizations
    expected_rels = {
        ('1aeab22b-1c3e-4829-a64f-a51d52014073', '3c31bfaa-3ba9-4f10-b468-404762ffa6a0'),
    }
    assert check_rels(
        neo4j_session,
        'GandiOrganization', 'id',
        'GandiDNSZone', 'id',
        'RESOURCE',
        rel_direction_right=True,
    ) == expected_rels

    # Asserts records are linked to zones
    expected_rels = {
        ('3c31bfaa-3ba9-4f10-b468-404762ffa6a0', 'e1c458121cc75d19801a5fc261267446'),
        ('3c31bfaa-3ba9-4f10-b468-404762ffa6a0', '09ca0af5ae3a005d87fd617c734006cc'),
        ('3c31bfaa-3ba9-4f10-b468-404762ffa6a0', 'aadda9b146e8ac211703fe758eea7579'),
        ('3c31bfaa-3ba9-4f10-b468-404762ffa6a0', '71b0716bcebab7d820f34417a7c8e017'),
        ('3c31bfaa-3ba9-4f10-b468-404762ffa6a0', '31c058a2af95ce4a763113adc7af8a65'),
        ('3c31bfaa-3ba9-4f10-b468-404762ffa6a0', '32b136cf5f96c5240362292782772fa1'),
    }
    assert check_rels(
        neo4j_session,
        'GandiDNSZone', 'id',
        'GandiDNSRecord', 'id',
        'RESOURCE',
        rel_direction_right=True,
    ) == expected_rels

    # Asserts records are linked to ips
    excepted_rels = {
        ('32b136cf5f96c5240362292782772fa1', '1.1.1.1'),
    }
    assert check_rels(
        neo4j_session,
        'GandiDNSRecord', 'id',
        'Ip', 'ip',
        'DNS_POINTS_TO',
        rel_direction_right=True,
    ) == excepted_rels
