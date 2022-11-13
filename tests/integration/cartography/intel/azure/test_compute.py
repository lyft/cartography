from cartography.intel.azure import compute
from tests.data.azure.compute import DESCRIBE_DISKS
from tests.data.azure.compute import DESCRIBE_SNAPSHOTS
from tests.data.azure.compute import DESCRIBE_VM_DATA_DISKS
from tests.data.azure.compute import DESCRIBE_VMAVAILABLESIZES
from tests.data.azure.compute import DESCRIBE_VMEXTENSIONS
from tests.data.azure.compute import DESCRIBE_VMS
from tests.data.azure.compute import DESCRIBE_VMSCALESETEXTENSIONS
from tests.data.azure.compute import DESCRIBE_VMSCALESETS

TEST_SUBSCRIPTION_ID = '00-00-00-00'
TEST_RESOURCE_GROUP = 'TestRG'
TEST_UPDATE_TAG = 123456789


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
        MERGE (as:AzureSubscription{id: {subscription_id}})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = {update_tag}
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
