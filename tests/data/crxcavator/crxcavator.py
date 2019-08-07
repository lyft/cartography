# flake8: noqa
REPORT_RESPONSE = {
    'f06981cbc72a3c6e2e9e736cbdaef4865a4571bc':
        [
            {
                'data':
                {
                    'risk':
                        {
                            'total': 437,
                            'metadata': {},
                        },
                    'webstore':
                        {
                            'address': '',
                            'email': '',
                            'icon': 'https://lh3.googleusercontent.com/fake',
                            'last_updated': '2016-02-22',
                            'name': 'CartographyIntegrationTest',
                            'offered_by': '',
                            'permission_warnings': [
                                'Your data on all websites',
                            ],
                            'privacy_policy': '',
                            'rating': 4.6778846,
                            'rating_users': 208,
                            'short_description': 'fake extension for Cartography integration testing',
                            'size': '13.95KiB',
                            'support_site': '',
                            'users': 38241,
                            'version': '',
                            'website': '',
                            'type': 'Extension',
                            'price': '',
                        },
                },
                'extension_id': 'f06981cbc72a3c6e2e9e736cbdaef4865a4571bc',
                'version': '1.0',
            },
        ],
}

TRANSFORMED_EXTENSIONS_DATA = [
    {
        'id': 'f06981cbc72a3c6e2e9e736cbdaef4865a4571bc|1.0',
        'extension_id': 'f06981cbc72a3c6e2e9e736cbdaef4865a4571bc',
        'version': '1.0',
        'risk_total': 437,
        'risk_metadata': '{}',
        'address': '',
        'email': '',
        'icon': 'https://lh3.googleusercontent.com/fake',
        'crxcavator_last_updated': '2016-02-22',
        'name': 'CartographyIntegrationTest',
        'offered_by': '',
        'permissions_warnings': ['Your data on all websites'],
        'privacy_policy': '',
        'rating': 4.6778846,
        'rating_users': 208,
        'short_description': 'fake extension for Cartography integration testing',
        'size': '13.95KiB',
        'support_site': '',
        'users': 38241,
        'website': '',
        'type': 'Extension',
        'price': '',
        'report_link': 'https://crxcavator.io/report/f06981cbc72a3c6e2e9e736cbdaef4865a4571bc/1.0',
    },
]

USER_RESPONSE = {
    'f06981cbc72a3c6e2e9e736cbdaef4865a4571bc':
        {
            '4.8':
            {
                'name': 'CartographyIntegrationTest',
                'users': ['user@example.com'],
            },
        },
}

TRANSFORMED_USER_DATA = ['user@example.com']

TRANSFORMED_USER_EXTENSION_DATA = [
    {
        'id': 'f06981cbc72a3c6e2e9e736cbdaef4865a4571bc|1.0',
        'user': 'user@example.com',
    },
]
