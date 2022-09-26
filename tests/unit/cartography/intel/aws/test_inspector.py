from datetime import datetime
from unittest import mock

from cartography.intel.aws.inspector import cleanup
from cartography.intel.aws.inspector import get_inspector_findings
from cartography.intel.aws.inspector import load_inspector_findings
from cartography.intel.aws.inspector import load_inspector_packages
from cartography.intel.aws.inspector import sync
from cartography.intel.aws.inspector import transform_inspector_findings
from tests.data.aws.inspector import LIST_FINDINGS_EC2_PACKAGE
from tests.data.aws.inspector import LIST_FINDINGS_NETWORK


TEST_UPDATE_TAG = 123456789


def test_get_inspector_findings():
    mock_boto = mock.MagicMock()

    ret = get_inspector_findings(mock_boto, 'us-east-1', '0000')

    assert ret == []
    mock_boto.client.assert_called_once_with('inspector2', region_name='us-east-1')
    mock_boto.client().get_paginator.assert_called_with('list_findings')


def test_transform_inspector_findings_network():
    findings, _packages = transform_inspector_findings(LIST_FINDINGS_NETWORK)
    assert findings == [
        {
            'id': 'arn:aws:test123',
            'arn': 'arn:aws:test123',
            'instanceid': 'i-instanceid',
            'severity': 'INFORMATIONAL',
            'name': 'string',
            'firstobservedat': datetime(2015, 1, 1, 0, 0),
            'updatedat': datetime(2015, 1, 1, 0, 0),
            'awsaccount': '123456789011',
            'description': 'string',
            'cvssscore': 123.0,
            'protocol': 'TCP',
            'portrange': '123-124',
            'portrangeend': 124,
            'portrangebegin': 123,
            'type': 'NETWORK_REACHABILITY',
            'status': 'ACTIVE',
        },
    ]


def test_transform_inspector_findings_package():
    findings, packages = transform_inspector_findings(LIST_FINDINGS_EC2_PACKAGE)
    assert findings == [
        {
            'id': 'arn:aws:test456',
            'arn': 'arn:aws:test456',
            'vulnerabilityid': 'CVE-2017-9059',
            'instanceid': 'i-88503981029833100',
            'severity': 'MEDIUM',
            'name': 'CVE-2017-9059 - kernel-tools, kernel',
            'firstobservedat': datetime(2022, 5, 4, 16, 23, 3, 692000),
            'updatedat': datetime(2022, 5, 4, 16, 23, 3, 692000),
            'awsaccount': '123456789012',
            'description': 'The NFSv4 implementation in the Linux kernel through '
            '4.11.1 allows local users to cause a denial of service '
            '(resource consumption) by leveraging improper channel '
            'callback shutdown when unmounting an NFSv4 filesystem, aka '
            'a "module reference and kernel daemon" leak.',
            'cvssscore': 5.5,
            'type': 'PACKAGE_VULNERABILITY',
            'vulnerabilityid': 'CVE-2017-9059',
            'referenceurls': [],
            'relatedvulnerabilities': [],
            'source': 'REDHAT_CVE',
            'vendorcreatedat': datetime(2017, 4, 25, 17, 0),
            'vendorupdatedat': None,
            'vendorseverity': 'Moderate',
            'sourceurl': 'https://access.redhat.com/security/cve/CVE-2017-9059',
            'status': 'ACTIVE',

            'vulnerablepackageids': [
                'kernel-tools|X86_64|4.9.17|6.29.amzn1|0',
                'kernel|X86_64|4.9.17|6.29.amzn1|0',
            ],
        },
    ]
    assert packages == [
        {
            'arch': 'X86_64',
            'awsaccount': '123456789012',
            'epoch': 0,
            'filepath': None,
            'findingarn': 'arn:aws:test456',
            'fixedinversion': None,
            'id': 'kernel-tools|X86_64|4.9.17|6.29.amzn1|0',
            'manager': 'OS',
            'name': 'kernel-tools',
            'release': '6.29.amzn1',
            'sourcelayerhash': None,
            'version': '4.9.17',
        },
        {
            'arch': 'X86_64',
            'awsaccount': '123456789012',
            'epoch': 0,
            'filepath': None,
            'findingarn': 'arn:aws:test456',
            'fixedinversion': None,
            'id': 'kernel|X86_64|4.9.17|6.29.amzn1|0',
            'manager': 'OS',
            'name': 'kernel',
            'release': '6.29.amzn1',
            'sourcelayerhash': None,
            'version': '4.9.17',
        },
    ]


@mock.patch("cartography.intel.aws.inspector._load_findings_tx")
def test_load_inspector_findings(load_mock):
    mock_neo4j = mock.MagicMock()
    findings = ['any']
    region = 'us-east-1'
    aws_update_tag = 0

    load_inspector_findings(mock_neo4j, findings, region, aws_update_tag)

    mock_neo4j.write_transaction.assert_called_once_with(
        load_mock, findings=['any'], region='us-east-1', aws_update_tag=0,
    )


@mock.patch("cartography.intel.aws.inspector._load_packages_tx")
def test_load_inspector_packages(load_mock):
    mock_neo4j = mock.MagicMock()
    packages = []
    region = 'us-east-1'
    aws_update_tag = 0

    load_inspector_packages(mock_neo4j, packages, region, aws_update_tag)

    mock_neo4j.write_transaction.assert_called_once_with(
        load_mock, packages=[], region='us-east-1', aws_update_tag=0,
    )


@mock.patch("cartography.intel.aws.inspector.run_cleanup_job")
def test_cleanup(run_cleanup_mock):
    mock_neo4j = mock.MagicMock()

    cleanup(mock_neo4j, {})

    run_cleanup_mock.assert_called_once_with(
        'aws_import_inspector_cleanup.json', mock_neo4j, {},
    )


@mock.patch("cartography.intel.aws.inspector.get_inspector_findings")
@mock.patch("cartography.intel.aws.inspector.transform_inspector_findings")
@mock.patch("cartography.intel.aws.inspector.load_inspector_packages")
@mock.patch("cartography.intel.aws.inspector.load_inspector_findings")
@mock.patch("cartography.intel.aws.inspector.cleanup")
def test_sync(
    cleanup_mock,
    load_findings_mock,
    load_packages_mock,
    transform_mock,
    get_findings_mock,
):
    get_findings_mock.return_value = []
    transform_mock.return_value = [], []
    mock_neo4j = mock.MagicMock()
    mock_boto3 = mock.MagicMock()
    regions = ['us-east-1', 'us-east-2']
    current_aws_account_id = "1234"
    update_tag = 0
    common_job_parameters = {}

    sync(mock_neo4j, mock_boto3, regions, current_aws_account_id, update_tag, common_job_parameters)

    get_findings_mock.assert_has_calls([
        mock.call(mock_boto3, 'us-east-1', current_aws_account_id),
        mock.call(mock_boto3, 'us-east-2', current_aws_account_id),
    ])
    transform_mock.assert_has_calls([
        mock.call([]),
        mock.call([]),
    ])
    load_packages_mock.assert_has_calls([
        mock.call(mock_neo4j, [], 'us-east-1', 0),
        mock.call(mock_neo4j, [], 'us-east-2', 0),
    ])
    load_findings_mock.assert_has_calls([
        mock.call(mock_neo4j, [], 'us-east-1', 0),
        mock.call(mock_neo4j, [], 'us-east-2', 0),
    ])
    cleanup_mock.assert_has_calls([
        mock.call(mock_neo4j, {}),
        mock.call(mock_neo4j, {}),
    ])
