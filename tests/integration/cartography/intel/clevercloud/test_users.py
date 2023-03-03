import cartography.intel.clevercloud.organization
import cartography.intel.clevercloud.users
import tests.data.clevercloud.organization
import tests.data.clevercloud.users


COMMON_JOB_PARAMETERS = {
    "UPDATE_TAG": 123456789,
    "ORG_ID": 'orga_f3b3bb57-db31-4dff-8708-0dd91cc31826',
}


def test_load_clevercloud_users_and_organization(neo4j_session):

    cartography.intel.clevercloud.users.load(
        neo4j_session,
        tests.data.clevercloud.users.CLEVERCLOUD_USERS,
        COMMON_JOB_PARAMETERS,
    )

    cartography.intel.clevercloud.organization.load(
        neo4j_session,
        tests.data.clevercloud.organization.CLEVERCLOUD_ORGANIZATION,
        COMMON_JOB_PARAMETERS,
    )

    # Ensure organization got loaded
    nodes = neo4j_session.run(
        """
        MATCH (org:CleverCloudOrganization) RETURN org.id, org.name;
        """,
    )
    expected_nodes = {
        ("orga_f3b3bb57-db31-4dff-8708-0dd91cc31826", "Dummy"),
    }
    actual_nodes = {
        (
            n['org.id'],
            n['org.name'],
        ) for n in nodes
    }
    assert actual_nodes == expected_nodes

    # Ensure users got loaded
    nodes = neo4j_session.run(
        """
        MATCH (usr:CleverCloudUser) RETURN usr.id, usr.email;
        """,
    )
    expected_nodes = {
        ('user_8f0c3cb0-c096-4f7e-a249-aa46c24a5941', 'john.doe@domain.tld'),
    }
    actual_nodes = {
        (
            n['usr.id'],
            n['usr.email'],
        ) for n in nodes
    }
    assert actual_nodes == expected_nodes

    # Ensure link user - organization
    nodes = neo4j_session.run(
        """
        MATCH(usr:CleverCloudUser)-[:MEMBER_OF]->(org:CleverCloudOrganization)
        RETURN usr.id, org.id
        """,
    )
    actual_nodes = {
        (
            n['usr.id'],
            n['org.id'],
        ) for n in nodes
    }
    expected_nodes = {
        (
            'user_8f0c3cb0-c096-4f7e-a249-aa46c24a5941',
            'orga_f3b3bb57-db31-4dff-8708-0dd91cc31826',
        ),
    }
    assert actual_nodes == expected_nodes
