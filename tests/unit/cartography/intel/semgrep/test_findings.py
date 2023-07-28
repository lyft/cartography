from unittest.mock import MagicMock
from unittest.mock import patch

from requests import RequestException

from cartography.intel.semgrep.findings import get_deployment
from cartography.intel.semgrep.findings import get_sca_vulns
from cartography.intel.semgrep.findings import transform_sca_vulns
from tests.data.semgrep.sca import RAW_VULNS
from tests.data.semgrep.sca import SCA_RESPONSE
from tests.data.semgrep.sca import USAGES


@patch("cartography.intel.semgrep.findings.requests")
def test_get_deployment(mock_requests):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "deployments": [
            {
                "id": 1234,
                "name": "YourOrg",
                "slug": "yourorg",
                "findings": {
                    "url": "https://semgrep.dev/api/v1/deployments/yourorg/findings",
                },
            },
        ],
    }
    mock_requests.get.return_value = mock_response
    semgrep_app_token = "your_semgrep_app_token"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {semgrep_app_token}",
    }

    # Act
    deployment = get_deployment(semgrep_app_token)

    # Assert
    assert mock_requests.get.called_once_with('https://semgrep.dev/api/v1/deployments', headers=headers)
    assert deployment["id"] == 1234
    assert deployment["name"] == "YourOrg"
    assert deployment["slug"] == "yourorg"


@patch("cartography.intel.semgrep.findings.requests")
def test_get_deployment_exception(mock_requests):
    # Arrange
    mock_requests.RequestException = RequestException
    mock_requests.get.side_effect = RequestException(
        "Server Error",
        request=mock_requests,
        response=MagicMock(status_code=500),
    )

    # Act
    try:
        get_deployment("your_semgrep_app_token")
    except RequestException as e:
        # Assert
        assert e.args[0] == "Server Error"
        assert e.request == mock_requests
        assert e.response.status_code == 500


def mock_get_sca_vulns_response(url, headers, params):
    mock_response = MagicMock()
    mock_response.status_code = 200
    cursor = params.get('cursor')
    if url == 'https://semgrep.dev/api/sca/deployments/yourorgid/vulns' and not cursor:
        mock_response.json.return_value = SCA_RESPONSE
    elif url == 'https://semgrep.dev/api/sca/deployments/yourorgid/vulns' and cursor == SCA_RESPONSE['cursor']:
        mock_response.json.return_value = {
            "vulns": [],
            "cursor": "789012",
            "hasMore": False,
        }
    return mock_response


@patch("cartography.intel.semgrep.findings.requests")
def test_get_sca_vulns(mock_requests):
    # Arrange

    mock_requests.get.side_effect = mock_get_sca_vulns_response
    semgrep_app_token = "your_semgrep_app_token"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {semgrep_app_token}",
    }

    # Act
    vulns = get_sca_vulns(semgrep_app_token, "yourorgid")

    # Assert
    assert mock_requests.get.any_call(
        'https://semgrep.dev/api/sca/deployments/yourorgid/vulns',
        headers=headers,
    )
    assert mock_requests.get.any_call(
        'https://semgrep.dev/api/sca/deployments/yourorgid/vulns',
        headers=headers, params={'cursor': SCA_RESPONSE['cursor']},
    )
    assert vulns == RAW_VULNS


@patch("cartography.intel.semgrep.findings.requests")
def test_get_sca_vulns_exception(mock_requests):
    # Arrange
    mock_requests.RequestException = RequestException
    mock_response = MagicMock(status_code=500)
    mock_requests.get.side_effect = RequestException("Server Error", request=mock_requests, response=mock_response)

    # Act
    try:
        get_sca_vulns("your_semgrep_app_token", "yourorgid")
    except RequestException as e:
        # Assert
        assert e.args[0] == "Server Error"
        assert e.request == mock_requests
        assert e.response.status_code == 500


def test_transform_sca_vulns():
    # Arrange
    raw_vulns = SCA_RESPONSE["vulns"]
    # Act
    vulns, usages = transform_sca_vulns(raw_vulns)
    # Assert
    expected_vuln = {
        "id": "yourorg/yourrepo|ssc-92af1d99-4fb3-4d4e-a9f4-d57572cd6590",
        "repositoryName": "yourorg/yourrepo",
        "ruleId": "ssc-92af1d99-4fb3-4d4e-a9f4-d57572cd6590",
        "title": "Reachable vuln",
        "description": "description",
        "ecosystem": "go",
        "severity": "HIGH",
        "cveId": "CVE-2023-37897",
        "reachability": "MANUAL_REVIEW_REACHABLE",
        "exposureType": "REACHABLE",
        "reachableIf": "a non-administrator, user account that has Admin panel access and Create/Update page permissions",  # noqa E501
        "matchedDependency": "grav|1.7.42.0",
        "closestSafeDependency": "grav|1.7.42.2",
        "cveId": "CVE-2023-37897",
        "dependencyFileLocation_path": "go.mod",
        "dependencyFileLocation_url": "https://github.com/yourorg/yourrepo/blame/71bbed12f950de8335006d7f91112263d8504f1b/go.mod#L111",  # noqa E501
        "ref_urls": "https://github.com/advisories//GHSA-9436-3gmp-4f53,https://nvd.nist.gov/vuln/detail/CVE-2023-37897",  # noqa E501
        "openedAt": "2023-07-19T12:51:53Z",
    }
    assert vulns == [expected_vuln]
    expected_usages = USAGES
    assert usages == expected_usages
