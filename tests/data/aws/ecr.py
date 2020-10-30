import datetime


DESCRIBE_REPOSITORIES = {
    'repositories': [
        {
            'repositoryArn': 'arn:aws:ecr:us-east-1:000000000000:repository/example-repository',
            'registryId': '000000000000',
            'repositoryName': 'example-repository',
            'repositoryUri': '000000000000.dkr.ecr.us-east-1/example-repository',
            'createdAt': datetime.datetime(2019, 1, 1, 0, 0, 1),
        },
        {
            'repositoryArn': 'arn:aws:ecr:us-east-1:000000000000:repository/sample-repository',
            'registryId': '000000000000',
            'repositoryName': 'sample-repository',
            'repositoryUri': '000000000000.dkr.ecr.us-east-1/sample-repository',
            'createdAt': datetime.datetime(2019, 1, 1, 0, 0, 1),
        },
        {
            'repositoryArn': 'arn:aws:ecr:us-east-1:000000000000:repository/test-repository',
            'registryId': '000000000000',
            'repositoryName': 'test-repository',
            'repositoryUri': '000000000000.dkr.ecr.us-east-1/test-repository',
            'createdAt': datetime.datetime(2019, 1, 1, 0, 0, 1),
        },
    ],
}


LIST_REPOSITORY_IMAGES = {
    '000000000000.dkr.ecr.us-east-1/example-repository': [
        {
            'imageDigest': 'sha256:0000000000000000000000000000000000000000000000000000000000000000',
            'imageTag': '1',
        },
        {
            'imageDigest': 'sha256:0000000000000000000000000000000000000000000000000000000000000001',
            'imageTag': '2',
        },
    ],
    '000000000000.dkr.ecr.us-east-1/sample-repository': [
        {
            # NOTE same digest and tag as image in example-repository
            'imageDigest': 'sha256:0000000000000000000000000000000000000000000000000000000000000000',
            'imageTag': '1',
        },
        {
            'imageDigest': 'sha256:0000000000000000000000000000000000000000000000000000000000000011',
            'imageTag': '2',
        },
    ],
    '000000000000.dkr.ecr.us-east-1/test-repository': [
        {
            # NOTE same digest but different tag from image in example-repository
            'imageDigest': 'sha256:0000000000000000000000000000000000000000000000000000000000000000',
            'imageTag': '1234567890',
        },
        {
            'imageDigest': 'sha256:0000000000000000000000000000000000000000000000000000000000000021',
            'imageTag': '1',
        },
    ],
}

GET_ECR_REPOSITORY_IMAGE_VULNS = {
    'imageDigest': 'sha256:0000000000000000000000000000000000000000000000000000000000000000',
    'findings_count': {
        'HIGH': 1, 'INFORMATIONAL': 13, 'LOW': 43, 'MEDIUM': 19,
    },
    'findings': [
        {
            'attributes': [
                {
                    'key': 'package_version',
                    'value': '1.2.3',
                }, {
                    'key': 'package_name',
                    'value': 'some_name',
                },
            ],
            'name': 'CVE-1234-12345',
            'severity': 'HIGH',
            'uri': 'http://example.com',
        },
        {
            'attributes': [
                {
                    'key': 'package_version',
                    'value': '10.2.9',
                },
                {
                    'key': 'package_name',
                    'value': 'my_software',
                },
                {
                    'key': 'CVSS2_SCORE',
                    'value': '2',
                },
            ],
            'name': 'CVE-9876-1212',
            'severity': 'LOW',
            'uri': 'http://example.com/fakefakefake',
        },
    ],
    'scan_completed_at': 'abcd',
}
