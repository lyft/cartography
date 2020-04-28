#Copyright (c) 2020, Oracle and/or its affiliates.
import cartography.intel.oci.iam
import tests.data.oci.iam
import cartography.intel.oci.utils


TEST_TENANCY_ID = "ocid1.user.oc1..nqilyrb1l5t6gnmlcjgeim8q47vccnklev8k2ud9skn78eapu116oyv9wcr0"
TEST_REGION = 'us-phoenix-1'
TEST_UPDATE_TAG = 123456789


def test_load_users(neo4j_session):
    data = tests.data.oci.iam.LIST_USERS['Users']

    cartography.intel.oci.iam.load_users(
        neo4j_session,
        data,
        TEST_TENANCY_ID,
        TEST_UPDATE_TAG,
    )

def test_load_groups(neo4j_session):
    data = tests.data.oci.iam.LIST_GROUPS['Groups']

    cartography.intel.oci.iam.load_groups(
        neo4j_session,
        data,
        TEST_TENANCY_ID,
        TEST_UPDATE_TAG,
    )


def test_load_policies(neo4j_session):
    data = tests.data.oci.iam.LIST_POLICIES['Policies']

    cartography.intel.oci.iam.load_policies(
        neo4j_session,
        data,
        TEST_TENANCY_ID,
        TEST_UPDATE_TAG,
    )

def test_load_compartments(neo4j_session):
    data = tests.data.oci.iam.LIST_COMPARTMENTS['Compartments']

    cartography.intel.oci.iam.load_compartments(
        neo4j_session,
        data,
        TEST_TENANCY_ID,
        TEST_UPDATE_TAG,
    )

def test_load_group_memberships(neo4j_session):
    group_memberships = tests.data.oci.iam.LIST_GROUP_MEMBERSHIPS
    groups=list(cartography.intel.oci.utils.get_groups_in_tenancy(neo4j_session,TEST_TENANCY_ID))
    data = {group["ocid"]: group_memberships for group in groups}
    cartography.intel.oci.iam.load_compartments(
        neo4j_session,
        data,
        TEST_TENANCY_ID,
        TEST_UPDATE_TAG,
    )