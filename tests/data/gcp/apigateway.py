TEST_APIGATEWAY_LOCATIONS = [
    {
        'name': 'projects/project123/locations/us-east1',
        'id': 'us-east1',
        'locationId': 'us-east1',
        'displayName': 'South Carolina',
    },
    {
        'name': 'projects/project123/locations/us-east4',
        'id': 'us-east4',
        'locationId': 'us-east1',
        'displayName': 'Virginia',
    },
]
TEST_APIGATEWAY_APIS = [
    {
        'name': 'projects/project123/locations/global/apis/compute',
        'id': 'compute',
        'createTime': '2020-10-02T15:01:23Z',
        'updateTime': '2020-11-02T15:01:23Z',
        'displayName': 'compute',
        'managedService': 'compute',
    },
    {
        'name': 'projects/project123/locations/global/apis/storage',
        'id': 'storage',
        'createTime': '2020-10-02T15:01:23Z',
        'updateTime': '2020-11-02T15:01:23Z',
        'displayName': 'storage',
        'managedService': 'storage',
    },
]
TEST_API_CONFIGS = [
    {
        'name': 'projects/project123/locations/global/apis/compute/configs/config123',
        'id': 'config123',
        'api_id': 'compute',
        'createTime': '2020-10-02T15:01:23Z',
        'updateTime': '2020-11-02T15:01:23Z',
        'displayName': 'config123',
        'gatewayServiceAccount': 'abc@example.com',
        'serviceConfigId': '123',
        'state': 'ACTIVE',
    },
    {
        'name': 'projects/project123/locations/global/apis/storage/configs/config456',
        'id': 'config456',
        'api_id': 'storage',
        'createTime': '2020-10-02T15:01:23Z',
        'updateTime': '2020-11-02T15:01:23Z',
        'displayName': 'config123',
        'gatewayServiceAccount': 'abc@example.com',
        'serviceConfigId': '456',
        'state': 'ACTIVE',
    },
]
TEST_GATEWAYS = [
    {
        'name': 'projects/project123/locations/us-east1/gateways/gateway123',
        'id': 'gateway123',
        'apiConfig': 'config123',
        'createTime': '2020-10-02T15:01:23Z',
        'updateTime': '2020-11-02T15:01:23Z',
        'displayName': 'gateway123',
        'state': 'ACTIVE',
        'defaultHostname': 'host123',
    },
    {
        'name': 'projects/project123/locations/us-east1/gateways/gateway456',
        'id': 'gateway456',
        'apiConfig': 'config456',
        'createTime': '2020-10-02T15:01:23Z',
        'updateTime': '2020-11-02T15:01:23Z',
        'displayName': 'gateway123',
        'state': 'ACTIVE',
        'defaultHostname': 'host456',
    },
]
