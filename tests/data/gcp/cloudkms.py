CLOUD_KMS_LOCATIONS = [
    {
        'id': 'us-east1',
        'name': 'us-east1',
        'locationId': 'us-east1',
        'displayName': 'South Carolina',
    },
    {
        'id': 'us-east4',
        'name': 'us-east4',
        'locationId': 'us-east4',
        'displayName': 'Virginia',
    },
]

CLOUD_KMS_KEYRINGS = [
    {
        'id': 'keyring1',
        'loc_id': 'us-east1',
        'name': 'keyring1',
        'createTime': '2021-10-02T15:01:23Z',
    },
    {
        'id': 'keyring2',
        'loc_id': 'us-east4',
        'name': 'keyring2',
        'createTime': '2021-01-02T22:12:00Z',
    },
]

CLOUD_KMS_CRYPTO_KEYS = [
    {
        'id': 'cryptokey123',
        'keyring_id': 'keyring1',
        'name': 'cryptokey123',
        'purpose': 'ENCRYPT_DECRYPT',
        'createTime': '2020-01-01T00:00:00Z',
        'nextRotationTime': '2020-01-02T00:00:00Z',
        'rotationPeriod': '86400s',
    },
    {
        'id': 'cryptokey456',
        'keyring_id': 'keyring2',
        'name': 'cryptokey456',
        'purpose': 'ENCRYPT_DECRYPT',
        'createTime': '2020-02-01T00:00:00Z',
        'nextRotationTime': '2020-02-02T00:00:00Z',
        'rotationPeriod': '86400s',
    },
]
FUNCTION_POLICY_BINDINGS = [

    {
        'id': 'projects/000000000000/function/keyring1/role/viewer',
        'members': [
            'allUsers',
            'allAuthenticatedUsers',
        ],
        'role': 'viewer',

    },
]
