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
        'requirements': None,
    },
]

TRANSFORMED_REPOS_DATA = {
    'repos': [
        {
            'id': 'https://github.com/example_org/sample_repo',
            'createdat': '2011-02-15T18:40:15Z',
            'name': 'sample_repo',
            'fullname': 'example_org/sample_repo',
            'description': 'My description',
            'primarylanguage': {'name': 'Python'},
            'homepage': '',
            'defaultbranch': 'master',
            'defaultbranchid': 'https://github.com/example_org/sample_repo:branch_ref_id==',
            'private': True,
            'disabled': False,
            'archived': False,
            'locked': True,
            'giturl': 'git://github.com:example_org:sample_repo.git',
            'url': 'https://github.com/example_org/sample_repo',
            'sshurl': 'git@github.com:example_org/sample_repo.git',
            'updatedat': '2020-01-02T20:10:09Z',
        }, {
            'id': 'https://github.com/example_org/SampleRepo2',
            'createdat': '2011-09-21T18:55:16Z',
            'name': 'SampleRepo2',
            'fullname': 'example_org/SampleRepo2',
            'description': 'Some other description',
            'primarylanguage': {'name': 'Python'},
            'homepage': 'http://example.com/',
            'defaultbranch': 'master',
            'defaultbranchid': 'https://github.com/example_org/SampleRepo2:other_branch_ref_id==',
            'private': False,
            'disabled': False,
            'archived': False,
            'locked': False,
            'giturl': 'git://github.com:example_org:SampleRepo2.git',
            'url': 'https://github.com/example_org/SampleRepo2',
            'sshurl': 'git@github.com:example_org/SampleRepo2.git',
            'updatedat': '2020-07-03T00:25:25Z',
        },
    ],
    'repo_languages': [
        {
            'repo_id': 'https://github.com/example_org/sample_repo',
            'language_name': 'Python',
        }, {
            'repo_id': 'https://github.com/example_org/SampleRepo2',
            'language_name': 'Python',
        },
    ],
    'repo_owners': [
        {
            'repo_id': 'https://github.com/example_org/sample_repo',
            'owner': 'example_org',
            'owner_id': 'https://github.com/example_org',
            'type': 'Organization',
        }, {
            'repo_id': 'https://github.com/example_org/SampleRepo2',
            'owner': 'example_org',
            'owner_id': 'https://github.com/example_org',
            'type': 'Organization',
        },
    ],
    'python_requirements': [
        {
            'id': 'cartography|Unknown',
            'name': 'cartography',
            'repo_url': 'https://github.com/example_org/sample_repo',
            'uri': None,
            'version': 'Unknown',
        }, {
            'id': 'httplib2|0.7.0',
            'name': 'httplib2',
            'repo_url': 'https://github.com/example_org/sample_repo',
            'uri': None,
            'version': '0.7.0',
        }, {
            'id': 'jinja2|Unknown',
            'name': 'jinja2',
            'repo_url': 'https://github.com/example_org/sample_repo',
            'uri': None,
            'version': 'Unknown',
        }, {
            'id': 'lxml|Unknown',
            'name': 'lxml',
            'repo_url': 'https://github.com/example_org/sample_repo',
            'uri': None,
            'version': 'Unknown',
        },
    ],
}
