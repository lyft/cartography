config = {
    "authorization": {
        "key": "Authorization",
        "value": "some-auth-token"
    },
    "lambda": {
        "authorization": "ftWtPSJUc3phkh"
    },
    "neo4j": {
        "uri": "bolt://ec2-18-191-150-182.us-east-2.compute.amazonaws.com:7687/",
        "browser": "http://ec2-18-191-150-182.us-east-2.compute.amazonaws.com:7474/browser/",
        "user": "neo4j",
        "pwd": "QhzhgUU7CFGTKmTdurRFaSY8B2"
    },
    "kms": {
        "region": "us-east-2",
        "assumeRoleAccessKeyKMSKeyID": "c8e19213-3e5f-4600-ae85-b7986c0562a3",
        "assumeRoleAccessKeyCipher": "AQICAHhya2gwASGqw/ZLunc+BIVfpFpO25GaCcIDZDQiUjmDXwEIrUHXPzCmped/r38iHO6kAAAAcjBwBgkqhkiG9w0BBwagYzBhAgEAMFwGCSqGSIb3DQEHATAeBglghkgBZQMEAS4wEQQM/QHnNEoBg8UM42pGAgEQgC+OZtT8bm8LTwh148ggpb5v+KXFlzliFCIXvDs5gxgEtvF+5KZFBT3NvVv06ZJ65A==",
        "assumeRoleAccessSecretKMSKeyID": "70746045-682e-4009-b797-072f09e06f45",
        "assumeRoleAccessSecretCipher": "AQICAHg9c8cececNHNax8rne9Ojo71KlIMY5aOjrjNuuYEINNgFioDpeuewAt2ZL1fw84prEAAAAhzCBhAYJKoZIhvcNAQcGoHcwdQIBADBwBgkqhkiG9w0BBwEwHgYJYIZIAWUDBAEuMBEEDOMtMkLeOgFEiNyBIQIBEIBDaJ7QHddceHWcZdXvTymo9sVkD7E3Be4sSpvP4IbQ0KeQoMzUPQNRPjqpUZhTYrxro2sOIleRg/ousNS/0sdaXn1vGQ=="
    },
    "aws": {
        "sessionDuration": 3600,
        "region": "us-east-2",
        "logLevel": "DEBUG"
    },
    "sns": {
        "region": "us-east-2",
        "requestTopic": "arn:aws:sns:us-east-2:774118602354:inventory-sync-aws-requests",
        "resultTopic": "arn:aws:sns:us-east-2:774118602354:inventory-sync-aws-results",
        "offlineURL": "http://127.0.0.1:5002/inventory-sync-aws-prod-inventorySyncWorker"
    }
}
