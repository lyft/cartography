import logging
from azure.mgmt.compute import ComputeManagementClient
from cartography.util import get_optional_value
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
    MERGE (vm:VirtualMachine{id: {id}})
    ON CREATE SET vm.firstseen = timestamp(),
    vm.type = {type}, vm.location = {location},
    vm.resourcegroup = {resourceGroup}
    SET vm.lastupdated = {azure_update_tag}, vm.name = {name},
    vm.plan = {plan}, vm.size = {size},
    vm.license_type={licenseType}, vm.computer_name={computerName},
    vm.identity_type={identityType}, vm.zones={zones},
    vm.ultra_ssd_enabled={ultraSSDEnabled}, vm.encryption_at_host={encryptionAtHost},
    vm.priority={priority}, vm.eviction_policy={evictionPolicy}
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
            id=vm['id'],
            name=vm['name'],
            type=vm['type'],
            location=vm['location'],
            resourceGroup=vm['resource_group'],
            plan=get_optional_value(vm, ['plan', 'product']),
            size=get_optional_value(vm, ['hardware_profile', 'vm_size']),
            licenseType=get_optional_value(vm, 'license_type'),
            computerName=get_optional_value(vm, ['os_profile', 'computer_name']),
            identityType=get_optional_value(vm, ['identity', 'type']),
            zones=get_optional_value(vm, ['zones']),
            ultraSSDEnabled=get_optional_value(vm, ['additional_capabilities', 'ultra_ssd_enabled']),
            encryptionAtHost=get_optional_value(vm, ['storage_profile', 'encryption_at_host']),
            priority=get_optional_value(vm, ['priority']),
            evictionPolicy=get_optional_value(vm, ['eviction_policy']),
            SUBSCRIPTION_ID=subscription_id,
            azure_update_tag=azure_update_tag
        )

        if 'storage_profile' in vm:
            if 'data_disks' in vm['storage_profile']:
                load_vm_data_disks(neo4j_session, vm['id'], vm['storage_profile'].get('data_disks'), azure_update_tag, common_job_parameters)


def load_vm_data_disks(neo4j_session, vm_id, data_disks, azure_update_tag, common_job_parameters):
    ingest_data_disk = """
    MERGE (disk:AzureDataDisk{id: {id}})
    ON CREATE SET disk.firstseen = timestamp(), disk.lun = {lun}
    SET disk.lastupdated = {azure_update_tag}, disk.name = {name},
    disk.vhd = {vhd}, disk.image = {image}, disk.size = {size},
    disk.caching = {caching}, disk.createoption = {createOption},
    disk.write_accelerator_enabled={writeAcceleratorEnabled},disk.managed_disk_storage_type={managedDiskStorageType}
    WITH disk
    MATCH (owner:VirtualMachine{id: {VM_ID}})
    MERGE (owner)-[r:ATTACHED_TO]->(disk)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for disk in data_disks:
        neo4j_session.run(
            ingest_data_disk,
            id=vm_id + str(disk['lun']),
            lun=disk['lun'],
            name=get_optional_value(disk, ['name']),
            vhd=get_optional_value(disk, ['vhd', 'uri']),
            image=get_optional_value(disk, ['image', 'uri']),
            size=get_optional_value(disk, ['disk_size_gb']),
            caching=get_optional_value(disk, ['caching']),
            createOption=get_optional_value(disk, ['create_option']),
            writeAcceleratorEnabled=get_optional_value(disk, ['write_accelerator_enabled']),
            managedDiskStorageType=get_optional_value(disk, ['managed_disk', 'storage_account_type']),
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
    MERGE (disk:AzureDisk{id: {id}})
    ON CREATE SET disk.firstseen = timestamp(),
    disk.type = {type}, disk.location = {location},
    disk.resourcegroup = {resourceGroup}
    SET disk.name = {name}, disk.type = {type},
    disk.location = {location}, disk.lastupdated = {azure_update_tag},
    disk.createoption = {createOption}, disk.disksizegb = {diskSize},
    disk.encryption = {encryption}, disk.maxshares = {maxShares},
    disk.network_access_policy = {accessPolicy},
    disk.ostype = {osType}, disk.tier = {tier},
    disk.sku = {sku}, disk.zones = {zones}
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
            id=disk['id'],
            name=disk['name'],
            type=disk['type'],
            location=disk['location'],
            resourceGroup=disk['resource_group'],
            createOption=get_optional_value(disk, ['creation_data', 'create_option']),
            diskSize=get_optional_value(disk, ['disk_size_gb']),
            encryption=get_optional_value(disk, ['encryption_settings_collection', 'enabled']),
            maxShares=get_optional_value(disk, ['max_shares']),
            accessPolicy=get_optional_value(disk, ['network_access_policy']),
            osType=get_optional_value(disk, ['os_type']),
            tier=get_optional_value(disk, ['tier']),
            sku=get_optional_value(disk, ['sku', 'name']),
            zones=get_optional_value(disk, ['zones']),
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
    MERGE (snapshot:AzureSnapshot{id: {id}})
    ON CREATE SET snapshot.firstseen = timestamp(),
    snapshot.resourcegroup = {resourceGroup}
    SET snapshot.name= {name},snapshot.type = {type},
    snapshot.location = {location}, snapshot.lastupdated = {azure_update_tag},
    snapshot.createoption = {createOption}, snapshot.disksizegb = {diskSize},
    snapshot.encryption = {encryption}, snapshot.incremental = {incremental},
    snapshot.network_access_policy = {accessPolicy},
    snapshot.ostype = {osType}, snapshot.tier = {tier},
    snapshot.sku = {sku}
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
            id=snapshot['id'],
            name=snapshot['name'],
            type=snapshot['type'],
            location=snapshot['location'],
            resourceGroup=snapshot['resource_group'],
            createOption=get_optional_value(snapshot, ['creation_data', 'create_option']),
            diskSize=get_optional_value(snapshot, ['disk_size_gb']),
            encryption=get_optional_value(snapshot, ['encryption_settings_collection', 'enabled']),
            incremental=get_optional_value(snapshot, ['incremental']),
            accessPolicy=get_optional_value(snapshot, ['network_access_policy']),
            osType=get_optional_value(snapshot, ['os_type']),
            tier=get_optional_value(snapshot, ['tier']),
            sku=get_optional_value(snapshot, ['sku', 'name']),
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
