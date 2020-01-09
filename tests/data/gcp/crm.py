# flake8: noqa
GCP_PROJECTS = [
    {
        'createTime': '2019-05-22T19:28:30.592Z',
        'lifecycleState': 'ACTIVE',
        'name': 'Group 1',
        'parent': {'id': '12345', 'type': 'folder'},
        'projectId': 'sample-id-232323',
        'projectNumber': 'sample-number-121212',
    },
]

GCP_PROJECTS_WITHOUT_PARENT = [
    {
        'createTime': '2019-11-11T21:06:32.043Z',
        'lifecycleState': 'ACTIVE',
        'name': 'my-parentless-project',
        'projectId': 'my-parentless-project-987654',
        'projectNumber': '123456789012',
    },
]
