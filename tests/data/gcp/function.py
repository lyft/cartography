CLOUD_FUNCTION = [
    {
        "name": "function123",
        "id": "function123",
        "description": "Cloud Function123",
        "status": "ACTIVE",
        "entryPoint": "function123.cloud.google.com",
        "runtime": "python3.8",
        "timeout": "3s",
        "availableMemoryMb": 256,
        "serviceAccountEmail": "abc123456@gmail.com",
        "updateTime": "2021-10-02T15:01:23Z",
        "versionId": "123.1",
        "network": "vpc123",
        "maxInstances": 2,
        "vpcConnector": "vpc-c123",
        "vpcConnectorEgressSettings": "PRIVATE_RANGES_ONLY",
        "ingressSettings": "ALLOW_INTERNAL_ONLY",
        "buildWorkerPool": "buildWorkerPool123",
        "buildId": "bwp123",
        "sourceToken": "abc@%112",
        "sourceArchiveUrl": "function123archive.cloud.google.com",
    },
    {
        "name": "function456",
        "id": "function456",
        "description": "Cloud Function456",
        "status": "ACTIVE",
        "entryPoint": "function456.cloud.google.com",
        "runtime": "python3.8",
        "timeout": "3.5s",
        "availableMemoryMb": 512,
        "serviceAccountEmail": "abc123456@gmail.com",
        "updateTime": "2021-10-02T15:01:23Z",
        "versionId": "123.1",
        "network": "vpc123",
        "maxInstances": 2,
        "vpcConnector": "vpc-c123",
        "vpcConnectorEgressSettings": "PRIVATE_RANGES_ONLY",
        "ingressSettings": "ALLOW_INTERNAL_ONLY",
        "buildWorkerPool": "buildWorkerPool456",
        "buildId": "bwp456",
        "sourceToken": "abc@%345",
        "sourceArchiveUrl": "function123archive.cloud.google.com",
    },
]

FUNCTION_POLICY_BINDINGS = [

    {
        'id': 'projects/abcd12345/function/function123/role/viewer',
        'members': [
            'allUsers',
            'allAuthenticatedUsers',
        ],
        'role': 'viewer',

    },
]
