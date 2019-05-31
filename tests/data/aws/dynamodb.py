import datetime


LIST_DYNAMODB_TABLES = {
    "Tables": [
        {
            "TableArn": "arn:aws:dynamodb::000000000000:table/example-table",
            "TableName": "sample-table",
            "Rows": 1000000,
            "GSIs": [
                {
                    "IndexArn": "arn:aws:dynamodb::table/sample_gsi_1",
                    "GSIName": "sample_index_1",
                    "ProvisionedThroughputReadCapacityUnits": 10,
                    "ProvisionedThroughputWriteCapacityUnits": 10
                 },
                {
                    "IndexArn": "arn:aws:dynamodb::table/sample_gsi_2",
                    "GSIName": "sample_index_2",
                    "ProvisionedThroughputReadCapacityUnits": 20,
                    "ProvisionedThroughputWriteCapacityUnits": 20
                }
            ],
            "Size": 123456789,
            "ProvisionedThroughputReadCapacityUnits": 10,
            "ProvisionedThroughputWriteCapacityUnits": 10
        }
    ]
}


LIST_DYNAMODB_TABLES_FORMATTED = {
    "Tables": [
        {
            "Table": {
                "TableArn": "arn:aws:dynamodb::000000000000:table/example-table",
                "AttributeDefinitions": [
                    {
                        "AttributeName": "sample_1",
                        "AttributeType": "A"
                    },
                    {
                        "AttributeName": "sample_2",
                        "AttributeType": "B"
                    },
                    {
                        "AttributeName": "sample_3",
                        "AttributeType": "C"
                    }
                ],
                "GlobalSecondaryIndexes": [
                    {
                        "IndexSizeBytes": 11111111,
                        "IndexName": "sample_index_1",
                        "Projection": {
                            "ProjectionType": "ALL"
                        },
                        "ProvisionedThroughput": {
                            "WriteCapacityUnits": 10,
                            "ReadCapacityUnits": 10
                        },
                        "IndexStatus": "ACTIVE",
                        "KeySchema": [
                            {
                                "KeyType": "HASH",
                                "AttributeName": "sample_schema"
                            }
                        ],
                        "IndexArn": "arn:aws:dynamodb::table/sample_gsi_1",
                        "ItemCount": 1000000
                    },
                    {
                        "IndexSizeBytes": 22222222,
                        "IndexName": "sample_index_2",
                        "Projection": {
                            "ProjectionType": "ALL"
                        },
                        "ProvisionedThroughput": {
                            "WriteCapacityUnits": 10,
                            "ReadCapacityUnits": 10
                        },
                        "IndexStatus": "ACTIVE",
                        "KeySchema": [
                            {
                                "KeyType": "HASH",
                                "AttributeName": "sample_schema"
                            }
                        ],
                        "IndexArn": "arn:aws:dynamodb::table/sample_gsi_2",
                        "ItemCount": 1000000
                    }
                ],
                "ProvisionedThroughput": {
                    "NumberOfDecreasesToday": 10,
                    "WriteCapacityUnits": 10,
                    "LastIncreaseDateTime": 1000000000.000,
                    "ReadCapacityUnits": 10,
                    "LastDecreaseDateTime": 1000000000.000
                },
                "TableSizeBytes": 100000000,
                "TableName": "sample-table",
                "TableStatus": "ACTIVE",
                "StreamSpecification": {
                    "StreamViewType": "SAMPLE_STREAM_VIEW_TYPE",
                    "StreamEnabled": True
                },
                "TableId": "00000000-0000-0000-0000-000000000000",
                "LatestStreamLabel": "0000-00-00000:00:00.000",
                "KeySchema": [
                    {
                        "KeyType": "HASH",
                        "AttributeName": "sample_schema"
                    }
                ],
                "ItemCount": 1000000,
                "CreationDateTime": 1000000000.000,
                "LatestStreamArn": "arn:aws:dynamodb::table/sample-table/stream/0000-00-00000:00:00.000"
            }
        }
    ]
}
