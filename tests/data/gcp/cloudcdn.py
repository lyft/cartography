TEST_BACKEND_BUCKET = [
    {
        "name": "backendbucket123",
        "id": "projects/projects123/global/backendBuckets/backendbucket123",
        "enableCdn": True,
        "cdnPolicy": {
            "defaultTtl": 122,
            "maxTtl": 300,
        },

    },
]

TEST_GLOBAL_BACKEND_SERVICE = [
    {
        "name": "globalser123",
        "id": "projects/project123/global/backendServices/globalser123",
        "enableCdn": True,
        "cdnPolicy": {
            "defaultTtl": 122,
            "maxTtl": 300,
        },
    },
]

TEST_REGIONAL_BACKEND_SERVICE = [
    {
        "name": "regionalser123",
        "id": "projects/project123/regions/us-east1-a/backendServices/regionalser123",
        "region": "us-east1-a",
        "enableCdn": True,
        "cdnPolicy": {
            "defaultTtl": 122,
            "maxTtl": 300,
        },
    },
]

TEST_GLOBAL_URL_MAP = [
    {
        "name": "globalmap123",
        "id": "projects/project123/global/urlmaps/globalmap123",
        "defaultService": "service123",
    },
]

TEST_REGIONAL_URL_MAP = [
    {
        "name": "regionalmap123",
        "id": "projects/project123/regions/us-east1-a/urlmaps/regionalmap123",
        "region": "us-east1-a",
        "defaultService": "service123",
    },
]
