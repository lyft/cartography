IAM_ROLES = [
    {
        'name': 'projects/project123/roles/logging.viewer',
        'id': 'projects/project123/roles/logging.viewer',
        'title': 'logging.viewer',
        'description': 'Can view logs',
        'deleted': False,
        'includedPermissions': 'logging.buckets.get',
    },
    {
        'name': 'projects/project123/roles/compute.viewer',
        'id': 'projects/project123/roles/compute.viewer',
        'title': 'compute.viewer',
        'description': 'Can view compute instances',
        'deleted': False,
        'includedPermissions': 'compute.instances.get',
    },
]
IAM_SERVICE_ACCOUNTS = [
    {
        'name': 'projects/project123/serviceAccounts/abc@gmail.com',
        'id': 'projects/project123/serviceAccounts/abc@gmail.com',
        'projectId': 'project123',
        'uniqueId': 'abcproject123',
        'displayName': 'abc',
        'disabled': False,
    },
    {
        'name': 'projects/project123/serviceAccounts/defg@gmail.com',
        'id': 'projects/project123/serviceAccounts/defg@gmail.com',
        'projectId': 'project123',
        'uniqueId': 'defgproject123',
        'displayName': 'defg',
        'disabled': False,
    },
]
IAM_SERVICE_ACCOUNT_KEYS = [
    {
        'name': 'abc@gmail.com/key123',
        'id': 'abc@gmail.com/key123',
        'serviceaccount': 'projects/project123/serviceAccounts/abc@gmail.com',
        'keyType': 'USER_MANAGED',
        'keyOrigin': 'USER_PROVIDED',
        'keyAlgorithm': 'KEY_ALG_RSA_2048',
        'validBeforeTime': '2019-10-02T15:01:23Z',
        'validAfterTime': '2020-10-02T15:01:23Z',
    },
    {
        'name': 'defg@gmail.com/key456',
        'id': 'defg@gmail.com/key456',
        'serviceaccount': 'projects/project123/serviceAccounts/defg@gmail.com',
        'keyType': 'SYSTEM_MANAGED',
        'keyOrigin': 'GOOGLE_PROVIDED',
        'keyAlgorithm': 'KEY_ALG_RSA_2048',
        'validBeforeTime': '2019-10-02T15:01:23Z',
        'validAfterTime': '2020-10-02T15:01:23Z',
    },
]
IAM_USERS = [
    {
        'id': 'user123',
        'customerId': 'customer123',
        'primaryEmail': 'abc@example.com',
        'isAdmin': False,
        'isDelegatedAdmin': False,
        'agreedToTerms': True,
        'suspended': False,
        'changePasswordAtNextLogin': False,
        'ipWhitelisted': True,
        'name': {
            'fullName': 'abc',
            'familyName': '123',
            'givenName': 'abc',
        },
        'isMailboxSetup': True,
        'customerId': 'customer123',
        'addresses': 'street123',
        'organizations': 'org123',
        'lastLoginTime': '2020-10-02T15:01:23Z',
        'suspensionReason': [],
        'creationTime': '2019-10-02T15:01:23Z',
        'deletionTime': '2021-10-02T15:01:23Z',
        'gender': 'Male',
    },
    {
        'id': 'user456',
        'customerId': 'customer123',
        'primaryEmail': 'def@example.com',
        'isAdmin': False,
        'isDelegatedAdmin': False,
        'agreedToTerms': True,
        'suspended': False,
        'changePasswordAtNextLogin': False,
        'ipWhitelisted': True,
        'name': {
            'fullName': 'def',
            'familyName': '456',
            'givenName': 'def',
        },
        'isMailboxSetup': True,
        'customerId': 'customer123',
        'addresses': 'street456',
        'organizations': 'org456',
        'lastLoginTime': '2020-10-02T15:01:23Z',
        'suspensionReason': [],
        'creationTime': '2020-01-01T15:01:23Z',
        'deletionTime': '2020-12-31T15:01:23Z',
        'gender': 'Female',
    },
]
IAM_GROUPS = [
    {
        'id': 'group123',
        'customerId': 'customer123',
        'groupEmail': 'group123@example.com',
        'adminCreated': True,
        'directMembersCount': 5,
    },
    {
        'id': 'group456',
        'customerId': 'customer123',
        'groupEmail': 'group456@example.com',
        'adminCreated': True,
        'directMembersCount': 10,
    },
]
IAM_DOMAINS = [
    {
        'id': 'xyz.com',
        'customerId': 'customer123',
        'domainAliases': {
            'parentDomainName': 'www.xyz.com',
            'domainAliasName': 'helloworld.com',
        },
        'verified': True,
        'isPrimary': True,
        'domainName': 'xyz.com',
    },
    {
        'id': 'pqr.com',
        'customerId': 'customer123',
        'domainAliases': {
            'parentDomainName': 'www.pqr.com',
            'domainAliasName': 'hellouniverse.com',
        },
        'verified': True,
        'isPrimary': True,
        'domainName': 'pqr.com',
    },
]
API_KEY = [
    {
        "name": "projects/project123/locations/global/keys/key123",
        "id": "projects/project123/locations/global/keys/key123",
        "updateTime": "2022-07-02T15:01:23Z",
        "deleteTime": "2022-08-02T15:01:23Z",
        "region": "global",
    },
]
