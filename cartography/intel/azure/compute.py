import logging
from azure.mgmt.compute import ComputeManagementClient
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get_client(credentials, subscription_id):
    client = ComputeManagementClient(credentials, subscription_id)
    return client


def get_vm_list(credentials, subscription_id):
    try:
        client = get_client(credentials, subscription_id)
        vm_list = list(map(lambda x: x.as_dict(), client.virtual_machines.list_all()))

        return vm_list

    except Exception as e:
        logger.warning("Error while retrieving virtual machines - {}".format(e))
        return []


def load_vm_data(neo4j_session, subscription_id, vm_list, azure_update_tag, common_job_parameters):
    ingest_vm = """
    UNWIND {vms} AS vm
    MERGE (vm:VirtualMachine{id: {vm.id}})
    ON CREATE SET vm.firstseen = timestamp(),
    vm.type = vm.type, vm.location = vm.location,
    vm.resourcegroup = vm.resource_group
    SET vm.lastupdated = {azure_update_tag}, vm.name = vm.name,
    vm.plan = vm.plan.product, vm.size = vm.hardware_profile.vm_size,
    vm.license_type=vm.license_type, vm.computer_name=vm.os_profile.computer_ame,
    vm.identity_type=vm.identity.type, vm.zones=vm.zones,
    vm.ultra_ssd_enabled=vm.additional_capabilities.ultra_ssd_enabled,
    vm.priority=vm.priority, vm.eviction_policy=vm.eviction_policy
    WITH vm
    MATCH (owner:AzureSubscription{id: {SUBSCRIPTION_ID}})
    MERGE (owner)-[r:RESOURCE]->(vm)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for vm in vm_list:
        x = vm['id'].split('/')
        vm['resource_group'] = x[x.index('resourceGroups') + 1]

    neo4j_session.run(
        ingest_vm,
        vms=vm_list,
        SUBSCRIPTION_ID=subscription_id,
        azure_update_tag=azure_update_tag
    )

    if vm.get('storage_profile', {}).get('data_disks'):
        disks = vm['storage_profile']['data_disks']
        load_vm_data_disks(neo4j_session, vm['id'], disks, azure_update_tag, common_job_parameters)


def load_vm_data_disks(neo4j_session, vm_id, data_disks, azure_update_tag, common_job_parameters):
    ingest_data_disk = """
    UNWIND {disks} AS disk
    MERGE (d:AzureDataDisk{id: {(disk.id + disk.lun)}})
    ON CREATE SET d.firstseen = timestamp(), d.lun = disk.lun
    SET d.lastupdated = {azure_update_tag}, d.name = disk.name,
    d.vhd = disk.vhd.uri, d.image = disk.image.uri,
    d.size = disk.disk_size_gb, d.caching = disk.caching,
    d.createoption = disk.create_option, d.write_accelerator_enabled=disk.write_accelerator_enabled,
    d.managed_disk_storage_type=disk.managed_disk.storage_account_type
    WITH disk
    MATCH (owner:VirtualMachine{id: {VM_ID}})
    MERGE (owner)-[r:ATTACHED_TO]->(disk)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    # for disk in data_disks:
    neo4j_session.run(
        ingest_data_disk,
        disks=data_disks,
        VM_ID=vm_id,
        azure_update_tag=azure_update_tag
    )


def cleanup_virtual_machine(neo4j_session, common_job_parameters):
    run_cleanup_job('azure_import_virtual_machines_cleanup.json', neo4j_session, common_job_parameters)


def get_disks(credentials, subscription_id):
    try:
        client = get_client(credentials, subscription_id)
        disk_list = list(map(lambda x: x.as_dict(), client.disks.list()))

        return disk_list

    except Exception as e:
        logger.warning("Error while retrieving disks - {}".format(e))
        return []


def load_disks(neo4j_session, subscription_id, disk_list, azure_update_tag, common_job_parameters):
    ingest_disks = """
    UNWIND {disks} AS disk
    MERGE (d:AzureDisk{id: {disk.id}})
    ON CREATE SET d.firstseen = timestamp(),
    d.type = disk.type, d.location = disk.location,
    d.resourcegroup = disk.resource_group
    SET d.lastupdated = {azure_update_tag}, d.name = disk.name,
    d.createoption = disk.creation_data.create_option, d.disksizegb = disk.disk_size_gb,
    d.encryption = disk.encryption_settings_collection.enabled, d.maxshares = disk.max_shares,
    d.network_access_policy = disk.network_access_policy,
    d.ostype = disk.os_type, d.tier = disk.tier,
    d.sku = disk.sku.name, d.zones = disk.zones
    WITH disk
    MATCH (owner:AzureSubscription{id: {SUBSCRIPTION_ID}})
    MERGE (owner)-[r:RESOURCE]->(disk)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}"""

    for disk in disk_list:
        x = disk['id'].split('/')
        disk['resource_group'] = x[x.index('resourceGroups') + 1]

    neo4j_session.run(
        ingest_disks,
        disks=disk_list,
        SUBSCRIPTION_ID=subscription_id,
        azure_update_tag=azure_update_tag,
    )


def cleanup_disks(neo4j_session, common_job_parameters):
    run_cleanup_job('azure_import_disks_cleanup.json', neo4j_session, common_job_parameters)


def get_snapshots_list(credentials, subscription_id):
    try:
        client = get_client(credentials, subscription_id)
        snapshot_list = list(map(lambda x: x.as_dict(), client.snapshots.list()))

        return snapshot_list

    except Exception as e:
        logger.warning("Error while retrieving disks - {}".format(e))
        return []


def load_snapshots(neo4j_session, subscription_id, snapshot_list, azure_update_tag, common_job_parameters):
    ingest_snapshots = """
    UNWIND {snapshots} as snapshot
    MERGE (s:AzureSnapshot{id: {snapshot.id}})
    ON CREATE SET s.firstseen = timestamp(),
    s.resourcegroup = snapshot.resource_group,
    s.type = snapshot.type, s.location = snapshot.location,
    SET s.lastupdated = {azure_update_tag}, s.name = snapshot.name,
    s.createoption = snapshot.creation_data.create_option, s.disksizegb = snapshot.disk_size_gb,
    s.encryption = snapshot.encryption_settings_collection.enabled, s.incremental = snapshot.incremental,
    s.network_access_policy = snapshot.network_access_policy, s.ostype = snapshot.os_type,
    s.tier = snapshot.tier, s.sku = snapshot.sku.name
    WITH snapshot
    MATCH (owner:AzureSubscription{id: {SUBSCRIPTION_ID}})
    MERGE (owner)-[r:RESOURCE]->(snapshot)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}"""

    for snapshot in snapshot_list:
        x = snapshot['id'].split('/')
        snapshot['resource_group'] = x[x.index('resourceGroups') + 1]

    neo4j_session.run(
        ingest_snapshots,
        snapshots=snapshot_list,
        SUBSCRIPTION_ID=subscription_id,
        azure_update_tag=azure_update_tag,
    )


def cleanup_snapshot(neo4j_session, common_job_parameters):
    run_cleanup_job('azure_import_snapshots_cleanup.json', neo4j_session, common_job_parameters)


def sync_virtual_machine(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters):
    vm_list = get_vm_list(credentials, subscription_id)
    load_vm_data(neo4j_session, subscription_id, vm_list, sync_tag, common_job_parameters)
    cleanup_virtual_machine(neo4j_session, common_job_parameters)


def sync_disk(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters):
    disk_list = get_disks(credentials, subscription_id)
    load_disks(neo4j_session, subscription_id, disk_list, sync_tag, common_job_parameters)
    cleanup_disks(neo4j_session, common_job_parameters)


def sync_snapshot(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters):
    snapshot_list = get_snapshots_list(credentials, subscription_id)
    load_snapshots(neo4j_session, subscription_id, snapshot_list, sync_tag, common_job_parameters)
    cleanup_snapshot(neo4j_session, common_job_parameters)


@timeit
def sync(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters):
    logger.info("Syncing VM for subscription '%s'.", subscription_id)

    sync_virtual_machine(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters)
    sync_disk(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters)
    sync_snapshot(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters)
