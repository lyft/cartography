import cartography.intel.clevercloud.addons
import cartography.intel.clevercloud.applications
import cartography.intel.clevercloud.organization
import tests.data.clevercloud.addons
import tests.data.clevercloud.apps
import tests.data.clevercloud.organization


COMMON_JOB_PARAMETERS = {
    "UPDATE_TAG": 123456789,
    "ORG_ID": 'orga_f3b3bb57-db31-4dff-8708-0dd91cc31826',
}


def test_load_clevercloud_apps_and_addons(neo4j_session):

    cartography.intel.clevercloud.organization.load(
        neo4j_session,
        tests.data.clevercloud.organization.CLEVERCLOUD_ORGANIZATION,
        COMMON_JOB_PARAMETERS,
    )

    cartography.intel.clevercloud.addons.load(
        neo4j_session,
        tests.data.clevercloud.addons.CLEVERCLOUD_ADDONS,
        COMMON_JOB_PARAMETERS,
    )

    data = tests.data.clevercloud.apps.CLEVERCLOUD_APPS
    apps, vhosts = cartography.intel.clevercloud.applications.transform(data)
    cartography.intel.clevercloud.applications.load(
        neo4j_session,
        apps,
        vhosts,
        COMMON_JOB_PARAMETERS,
    )

    # Ensure addon got loaded
    nodes = neo4j_session.run(
        """
        MATCH (a:CleverCloudAddon) RETURN a.id, a.name;
        """,
    )
    expected_nodes = {
        ("addon_f9deff34-d8cc-4bfb-995b-c1d0db37067c", "dummy-db-production"),
    }
    actual_nodes = {
        (
            n['a.id'],
            n['a.name'],
        ) for n in nodes
    }
    assert actual_nodes == expected_nodes

    # Ensure app got loaded
    nodes = neo4j_session.run(
        """
        MATCH (a:CleverCloudApplication) RETURN a.id, a.name;
        """,
    )
    expected_nodes = {
        ("app_6cb7fded-72d8-4994-b813-c7caa2208019", "dummy-api-production"),
    }
    actual_nodes = {
        (
            n['a.id'],
            n['a.name'],
        ) for n in nodes
    }
    assert actual_nodes == expected_nodes

    # Ensure link addon - organization
    nodes = neo4j_session.run(
        """
        MATCH(a:CleverCloudAddon)-[:RESOURCE]->(org:CleverCloudOrganization)
        RETURN a.id, org.id
        """,
    )
    actual_nodes = {
        (
            n['a.id'],
            n['org.id'],
        ) for n in nodes
    }
    expected_nodes = {
        (
            'addon_f9deff34-d8cc-4bfb-995b-c1d0db37067c',
            'orga_f3b3bb57-db31-4dff-8708-0dd91cc31826',
        ),
    }
    assert actual_nodes == expected_nodes

    # Ensure link app - organization
    nodes = neo4j_session.run(
        """
        MATCH(a:CleverCloudApplication)-[:RESOURCE]->(org:CleverCloudOrganization)
        RETURN a.id, org.id
        """,
    )
    actual_nodes = {
        (
            n['a.id'],
            n['org.id'],
        ) for n in nodes
    }
    expected_nodes = {
        (
            'app_6cb7fded-72d8-4994-b813-c7caa2208019',
            'orga_f3b3bb57-db31-4dff-8708-0dd91cc31826',
        ),
    }
    assert actual_nodes == expected_nodes

    # Ensure link app - Addon
    nodes = neo4j_session.run(
        """
        MATCH(a:CleverCloudApplication)<-[:RESOURCE]-(b:CleverCloudAddon)
        RETURN a.id, b.id
        """,
    )
    actual_nodes = {
        (
            n['a.id'],
            n['b.id'],
        ) for n in nodes
    }
    expected_nodes = {
        (
            'app_6cb7fded-72d8-4994-b813-c7caa2208019',
            'addon_f9deff34-d8cc-4bfb-995b-c1d0db37067c',
        ),
    }
    assert actual_nodes == expected_nodes
