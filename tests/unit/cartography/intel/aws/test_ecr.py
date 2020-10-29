from cartography.intel.aws import ecr


TEST_DATA = {
    'imageDigest': 'sha256:1234',
    'findings_count': {
        'HIGH': 1, 'INFORMATIONAL': 13, 'LOW': 43, 'MEDIUM': 19,
    },
    'findings': [{
        'attributes': [{
                'key': 'package_version',
                'value': '1.2.3',
            },{
                'key': 'package_name',
                'value': 'some_name',
            }],
        'name': 'CVE-1234-12345',
        'severity': 'HIGH',
        'uri': 'http://example.com',
    }],
    'scan_completed_at': 'abcd',
}

def test_transform_repository_images_vulns_findings():
    ecr.transform_repository_images_vulns_findings(TEST_DATA)
    assert TEST_DATA['findings'][0]['package_name'] == 'some_name'
    assert TEST_DATA['findings'][0]['package_version'] == '1.2.3'
