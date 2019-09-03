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
    'arn:aws:ecr:us-east-1:000000000000:repository/example-repository': [],
    'arn:aws:ecr:us-east-1:000000000000:repository/sample-repository': [],
    'arn:aws:ecr:us-east-1:000000000000:repository/test-repository': [],
}
