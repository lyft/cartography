DESCRIBE_VPC_PEERINGS = [
    {
        "AccepterVpcInfo": {
            "CidrBlock": "10.0.0.0/16",
            "CidrBlockSet": [
                {
                    "CidrBlock": "10.0.0.0/16",
                },
            ],
            "OwnerId": "000000000000",
            "PeeringOptions": {
                "AllowDnsResolutionFromRemoteVpc": True,
                "AllowEgressFromLocalClassicLinkToRemoteVpc": False,
                "AllowEgressFromLocalVpcToRemoteClassicLink": False,
            },
            "Region": "eu-north-1",
            "VpcId": "vpc-0015dc961e537676a",
        },
        "RequesterVpcInfo": {
            "CidrBlock": "10.1.0.0/16",
            "CidrBlockSet": [
                {
                    "CidrBlock": "10.1.0.0/16",
                },
            ],
            "OwnerId": "000000000000",
            "PeeringOptions": {
                "AllowDnsResolutionFromRemoteVpc": False,
                "AllowEgressFromLocalClassicLinkToRemoteVpc": False,
                "AllowEgressFromLocalVpcToRemoteClassicLink": False,
            },
            "Region": "eu-north-1",
            "VpcId": "vpc-055d355d6d2e498fa",
        },
        "Status": {
            "Code": "active",
            "Message": "Active",
        },
        "Tags": [
            {
                "Key": "Name",
                "Value": "VPC Peering between life and possibilities",
            },
        ],
        "VpcPeeringConnectionId": "pcx-09969456d9ec69ab6",
    },
]
