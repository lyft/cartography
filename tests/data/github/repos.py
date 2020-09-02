GET_REPOS = [
    {
        'name': 'sample_repo',
        'nameWithOwner': 'example_org/sample_repo',
        'primaryLanguage': {
            'name': 'Python',
        },
        'url': 'https://github.com/example_org/sample_repo',
        'sshUrl': 'git@github.com:example_org/sample_repo.git',
        'createdAt': '2011-02-15T18:40:15Z',
        'description': 'My description',
        'updatedAt': '2020-01-02T20:10:09Z',
        'homepageUrl': '',
        'languages': {
            'totalCount': 1,
            'nodes': [
                {'name': 'Python'},
            ],
        },
        'defaultBranchRef': {
            'name': 'master',
            'id': 'branch_ref_id==',
        },
        'isPrivate': True,
        'isArchived': False,
        'isDisabled': False,
        'isLocked': True,
        'owner': {
            'url': 'https://github.com/example_org',
            'login': 'example_org',
            '__typename': 'Organization',
        },
        'requirements': {'text': 'cartography\nhttplib2>=0.7.0\njinja2\nlxml\n'},
    }, {
        'name': 'SampleRepo2',
        'nameWithOwner': 'example_org/SampleRepo2',
        'primaryLanguage': {
            'name': 'Python',
        },
        'url': 'https://github.com/example_org/SampleRepo2',
        'sshUrl': 'git@github.com:example_org/SampleRepo2.git',
        'createdAt': '2011-09-21T18:55:16Z',
        'description': 'Some other description',
        'updatedAt': '2020-07-03T00:25:25Z',
        'homepageUrl': 'http://example.com/',
        'languages': {
            'totalCount': 1,
            'nodes': [
                {'name': 'Python'},
            ],
        },
        'defaultBranchRef': {
            'name': 'master',
            'id': 'other_branch_ref_id==',
        },
        'isPrivate': False,
        'isArchived': False,
        'isDisabled': False,
        'isLocked': False,
        'owner': {
            'url': 'https://github.com/example_org',
            'login': 'example_org', '__typename': 'Organization',
        },
        'requirements': {'text': 'cartography==0.1.0\nhttplib2>=0.7.0\njinja2\nlxml\n# This is a comment line and should be ignored\n'},
    },
]
