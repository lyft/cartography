DESCRIBE_NETWORK_INTERFACES = [
{
    "Attachment": {
        "AttachTime": "2020-10-09 06:51:30+00:00",
        "AttachmentId": "eni-attach-03b64671f048b2e07",
        "DeleteOnTermination": True,
        "DeviceIndex": 0,
        "InstanceId": "i-0d7654b940dcf5766",
        "InstanceOwnerId": "000000000000",
        "Status": "attached"
    },
    "AvailabilityZone": "eu-north-1a",
    "Description": "",
    "Groups": [
        {
            "GroupId": "sg-0e866e64db0c84705",
            "GroupName": "new-life"
        }
    ],
    "InterfaceType": "interface",
    "Ipv6Addresses": [],
    "MacAddress": "06:3a:21:f4:bf:62",
    "NetworkInterfaceId": "eni-0e106a07c15ff7d14",
    "OwnerId": "000000000000",
    "PrivateDnsName": "ip-10-0-4-180.eu-north-1.compute.internal",
    "PrivateIpAddress": "10.0.4.180",
    "PrivateIpAddresses": [
        {
            "Primary": True,
            "PrivateDnsName": "ip-10-0-4-180.eu-north-1.compute.internal",
            "PrivateIpAddress": "10.0.4.180"
        }
    ],
    "RequesterManaged": False,
    "SourceDestCheck": True,
    "Status": "in-use",
    "SubnetId": "subnet-0fa10e76eeb24dbe7",
    "TagSet": [],
    "VpcId": "vpc-009e59023d444cfb4"
},
{
    "Association": {
        "IpOwnerId": "amazon-elb",
        "PublicDnsName": "ec2-13-48-164-202.eu-north-1.compute.amazonaws.com",
        "PublicIp": "13.48.164.202"
    },
    "Attachment": {
        "AttachTime": "2020-10-09 06:47:06+00:00",
        "AttachmentId": "eni-attach-0ddd4cc8a04315498",
        "DeleteOnTermination": False,
        "DeviceIndex": 1,
        "InstanceOwnerId": "amazon-elb",
        "Status": "attached"
    },
    "AvailabilityZone": "eu-north-1a",
    "Description": "ELB new-life-001",
    "Groups": [
        {
            "GroupId": "sg-0e866e64db0c84705",
            "GroupName": "new-life"
        }
    ],
    "InterfaceType": "interface",
    "Ipv6Addresses": [],
    "MacAddress": "06:91:21:1e:7e:3a",
    "NetworkInterfaceId": "eni-0d9877f559c240362",
    "OwnerId": "000000000000",
    "PrivateDnsName": "ip-10-0-4-96.eu-north-1.compute.internal",
    "PrivateIpAddress": "10.0.4.96",
    "PrivateIpAddresses": [
        {
            "Association": {
                "IpOwnerId": "amazon-elb",
                "PublicDnsName": "ec2-13-48-164-202.eu-north-1.compute.amazonaws.com",
                "PublicIp": "13.48.164.202"
            },
            "Primary": True,
            "PrivateDnsName": "ip-10-0-4-96.eu-north-1.compute.internal",
            "PrivateIpAddress": "10.0.4.96"
        }
    ],
    "RequesterId": "amazon-elb",
    "RequesterManaged": True,
    "SourceDestCheck": True,
    "Status": "in-use",
    "SubnetId": "subnet-0fa10e76eeb24dbe7",
    "TagSet": [],
    "VpcId": "vpc-009e59023d444cfb4"
},
{
    "Attachment": {
        "AttachTime": "2020-10-09 06:46:17+00:00",
        "AttachmentId": "eni-attach-0448443528bf22544",
        "DeleteOnTermination": True,
        "DeviceIndex": 0,
        "InstanceId": "i-0892c8f9514ecffb7",
        "InstanceOwnerId": "000000000000",
        "Status": "attached"
    },
    "AvailabilityZone": "eu-north-1a",
    "Description": "",
    "Groups": [
        {
            "GroupId": "sg-0e866e64db0c84705",
            "GroupName": "new-life"
        }
    ],
    "InterfaceType": "interface",
    "Ipv6Addresses": [],
    "MacAddress": "06:25:81:d1:86:e4",
    "NetworkInterfaceId": "eni-04b4289e1be7634e4",
    "OwnerId": "000000000000",
    "PrivateDnsName": "ip-10-0-4-5.eu-north-1.compute.internal",
    "PrivateIpAddress": "10.0.4.5",
    "PrivateIpAddresses": [
        {
            "Primary": True,
            "PrivateDnsName": "ip-10-0-4-5.eu-north-1.compute.internal",
            "PrivateIpAddress": "10.0.4.5"
        },
        {
            "Primary": False,
            "PrivateDnsName": "ip-10-0-4-12.eu-north-1.compute.internal",
            "PrivateIpAddress": "10.0.4.12"
        }
    ],
    "RequesterManaged": False,
    "SourceDestCheck": True,
    "Status": "in-use",
    "SubnetId": "subnet-0fa10e76eeb24dbe7",
    "TagSet": [],
    "VpcId": "vpc-009e59023d444cfb4"
}
]
