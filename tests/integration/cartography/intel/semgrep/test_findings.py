from unittest.mock import patch

import cartography.intel.semgrep.findings
import tests.data.semgrep.sca
from cartography.intel.semgrep.findings import sync
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_REPO_ID = "https://github.com/yourorg/yourrepo"
TEST_REPO_FULL_NAME = "yourorg/yourrepo"
TEST_REPO_NAME = "yourrepo"
TEST_UPDATE_TAG = 123456789


def _create_github_repos(neo4j_session):
    # Creates a set of GitHub repositories in the graph
    neo4j_session.run(
        """
        MERGE (repo:GitHubRepository{id: $repo_id, fullname: $repo_fullname, name: $repo_name})
        ON CREATE SET repo.firstseen = timestamp()
        SET repo.lastupdated = $update_tag
        """,
        repo_id=TEST_REPO_ID,
        repo_fullname=TEST_REPO_FULL_NAME,
        update_tag=TEST_UPDATE_TAG,
        repo_name=TEST_REPO_NAME,
    )


@patch.object(
    cartography.intel.semgrep.findings,
    "get_deployment",
    return_value=tests.data.semgrep.sca.DEPLOYMENTS,
)
@patch.object(
    cartography.intel.semgrep.findings,
    "get_sca_vulns",
    return_value=tests.data.semgrep.sca.RAW_VULNS,
)
def test_sync(mock_get_sca_vulns, mock_get_deployment, neo4j_session):
    # Arrange
    _create_github_repos(neo4j_session)
    semgrep_app_token = "your_semgrep_app_token"
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    sync(neo4j_session, semgrep_app_token, TEST_UPDATE_TAG, common_job_parameters)

    # Assert
    expected_deployment_nodes = {("123456", "YourOrg", "yourorg")}

    assert (
        check_nodes(
            neo4j_session,
            "SemgrepDeployment",
            ["id", "name", "slug"],
        ) ==
        expected_deployment_nodes
    )
    expected_sca_vuln_nodes = {
        (
            "yourorg/yourrepo|ssc-92af1d99-4fb3-4d4e-a9f4-d57572cd6590",
            TEST_UPDATE_TAG,
            "yourorg/yourrepo",
            "ssc-92af1d99-4fb3-4d4e-a9f4-d57572cd6590",
            "Reachable vuln",
            "description",
            "go",
            "HIGH",
            "CVE-2023-37897",
            "MANUAL_REVIEW_REACHABLE",
            "REACHABLE",
            "DIRECT",
            "grav|1.7.42.0",
            "grav|1.7.42.2",
            "go.mod",
            "https://github.com/yourorg/yourrepo/blame/71bbed12f950de8335006d7f91112263d8504f1b/go.mod#L111",
            "https://github.com/advisories//GHSA-9436-3gmp-4f53,https://nvd.nist.gov/vuln/detail/CVE-2023-37897",
            "2023-07-19T12:51:53Z",
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "SemgrepSCAFinding",
            [
                "id",
                "lastupdated",
                "repository",
                "rule_id",
                "summary",
                "description",
                "package_manager",
                "severity",
                "cve_id",
                "reachability_check",
                "reachability",
                "transitivity",
                "dependency",
                "dependency_fix",
                "dependency_file",
                "dependency_file_url",
                "ref_urls",
                "scan_time",
            ],
        ) ==
        expected_sca_vuln_nodes
    )
    expected_sca_location_nodes = {
        (
            "20128504",
            "src/packages/directory/file1.go",
            "24",
            "57",
            "24",
            "78",
            "https://github.com/yourorg/yourrepo/blame/6fdee8f2727f4506cfbbe553e23b895e27956588/src/packages/directory/file1.go.ts#L24",  # noqa E501
        ),
        (
            "20128505",
            "src/packages/directory/file2.go",
            "24",
            "37",
            "24",
            "54",
            "https://github.com/yourorg/yourrepo/blame/6fdee8f2727f4506cfbbe553e23b895e27956588/src/packages/directory/file2.go.ts#L24",  # noqa E501
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "SemgrepSCALocation",
            [
                "id",
                "path",
                "start_line",
                "start_col",
                "end_line",
                "end_col",
                "url",
            ],
        ) ==
        expected_sca_location_nodes
    )
    expected_findings_resource_relationships = {
        (
            "123456",
            "yourorg/yourrepo|ssc-92af1d99-4fb3-4d4e-a9f4-d57572cd6590",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "SemgrepDeployment",
            "id",
            "SemgrepSCAFinding",
            "id",
            "RESOURCE",
        ) ==
        expected_findings_resource_relationships
    )
    expected_locations_resource_relationships = {
        (
            "123456",
            "20128504",
        ),
        (
            "123456",
            "20128505",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "SemgrepDeployment",
            "id",
            "SemgrepSCALocation",
            "id",
            "RESOURCE",
        ) ==
        expected_locations_resource_relationships
    )
    expected_found_in_relationships = {
        (
            "yourorg/yourrepo",
            "yourorg/yourrepo|ssc-92af1d99-4fb3-4d4e-a9f4-d57572cd6590",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "GitHubRepository",
            "fullname",
            "SemgrepSCAFinding",
            "id",
            "FOUND_IN",
            rel_direction_right=False,
        ) ==
        expected_found_in_relationships
    )
    expected_location_relationships = {
        (
            "yourorg/yourrepo|ssc-92af1d99-4fb3-4d4e-a9f4-d57572cd6590",
            "20128504",
        ),
        (
            "yourorg/yourrepo|ssc-92af1d99-4fb3-4d4e-a9f4-d57572cd6590",
            "20128505",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "SemgrepSCAFinding",
            "id",
            "SemgrepSCALocation",
            "id",
            "USAGE_AT",
        ) ==
        expected_location_relationships
    )
