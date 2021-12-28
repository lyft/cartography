DESCRIBE_NETWORKS = [
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            virtualNetworks/TestNetwork1",
        "type": "Microsoft.Network/virtualNetworks",
        "location": "West US",
        "resource_group": "TestRG",
        "name": "TestNetwork1",
        "resource_guid": "assu-ttef-vdff",
        "provisioning_state": "Running",
        "enable_ddos_protection": True,
        "etag": "sewd-erd",
    },
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            virtualNetworks/TestNetwork2",
        "type": "Microsoft.Network/virtualNetworks",
        "location": "West US",
        "resource_group": "TestRG",
        "name": "TestNetwork2",
        "resource_guid": "assu-ttef-vdff",
        "provisioning_state": "Running",
        "enable_ddos_protection": True,
        "etag": "sewd-erd",
    },
]

DESCRIBE_NETWORKSUBNETS = [
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            virtualNetworks/TestNetwork1/subnets/subnet1",
        "type":
        "Microsoft.Network/virtualNetworks/subnets",
        "resource_group":
        "TestRG",
        "name":
        "subnet1",
        "private_endpoint_network_policies":
        "ads-dgs.net",
        "private_link_service_network_policies":
        ".net",
        "etag":
        "hhd-fftt-fsc",
        "network_id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            virtualNetworks/TestNetwork1",
    },
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            virtualNetworks/TestNetwork2/subnets/subnet2",
        "type":
        "Microsoft.Network/virtualNetworks/subnets",
        "resource_group":
        "TestRG",
        "name":
        "subnet2",
        "private_endpoint_network_policies":
        "ads-dgs.net",
        "private_link_service_network_policies":
        ".net",
        "etag":
        "hhd-fftt-fsc",
        "network_id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            virtualNetworks/TestNetwork2",
    },
]

DESCRIBE_ROUTETABLE = [
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            routeTables/TestRoutetable1",
        "type": "Microsoft.Network/routeTables",
        "location": "West US",
        "resource_group": "TestRG",
        "name": "TestRoutetable1",
        "etag": "sewd-erd",
    },
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            routeTables/TestRoutetable2",
        "type": "Microsoft.Network/routeTables",
        "location": "West US",
        "resource_group": "TestRG",
        "name": "TestRoutetable2",
        "etag": "sewd-erd",
    },
]

DESCRIBE_NETWORKROUTE = [
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            routeTables/TestRoutetable1/routes1",
        "type":
        "Microsoft.Network/routeTables/routes",
        "name":
        "route1",
        "etag":
        "hhd-fftt-fsc",
        "routetable_id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            routeTables/TestRoutetable1",
    },
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            routeTables/TestRoutetable2/routes2",
        "type":
        "Microsoft.Network/routeTables/routes",
        "name":
        "route2",
        "etag":
        "hhd-fftt-fsc",
        "routetable_id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            routeTables/TestRoutetable2",
    },
]

DESCRIBE_NETWORKSECURITYGROUPS = [
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            networkSecurityGroups/Testgroup1",
        "type": "Microsoft.Network/networkSecurityGroups",
        "location": "West US",
        "resource_group": "TestRG",
        "name": "Testgroup1",
        "etag": "sewd-erd",
    },
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            networkSecurityGroups/Testgroup2",
        "type": "Microsoft.Network/networkSecurityGroups",
        "location": "West US",
        "resource_group": "TestRG",
        "name": "Testgroup2",
        "etag": "sewd-erd",
    },
]

DESCRIBE_NETWORKSECURITYRULES = [
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            networkSecurityGroups/Testgroup1/securityRules/rule1",
        "type":
        "Microsoft.Network/networkSecurityGroups/securityRules",
        "name":
        "rule1",
        "etag":
        "hhd-fftt-fsc",
        "security_group_id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            networkSecurityGroups/Testgroup1",
    },
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            networkSecurityGroups/Testgroup2/securityRules/rule2",
        "type":
        "Microsoft.Network/networkSecurityGroups/securityRules",
        "name":
        "rule2",
        "etag":
        "hhd-fftt-fsc",
        "security_group_id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            networkSecurityGroups/Testgroup2",
    },
]

DESCRIBE_PUBLICIPADDRESSES = [
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            publicIPAddresses/ip1",
        "type": "Microsoft.Network/publicIPAddresses",
        "location": "West US",
        "name": "ip1",
        "etag": "sewd-erd",
    },
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            publicIPAddresses/ip2",
        "type": "Microsoft.Network/publicIPAddresses",
        "location": "West US",
        "resource_group": "TestRG",
        "name": "ip2",
        "etag": "sewd-erd",
    },
]

DESCRIBE_NETWORKUSAGES = [
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            virtualNetworks/TestNetwork1/subnets/subnet1",
        "unit": "unit",
        "currentValue": 1234,
        "limit": 9999,
        "network_id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            virtualNetworks/TestNetwork1",
    },
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            virtualNetworks/TestNetwork2/subnets/subnet2",
        "unit": "unit",
        "currentValue": 1234,
        "limit": 9999,
        "network_id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            virtualNetworks/TestNetwork2",
    },
]
