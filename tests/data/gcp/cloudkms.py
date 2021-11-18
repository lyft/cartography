CLOUD_KMS_LOCATIONS = [
    {
        'name': 'us-east1',
        'locationId': 'us-east1',
        'displayName': 'South Carolina'
    },
    {
        'name': 'us-east4',
        'locationId': 'us-east4',
        'displayName': 'Virginia'
    }
]

CLOUD_KMS_KEYRINGS = [
    {
        'name': 'keyring1',
        'createTime': '2021-10-02T15:01:23Z'
    },
    {
        'name': 'keyring2',
        'createTime': '2021-01-02T22:12:00Z'
    }
]

CLOUD_KMS_CRYPTO_KEYS = [
    {
        'name': 'cryptokey123',
        'purpose': 'ENCRYPT_DECRYPT',
        'createTime': '2020-01-01T00:00:00Z',
        'nextRotationTime': '2020-01-02T00:00:00Z',
        'rotationPeriod': '86400s'
    },
    {
        'name': 'cryptokey456',
        'purpose': 'ENCRYPT_DECRYPT',
        'createTime': '2020-02-01T00:00:00Z',
        'nextRotationTime': '2020-02-02T00:00:00Z',
        'rotationPeriod': '86400s'
    }
]
