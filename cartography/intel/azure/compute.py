import logging
from typing import Dict
from typing import List

import neo4j
from azure.core.exceptions import HttpResponseError
from azure.mgmt.compute import ComputeManagementClient

from .util.credentials import Credentials
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def load_vm_extensions(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_vm_extensions_tx, data_list, update_tag)


def load_vm_available_sizes(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_vm_available_sizes_tx, data_list, update_tag)


def load_vm_scale_sets(session: neo4j.Session, subscription_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_vm_scale_sets_tx, subscription_id, data_list, update_tag)


def load_vm_scale_sets_extensions(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_vm_scale_sets_extensions_tx, data_list, update_tag)


def get_client(credentials: Credentials, subscription_id: str) -> ComputeManagementClient:
    client = ComputeManagementClient(credentials, subscription_id)
    return client


def get_vm_list(credentials: Credentials, subscription_id: str) -> List[Dict]:
    try:
        client = get_client(credentials, subscription_id)
        vm_list = list(map(lambda x: x.as_dict(), client.virtual_machines.list_all()))

        for vm in vm_list:
            x = vm['id'].split('/')
            vm['resource_group'] = x[x.index('resourceGroups') + 1]

        return vm_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving virtual machines - {e}")
        return []


def load_vms(neo4j_session: neo4j.Session, subscription_id: str, vm_list: List[Dict], update_tag: int) -> None:
    ingest_vm = """
    UNWIND {vms} AS vm
    MERGE (v:AzureVirtualMachine{id: vm.id})
    ON CREATE SET v.firstseen = timestamp(),
    v.type = vm.type, v.location = vm.location,
    v.resourcegroup = vm.resource_group
    SET v.lastupdated = {update_tag}, v.name = vm.name,
    v.plan = vm.plan.product, v.size = vm.hardware_profile.vm_size,
    v.license_type=vm.license_type, v.computer_name=vm.os_profile.computer_ame,
    v.identity_type=vm.identity.type, v.zones=vm.zones,
    v.ultra_ssd_enabled=vm.additional_capabilities.ultra_ssd_enabled,
    v.priority=vm.priority, v.eviction_policy=vm.eviction_policy
    WITH v
    MATCH (owner:AzureSubscription{id: {SUBSCRIPTION_ID}})
    MERGE (owner)-[r:RESOURCE]->(v)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """

    neo4j_session.run(
        ingest_vm,
        vms=vm_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )

    for vm in vm_list:
        if vm.get('storage_profile', {}).get('data_disks'):
            load_vm_data_disks(neo4j_session, vm['id'], vm['storage_profile']['data_disks'], update_tag)


def get_vm_extensions_list(vm_list: List[Dict], client: ComputeManagementClient) -> List[Dict]:
    try:
        vm_extensions_list: List[Dict] = []
        for vm in vm_list:
            vm_extensions_list = vm_extensions_list + \
                list(
                    map(
                        lambda x: x.as_dict(), client.virtual_machine_extensions.list(
                            resource_group_name=vm['resource_group'], vm_name=vm['name'],
                        ),
                    ),
                )

        for extension in vm_extensions_list:
            x = extension['id'].split('/')
            extension['resource_group'] = x[x.index('resourceGroups') + 1]
            extension['vm_id'] = extension['id'][:extension['id'].index("/extensions")]

        return vm_extensions_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving virtual machine extensions- {e}")
        return []


def _load_vm_extensions_tx(tx: neo4j.Transaction, vm_extensions_list: List[Dict], update_tag: int) -> None:
    ingest_vm_extension = """
    UNWIND {vm_extensions_list} AS extension
    MERGE (v:AzureVirtualMachineExtension{id: extension.id})
    ON CREATE SET v.firstseen = timestamp(), v.location = extension.location
    SET v.lastupdated = {update_tag}, v.name = extension.name,
    v.type = extension.type
    WITH v,extension
    MATCH (owner:AzureVirtualMachine{id: extension.vm_id})
    MERGE (owner)-[r:CONTAIN]->(v)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """

    tx.run(
        ingest_vm_extension,
        vm_extensions_list=vm_extensions_list,
        update_tag=update_tag,
    )


def cleanup_virtual_machine_extensions(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_virtual_machines_extensions_cleanup.json', neo4j_session, common_job_parameters)


def sync_virtual_machine_extensions(
    neo4j_session: neo4j.Session, client: ComputeManagementClient, vm_list: List[Dict], update_tag: int,
    common_job_parameters: Dict,
) -> None:
    vm_extensions_list = get_vm_extensions_list(vm_list, client)
    load_vm_extensions(neo4j_session, vm_extensions_list, update_tag)
    cleanup_virtual_machine_extensions(neo4j_session, common_job_parameters)


def get_vm_available_sizes_list(vm_list: List[Dict], client: ComputeManagementClient) -> List[Dict]:
    try:
        vm_available_sizes_list: List[Dict] = []
        for vm in vm_list:
            vm_available_size_list = list(
                map(
                    lambda x: x.as_dict(), client.virtual_machines.list_available_sizes(
                        resource_group_name=vm['resource_group'], vm_name=vm['name'],
                    ),
                ),
            )

            for size in vm_available_size_list:
                size['resource_group'] = vm['resource_group']
                size['vm_id'] = vm['id']
                size['id'] = f"{vm['id']}/Size/{size['name']}"
            vm_available_sizes_list = vm_available_sizes_list + vm_available_size_list

        return vm_available_sizes_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving virtual machine available_sizes - {e}")
        return []


def _load_vm_available_sizes_tx(tx: neo4j.Transaction, vm_available_sizes_list: List[Dict], update_tag: int) -> None:
    ingest_vm_size = """
    UNWIND {vm_available_sizes_list} AS size
    MERGE (v:AzureVirtualMachineAvailableSize{id: size.id})
    ON CREATE SET v.firstseen = timestamp(), v.numberOfCores = size.numberOfCores
    SET v.lastupdated = {update_tag}, v.osDiskSizeInMB = size.osDiskSizeInMB,
    v.name = size.name,
    v.resourceDiskSizeInMB = size.resourceDiskSizeInMB,
    v.memoryInMB=size.memoryInMB,
    v.maxDataDiskCount=size.maxDataDiskCount
    WITH v,size
    MATCH (owner:AzureVirtualMachine{id: size.vm_id})
    MERGE (owner)-[r:CONTAIN]->(v)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """

    tx.run(
        ingest_vm_size,
        vm_available_sizes_list=vm_available_sizes_list,
        update_tag=update_tag,
    )


def cleanup_virtual_machine_available_sizes(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job(
        'azure_import_virtual_machines_vm_available_sizes_list_cleanup.json',
        neo4j_session, common_job_parameters,
    )


def sync_virtual_machine_available_sizes(
    neo4j_session: neo4j.Session, client: ComputeManagementClient, vm_list: List[Dict], update_tag: int,
    common_job_parameters: Dict,
) -> None:
    vm_available_sizes_list = get_vm_available_sizes_list(vm_list, client)
    load_vm_available_sizes(neo4j_session, vm_available_sizes_list, update_tag)
    cleanup_virtual_machine_available_sizes(neo4j_session, common_job_parameters)


def get_vm_scale_sets_list(credentials: Credentials, subscription_id: str) -> List[Dict]:
    try:
        client = get_client(credentials, subscription_id)
        vm_scale_sets_list = list(map(lambda x: x.as_dict(), client.virtual_machine_scale_sets.list_all()))

        for set in vm_scale_sets_list:
            x = set['id'].split('/')
            set['resource_group'] = x[x.index('resourceGroups') + 1]

        return vm_scale_sets_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving virtual machines scale_sets_list - {e}")
        return []


def _load_vm_scale_sets_tx(
    tx: neo4j.Transaction, subscription_id: str, vm_scale_sets_list: List[Dict], update_tag: int,
) -> None:
    ingest_scale_set = """
    UNWIND {vm_scale_sets_list} AS set
    MERGE (a:AzureVirtualMachineScaleSet{id: set.id})
    ON CREATE SET a.firstseen = timestamp(),
    a.type = set.type,
    a.location = set.location,
    a.resourcegroup = set.resource_group
    SET a.lastupdated = {update_tag},
    a.name = set.name
    WITH a
    MATCH (owner:AzureSubscription{id: {SUBSCRIPTION_ID}})
    MERGE (owner)-[r:RESOURCE]->(a)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """

    tx.run(
        ingest_scale_set,
        vm_scale_sets_list=vm_scale_sets_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )


def cleanup_vm_scale_sets(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_virtual_machines_scale_sets_cleanup.json', neo4j_session, common_job_parameters)


def sync_vm_scale_sets(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    client = get_client(credentials, subscription_id)
    vm_scale_sets_list = get_vm_scale_sets_list(credentials, subscription_id)
    load_vm_scale_sets(neo4j_session, subscription_id, vm_scale_sets_list, update_tag)
    cleanup_vm_scale_sets(neo4j_session, common_job_parameters)
    sync_virtual_machine_scale_sets_extensions(
        neo4j_session, client, vm_scale_sets_list, update_tag, common_job_parameters,
    )


def get_vm_scale_sets_extensions_list(vm_scale_sets_list: List[Dict], client: ComputeManagementClient) -> List[Dict]:
    try:
        vm_scale_sets_extensions_list: List[Dict] = []
        for set in vm_scale_sets_list:
            vm_scale_sets_extensions_list = vm_scale_sets_extensions_list + \
                list(
                    map(
                        lambda x: x.as_dict(), client.virtual_machine_scale_set_extensions.list(
                            resource_group_name=set['resource_group'], vm_name=set['name'],
                        ),
                    ),
                )

        for extension in vm_scale_sets_extensions_list:
            x = extension['id'].split('/')
            extension['resource_group'] = x[x.index('resourceGroups') + 1]
            extension['set_id'] = extension['id'][:extension['id'].index("/extensions")]

        return vm_scale_sets_extensions_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving virtual machine scale set extensions- {e}")
        return []


def _load_vm_scale_sets_extensions_tx(
    tx: neo4j.Transaction, vm_scale_sets_extensions_list: List[Dict], update_tag: int,
) -> None:
    ingest_vm_scale_sets_extension = """
    UNWIND {vm_scale_sets_extensions_list} AS extension
    MERGE (v:AzureVirtualMachineScaleSetExtension{id: extension.id})
    ON CREATE SET v.firstseen = timestamp()
    SET v.lastupdated = {update_tag}, v.name = extension.name,
    v.type = extension.type
    WITH v,extension
    MATCH (owner:AzureVirtualMachineScaleSet{id: extension.set_id})
    MERGE (owner)-[r:CONTAIN]->(v)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """

    tx.run(
        ingest_vm_scale_sets_extension,
        vm_scale_sets_extensions_list=vm_scale_sets_extensions_list,
        update_tag=update_tag,
    )


def cleanup_virtual_machine_scale_sets_extensions(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job(
        'azure_import_virtual_machines_scale_sets_extensions_cleanup.json',
        neo4j_session, common_job_parameters,
    )


def sync_virtual_machine_scale_sets_extensions(
    neo4j_session: neo4j.Session, client: ComputeManagementClient, vm_list: List[Dict], update_tag: int,
    common_job_parameters: Dict,
) -> None:
    vm_scale_sets_extensions_list = get_vm_scale_sets_extensions_list(vm_list, client)
    load_vm_scale_sets_extensions(neo4j_session, vm_scale_sets_extensions_list, update_tag)
    cleanup_virtual_machine_scale_sets_extensions(neo4j_session, common_job_parameters)


def load_vm_data_disks(neo4j_session: neo4j.Session, vm_id: str, data_disks: List[Dict], update_tag: int) -> None:
    ingest_data_disk = """
    UNWIND {disks} AS disk
    MERGE (d:AzureDataDisk{id: disk.managed_disk.id})
    ON CREATE SET d.firstseen = timestamp(), d.lun = disk.lun
    SET d.lastupdated = {update_tag}, d.name = disk.name,
    d.vhd = disk.vhd.uri, d.image = disk.image.uri,
    d.size = disk.disk_size_gb, d.caching = disk.caching,
    d.createoption = disk.create_option, d.write_accelerator_enabled=disk.write_accelerator_enabled,
    d.managed_disk_storage_type=disk.managed_disk.storage_account_type
    WITH d
    MATCH (owner:AzureVirtualMachine{id: {VM_ID}})
    MERGE (owner)-[r:ATTACHED_TO]->(d)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """

    # for disk in data_disks:
    neo4j_session.run(
        ingest_data_disk,
        disks=data_disks,
        VM_ID=vm_id,
        update_tag=update_tag,
    )


def cleanup_virtual_machine(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_virtual_machines_cleanup.json', neo4j_session, common_job_parameters)


def get_disks(credentials: Credentials, subscription_id: str) -> List[Dict]:
    try:
        client = get_client(credentials, subscription_id)
        disk_list = list(map(lambda x: x.as_dict(), client.disks.list()))

        for disk in disk_list:
            x = disk['id'].split('/')
            disk['resource_group'] = x[x.index('resourceGroups') + 1]

        return disk_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving disks - {e}")
        return []


def load_disks(neo4j_session: neo4j.Session, subscription_id: str, disk_list: List[Dict], update_tag: int) -> None:
    ingest_disks = """
    UNWIND {disks} AS disk
    MERGE (d:AzureDisk{id: disk.id})
    ON CREATE SET d.firstseen = timestamp(),
    d.type = disk.type, d.location = disk.location,
    d.resourcegroup = disk.resource_group
    SET d.lastupdated = {update_tag}, d.name = disk.name,
    d.createoption = disk.creation_data.create_option, d.disksizegb = disk.disk_size_gb,
    d.encryption = disk.encryption_settings_collection.enabled, d.maxshares = disk.max_shares,
    d.network_access_policy = disk.network_access_policy,
    d.ostype = disk.os_type, d.tier = disk.tier,
    d.sku = disk.sku.name, d.zones = disk.zones
    WITH d
    MATCH (owner:AzureSubscription{id: {SUBSCRIPTION_ID}})
    MERGE (owner)-[r:RESOURCE]->(d)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}"""

    neo4j_session.run(
        ingest_disks,
        disks=disk_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )


def cleanup_disks(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_disks_cleanup.json', neo4j_session, common_job_parameters)


def get_snapshots_list(credentials: Credentials, subscription_id: str) -> List[Dict]:
    try:
        client = get_client(credentials, subscription_id)
        snapshots = list(map(lambda x: x.as_dict(), client.snapshots.list()))

        for snapshot in snapshots:
            x = snapshot['id'].split('/')
            snapshot['resource_group'] = x[x.index('resourceGroups') + 1]

        return snapshots

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving snapshots - {e}")
        return []


def load_snapshots(neo4j_session: neo4j.Session, subscription_id: str, snapshots: List[Dict], update_tag: int) -> None:
    ingest_snapshots = """
    UNWIND {snapshots} as snapshot
    MERGE (s:AzureSnapshot{id: snapshot.id})
    ON CREATE SET s.firstseen = timestamp(),
    s.resourcegroup = snapshot.resource_group,
    s.type = snapshot.type, s.location = snapshot.location
    SET s.lastupdated = {update_tag}, s.name = snapshot.name,
    s.createoption = snapshot.creation_data.create_option, s.disksizegb = snapshot.disk_size_gb,
    s.encryption = snapshot.encryption_settings_collection.enabled, s.incremental = snapshot.incremental,
    s.network_access_policy = snapshot.network_access_policy, s.ostype = snapshot.os_type,
    s.tier = snapshot.tier, s.sku = snapshot.sku.name
    WITH s
    MATCH (owner:AzureSubscription{id: {SUBSCRIPTION_ID}})
    MERGE (owner)-[r:RESOURCE]->(s)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}"""

    neo4j_session.run(
        ingest_snapshots,
        snapshots=snapshots,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )


def cleanup_snapshot(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_snapshots_cleanup.json', neo4j_session, common_job_parameters)


def sync_virtual_machine(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    client = get_client(credentials, subscription_id)
    vm_list = get_vm_list(credentials, subscription_id)
    load_vms(neo4j_session, subscription_id, vm_list, update_tag)
    cleanup_virtual_machine(neo4j_session, common_job_parameters)
    sync_virtual_machine_extensions(neo4j_session, client, vm_list, update_tag, common_job_parameters)
    sync_virtual_machine_available_sizes(neo4j_session, client, vm_list, update_tag, common_job_parameters)


def sync_disk(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    disk_list = get_disks(credentials, subscription_id)
    load_disks(neo4j_session, subscription_id, disk_list, update_tag)
    cleanup_disks(neo4j_session, common_job_parameters)


def sync_snapshot(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    snapshots = get_snapshots_list(credentials, subscription_id)
    load_snapshots(neo4j_session, subscription_id, snapshots, update_tag)
    cleanup_snapshot(neo4j_session, common_job_parameters)


@ timeit
def sync(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info("Syncing VM for subscription '%s'.", subscription_id)

    sync_virtual_machine(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters)
    sync_vm_scale_sets(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters)
    sync_disk(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters)
    sync_snapshot(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters)
