DESCRIBE_RESOURCE_GROUPS = [
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG",
        "type": "Microsoft.Resources/resourceGroups",
        "location": "West US",
        "name": "TestRG",
        "managedBy": "assu-ttef-vdff",

    },
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG1",
        "type": "Microsoft.Resources/resourceGroups",
        "location": "West US",
        "resource_group": "TestRG",
        "name": "TestRG1",
        "managedBy": "assu-ttef-vdff",
    },
]

DESCRIBE_TAGS = [
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Resources/tags/tag1",
        "type": "Microsoft.Resources/tags",
        "resource_group": "TestRG",
        "name": "tag1",
        "value": "ssdw",
        "resource_id": "/subscriptions/00-00-00-00/resourceGroups/TestRG",
    },
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG1/providers/Microsoft.Resources/tags/tag2",
        "type": "Microsoft.Resources/tags",
        "resource_group": "TestRG1",
        "name": "tag2",
        "value": "sdewa",
        "resource_id": "/subscriptions/00-00-00-00/resourceGroups/TestRG1",
    },
]
