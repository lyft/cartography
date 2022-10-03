DESCRIBE_VMS = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM",
        "type": "Microsoft.Compute/virtualMachines",
        "location": "West US",
        "resource_group": "TestRG",
        "name": "TestVM",
        "plan": {
            "product": "Standard",
        },
        "handware_profile": {
            "vm_size": "Standard_D2s_v3",
        },
        "license_type": "Windows_Client ",
        "os_profile": {
            "computer_name": "TestVM",
        },
        "identity": {
            "type": "SystemAssigned",
        },
        "zones": [
            "West US 2",
        ],
        "additional_capabilities": {
            "ultra_ssd_enabled": True,
        },
        "priority": "Low",
        "eviction_policy": "Deallocate",
    },
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM1",
        "type": "Microsoft.Compute/virtualMachines",
        "location": "West US",
        "resource_group": "TestRG",
        "name": "TestVM1",
        "plan": {
            "product": "Standard",
        },
        "handware_profile": {
            "vm_size": "Standard_D2s_v3",
        },
        "license_type": "Windows_Client ",
        "os_profile": {
            "computer_name": "TestVM1",
        },
        "identity": {
            "type": "SystemAssigned",
        },
        "zones": [
            "West US 2",
        ],
        "additional_capabilities": {
            "ultra_ssd_enabled": True,
        },
        "priority": "Low",
        "eviction_policy": "Deallocate",
    },
]


DESCRIBE_VM_DATA_DISKS = [
    {
        "lun": 0,
        "name": "dd0",
        "create_option": "Empty",
        "caching": "ReadWrite",
        "managed_disk": {
            "storage_account_type": "Premium_LRS",
            "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/disks/dd0",
        },
        "disk_size_gb": 30,
    },
    {
        "lun": 0,
        "name": "dd1",
        "create_option": "Empty",
        "caching": "ReadWrite",
        "managed_disk": {
            "storage_account_type": "Premium_LRS",
            "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/disks/dd1",
        },
        "disk_size_gb": 30,
    },
]

DESCRIBE_DISKS = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/disks/dd0",
        "type": "Microsoft.Compute/disks",
        "location": "West US",
        "resource_group": "TestRG",
        "name": "dd0",
        "creation_data": {
            "create_option": "Attach",
        },
        "disk_size_gb": 100,
        "encryption_settings_collection": {
            "enabled": True,
        },
        "max_shares": 10,
        "network_access_policy": "AllowAll",
        "os_type": "Windows",
        "tier": "P4",
        "sku": {
            "name": "Standard_LRS",
        },
        "zones": [
            "West US 2",
        ],
    },
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/disks/dd1",
        "type": "Microsoft.Compute/disks",
        "location": "West US",
        "resource_group": "TestRG",
        "name": "dd1",
        "creation_data": {
            "create_option": "Attach",
        },
        "disk_size_gb": 100,
        "encryption_settings_collection": {
            "enabled": True,
        },
        "max_shares": 10,
        "network_access_policy": "AllowAll",
        "os_type": "Windows",
        "tier": "P4",
        "sku": {
            "name": "Standard_LRS",
        },
        "zones": [
            "West US 2",
        ],
    },
]

DESCRIBE_SNAPSHOTS = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/snapshots/ss0",
        "type": "Microsoft.Compute/snapshots",
        "location": "West US",
        "resource_group": "TestRG",
        "name": "ss0",
        "creation_data": {
            "create_option": "Attach",
        },
        "disk_size_gb": 100,
        "encryption_settings_collection": {
            "enabled": True,
        },
        "incremental": True,
        "network_access_policy": "AllowAll",
        "os_type": "Windows",
        "tier": "P4",
        "sku": {
            "name": "Standard_LRS",
        },
    },
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/snapshots/ss1",
        "type": "Microsoft.Compute/snapshots",
        "location": "West US",
        "resource_group": "TestRG",
        "name": "ss1",
        "creation_data": {
            "create_option": "Attach",
        },
        "disk_size_gb": 100,
        "encryption_settings_collection": {
            "enabled": True,
        },
        "incremental": True,
        "network_access_policy": "AllowAll",
        "os_type": "Windows",
        "tier": "P4",
        "sku": {
            "name": "Standard_LRS",
        },
    },
]

DESCRIBE_VMEXTENSIONS = [
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/\
            virtualMachines/TestVM/extensions/extensions1",
        "type":
        "Microsoft.Compute/virtualMachines/extensions",
        "resource_group":
        "TestRG",
        "name":
        "extensions1",
        "location": "West US",
        "vm_id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM",
    },
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/\
            virtualMachines/TestVM1/extensions/extensions2",
        "type":
        "Microsoft.Compute/virtualMachines/extensions",
        "resource_group":
        "TestRG",
        "name":
        "extensions2",
        "location": "West US",
        "vm_id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM1",
    },
]

DESCRIBE_VMAVAILABLESIZES = [
    {
        "numberOfCores":
        2,
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM",
        "type":
        "Microsoft.Compute/virtualMachines/availablesizes",
        "osDiskSizeInMB":
        1234,
        "name":
        "size1",
        "resourceDiskSizeInMB":
        2312,
        "memoryInMB":
        4352,
        "maxDataDiskCount":
        3214,
        "vm_id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM",
    },
    {
        "numberOfCores":
        2,
        "type":
        "Microsoft.Compute/virtualMachines/availablesizes",
        "osDiskSizeInMB":
        1234,
        "name":
        "size2",
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM1",

        "resourceDiskSizeInMB":
        2312,
        "memoryInMB":
        4352,
        "maxDataDiskCount":
        3214,
        "vm_id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM1",
    },
]

DESCRIBE_VMSCALESETS = [
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/\
            virtualMachineScaleSets/set1",
        "type":
        "Microsoft.Compute/virtualMachineScaleSets",
        "resource_group":
        "TestRG",
        "name":
        "set1",
        "location": "West US",
    },
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/\
            virtualMachineScaleSets/set2",
        "type":
        "Microsoft.Compute/virtualMachineScaleSets",
        "resource_group":
        "TestRG",
        "name":
        "set2",
        "location": "West US",
    },
]

DESCRIBE_VMSCALESETEXTENSIONS = [
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/\
            virtualMachineScaleSets/set1/extensions/extension1",
        "type":
        "Microsoft.Compute/virtualMachineScaleSets/extensions",
        "resource_group":
        "TestRG",
        "name":
        "extension1",
        "set_id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/\
            virtualMachineScaleSets/set1",
    },
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/\
            virtualMachineScaleSets/set2/extensions/extension2",
        "type":
        "Microsoft.Compute/virtualMachineScaleSets/extensions",
        "resource_group":
        "TestRG",
        "name":
        "extension2",
        "set_id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/\
            virtualMachineScaleSets/set2",
    },
]
