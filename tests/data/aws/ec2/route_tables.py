DESCRIBE_ROUTE_TABLES = {

    'RouteTables': [
        {
            'Associations': [{
                'Main': False,
                'RouteTableAssociationId': 'rtbassoc-0841fc30c269a6f57',
                'RouteTableId': 'rtb-01fbd15d4b6e8e14f',
                'SubnetId': 'subnet-0c7b7f891a4bab804',
                'AssociationState': {
                    'State': 'associated',
                },
            }],
            'PropagatingVgws': [],
            'RouteTableId': 'rtb-01fbd15d4b6e8e14f',
            'Routes': [
                {
                    'DestinationCidrBlock': '10.48.12.0/24',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.52.1.0/24',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.110.22.0/20',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '0.0.0.0/0',
                    'GatewayId': 'igw-007fe6f07b9419e44',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                }, {
                    'DestinationPrefixListId': 'pl-6e4ea72d',
                    'GatewayId': 'vpce-0d2c1a3077aaa76bd',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                },
            ],
            'Tags': [],
            'VpcId': 'vpc-053cbd10cac618f56',
            'OwnerId': '000000000000',
        }, {
            'Associations': [{
                'Main': False,
                'RouteTableAssociationId': 'rtbassoc-06f485c91fff16ef4',
                'RouteTableId': 'rtb-0d49710751f04455d',
                'SubnetId': 'subnet-061a59c1e8a0ce808',
                'AssociationState': {
                    'State': 'associated',
                },
            }],
            'PropagatingVgws': [],
            'RouteTableId': 'rtb-0d49710751f04455d',
            'Routes': [
                {
                    'DestinationCidrBlock': '10.48.12.0/24',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.52.1.0/24',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.110.22.0/20',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '0.0.0.0/0',
                    'GatewayId': 'igw-007fe6f07b9419e44',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                }, {
                    'DestinationPrefixListId': 'pl-6e4ea72d',
                    'GatewayId': 'vpce-0d2c1a3077aaa76bd',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                },
            ],
            'Tags': [],
            'VpcId': 'vpc-053cbd10cac618f56',
            'OwnerId': '000000000000',
        }, {
            'Associations': [{
                'Main': False,
                'RouteTableAssociationId': 'rtbassoc-0fd39893ad30fe965',
                'RouteTableId': 'rtb-0598ecac672acbf05',
                'SubnetId': 'subnet-0c43238df6ad49d47',
                'AssociationState': {
                    'State': 'associated',
                },
            }],
            'PropagatingVgws': [],
            'RouteTableId': 'rtb-0598ecac672acbf05',
            'Routes': [
                {
                    'DestinationCidrBlock': '10.48.12.0/24',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.52.1.0/24',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.110.22.0/20',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '0.0.0.0/0',
                    'GatewayId': 'igw-007fe6f07b9419e44',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                }, {
                    'DestinationPrefixListId': 'pl-6e4ea72d',
                    'GatewayId': 'vpce-0d2c1a3077aaa76bd',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                },
            ],
            'Tags': [],
            'VpcId': 'vpc-053cbd10cac618f56',
            'OwnerId': '000000000000',
        }, {
            'Associations': [{
                'Main': False,
                'RouteTableAssociationId': 'rtbassoc-05c2805cf54c91f28',
                'RouteTableId': 'rtb-08f8aaf2ada59d690',
                'SubnetId': 'subnet-0c90bc569203c5262',
                'AssociationState': {
                    'State': 'associated',
                },
            }],
            'PropagatingVgws': [],
            'RouteTableId': 'rtb-08f8aaf2ada59d690',
            'Routes': [
                {
                    'DestinationCidrBlock': '10.48.12.0/24',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.52.1.0/24',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.111.4.0/24',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0324c63d04ee3c9ed',
                }, {
                    'DestinationCidrBlock': '10.110.22.0/20',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.0.0.0/16',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0eaf218d38475cc58',
                }, {
                    'DestinationCidrBlock': '0.0.0.0/0',
                    'NatGatewayId': 'nat-07a8fec9c93adce98',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                }, {
                    'DestinationPrefixListId': 'pl-6e4ea72d',
                    'GatewayId': 'vpce-0d2c1a3077aaa76bd',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                },
            ],
            'Tags': [],
            'VpcId': 'vpc-053cbd10cac618f56',
            'OwnerId': '000000000000',
        }, {
            'Associations': [{
                'Main': False,
                'RouteTableAssociationId': 'rtbassoc-0dc5f343861927899',
                'RouteTableId': 'rtb-07a78a66193459750',
                'SubnetId': 'subnet-088d675bb0b364938',
                'AssociationState': {
                    'State': 'associated',
                },
            }],
            'PropagatingVgws': [],
            'RouteTableId': 'rtb-07a78a66193459750',
            'Routes': [
                {
                    'DestinationCidrBlock': '10.74.14.0/24',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '0.0.0.0/0',
                    'GatewayId': 'igw-0cc1d5db8cb8ff02e',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                },
            ],
            'Tags': [],
            'VpcId': 'vpc-0b759af612e451fa8',
            'OwnerId': '000000000000',
        }, {
            'Associations': [{
                'Main': False,
                'RouteTableAssociationId': 'rtbassoc-02d4565241c0ad970',
                'RouteTableId': 'rtb-09283c3c06ce8e5e7',
                'SubnetId': 'subnet-093db86655a0c34e0',
                'AssociationState': {
                    'State': 'associated',
                },
            }],
            'PropagatingVgws': [],
            'RouteTableId': 'rtb-09283c3c06ce8e5e7',
            'Routes': [
                {
                    'DestinationCidrBlock': '172.183.21.203/32',
                    'GatewayId': 'vgw-0afe079e97f2c77f8',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '172.154.90.0/24',
                    'GatewayId': 'vgw-0afe079e97f2c77f8',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '172.24.29.0/24',
                    'GatewayId': 'vgw-0afe079e97f2c77f8',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.74.14.0/24',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.110.22.0/22',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0a789485435a19f67',
                }, {
                    'DestinationCidrBlock': '10.110.26.0/22',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0a789485435a19f67',
                }, {
                    'DestinationCidrBlock': '10.110.30.0/22',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0a789485435a19f67',
                }, {
                    'DestinationCidrBlock': '0.0.0.0/0',
                    'NatGatewayId': 'nat-0cd63b8fc50ad665c',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                },
            ],
            'Tags': [],
            'VpcId': 'vpc-0b759af612e451fa8',
            'OwnerId': '000000000000',
        }, {
            'Associations': [{
                'Main': False,
                'RouteTableAssociationId': 'rtbassoc-017cc79a2860caaf3',
                'RouteTableId': 'rtb-0207beae6b93bd50d',
                'SubnetId': 'subnet-0d5fae10e854b5605',
                'AssociationState': {
                    'State': 'associated',
                },
            }],
            'PropagatingVgws': [],
            'RouteTableId': 'rtb-0207beae6b93bd50d',
            'Routes': [
                {
                    'DestinationCidrBlock': '172.183.21.203/32',
                    'GatewayId': 'vgw-0edf43fc6fce8a9c5',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.12.64.0/28',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0a789485435a19f67',
                }, {
                    'DestinationCidrBlock': '10.12.64.32/28',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0a789485435a19f67',
                }, {
                    'DestinationCidrBlock': '10.12.64.64/28',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0a789485435a19f67',
                }, {
                    'DestinationCidrBlock': '172.154.90.0/24',
                    'GatewayId': 'vgw-0edf43fc6fce8a9c5',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '172.24.29.0/24',
                    'GatewayId': 'vgw-0edf43fc6fce8a9c5',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.48.12.0/24',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.52.1.0/24',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.111.4.0/24',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0324c63d04ee3c9ed',
                }, {
                    'DestinationCidrBlock': '10.165.0.0/24',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0d00fdcb9cbcf430b',
                }, {
                    'DestinationCidrBlock': '10.110.22.0/20',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '0.0.0.0/0',
                    'NatGatewayId': 'nat-07a8fec9c93adce98',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                },
            ],
            'Tags': [],
            'VpcId': 'vpc-053cbd10cac618f56',
            'OwnerId': '000000000000',
        }, {
            'Associations': [{
                'Main': False,
                'RouteTableAssociationId': 'rtbassoc-083579dd8c00207c9',
                'RouteTableId': 'rtb-0d5006b1d9278e552',
                'SubnetId': 'subnet-0ec4e216c304a4c33',
                'AssociationState': {
                    'State': 'associated',
                },
            }],
            'PropagatingVgws': [],
            'RouteTableId': 'rtb-0d5006b1d9278e552',
            'Routes': [
                {
                    'DestinationCidrBlock': '10.48.12.0/24',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.52.1.0/24',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.110.22.0/20',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.0.0.0/16',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0eaf218d38475cc58',
                }, {
                    'DestinationCidrBlock': '0.0.0.0/0',
                    'NatGatewayId': 'nat-0154d629d13405a3f',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                }, {
                    'DestinationPrefixListId': 'pl-6e4ea72d',
                    'GatewayId': 'vpce-0f6f47426160c8cb1',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                },
            ],
            'Tags': [],
            'VpcId': 'vpc-053cbd10cac618f56',
            'OwnerId': '000000000000',
        }, {
            'Associations': [{
                'Main': False,
                'RouteTableAssociationId': 'rtbassoc-00868c5ea539aebbb',
                'RouteTableId': 'rtb-0c0188db3fa50c49f',
                'SubnetId': 'subnet-05e2c6eb0aad65b91',
                'AssociationState': {
                    'State': 'associated',
                },
            }],
            'PropagatingVgws': [],
            'RouteTableId': 'rtb-0c0188db3fa50c49f',
            'Routes': [
                {
                    'DestinationCidrBlock': '10.48.12.0/24',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.52.1.0/24',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.110.22.0/20',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.0.0.0/16',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0eaf218d38475cc58',
                }, {
                    'DestinationCidrBlock': '0.0.0.0/0',
                    'NatGatewayId': 'nat-026fa5c134732f383',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                }, {
                    'DestinationPrefixListId': 'pl-6e4ea72d',
                    'GatewayId': 'vpce-0f6f47426160c8cb1',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                },
            ],
            'Tags': [],
            'VpcId': 'vpc-053cbd10cac618f56',
            'OwnerId': '000000000000',
        }, {
            'Associations': [{
                'Main': True,
                'RouteTableAssociationId': 'rtbassoc-0bcddcb814d455ed4',
                'RouteTableId': 'rtb-0dc050eb977881a19',
                'AssociationState': {
                    'State': 'associated',
                },
            }],
            'PropagatingVgws': [],
            'RouteTableId': 'rtb-0dc050eb977881a19',
            'Routes': [
                {
                    'DestinationCidrBlock': '10.48.12.0/24',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.52.1.0/24',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.110.22.0/20',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                },
            ],
            'Tags': [],
            'VpcId': 'vpc-053cbd10cac618f56',
            'OwnerId': '000000000000',
        }, {
            'Associations': [{
                'Main': True,
                'RouteTableAssociationId': 'rtbassoc-05b01e3c7b8f50557',
                'RouteTableId': 'rtb-063d90f2ffa00ef6e',
                'AssociationState': {
                    'State': 'associated',
                },
            }],
            'PropagatingVgws': [],
            'RouteTableId': 'rtb-063d90f2ffa00ef6e',
            'Routes': [{
                'DestinationCidrBlock': '10.74.14.0/24',
                'GatewayId': 'local',
                'Origin': 'CreateRouteTable',
                'State': 'active',
            }],
            'Tags': [],
            'VpcId': 'vpc-0b759af612e451fa8',
            'OwnerId': '000000000000',
        }, {
            'Associations': [{
                'Main': False,
                'RouteTableAssociationId': 'rtbassoc-03e0527ddda87bd3b',
                'RouteTableId': 'rtb-098b040d4e81f0f7a',
                'SubnetId': 'subnet-024ad69f0f023ab2c',
                'AssociationState': {
                    'State': 'associated',
                },
            }],
            'PropagatingVgws': [],
            'RouteTableId': 'rtb-098b040d4e81f0f7a',
            'Routes': [
                {
                    'DestinationCidrBlock': '172.183.21.203/32',
                    'GatewayId': 'vgw-0edf43fc6fce8a9c5',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.12.64.0/28',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0a789485435a19f67',
                }, {
                    'DestinationCidrBlock': '10.12.64.32/28',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0a789485435a19f67',
                }, {
                    'DestinationCidrBlock': '10.12.64.64/28',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0a789485435a19f67',
                }, {
                    'DestinationCidrBlock': '172.154.90.0/24',
                    'GatewayId': 'vgw-0edf43fc6fce8a9c5',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '172.24.29.0/24',
                    'GatewayId': 'vgw-0edf43fc6fce8a9c5',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.48.12.0/24',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.52.1.0/24',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.111.4.0/24',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0324c63d04ee3c9ed',
                }, {
                    'DestinationCidrBlock': '10.165.0.0/24',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0d00fdcb9cbcf430b',
                }, {
                    'DestinationCidrBlock': '10.110.22.0/20',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '0.0.0.0/0',
                    'NatGatewayId': 'nat-0154d629d13405a3f',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                },
            ],
            'Tags': [],
            'VpcId': 'vpc-053cbd10cac618f56',
            'OwnerId': '000000000000',
        }, {
            'Associations': [{
                'Main': False,
                'RouteTableAssociationId': 'rtbassoc-087ab44313d08de0f',
                'RouteTableId': 'rtb-0117d21e47a6a7c3b',
                'SubnetId': 'subnet-014f6e6a1612f8b80',
                'AssociationState': {
                    'State': 'associated',
                },
            }],
            'PropagatingVgws': [],
            'RouteTableId': 'rtb-0117d21e47a6a7c3b',
            'Routes': [
                {
                    'DestinationCidrBlock': '10.48.12.0/24',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.52.1.0/24',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.111.4.0/24',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0324c63d04ee3c9ed',
                }, {
                    'DestinationCidrBlock': '10.110.22.0/20',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.0.0.0/16',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0eaf218d38475cc58',
                }, {
                    'DestinationCidrBlock': '0.0.0.0/0',
                    'NatGatewayId': 'nat-0154d629d13405a3f',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                }, {
                    'DestinationPrefixListId': 'pl-6e4ea72d',
                    'GatewayId': 'vpce-0d2c1a3077aaa76bd',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                },
            ],
            'Tags': [],
            'VpcId': 'vpc-053cbd10cac618f56',
            'OwnerId': '000000000000',
        }, {
            'Associations': [{
                'Main': False,
                'RouteTableAssociationId': 'rtbassoc-0eebc451be199e2ff',
                'RouteTableId': 'rtb-01248d9044975822b',
                'SubnetId': 'subnet-065a22958fc169a9f',
                'AssociationState': {
                    'State': 'associated',
                },
            }],
            'PropagatingVgws': [],
            'RouteTableId': 'rtb-01248d9044975822b',
            'Routes': [
                {
                    'DestinationCidrBlock': '172.183.21.203/32',
                    'GatewayId': 'vgw-0edf43fc6fce8a9c5',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.12.64.0/28',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0a789485435a19f67',
                }, {
                    'DestinationCidrBlock': '10.12.64.32/28',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0a789485435a19f67',
                }, {
                    'DestinationCidrBlock': '10.12.64.64/28',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0a789485435a19f67',
                }, {
                    'DestinationCidrBlock': '172.154.90.0/24',
                    'GatewayId': 'vgw-0edf43fc6fce8a9c5',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '172.24.29.0/24',
                    'GatewayId': 'vgw-0edf43fc6fce8a9c5',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.48.12.0/24',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.52.1.0/24',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.111.4.0/24',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0324c63d04ee3c9ed',
                }, {
                    'DestinationCidrBlock': '10.165.0.0/24',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0d00fdcb9cbcf430b',
                }, {
                    'DestinationCidrBlock': '10.110.22.0/20',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '0.0.0.0/0',
                    'NatGatewayId': 'nat-026fa5c134732f383',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                },
            ],
            'Tags': [],
            'VpcId': 'vpc-053cbd10cac618f56',
            'OwnerId': '000000000000',
        }, {
            'Associations': [{
                'Main': False,
                'RouteTableAssociationId': 'rtbassoc-0441787bc423a440f',
                'RouteTableId': 'rtb-0dce814dd3fdb321f',
                'SubnetId': 'subnet-063c3e2018bc27009',
                'AssociationState': {
                    'State': 'associated',
                },
            }],
            'PropagatingVgws': [],
            'RouteTableId': 'rtb-0dce814dd3fdb321f',
            'Routes': [
                {
                    'DestinationCidrBlock': '10.48.12.0/24',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.52.1.0/24',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.111.4.0/24',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0324c63d04ee3c9ed',
                }, {
                    'DestinationCidrBlock': '10.110.22.0/20',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.0.0.0/16',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0eaf218d38475cc58',
                }, {
                    'DestinationCidrBlock': '0.0.0.0/0',
                    'NatGatewayId': 'nat-026fa5c134732f383',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                }, {
                    'DestinationPrefixListId': 'pl-6e4ea72d',
                    'GatewayId': 'vpce-0d2c1a3077aaa76bd',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                },
            ],
            'Tags': [],
            'VpcId': 'vpc-053cbd10cac618f56',
            'OwnerId': '000000000000',
        }, {
            'Associations': [{
                'Main': True,
                'RouteTableAssociationId': 'rtbassoc-cd11ac78',
                'RouteTableId': 'rtb-d1b7ceb3',
                'AssociationState': {
                    'State': 'associated',
                },
            }],
            'PropagatingVgws': [],
            'RouteTableId': 'rtb-d1b7ceb3',
            'Routes': [
                {
                    'DestinationCidrBlock': '172.132.0.0/16',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '0.0.0.0/0',
                    'GatewayId': 'igw-99e55322',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                },
            ],
            'Tags': [],
            'VpcId': 'vpc-787aeebb',
            'OwnerId': '000000000000',
        }, {
            'Associations': [{
                'Main': False,
                'RouteTableAssociationId': 'rtbassoc-011ae63015ba811c5',
                'RouteTableId': 'rtb-04bc62120121cfbef',
                'SubnetId': 'subnet-0e873330aa6826631',
                'AssociationState': {
                    'State': 'associated',
                },
            }],
            'PropagatingVgws': [],
            'RouteTableId': 'rtb-04bc62120121cfbef',
            'Routes': [
                {
                    'DestinationCidrBlock': '172.183.21.203/32',
                    'GatewayId': 'vgw-0afe079e97f2c77f8',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '172.154.90.0/24',
                    'GatewayId': 'vgw-0afe079e97f2c77f8',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '172.24.29.0/24',
                    'GatewayId': 'vgw-0afe079e97f2c77f8',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.74.14.0/24',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.110.22.0/22',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0a789485435a19f67',
                }, {
                    'DestinationCidrBlock': '10.110.26.0/22',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0a789485435a19f67',
                }, {
                    'DestinationCidrBlock': '10.110.30.0/22',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0a789485435a19f67',
                }, {
                    'DestinationCidrBlock': '0.0.0.0/0',
                    'NatGatewayId': 'nat-0cd63b8fc50ad665c',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                },
            ],
            'Tags': [],
            'VpcId': 'vpc-0b759af612e451fa8',
            'OwnerId': '000000000000',
        }, {
            'Associations': [{
                'Main': False,
                'RouteTableAssociationId': 'rtbassoc-0ef799522e3488d38',
                'RouteTableId': 'rtb-0fa0eb0f6130f6a2e',
                'SubnetId': 'subnet-0d65a01441fc71c89',
                'AssociationState': {
                    'State': 'associated',
                },
            }],
            'PropagatingVgws': [],
            'RouteTableId': 'rtb-0fa0eb0f6130f6a2e',
            'Routes': [
                {
                    'DestinationCidrBlock': '172.183.21.203/32',
                    'GatewayId': 'vgw-0afe079e97f2c77f8',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '172.154.90.0/AQ24',
                    'GatewayId': 'vgw-0afe079e97f2c77f8',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '172.24.29.0/24',
                    'GatewayId': 'vgw-0afe079e97f2c77f8',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.74.14.0/24',
                    'GatewayId': 'local',
                    'Origin': 'CreateRouteTable',
                    'State': 'active',
                }, {
                    'DestinationCidrBlock': '10.110.22.0/22',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0a789485435a19f67',
                }, {
                    'DestinationCidrBlock': '10.110.26.0/22',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0a789485435a19f67',
                }, {
                    'DestinationCidrBlock': '10.110.30.0/22',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                    'VpcPeeringConnectionId': 'pcx-0a789485435a19f67',
                }, {
                    'DestinationCidrBlock': '0.0.0.0/0',
                    'NatGatewayId': 'nat-0cd63b8fc50ad665c',
                    'Origin': 'CreateRoute',
                    'State': 'active',
                },
            ],
            'Tags': [],
            'VpcId': 'vpc-0b759af612e451fa8',
            'OwnerId': '000000000000',
        },
    ],


}
