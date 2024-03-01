DESCRIBE_IDENTITIES_RESPONSE = [
    {
        "name": 'example.com',
        'region': 'us-east-1',
        'arn': "arn:aws:ses:us-east-1:123456789012:identity/example.com",
        "dkim": {
            "DkimTokens": [
               "EXAMPLEjcs5xoyqytjsotsijas7236gr",
               "EXAMPLEjr76cvoc6mysspnioorxsn6ep",
               "EXAMPLEkbmkqkhlm2lyz77ppkulerm4k",
            ],
            "DkimEnabled": True,
            "DkimVerificationStatus": "Success",
        },
        "verification": {
            "VerificationStatus": "Success",
        },
    },
]
