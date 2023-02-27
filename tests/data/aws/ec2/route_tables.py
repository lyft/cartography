DESCRIBE_ROUTE_TABLES = [
    {
        'Associations': [
            {
                'Main': False,
                'RouteTableAssociationId': 'route_table_assoc-1',
                'SubnetId': 'subnet-0fa9c8fa7cb241479',
                'GatewayId': 'string',
            },
            {
                'Main': False,
                'RouteTableAssociationId': 'route_table_assoc-2',
                'SubnetId': 'subnet-020b2f3928f190ce8',
                'GatewayId': 'string',
            }
        ],
        'RouteTableId': 'route_table-1',
        'Routes': [
            {
                'DestinationCidrBlock': '0.0.0.0/0',
                'DestinationIpv6CidrBlock': 'ff::ff/32',
                'GatewayId': 'igw-a90d73f',
                'State': 'active',
            },
            {
                'DestinationCidrBlock': '11.10.10.10/8',
                'DestinationIpv6CidrBlock': '::/0',
                'GatewayId': 'egw-a90d73f',
                'State': 'active',
            },
        ],
        'VpcId': 'vpc-05326141848d1c681',
        'OwnerId': 'string'
    },
    {
        'Associations': [
            {
                'Main': True,
                'RouteTableAssociationId': 'route_table_assoc-3',
                'SubnetId': 'subnet-0773409557644dca4',
                'GatewayId': 'string',
            },
        ],
        'RouteTableId': 'route_table-2',
        'Routes': [
            {
                'DestinationCidrBlock': '0.0.0.0/0',
                'DestinationIpv6CidrBlock': 'ff::ff/32',
                'GatewayId': 'egw-a90d73f',
                'State': 'active',
            },
            {
                'DestinationCidrBlock': '11.10.10.10/8',
                'DestinationIpv6CidrBlock': '::/0',
                'GatewayId': 'igw-a90d73f',
                'State': 'active',
            },
        ],
        'VpcId': 'vpc-025873e026b9e8ee6',
        'OwnerId': 'string'
    },
]
