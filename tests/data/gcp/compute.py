# flake8: noqa
VPC_RESPONSE = {
    'id': 'projects/project-abc/global/networks',
    'items': [{
        'autoCreateSubnetworks': True,
        'creationTimestamp': '2018-05-10T17:33:18.968-07:00',
        'description': 'Default network for the project',
        'id': '123456',
        'kind': 'compute#network',
        'name': 'default',
        'routingConfig': {
            'routingMode': 'REGIONAL'
        },
        'selfLink': 'https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default',
        'subnetworks': [
            'https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/subnetworks/default',
            'https://www.googleapis.com/compute/v1/projects/project-abc/regions/asia-east2/subnetworks/default',
            'https://www.googleapis.com/compute/v1/projects/project-abc/regions/asia-east1/subnetworks/default',
            'https://www.googleapis.com/compute/v1/projects/project-abc/regions/us-east1/subnetworks/default',
            'https://www.googleapis.com/compute/v1/projects/project-abc/regions/northamerica-northeast1/subnetworks/default',
            'https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west1/subnetworks/default',
            'https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west3/subnetworks/default',
            'https://www.googleapis.com/compute/v1/projects/project-abc/regions/asia-south1/subnetworks/default',
            'https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west4/subnetworks/default',
            'https://www.googleapis.com/compute/v1/projects/project-abc/regions/asia-southeast1/subnetworks/default',
            'https://www.googleapis.com/compute/v1/projects/project-abc/regions/us-west2/subnetworks/default',
            'https://www.googleapis.com/compute/v1/projects/project-abc/regions/us-central1/subnetworks/default',
            'https://www.googleapis.com/compute/v1/projects/project-abc/regions/asia-northeast2/subnetworks/default',
            'https://www.googleapis.com/compute/v1/projects/project-abc/regions/us-east4/subnetworks/default',
            'https://www.googleapis.com/compute/v1/projects/project-abc/regions/us-west1/subnetworks/default',
            'https://www.googleapis.com/compute/v1/projects/project-abc/regions/southamerica-east1/subnetworks/default',
            'https://www.googleapis.com/compute/v1/projects/project-abc/regions/asia-northeast1/subnetworks/default',
            'https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west6/subnetworks/default',
            'https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-north1/subnetworks/default',
            'https://www.googleapis.com/compute/v1/projects/project-abc/regions/australia-southeast1/subnetworks/default'
        ]
    }],
    'kind': 'compute#networkList',
    'selfLink': 'https://www.googleapis.com/compute/v1/projects/project-abc/global/networks'
}

VPC_SUBNET_RESPONSE = {
    'id': 'projects/project-abc/regions/europe-west2/subnetworks',
    'items': [{
        'creationTimestamp': '2018-05-10T17:33:24.446-07:00',
        'fingerprint': '!@#$%ASDF',
        'gatewayAddress': '10.0.0.1',
        'id': '98765',
        'ipCidrRange': '10.0.0.0/20',
        'kind': 'compute#subnetwork',
        'name': 'default',
        'network': 'https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default',
        'privateIpGoogleAccess': False,
        'region': 'https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2',
        'selfLink': 'https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/subnetworks/default'
    }],
    'kind': 'compute#subnetworkList',
    'selfLink': 'https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/subnetworks'
}

GCP_LIST_INSTANCES_RESPONSE = {
    'id': 'projects/project-abc/zones/europe-west2-b/instances',
    'items': [{
        'canIpForward': False,
        'cpuPlatform': 'Intel Haswell',
        'creationTimestamp': '2018-02-16T10:42:04.362-08:00',
        'deletionProtection': True,
        'description': '',
        'disks': [{
            'autoDelete': True,
            'boot': True,
            'deviceName': 'instance-1',
            'guestOsFeatures': [{
                'type': 'VIRTIO_SCSI_MULTIQUEUE'
            }],
            'index': 0,
            'interface': 'SCSI',
            'kind': 'compute#attachedDisk',
            'licenses': [
                'https://www.googleapis.com/compute/v1/projects/project-that-has-license/global/licenses/ubuntu-1404-trusty'
            ],
            'mode': 'READ_WRITE',
            'source': 'https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b/disks/instance-1',
            'type': 'PERSISTENT'
        }],
        'id': '1234',
        'kind': 'compute#instance',
        'labelFingerprint': 'fingerprint1234=',
        'machineType': 'https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b/machineTypes/n1-standard-1',
        'metadata': {
            'fingerprint': 'fingerprint2345',
            'kind': 'compute#metadata'
        },
        'name': 'instance-1',
        'networkInterfaces': [{
            'accessConfigs': [{
                'kind': 'compute#accessConfig',
                'name': 'External NAT',
                'natIP': '1.2.3.4',
                'networkTier': 'PREMIUM',
                'type': 'ONE_TO_ONE_NAT'
            }],
            'fingerprint': 'fingerprint-3456',
            'kind': 'compute#networkInterface',
            'name': 'nic0',
            'network': 'https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default',
            'networkIP': '10.0.0.2',
            'subnetwork': 'https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/subnetworks/default'
        }],
        'scheduling': {
            'automaticRestart': True,
            'onHostMaintenance': 'MIGRATE',
            'preemptible': False
        },
        'selfLink': 'https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b/instances/instance-1',
        'serviceAccounts': [{
            'email': 'my-svc-account@developer.gserviceaccount.com',
            'scopes': [
                'https://www.googleapis.com/auth/devstorage.read_only',
                'https://www.googleapis.com/auth/logging.write',
                'https://www.googleapis.com/auth/monitoring.write',
                'https://www.googleapis.com/auth/servicecontrol',
                'https://www.googleapis.com/auth/service.management.readonly',
                'https://www.googleapis.com/auth/trace.append'
            ]
        }],
        'startRestricted': False,
        'status': 'RUNNING',
        'tags': {
            'fingerprint': 'fingerprint3456',
            'items': ['scale']
        },
        'zone': 'https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b'
    }, {
        'canIpForward': True,
        'cpuPlatform': 'Intel Haswell',
        'creationTimestamp': '2018-04-19T05:24:54.903-07:00',
        'deletionProtection': False,
        'description': '',
        'disks': [{
            'autoDelete': True,
            'boot': True,
            'deviceName': 'instance-1-test',
            'guestOsFeatures': [{
                'type': 'VIRTIO_SCSI_MULTIQUEUE'
            }],
            'index': 0,
            'interface': 'SCSI',
            'kind': 'compute#attachedDisk',
            'licenses': [
                'https://www.googleapis.com/compute/v1/projects/project-that-has-license/global/licenses/ubuntu-1404-trusty'
            ],
            'mode': 'READ_WRITE',
            'source': 'https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b/disks/instance-1-test',
            'type': 'PERSISTENT'
        }],
        'id': '2345',
        'kind': 'compute#instance',
        'labelFingerprint': 'fingerprint1234=',
        'machineType': 'https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b/machineTypes/n1-standard-1',
        'metadata': {
            'fingerprint': 'fingerprint2345',
            'kind': 'compute#metadata'
        },
        'name': 'instance-1-test',
        'networkInterfaces': [{
            'accessConfigs': [{
                'kind': 'compute#accessConfig',
                'name': 'External NAT',
                'natIP': '1.3.4.5',
                'networkTier': 'PREMIUM',
                'type': 'ONE_TO_ONE_NAT'
            }],
            'fingerprint': 'fingerprint4567',
            'kind': 'compute#networkInterface',
            'name': 'nic0',
            'network': 'https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default',
            'networkIP': '10.0.0.3',
            'subnetwork': 'https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/subnetworks/default'
        }],
        'scheduling': {
            'automaticRestart': True,
            'onHostMaintenance': 'MIGRATE',
            'preemptible': False
        },
        'selfLink': 'https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b/instances/instance-1-test',
        'serviceAccounts': [{
            'email': 'my-svc-account@developer.gserviceaccount.com',
            'scopes': [
                'https://www.googleapis.com/auth/devstorage.read_only',
                'https://www.googleapis.com/auth/logging.write',
                'https://www.googleapis.com/auth/monitoring.write',
                'https://www.googleapis.com/auth/servicecontrol',
                'https://www.googleapis.com/auth/service.management.readonly',
                'https://www.googleapis.com/auth/trace.append'
            ]
        }],
        'startRestricted': False,
        'status': 'RUNNING',
        'tags': {
            'fingerprint': 'fingerprint1234='
        },
        'zone': 'https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b'
    }],
    'kind': 'compute#instanceList',
    'selfLink': 'https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b/instances'
}

TRANSFORMED_GCP_VPCS = [{
    'partial_uri': 'projects/project-abc/global/networks/default',
    'name': 'default',
    'self_link': 'https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default',
    'project_id': 'project-abc',
    'auto_create_subnetworks': True,
    'description': 'Default network for the project',
    'routing_config_routing_mode': 'REGIONAL'
}]

TRANSFORMED_GCP_SUBNETS = [{
    'id': 'projects/project-abc/regions/europe-west2/subnetworks/default',
    'partial_uri': 'projects/project-abc/regions/europe-west2/subnetworks/default',
    'name': 'default',
    'vpc_self_link': 'https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default',
    'project_id': 'project-abc',
    'region': 'europe-west2',
    'gateway_address': '10.0.0.1',
    'ip_cidr_range': '10.0.0.0/20',
    'self_link': 'https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/subnetworks/default',
    'private_ip_google_access': False
}]

TRANSFORMED_GCP_INSTANCES = [{
    'canIpForward': False,
    'cpuPlatform': 'Intel Haswell',
    'creationTimestamp': '2018-02-16T10:42:04.362-08:00',
    'deletionProtection': True,
    'description': '',
    'disks': [{
        'autoDelete': True,
        'boot': True,
        'deviceName': 'instance-1',
        'guestOsFeatures': [{
            'type': 'VIRTIO_SCSI_MULTIQUEUE'
        }],
        'index': 0,
        'interface': 'SCSI',
        'kind': 'compute#attachedDisk',
        'licenses': [
            'https://www.googleapis.com/compute/v1/projects/project-that-has-license/global/licenses/ubuntu-1404-trusty'
        ],
        'mode': 'READ_WRITE',
        'source': 'https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b/disks/instance-1',
        'type': 'PERSISTENT'
    }],
    'id': '1234',
    'kind': 'compute#instance',
    'labelFingerprint': 'fingerprint1234=',
    'machineType': 'https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b/machineTypes/n1-standard-1',
    'metadata': {
        'fingerprint': 'fingerprint2345',
        'kind': 'compute#metadata'
    },
    'name': 'instance-1',
    'networkInterfaces': [{
        'accessConfigs': [{
            'kind': 'compute#accessConfig',
            'name': 'External NAT',
            'natIP': '1.2.3.4',
            'networkTier': 'PREMIUM',
            'type': 'ONE_TO_ONE_NAT'
        }],
        'fingerprint': 'fingerprint-3456',
        'kind': 'compute#networkInterface',
        'name': 'nic0',
        'network': 'https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default',
        'networkIP': '10.0.0.2',
        'subnetwork': 'https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/subnetworks/default'
    }],
    'scheduling': {
        'automaticRestart': True,
        'onHostMaintenance': 'MIGRATE',
        'preemptible': False
    },
    'selfLink': 'https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b/instances/instance-1',
    'serviceAccounts': [{
        'email': 'my-svc-account@developer.gserviceaccount.com',
        'scopes': [
            'https://www.googleapis.com/auth/devstorage.read_only',
            'https://www.googleapis.com/auth/logging.write',
            'https://www.googleapis.com/auth/monitoring.write',
            'https://www.googleapis.com/auth/servicecontrol',
            'https://www.googleapis.com/auth/service.management.readonly',
            'https://www.googleapis.com/auth/trace.append'
        ]
    }],
    'startRestricted': False,
    'status': 'RUNNING',
    'tags': {
        'fingerprint': 'fingerprint3456',
        'items': ['scale']
    },
    'zone': 'https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b',
    'partial_uri': 'projects/project-abc/zones/europe-west2-b/instances/instance-1',
    'project_id': 'project-abc',
    'zone_name': 'europe-west2-b'
}, {
    'canIpForward': True,
    'cpuPlatform': 'Intel Haswell',
    'creationTimestamp': '2018-04-19T05:24:54.903-07:00',
    'deletionProtection': False,
    'description': '',
    'disks': [{
        'autoDelete': True,
        'boot': True,
        'deviceName': 'instance-1-test',
        'guestOsFeatures': [{
            'type': 'VIRTIO_SCSI_MULTIQUEUE'
        }],
        'index': 0,
        'interface': 'SCSI',
        'kind': 'compute#attachedDisk',
        'licenses': [
            'https://www.googleapis.com/compute/v1/projects/project-that-has-license/global/licenses/ubuntu-1404-trusty'
        ],
        'mode': 'READ_WRITE',
        'source': 'https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b/disks/instance-1-test',
        'type': 'PERSISTENT'
    }],
    'id': '2345',
    'kind': 'compute#instance',
    'labelFingerprint': 'fingerprint1234=',
    'machineType': 'https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b/machineTypes/n1-standard-1',
    'metadata': {
        'fingerprint': 'fingerprint2345',
        'kind': 'compute#metadata'
    },
    'name': 'instance-1-test',
    'networkInterfaces': [{
        'accessConfigs': [{
            'kind': 'compute#accessConfig',
            'name': 'External NAT',
            'natIP': '1.3.4.5',
            'networkTier': 'PREMIUM',
            'type': 'ONE_TO_ONE_NAT'
        }],
        'fingerprint': 'fingerprint4567',
        'kind': 'compute#networkInterface',
        'name': 'nic0',
        'network': 'https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default',
        'networkIP': '10.0.0.3',
        'subnetwork': 'https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/subnetworks/default'
    }],
    'scheduling': {
        'automaticRestart': True,
        'onHostMaintenance': 'MIGRATE',
        'preemptible': False
    },
    'selfLink': 'https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b/instances/instance-1-test',
    'serviceAccounts': [{
        'email': 'my-svc-account@developer.gserviceaccount.com',
        'scopes': [
            'https://www.googleapis.com/auth/devstorage.read_only',
            'https://www.googleapis.com/auth/logging.write',
            'https://www.googleapis.com/auth/monitoring.write',
            'https://www.googleapis.com/auth/servicecontrol',
            'https://www.googleapis.com/auth/service.management.readonly',
            'https://www.googleapis.com/auth/trace.append'
        ]
    }],
    'startRestricted': False,
    'status': 'RUNNING',
    'tags': {
        'fingerprint': 'fingerprint1234='
    },
    'zone': 'https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b',
    'partial_uri': 'projects/project-abc/zones/europe-west2-b/instances/instance-1-test',
    'project_id': 'project-abc',
    'zone_name': 'europe-west2-b'
}]
