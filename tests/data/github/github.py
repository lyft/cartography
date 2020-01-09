# flake8: noqa
API_RESPONSE = {
    "data": {
        "organization": {
            "repositories": {
                "totalCount": 1,
                "pageInfo": {
                    "endCursor": "MQ",
                    "hasNextPage": True,
                },
                "nodes": [
                    {
                        'id': "MDEwOlJlcG9zaXRvcnkxNg==",
                        "name": "pythontestlib",
                        "nameWithOwner": "fake/pythontestlib",
                        "primaryLanguage": {
                            "name": "Python",
                        },
                        "url": "https://fake.github.net/pythontestlib",
                        "sshUrl": "git@fake.github.net/pythontestlib.git",
                        "createdAt": "2018-06-20T00:53:01Z",
                        "description": "Fake service for testing",
                        "updatedAt": "2019-10-07T21:49:08Z",
                        "homepageUrl": None,
                        "languages": {
                            "totalCount": 2,
                            "nodes": [
                                {
                                    "name": "Makefile",
                                },
                                {
                                    "name": "Python",
                                },
                            ],
                        },
                        "defaultBranchRef": {
                            "name": "master",
                            "id": "MDM6UmVmMTY6bWFzdGVy",
                        },
                        "isPrivate": True,
                        "isArchived": False,
                        "isDisabled": False,
                        "isLocked": False,
                        "owner": {
                            "login": "fake",
                            "id": "MDAxOk9yZ2FuaXphdGlvbjE=",
                            "__typename": "Organization",
                        },

                    },
                ],
            },
        },
    },
}

TRANSFORMED_REPOS_DATA = {
    "repos": [
        {
            "id": "https://fake.github.net/graphql/:MDEwOlJlcG9zaXRvcnkxNg==",
            "createdat": "2018-06-20T00:53:01Z",
            "name": "pythontestlib",
            "fullname": "fake/pythontestlib",
            "description": "Fake service for testing",
            "primarylanguage": "Python",
            "homepage": None,
            "defaultbranch": "master",
            "defaultbranchid": "https://fake.github.net/graphql/:MDM6UmVmMTY6bWFzdGVy",
            "private": True,
            "disabled": False,
            "archived": False,
            "locked": False,
            "giturl": "git://fake.github.net:pythontestlib.git",
            "url": "https://fake.github.net/pythontestlib",
            "sshurl": "git@fake.github.net/pythontestlib.git",
            "updatedat": "2019-10-07T21:49:08Z",
        },
    ],
    "repo_owners": [
        {
            "repoid": "https://fake.github.net/graphql/:MDEwOlJlcG9zaXRvcnkxNg==",
            "owner": "fake",
            "ownerid": "https://fake.github.net/graphql/:MDAxOk9yZ2FuaXphdGlvbjE=",
            "type": "Organization",
        },
    ],
    "repo_languages": [
        {
            "repoid": "https://fake.github.net/graphql/:MDEwOlJlcG9zaXRvcnkxNg==",
            "language": "Makefile",
            "languageid": "Makefile",
        },
        {
            "repoid": "https://fake.github.net/graphql/:MDEwOlJlcG9zaXRvcnkxNg==",
            "language": "Python",
            "languageid": "Python",
        },
    ],
}
