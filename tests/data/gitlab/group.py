GROUPS = [
    {
        "created_at": "2023-03-24T07:12:16.787134+00:00",
        "id":"id",
        "path": "foo-bar",
        "name": "Foobar Group",
        "description": "An interesting group",
        "visibility": "public",
    },
    {
        "created_at": "2023-04-17T09:46:47.454188+00:00",
        "id":"id12",
        "path": "foo-bar12",
        "name": "Foobar Group12",
        "description": "An interesting group12",
        "visibility": "public",
    },
]
PROJECTS = [
    {
        "created_at": "2023-05-11T05:04:17.808136+00:00",
        "id": "id",
        "name": "gitlab-test",
        "description": "gitlab-description",
        "name_with_namespace":"name-with-namespace",
        "visibility": "public",
        "namespace": {
            "id": 2,
            "name": "name",
            "path": "path",
            "kind": "group",
            "full_path": "path/",
            "parent_id": None,
        },
        "last_activity_at": "last-activity-at",
        "default_branch": "default-branch",
    },
    {
        "created_at": "2023-04-26T16:59:00.963792+00:00",
        "id": "id2",
        "name": "gitlab-test2",
        "description": "gitlab-description2",
        "name_with_namespace":"name-with-namespace2",
        "visibility": "public",
        "namespace": {
            "id": 3,
            "name": "name2",
            "path": "path2",
            "kind": "group2",
            "full_path": "path2/",
            "parent_id": None,
        },
        "last_activity_at": "last-activity-at2",
        "default_branch": "default-branch2",
    },
]
REPOSITORIES = [
    {
        "created_at": "2023-03-24T07:16:07.545221+00:00",
        "name": "name",
        "id": "id",
        "type": "type",
        "path": "files/html",
        "mode": "mode",
        "project": {
            "description": "project",
            "id": "project123",
            "name": "firstproject",
        },
    },
    {
        "created_at": "2023-04-17T06:06:08.630453+00:00",
        "name": "name2",
        "id": "id2",
        "type": "type2",
        "path": "files2/html",
        "mode" : "mode",
        "project": {
            "description": "project",
            "id": "project123",
            "name": "firstproject",
        },
    },
]
DEPENDENCIES = [
    {
        "created_at": "2023-03-24T07:16:07.545221+00:00",
        "name": "name",
        "id": "id",
        "version": "version",
        "dependency_file_path": "path",
        "vulnerabilities": [
            {
                "name": "DDoS",
                "severity": "unknown",
                "id": "id",
            }
        ],
        "licenses": [
            {
                "name": "MIT",
            }
        ],
        "project": {
            "description": "project",
            "id": "project123",
            "name": "firstproject",
        },
    },
    {
        "created_at": "2023-04-17T06:06:08.630453+00:00",
        "name": "name2",
        "id": "id2",
        "version": "version2",
        "dependency_file_path": "path",
        "vulnerabilities": [
            {
                "name": "DDoS",
                "severity": "unknown",
                "id": "id",
            }
        ],
        "licenses": [
            {
                "name": "MIT",
            }
        ],
        "project": {
            "description": "project",
            "id": "project123",
            "name": "firstproject",
        },
    },
]
MEMBERS = [
    {
        "created_at": "2023-03-24T07:12:16.787134+00:00",
        "name": "name",
        "id": "id",
        "username": "ABC",
        "state": "state",
        "created_by": "created_by",
        "group": {
            "id":"id456",
            "path": "path",
            "name": "name",
            "description": "description",
        },
    },
    {
        "created_at": "2023-04-17T09:46:47.454188+00:00",
        "name": "name2",
        "id": "id2",
        "username": "ABCD",
        "state": "state",
        "created_by": "created_by",
        "group": {
            "id":"id123",
            "path": "path",
            "name": "name",
            "description": "description",
        },
    },
]
