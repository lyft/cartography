

LIST_DYNAMODB_TABLES_FORMATTED = {
    "Tables": [
        {
            "TableArn": "arn:aws:dynamodb::000000000000:table/example-table-1",
            "TableName": "example-table-1",
            "Rows": 1000000,
            "GSIs": [
                {
                    "IndexArn": "arn:aws:dynamodb::table/example-table-1/index/sample_1-index",
                    "GSIName": "sample_index_1",
                    "ProvisionedThroughputReadCapacityUnits": 10,
                    "ProvisionedThroughputWriteCapacityUnits": 10
                 },
                {
                    "IndexArn": "arn:aws:dynamodb::table/example-table-1/index/sample_2-index",
                    "GSIName": "sample_index_2",
                    "ProvisionedThroughputReadCapacityUnits": 20,
                    "ProvisionedThroughputWriteCapacityUnits": 20
                }
            ],
            "Size": 123456789,
            "ProvisionedThroughputReadCapacityUnits": 10,
            "ProvisionedThroughputWriteCapacityUnits": 10
        },
        {
            "TableArn": "arn:aws:dynamodb::000000000000:table/example-table-2",
            "TableName": "example-table-2",
            "Rows": 1000000,
            "GSIs": [
                {
                    "IndexArn": "arn:aws:dynamodb::table/example-table-2/index/sample_1-index",
                    "GSIName": "sample_index_1",
                    "ProvisionedThroughputReadCapacityUnits": 10,
                    "ProvisionedThroughputWriteCapacityUnits": 10
                 },
                {
                    "IndexArn": "arn:aws:dynamodb::table/example-table-2/index/sample_2-index",
                    "GSIName": "sample_index_2",
                    "ProvisionedThroughputReadCapacityUnits": 20,
                    "ProvisionedThroughputWriteCapacityUnits": 20
                }
            ],
            "Size": 123456789,
            "ProvisionedThroughputReadCapacityUnits": 10,
            "ProvisionedThroughputWriteCapacityUnits": 10
        },
        {
            "TableArn": "arn:aws:dynamodb::000000000000:table/example-table-3",
            "TableName": "example-table-3",
            "Rows": 1000000,
            "GSIs": [
                {
                    "IndexArn": "arn:aws:dynamodb::table/example-table-3/index/sample_1-index",
                    "GSIName": "sample_index_1",
                    "ProvisionedThroughputReadCapacityUnits": 10,
                    "ProvisionedThroughputWriteCapacityUnits": 10
                 },
                {
                    "IndexArn": "arn:aws:dynamodb::table/example-table-3/index/sample_2-index",
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


LIST_DYNAMODB_TABLES = {
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
                            "WriteCapacityUnits": 30,
                            "ReadCapacityUnits": 30
                        },
                        "IndexStatus": "ACTIVE",
                        "KeySchema": [
                            {
                                "KeyType": "HASH",
                                "AttributeName": "sample_schema"
                            }
                        ],
                        "IndexArn": "arn:aws:dynamodb::table/example-table/index/sample_1-index",
                        "ItemCount": 1000000
                    },
                    {
                        "IndexSizeBytes": 22222222,
                        "IndexName": "sample_index_2",
                        "Projection": {
                            "ProjectionType": "ALL"
                        },
                        "ProvisionedThroughput": {
                            "WriteCapacityUnits": 40,
                            "ReadCapacityUnits": 40
                        },
                        "IndexStatus": "ACTIVE",
                        "KeySchema": [
                            {
                                "KeyType": "HASH",
                                "AttributeName": "sample_schema"
                            }
                        ],
                        "IndexArn": "arn:aws:dynamodb::table/example-table/index/sample_2-index",
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
                "TableName": "example-table",
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
        },
        {
            "Table": {
                "TableArn": "arn:aws:dynamodb::000000000000:table/sample-table",
                "GlobalSecondaryIndexes": [
                    {
                        "IndexSizeBytes": 11111111,
                        "IndexName": "sample_index_1",
                        "Projection": {
                            "ProjectionType": "ALL"
                        },
                        "ProvisionedThroughput": {
                            "WriteCapacityUnits": 30,
                            "ReadCapacityUnits": 30
                        },
                        "IndexStatus": "ACTIVE",
                        "KeySchema": [
                            {
                                "KeyType": "HASH",
                                "AttributeName": "sample_schema"
                            }
                        ],
                        "IndexArn": "arn:aws:dynamodb::table/sample-table/index/sample_1-index",
                        "ItemCount": 1000000
                    },
                    {
                        "IndexSizeBytes": 22222222,
                        "IndexName": "sample_index_2",
                        "Projection": {
                            "ProjectionType": "ALL"
                        },
                        "ProvisionedThroughput": {
                            "WriteCapacityUnits": 40,
                            "ReadCapacityUnits": 40
                        },
                        "IndexStatus": "ACTIVE",
                        "KeySchema": [
                            {
                                "KeyType": "HASH",
                                "AttributeName": "sample_schema"
                            }
                        ],
                        "IndexArn": "arn:aws:dynamodb::table/sample-table/index/sample_2-index",
                        "ItemCount": 1000000
                    },
                    {
                        "IndexSizeBytes": 33333333,
                        "IndexName": "sample_index_2",
                        "Projection": {
                            "ProjectionType": "ALL"
                        },
                        "ProvisionedThroughput": {
                            "WriteCapacityUnits": 50,
                            "ReadCapacityUnits": 50
                        },
                        "IndexStatus": "ACTIVE",
                        "KeySchema": [
                            {
                                "KeyType": "HASH",
                                "AttributeName": "sample_schema"
                            }
                        ],
                        "IndexArn": "arn:aws:dynamodb::table/sample-table/index/sample_3-index",
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
                "TableId": "00000000-0000-0000-0000-000000000000",
                "LatestStreamLabel": "0000-00-00000:00:00.000",
                "ItemCount": 1000000,
                "LatestStreamArn": "arn:aws:dynamodb::table/sample-table/stream/0000-00-00000:00:00.000"
            }
        }
    ]
}
