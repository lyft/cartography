from cartography.intel.azure import compute
from cartography.intel.azure import network
from tests.data.azure.compute import DESCRIBE_DISKS
from tests.data.azure.compute import DESCRIBE_SNAPSHOTS
from tests.data.azure.compute import DESCRIBE_VM_DATA_DISKS
from tests.data.azure.compute import DESCRIBE_VMAVAILABLESIZES
from tests.data.azure.compute import DESCRIBE_VMEXTENSIONS
from tests.data.azure.compute import DESCRIBE_VMS
from tests.data.azure.compute import DESCRIBE_VMSCALESETEXTENSIONS
from tests.data.azure.compute import DESCRIBE_VMSCALESETS
from tests.data.azure.network import DESCRIBE_NETWORKSECURITYGROUPS
from tests.data.azure.network import DESCRIBE_NETWORKSECURITYRULES
from tests.data.azure.network import DESCRIBE_NETWORKINTERFACES
from tests.data.azure.network import DESCRIBE_PUBLICIPADDRESSES
from tests.data.azure.network import DESCRIBE_PUBLICIPADDRESSES_REFERENCE
from tests.data.azure.network import DESCRIBE_NETWORKSUBNETS
from tests.data.azure.network import DESCRIBE_ROUTETABLE
from tests.data.azure.network import DESCRIBE_NETWORKROUTE
from tests.data.azure.network import DESCRIBE_NETWORKS
from cartography.util import run_analysis_job

TEST_SUBSCRIPTION_ID = '00-00-00-00'
TEST_RESOURCE_GROUP = 'TestRG'
TEST_UPDATE_TAG = 123456789
TEST_WORKSPACE_ID = '123'
TEST_TENANT_ID = '123'


def test_load_vms(neo4j_session):
    compute.load_vms(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_VMS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM1",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureVirtualMachine) RETURN r.id;
        """,
    )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_vms_relationships(neo4j_session):
    # Create Test Azure Subscription
    neo4j_session.run(
        """
        MERGE (as:AzureSubscription{id: $subscription_id})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = $update_tag
        """,
        subscription_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    compute.load_vms(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_VMS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM",
        ),
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM1",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureSubscription)-[:RESOURCE]->(n2:AzureVirtualMachine) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_vm_data_disks(neo4j_session):
    compute.load_vm_data_disks(
        neo4j_session,
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM",
        DESCRIBE_VM_DATA_DISKS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/disks/dd0",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/disks/dd1",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureDataDisk) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_vm_data_disk_relationships(neo4j_session):
    # Create Test Virtual Machines
    compute.load_vms(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        [DESCRIBE_VMS[0]],
        TEST_UPDATE_TAG,
    )

    compute.load_vm_data_disks(
        neo4j_session,
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM",
        DESCRIBE_VM_DATA_DISKS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/disks/dd0",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/disks/dd1",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureVirtualMachine)-[:ATTACHED_TO]->(n2:AzureDataDisk) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_disks(neo4j_session):
    compute.load_disks(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_DISKS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/disks/dd0",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/disks/dd1",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureDisk) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_disk_relationships(neo4j_session):
    # Create Test Azure Subscription
    neo4j_session.run(
        """
        MERGE (as:AzureSubscription{id: $subscription_id})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = $update_tag
        """,
        subscription_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    compute.load_disks(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_DISKS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/disks/dd0",
        ),
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/disks/dd1",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureSubscription)-[:RESOURCE]->(n2:AzureDisk) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_snapshots(neo4j_session):
    compute.load_snapshots(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_SNAPSHOTS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/snapshots/ss0",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/snapshots/ss1",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureSnapshot) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_snapshot_relationships(neo4j_session):
    # Create Test Azure Subscription
    neo4j_session.run(
        """
        MERGE (as:AzureSubscription{id: $subscription_id})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = $update_tag
        """,
        subscription_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    compute.load_snapshots(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_SNAPSHOTS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/snapshots/ss0",
        ),
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/snapshots/ss1",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureSubscription)-[:RESOURCE]->(n2:AzureSnapshot) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_vm_extensions(neo4j_session):
    compute.load_vm_extensions(
        neo4j_session,
        DESCRIBE_VMEXTENSIONS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/\
            virtualMachines/TestVM/extensions/extensions1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/\
            virtualMachines/TestVM1/extensions/extensions2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureVirtualMachineExtension) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_vm_extensions_relationships(neo4j_session):
    compute.load_vms(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_VMS,
        TEST_UPDATE_TAG,
    )

    compute.load_vm_extensions(
        neo4j_session,
        DESCRIBE_VMEXTENSIONS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/\
            virtualMachines/TestVM/extensions/extensions1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/\
            virtualMachines/TestVM1/extensions/extensions2",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureVirtualMachine)-[:CONTAIN]->(n2:AzureVirtualMachineExtension) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected


def test_load_vm_available_sizes(neo4j_session):
    compute.load_vm_available_sizes(
        neo4j_session,
        DESCRIBE_VMAVAILABLESIZES,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "size1",
        "size2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureVirtualMachineAvailableSize) RETURN r.name;
        """, )
    actual_nodes = {n['r.name'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_vm_available_sizes_relationships(neo4j_session):
    compute.load_vms(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_VMS,
        TEST_UPDATE_TAG,
    )

    compute.load_vm_available_sizes(
        neo4j_session,
        DESCRIBE_VMAVAILABLESIZES,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM",
            "size1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM1",
            "size2",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureVirtualMachine)-[:CONTAIN]->(n2:AzureVirtualMachineAvailableSize) RETURN n1.id, n2.name;
        """, )

    actual = {(r['n1.id'], r['n2.name']) for r in result}

    assert actual == expected


def test_load_vm_scale_sets(neo4j_session):
    compute.load_vm_scale_sets(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_VMSCALESETS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/\
            virtualMachineScaleSets/set1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/\
            virtualMachineScaleSets/set2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureVirtualMachineScaleSet) RETURN r.id;
        """,
    )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_vms_scale_sets_relationships(neo4j_session):
    neo4j_session.run(
        """
        MERGE (as:AzureSubscription{id: $subscription_id})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = $update_tag
        """,
        subscription_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    compute.load_vm_scale_sets(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_VMSCALESETS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/\
            virtualMachineScaleSets/set1",
        ),
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/\
            virtualMachineScaleSets/set2",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureSubscription)-[:RESOURCE]->(n2:AzureVirtualMachineScaleSet) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_vm_scale_set_extensions(neo4j_session):
    compute.load_vm_scale_sets_extensions(
        neo4j_session,
        DESCRIBE_VMSCALESETEXTENSIONS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/\
            virtualMachineScaleSets/set1/extensions/extension1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/\
            virtualMachineScaleSets/set2/extensions/extension2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureVirtualMachineScaleSetExtension) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_vm_scale_set_extensions_relationships(neo4j_session):
    compute.load_vm_scale_sets(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_VMSCALESETS,
        TEST_UPDATE_TAG,
    )

    compute.load_vm_scale_sets_extensions(
        neo4j_session,
        DESCRIBE_VMSCALESETEXTENSIONS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/\
            virtualMachineScaleSets/set1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/\
            virtualMachineScaleSets/set1/extensions/extension1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/\
            virtualMachineScaleSets/set2",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/\
            virtualMachineScaleSets/set2/extensions/extension2",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureVirtualMachineScaleSet)-[:CONTAIN]->(n2:AzureVirtualMachineScaleSetExtension)
         RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected


def test_vm_public_exposure_analysis(neo4j_session):
    neo4j_session.run(
        """
        MERGE (as:AzureSubscription{id: $subscription_id})<-[:RESOURCE]-(:AzureTenant{id: $AZURE_TENANT_ID})<-[:OWNER]-(:CloudanixWorkspace{id: $WORKSPACE_ID})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = $update_tag
        """,
        subscription_id=TEST_SUBSCRIPTION_ID,
        AZURE_TENANT_ID=TEST_TENANT_ID,
        WORKSPACE_ID=TEST_WORKSPACE_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    network.load_network_security_groups(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_NETWORKSECURITYGROUPS,
        TEST_UPDATE_TAG,
    )

    network.load_network_security_rules(
        neo4j_session,
        DESCRIBE_NETWORKSECURITYRULES,
        TEST_UPDATE_TAG,
    )

    network.load_network_interfaces(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_NETWORKINTERFACES,
        TEST_UPDATE_TAG
    )

    network.load_public_ip_addresses(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_PUBLICIPADDRESSES,
        TEST_UPDATE_TAG
    )

    network.load_public_ip_network_interfaces_relationship(
        neo4j_session,
        "/subscriptions/subid/resourceGroups/rg1/providers/Microsoft.Network/networkInterfaces/test-nic",
        DESCRIBE_PUBLICIPADDRESSES_REFERENCE,
        TEST_UPDATE_TAG
    )

    network.load_networks(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_NETWORKS,
        TEST_UPDATE_TAG,
    )

    network.load_networks_subnets(
        neo4j_session,
        DESCRIBE_NETWORKSUBNETS,
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG
    )

    network.load_network_routetables(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_ROUTETABLE,
        TEST_UPDATE_TAG
    )

    network.attach_network_routetables_to_subnet(
        neo4j_session,
        DESCRIBE_ROUTETABLE,
        TEST_UPDATE_TAG
    )

    network.load_network_routes(
        neo4j_session,
        DESCRIBE_NETWORKROUTE,
        TEST_UPDATE_TAG
    )

    compute.load_vms(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_VMS,
        TEST_UPDATE_TAG,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG + 1,
        "WORKSPACE_ID": TEST_WORKSPACE_ID,
        "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
        "AZURE_TENANT_ID": TEST_TENANT_ID
    }

    run_analysis_job(
        'azure_vm_asset_exposure.json',
        neo4j_session,
        common_job_parameters
    )

    expected_nodes = {('/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM',
        'direct_ipv4,public_ip,inbound_public_ports,public_icmp'),
       ('/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM1',
        'direct_ipv4,inbound_public_ports,public_icmp')}
    
    nodes = neo4j_session.run(
        """
        MATCH (r:AzureVirtualMachine{exposed_internet: true}) RETURN r.id, r.exposed_internet_type;
        """,
    )
    actual_nodes = {(n['r.id'], ",".join(n['r.exposed_internet_type'])) for n in nodes}
    assert actual_nodes == expected_nodes
