GITHUB_USER_DATA = [
    {
        'hasTwoFactorEnabled': None,
        'node': {
            'url': 'https://example.com/hjsimpson',
            'login': 'hjsimpson',
            'name': 'Homer Simpson',
            'isSiteAdmin': False,
            'email': 'hjsimpson@example.com',
            'company': 'Springfield Nuclear Power Plant',
        },
        'role': 'MEMBER',
    }, {
        'hasTwoFactorEnabled': None,
        'node': {
            'url': 'https://example.com/mbsimpson',
            'login': 'mbsimpson',
            'name': 'Marge Simpson',
            'isSiteAdmin': False,
            'email': 'mbsimpson@example.com',
            'company': 'Simpson Residence',
        },
        'role': 'ADMIN',
    },
]

GITHUB_ORG_DATA = {
    'url': 'https://example.com/my_org',
    'login': 'my_org',
}

USERS_WITH_RATE_LIMIT_DATA = {
    "data": {
        "organization": {
            "url": "https: //github.com/my_org",
            "login": "my_org",
            "membersWithRole": {
                "edges": [
                    {
                        "hasTwoFactorEnabled": None,
                        "node": {
                            "url": "https://github.com/example",
                            "login": "usher",
                            "name": "Ursha B",
                            "isSiteAdmin": False,
                            "email": "",
                            "company": None,
                        },
                        "role": "MEMBER",
                    },
                ],
                "pageInfo": {
                    "endCursor": "c29yOnYyx8Q=",
                    "hasNextPage": True,
                },
            },
        },
        "rateLimit": {
            "remaining": 4957,
            "resetAt": "2023-10-06T16:11:07Z",
        },
    },
}
