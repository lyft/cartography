import cartography.intel.aws.ec2
import tests.data.aws.ec2.route_tables


TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'eu-north-1'
TEST_UPDATE_TAG = 123456789


def test_load_route_tables(neo4j_session):
    data = tests.data.aws.ec2.route_tables.DESCRIBE_ROUTE_TABLES['RouteTables']
    cartography.intel.aws.ec2.route_tables.load_route_tables(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "rtb-01fbd15d4b6e8e14f",
        "rtb-0d49710751f04455d",
        "rtb-0598ecac672acbf05",
        "rtb-08f8aaf2ada59d690",
        "rtb-07a78a66193459750",
        "rtb-09283c3c06ce8e5e7",
        "rtb-0207beae6b93bd50d",
        "rtb-0d5006b1d9278e552",
        "rtb-0c0188db3fa50c49f",
        "rtb-0dc050eb977881a19",
        "rtb-063d90f2ffa00ef6e",
        "rtb-098b040d4e81f0f7a",
        "rtb-0117d21e47a6a7c3b",
        "rtb-01248d9044975822b",
        "rtb-0dce814dd3fdb321f",
        "rtb-d1b7ceb3",
        "rtb-04bc62120121cfbef",
        "rtb-0fa0eb0f6130f6a2e",

    }

    nodes = neo4j_session.run(
        """
        MATCH (rtb:EC2RouteTable) RETURN rtb.id;
        """,
    )
    actual_nodes = {n['rtb.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_route_table_associations(neo4j_session):
    data = tests.data.aws.ec2.route_tables.DESCRIBE_ROUTE_TABLES['RouteTables']
    cartography.intel.aws.ec2.route_tables.load_associations(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        ("subnet-0c7b7f891a4bab804", "rtb-01fbd15d4b6e8e14f"),
        ("subnet-061a59c1e8a0ce808", "rtb-0d49710751f04455d"),
        ("subnet-0c43238df6ad49d47", "rtb-0598ecac672acbf05"),
        ("subnet-0c90bc569203c5262", "rtb-08f8aaf2ada59d690"),
        ("subnet-088d675bb0b364938", "rtb-07a78a66193459750"),
        ("subnet-093db86655a0c34e0", "rtb-09283c3c06ce8e5e7"),
        ("subnet-0d5fae10e854b5605", "rtb-0207beae6b93bd50d"),
        ("subnet-0ec4e216c304a4c33", "rtb-0d5006b1d9278e552"),
        ("subnet-05e2c6eb0aad65b91", "rtb-0c0188db3fa50c49f"),
        ("subnet-024ad69f0f023ab2c", "rtb-098b040d4e81f0f7a"),
        ("subnet-014f6e6a1612f8b80", "rtb-0117d21e47a6a7c3b"),
        ("subnet-065a22958fc169a9f", "rtb-01248d9044975822b"),
        ("subnet-063c3e2018bc27009", "rtb-0dce814dd3fdb321f"),
        ("subnet-0e873330aa6826631", "rtb-04bc62120121cfbef"),
        ("subnet-0d65a01441fc71c89", "rtb-0fa0eb0f6130f6a2e"),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (snet:EC2Subnet)-[:ASSOCIATED]->(rtb:EC2RouteTable)
        RETURN snet.subnetid, rtb.id;
        """,
    )
    actual = {
        (r['snet.subnetid'], r['rtb.id']) for r in result
    }

    assert actual == expected_nodes


def load_routes(neo4j_session):
    data = tests.data.aws.ec2.route_tables.DESCRIBE_ROUTE_TABLES['RouteTables']
    cartography.intel.aws.ec2.route_tables.load_routes(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        ("rtb-0598ecac672acbf05", "rtb-0598ecac672acbf05|0.0.0.0/0", "igw-007fe6f07b9419e44"),
        ("rtb-08f8aaf2ada59d690", "rtb-08f8aaf2ada59d690|0.0.0.0/0", "nat-07a8fec9c93adce98"),
        ("rtb-08f8aaf2ada59d690", "rtb-08f8aaf2ada59d690|10.111.4.0/24", "pcx-0324c63d04ee3c9ed"),
        ("rtb-08f8aaf2ada59d690", "rtb-08f8aaf2ada59d690|10.0.0.0/16", "pcx-0eaf218d38475cc58"),
        ("rtb-07a78a66193459750", "rtb-07a78a66193459750|0.0.0.0/0", "igw-0cc1d5db8cb8ff02e"),
        ("rtb-09283c3c06ce8e5e7", "rtb-09283c3c06ce8e5e7|10.110.22.0/22", "pcx-0a789485435a19f67"),
        ("rtb-09283c3c06ce8e5e7", "rtb-09283c3c06ce8e5e7|172.183.21.203/32", "vgw-0afe079e97f2c77f8"),
        ("rtb-09283c3c06ce8e5e7", "rtb-09283c3c06ce8e5e7|10.110.26.0/22", "pcx-0a789485435a19f67"),
        ("rtb-09283c3c06ce8e5e7", "rtb-09283c3c06ce8e5e7|172.154.90.0/24", "vgw-0afe079e97f2c77f8"),
        ("rtb-09283c3c06ce8e5e7", "rtb-09283c3c06ce8e5e7|0.0.0.0/0", "nat-0cd63b8fc50ad665c"),
        ("rtb-09283c3c06ce8e5e7", "rtb-09283c3c06ce8e5e7|10.110.30.0/22", "pcx-0a789485435a19f67"),
        ("rtb-09283c3c06ce8e5e7", "rtb-09283c3c06ce8e5e7|172.24.29.0/24", "vgw-0afe079e97f2c77f8"),
        ("rtb-0207beae6b93bd50d", "rtb-0207beae6b93bd50d|10.111.4.0/24", "pcx-0324c63d04ee3c9ed"),
        ("rtb-0207beae6b93bd50d", "rtb-0207beae6b93bd50d|172.24.29.0/24", "vgw-0edf43fc6fce8a9c5"),
        ("rtb-0207beae6b93bd50d", "rtb-0207beae6b93bd50d|0.0.0.0/0", "nat-07a8fec9c93adce98"),
        ("rtb-0207beae6b93bd50d", "rtb-0207beae6b93bd50d|172.154.90.0/24", "vgw-0edf43fc6fce8a9c5"),
        ("rtb-0207beae6b93bd50d", "rtb-0207beae6b93bd50d|10.12.64.32/28", "pcx-0a789485435a19f67"),
        ("rtb-0207beae6b93bd50d", "rtb-0207beae6b93bd50d|172.183.21.203/32", "vgw-0edf43fc6fce8a9c5"),
        ("rtb-0207beae6b93bd50d", "rtb-0207beae6b93bd50d|10.12.64.0/28", "pcx-0a789485435a19f67"),
        ("rtb-0207beae6b93bd50d", "rtb-0207beae6b93bd50d|10.165.0.0/24", "pcx-0d00fdcb9cbcf430b"),
        ("rtb-0207beae6b93bd50d", "rtb-0207beae6b93bd50d|10.12.64.64/28", "pcx-0a789485435a19f67"),
        ("rtb-0d5006b1d9278e552", "rtb-0d5006b1d9278e552|0.0.0.0/0", "nat-0154d629d13405a3f"),
        ("rtb-0d5006b1d9278e552", "rtb-0d5006b1d9278e552|10.0.0.0/16", "pcx-0eaf218d38475cc58"),
        ("rtb-0c0188db3fa50c49f", "rtb-0c0188db3fa50c49f|10.0.0.0/16", "pcx-0eaf218d38475cc58"),
        ("rtb-0c0188db3fa50c49f", "rtb-0c0188db3fa50c49f|0.0.0.0/0", "nat-026fa5c134732f383"),
        ("rtb-098b040d4e81f0f7a", "rtb-098b040d4e81f0f7a|172.154.90.0/24", "vgw-0edf43fc6fce8a9c5"),
        ("rtb-098b040d4e81f0f7a", "rtb-098b040d4e81f0f7a|0.0.0.0/0", "nat-0154d629d13405a3f"),
        ("rtb-098b040d4e81f0f7a", "rtb-098b040d4e81f0f7a|10.111.4.0/24", "pcx-0324c63d04ee3c9ed"),
        ("rtb-098b040d4e81f0f7a", "rtb-098b040d4e81f0f7a|172.183.21.203/32", "vgw-0edf43fc6fce8a9c5"),
        ("rtb-098b040d4e81f0f7a", "rtb-098b040d4e81f0f7a|10.12.64.0/28", "pcx-0a789485435a19f67"),
        ("rtb-098b040d4e81f0f7a", "rtb-098b040d4e81f0f7a|10.12.64.64/28", "pcx-0a789485435a19f67"),
        ("rtb-098b040d4e81f0f7a", "rtb-098b040d4e81f0f7a|10.12.64.32/28", "pcx-0a789485435a19f67"),
        ("rtb-098b040d4e81f0f7a", "rtb-098b040d4e81f0f7a|10.165.0.0/24", "pcx-0d00fdcb9cbcf430b"),
        ("rtb-098b040d4e81f0f7a", "rtb-098b040d4e81f0f7a|172.24.29.0/24", "vgw-0edf43fc6fce8a9c5"),
        ("rtb-0117d21e47a6a7c3b", "rtb-0117d21e47a6a7c3b|10.0.0.0/16", "pcx-0eaf218d38475cc58"),
        ("rtb-0117d21e47a6a7c3b", "rtb-0117d21e47a6a7c3b|0.0.0.0/0", "nat-0154d629d13405a3f"),
        ("rtb-0117d21e47a6a7c3b", "rtb-0117d21e47a6a7c3b|10.111.4.0/24", "pcx-0324c63d04ee3c9ed"),
        ("rtb-01248d9044975822b", "rtb-01248d9044975822b|10.12.64.0/28", "pcx-0a789485435a19f67"),
        ("rtb-01248d9044975822b", "rtb-01248d9044975822b|10.12.64.64/28", "pcx-0a789485435a19f67"),
        ("rtb-01248d9044975822b", "rtb-01248d9044975822b|10.111.4.0/24", "pcx-0324c63d04ee3c9ed"),
        ("rtb-01248d9044975822b", "rtb-01248d9044975822b|10.165.0.0/24", "pcx-0d00fdcb9cbcf430b"),
        ("rtb-01248d9044975822b", "rtb-01248d9044975822b|0.0.0.0/0", "nat-026fa5c134732f383"),
        ("rtb-01248d9044975822b", "rtb-01248d9044975822b|10.12.64.32/28", "pcx-0a789485435a19f67"),
        ("rtb-01248d9044975822b", "rtb-01248d9044975822b|172.24.29.0/24", "vgw-0edf43fc6fce8a9c5"),
        ("rtb-01248d9044975822b", "rtb-01248d9044975822b|172.154.90.0/24", "vgw-0edf43fc6fce8a9c5"),
        ("rtb-01248d9044975822b", "rtb-01248d9044975822b|172.183.21.203/32", "vgw-0edf43fc6fce8a9c5"),
        ("rtb-0dce814dd3fdb321f", "rtb-0dce814dd3fdb321f|10.111.4.0/24", "pcx-0324c63d04ee3c9ed"),
        ("rtb-0dce814dd3fdb321f", "rtb-0dce814dd3fdb321f|0.0.0.0/0", "nat-026fa5c134732f383"),
        ("rtb-0dce814dd3fdb321f", "rtb-0dce814dd3fdb321f|10.0.0.0/16", "pcx-0eaf218d38475cc58"),
        ("rtb-d1b7ceb3", "rtb-d1b7ceb3|0.0.0.0/0", "igw-99e55322"),
        ("rtb-04bc62120121cfbef", "rtb-04bc62120121cfbef|10.110.26.0/22", "pcx-0a789485435a19f67"),
        ("rtb-04bc62120121cfbef", "rtb-04bc62120121cfbef|0.0.0.0/0", "nat-0cd63b8fc50ad665c"),
        ("rtb-04bc62120121cfbef", "rtb-04bc62120121cfbef|10.110.22.0/22", "pcx-0a789485435a19f67"),
        ("rtb-04bc62120121cfbef", "rtb-04bc62120121cfbef|10.110.30.0/22", "pcx-0a789485435a19f67"),
        ("rtb-04bc62120121cfbef", "rtb-04bc62120121cfbef|172.24.29.0/24", "vgw-0afe079e97f2c77f8"),
        ("rtb-04bc62120121cfbef", "rtb-04bc62120121cfbef|172.154.90.0/24", "vgw-0afe079e97f2c77f8"),
        ("rtb-04bc62120121cfbef", "rtb-04bc62120121cfbef|172.183.21.203/32", "vgw-0afe079e97f2c77f8"),
        ("rtb-0fa0eb0f6130f6a2e", "rtb-0fa0eb0f6130f6a2e|10.110.22.0/22", "pcx-0a789485435a19f67"),
        ("rtb-0fa0eb0f6130f6a2e", "rtb-0fa0eb0f6130f6a2e|10.110.30.0/22", "pcx-0a789485435a19f67"),
        ("rtb-0fa0eb0f6130f6a2e", "rtb-0fa0eb0f6130f6a2e|10.110.26.0/22", "pcx-0a789485435a19f67"),
        ("rtb-0fa0eb0f6130f6a2e", "rtb-0fa0eb0f6130f6a2e|172.24.29.0/24", "vgw-0afe079e97f2c77f8"),
        ("rtb-0fa0eb0f6130f6a2e", "rtb-0fa0eb0f6130f6a2e|0.0.0.0/0", "nat-0cd63b8fc50ad665c"),
        ("rtb-0fa0eb0f6130f6a2e", "rtb-0fa0eb0f6130f6a2e|172.154.90.0/AQ24", "vgw-0afe079e97f2c77f8"),
        ("rtb-0fa0eb0f6130f6a2e", "rtb-0fa0eb0f6130f6a2e|172.183.21.203/32", "vgw-0afe079e97f2c77f8"),
        ("rtb-01fbd15d4b6e8e14f", "rtb-01fbd15d4b6e8e14f|0.0.0.0/0", "igw-007fe6f07b9419e44"),
        ("rtb-0d49710751f04455d", "rtb-0d49710751f04455d|0.0.0.0/0", "igw-007fe6f07b9419e44"),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (rtb:EC2RouteTable)-[re:ROUTE]-(r:EC2Route)-[a:ASSOCIATED]-(gw)
        RETURN rtb.id,r.id, gw.id;
        """,
    )
    actual = {
        (r['rtb.id'], r['r.id'], r['gw.id']) for r in result
    }

    assert actual == expected_nodes
