TEST_DATASET = [
    {
        'id': 'dataset1',
        'details' : {
            'friendlyName': 'dataset123',
            'defaultTableExpirationMs': '23',
            'defaultPartitionExpirationMs': '20',
            'location': 'us-east1',
            'defaultCollation': 'und:ci',
            'maxTimeTravelHours': '2'
        }
    },
    {
        'id': 'dataset2',
        'details' : {
            'friendlyName': 'dataset1234',
            'defaultTableExpirationMs': '25',
            'defaultPartitionExpirationMs': '26',
            'location': 'us-east1',
            'defaultCollation': 'und:ci',
            'maxTimeTravelHours': '2'
        }
    }   
]

TEST_TABLE = [
    {
        'id': 'table1',
        'datasetId': 'dataset1',
        'details': {
            'friendlyName': 'table123',
            'requirePartitionFilter': True,
            'numBytes': '34',
            'numLongTermBytes': '128',
            'numRows': '4'
        }
    },
    {
        'id': 'table2',
        'datasetId': 'dataset2',
        'details': {
            'friendlyName': 'table1234',
            'requirePartitionFilter': True,
            'numBytes': '35',
            'numLongTermBytes': '256',
            'numRows': '3'
        }
    }
]