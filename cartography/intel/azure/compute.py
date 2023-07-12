import logging
from typing import Dict
from typing import List

import neo4j
from azure.core.exceptions import HttpResponseError
from azure.mgmt.compute import ComputeManagementClient
from cloudconsolelink.clouds.azure import AzureLinker

from .util.credentials import Credentials
from cartography.util import run_cleanup_job
from cartography.util import get_azure_resource_group_name
from cartography.util import timeit

logger = logging.getLogger(__name__)
azure_console_link = AzureLinker()


def load_vm_extensions(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_vm_extensions_tx, data_list, update_tag)


def load_vm_available_sizes(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_vm_available_sizes_tx, data_list, update_tag)


def load_vm_scale_sets(session: neo4j.Session, subscription_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_vm_scale_sets_tx, subscription_id, data_list, update_tag)


def load_vm_scale_sets_extensions(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_vm_scale_sets_extensions_tx, data_list, update_tag)


def load_vm_security_groups_relationship(session: neo4j.Session, vm_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_vm_security_groups_relationship, vm_id, data_list, update_tag)


def load_vm_network_interfaces_relationship(session: neo4j.Session, vm_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_vm_network_interfaces_relationship, vm_id, data_list, update_tag)

def get_client(credentials: Credentials, subscription_id: str) -> ComputeManagementClient:
    client = ComputeManagementClient(credentials, subscription_id)
    return client


def get_vm_list(credentials: Credentials, subscription_id: str, regions: list, common_job_parameters: Dict) -> List[Dict]:
    try:
        client = get_client(credentials, subscription_id)
        vm_list = list(map(lambda x: x.as_dict(), client.virtual_machines.list_all()))
        vm_data = []
        for vm in vm_list:
            vm['resource_group'] = get_azure_resource_group_name(vm.get('id'))
            vm['consolelink'] = azure_console_link.get_console_link(
                id=vm['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'])

            network_interfaces = []
            for interface in vm.get('network_profile', {}).get('network_interfaces', []):
                network_interfaces.append(interface)
            vm['network_interfaces'] = network_interfaces
            vm['user_assigned_identities'] = list(vm.get('identity', {}).get('user_assigned_identities', {}).keys())
            network_security_group = []
            for config in vm.get('network_profile', {}).get('network_interface_configurations', []):
                network_security_group.append(config.get('network_security_group'), None)
            vm['network_security_group'] = network_security_group
            if regions is None:
                vm_data.append(vm)
            else:
                if vm.get('location') in regions or vm.get('location') == 'global':
                    vm_data.append(vm)
        return vm_data

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving virtual machines - {e}")
        return []


def load_vms(neo4j_session: neo4j.Session, subscription_id: str, vm_list: List[Dict], update_tag: int) -> None:
    ingest_vm = """
    UNWIND $vms AS vm
    MERGE (v:AzureVirtualMachine{id: vm.id})
    ON CREATE SET v.firstseen = timestamp(),
    v.type = vm.type, v.location = vm.location,
    v.region = vm.location,
    v.consolelink = vm.consolelink,
    v.resourcegroup = vm.resource_group
    SET v.lastupdated = $update_tag, v.name = vm.name,
    v.plan = vm.plan.product, v.size = vm.hardware_profile.vm_size,
    v.license_type=vm.license_type, v.computer_name=vm.os_profile.computer_name,
    v.identity_type=vm.identity.type, v.zones=vm.zones,
    v.ultra_ssd_enabled=vm.additional_capabilities.ultra_ssd_enabled,
    v.priority=vm.priority, v.eviction_policy=vm.eviction_policy
    WITH vm, v
    MATCH (owner:AzureSubscription{id: $SUBSCRIPTION_ID})
    MERGE (owner)-[r:RESOURCE]->(v)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    WITH vm, v
    UNWIND vm.user_assigned_identities AS ua
    MATCH (i:AzureManagedIdentity{id: ua})
    MERGE (v)-[rel:HAS]->(i)
    ON CREATE SET rel.firstseen = timestamp()
    SET rel.lastupdated = $update_tag
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

        if vm.get('network_security_group', []) != []:
            load_vm_security_groups_relationship(neo4j_session, vm['id'], vm.get('network_security_group'), update_tag)

        if vm.get('network_interfaces', []) != []:
            load_vm_network_interfaces_relationship(neo4j_session, vm['id'], vm.get('network_interfaces'), update_tag)
        resource_group = get_azure_resource_group_name(vm.get('id'))
        _attach_vm_resource_group(neo4j_session, vm['id'],resource_group, update_tag)
        _attach_vm_properties_public_ip(neo4j_session,vm['id'],update_tag)
        _attach_vm_properties_private_ip(neo4j_session,vm['id'],update_tag)
            
def _attach_vm_properties_public_ip(tx: neo4j.Transaction, vm_id: str,update_tag) ->None:         
    ingest_vm_properties="""    
    MATCH (vm:AzureVirtualMachine{id: $vm_id})-[:MEMBER_NETWORK_INTERFACE]->(:AzureNetworkInterface)-[:MEMBER_PUBLIC_IP_ADDRESS]->(ip:AzurePublicIPAddress)
    SET vm.public_ip=ip.ipAddress,
     vm.lastupdated= $update_tag
    """
    tx.run(
        ingest_vm_properties,
        vm_id=vm_id,
        update_tag=update_tag
    )
def _attach_vm_properties_private_ip(tx: neo4j.Transaction, vm_id: str,update_tag) ->None:         
    ingest_vm_properties="""
    MATCH (vm:AzureVirtualMachine{id: $vm_id})-[:MEMBER_NETWORK_INTERFACE]->(:AzureNetworkInterface)-[:CONTAINS]->(ip:AzureNetworkInterfaceIPConfiguration)
    SET vm.private_ip=ip.private_ip_address,
    vm.lastupdated = $update_tag
    """
    tx.run(
        ingest_vm_properties,
        vm_id=vm_id,
        update_tag=update_tag
    )

def _load_vm_security_groups_relationship(tx: neo4j.Transaction, vm_id: str, data_list: List[Dict], update_tag: int) -> None:
    ingest_vm_sg = """
    UNWIND $sg_list AS sg
    MATCH (sg:AzureNetworkSecurityGroup{id: sg.id})
    WITH sg
    MATCH (v:AzureVirtualMachine{id: $vm_id})
    MERGE (v)-[r:MEMBER_NETWORK_SECURITY_GROUP]->(sg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_vm_sg,
        sg_list=data_list,
        vm_id=vm_id,
        update_tag=update_tag,
    )


def _load_vm_network_interfaces_relationship(tx: neo4j.Transaction, vm_id: str, data_list: List[Dict], update_tag: int) -> None:
    ingest_vm_ni = """
    UNWIND $ni_list AS ni
    MATCH (n:AzureNetworkInterface{id: ni.id})
    WITH n
    MATCH (v:AzureVirtualMachine{id: $vm_id})
    MERGE (v)-[r:MEMBER_NETWORK_INTERFACE]->(n)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    tx.run(
        ingest_vm_ni,
        ni_list=data_list,
        vm_id=vm_id,
        update_tag=update_tag,
    )

def _attach_vm_resource_group(tx: neo4j.Transaction, vm_id: str,resource_group:str, update_tag: int) -> None:
    ingest_vm = """
    match (vm:AzureVirtualMachine{id: $vm_id})
    with vm
    MATCH (res:AzureResourceGroup{name: $resource_group})
    MERGE (vm)-[r:RESOURCE_GROUP]->(res)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    tx.run(
        ingest_vm,
        resource_group=resource_group,
        vm_id=vm_id,
        update_tag=update_tag,
    )
   
    


def get_vm_extensions_list(vm_list: List[Dict], client: ComputeManagementClient, common_job_parameters: Dict) -> List[Dict]:
    try:
        vm_extensions_list: List[Dict] = []
        for vm in vm_list:
            exts = client.virtual_machine_extensions.list(resource_group_name=vm['resource_group'], vm_name=vm['name'])

            if len(exts.value) > 0:
                vm_extensions_list.extend(exts.value)

        exts = []
        for extension in vm_extensions_list:
            exts.append({
                'id': extension.id,
                'resource_group': get_azure_resource_group_name(extension.get('id')),
                'vm_id': extension.id[:extension.id.index("/extensions")],
                'consolelink': azure_console_link.get_console_link(id=vm['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name']),
                'type': extension.type,
                'name': extension.name,
                'location': extension.location,
            })

        return exts

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving virtual machine extensions- {e}")
        return []


def _load_vm_extensions_tx(tx: neo4j.Transaction, vm_extensions_list: List[Dict], update_tag: int) -> None:
    ingest_vm_extension = """
    UNWIND $vm_extensions_list AS extension
    MERGE (v:AzureVirtualMachineExtension{id: extension.id})
    ON CREATE SET v.firstseen = timestamp(), v.location = extension.location,
    v.consolelink = extension.consolelink,
    v.region = extension.location
    SET v.lastupdated = $update_tag, v.name = extension.name,
    v.type = extension.type
    WITH v,extension
    MATCH (owner:AzureVirtualMachine{id: extension.vm_id})
    MERGE (owner)-[r:CONTAIN]->(v)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_vm_extension,
        vm_extensions_list=vm_extensions_list,
        update_tag=update_tag,
    )
    for vm_extension in vm_extensions_list:
        resource_group = get_azure_resource_group_name(vm_extension.get('id'))
        _attach_resource_group_vm_extensions(tx, vm_extension['id'],resource_group, update_tag)
           

def _attach_resource_group_vm_extensions(tx: neo4j.Transaction, vm_extension_id:str,resource_group:str, update_tag: int) -> None:
    ingest_resource_group="""
    MATCH (v:AzureVirtualMachineExtension{id: $vm_extension_id})
    WITH v
    MATCH(rg:AzureResourceGroup{name: $resource_group})
        MERGE (v)-[res:RESOURCE_GROUP]->(rg)
        ON CREATE SET res.firstseen = timestamp()
        SET res.lastupdated = $update_tag
    """
    tx.run(
        ingest_resource_group,
        vm_extension_id=vm_extension_id,
        resource_group=resource_group,
        update_tag=update_tag,
    )

def cleanup_virtual_machine_extensions(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_virtual_machines_extensions_cleanup.json', neo4j_session, common_job_parameters)


def sync_virtual_machine_extensions(
    neo4j_session: neo4j.Session, client: ComputeManagementClient, vm_list: List[Dict], update_tag: int,
    common_job_parameters: Dict,
) -> None:
    vm_extensions_list = get_vm_extensions_list(vm_list, client, common_job_parameters)
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
                size["location"] = vm.get("location", "global")
            vm_available_sizes_list = vm_available_sizes_list + vm_available_size_list

        return vm_available_sizes_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving virtual machine available_sizes - {e}")
        return []


def _load_vm_available_sizes_tx(tx: neo4j.Transaction, vm_available_sizes_list: List[Dict], update_tag: int) -> None:
    ingest_vm_size = """
    UNWIND $vm_available_sizes_list AS size
    MERGE (v:AzureVirtualMachineAvailableSize{id: size.id})
    ON CREATE SET v.firstseen = timestamp(), v.numberOfCores = size.numberOfCores,
    v.location= size.location,v.region= size.location
    SET v.lastupdated = $update_tag, v.osDiskSizeInMB = size.osDiskSizeInMB,
    v.name = size.name,
    v.resourceDiskSizeInMB = size.resourceDiskSizeInMB,
    v.memoryInMB=size.memoryInMB,
    v.maxDataDiskCount=size.maxDataDiskCount
    WITH v,size
    MATCH (owner:AzureVirtualMachine{id: size.vm_id})
    MERGE (owner)-[r:CONTAIN]->(v)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_vm_size,
        vm_available_sizes_list=vm_available_sizes_list,
        update_tag=update_tag,
    )
    for vm_available_size in vm_available_sizes_list:
        resource_group = get_azure_resource_group_name(vm_available_size.get('id'))
        _attach_resource_group_vm_available_size(tx, vm_available_size['id'],resource_group, update_tag)

def _attach_resource_group_vm_available_size(tx: neo4j.Transaction, vm_available_size_id: str,resource_group:str ,update_tag: int) -> None:
    ingest_vm_size = """
    MATCH (v:AzureVirtualMachineAvailableSize{id: $size_id})
    WITH v
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (v)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_vm_size,
        size_id=vm_available_size_id,
        resource_group=resource_group,
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


def get_vm_scale_sets_list(credentials: Credentials, subscription_id: str, regions: list, common_job_parameters: Dict) -> List[Dict]:
    try:
        client = get_client(credentials, subscription_id)
        vm_scale_sets_list = list(map(lambda x: x.as_dict(), client.virtual_machine_scale_sets.list_all()))
        sets_list = []
        for set in vm_scale_sets_list:
            x = set['id'].split('/')
            set['resource_group'] = x[x.index('resourceGroups') + 1]
            set['consolelink'] = azure_console_link.get_console_link(
                id=set['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'])
            if regions is None:
                sets_list.append(set)
            else:
                if set.get('location') in regions or set.get('location') == 'global':
                    sets_list.append(set)
        return sets_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving virtual machines scale_sets_list - {e}")
        return []


def _load_vm_scale_sets_tx(
    tx: neo4j.Transaction, subscription_id: str, vm_scale_sets_list: List[Dict], update_tag: int,
) -> None:
    ingest_scale_set = """
    UNWIND $vm_scale_sets_list AS set
    MERGE (a:AzureVirtualMachineScaleSet{id: set.id})
    ON CREATE SET a.firstseen = timestamp(),
    a.type = set.type,
    a.location = set.location,
    a.region = set.location,
    a.consolelinke = set.consolelink,
    a.resourcegroup = set.resource_group
    SET a.lastupdated = $update_tag,
    a.name = set.name
    WITH a
    MATCH (owner:AzureSubscription{id: $SUBSCRIPTION_ID})
    MERGE (owner)-[r:RESOURCE]->(a)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_scale_set,
        vm_scale_sets_list=vm_scale_sets_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )
    for vm_scale_set in vm_scale_sets_list:
        resource_group = get_azure_resource_group_name(vm_scale_set.get('id'))
        _attach_resource_group_vm_scale_sets(tx,vm_scale_set['id'],resource_group,update_tag) 
    
def _attach_resource_group_vm_scale_sets( tx: neo4j.Transaction, vm_scale_set_id:str,resource_group:str ,update_tag: int) -> None:
    ingest_resource_group="""
        MATCH (a:AzureVirtualMachineScaleSet{id: $set_id})
        with a
        MATCH(rg:AzureResourceGroup{name:$resource_group})
        MERGE (a)-[res:RESOURCE_GROUP]->(rg)
        ON CREATE SET res.firstseen = timestamp()
        SET res.lastupdated = $update_tag
        """ 
    tx.run(
        ingest_resource_group,
        vm_scale_set_id=vm_scale_set_id,
        resource_group=resource_group,
        update_tag=update_tag,
    )

def cleanup_vm_scale_sets(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_virtual_machines_scale_sets_cleanup.json', neo4j_session, common_job_parameters)


def sync_vm_scale_sets(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict, regions: list
) -> None:
    client = get_client(credentials, subscription_id)
    vm_scale_sets_list = get_vm_scale_sets_list(credentials, subscription_id, regions, common_job_parameters)

    if common_job_parameters.get('pagination', {}).get('compute', None):
        pageNo = common_job_parameters.get("pagination", {}).get("compute", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("compute", None)["pageSize"]
        totalPages = len(vm_scale_sets_list) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1
        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for compute vm_scale_sets {pageNo}/{totalPages} pageSize is {pageSize}')
        page_start = (common_job_parameters.get('pagination', {}).get('compute', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('compute', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('compute', {})['pageSize']
        if page_end > len(vm_scale_sets_list) or page_end == len(vm_scale_sets_list):
            vm_scale_sets_list = vm_scale_sets_list[page_start:]
        else:
            has_next_page = True
            vm_scale_sets_list = vm_scale_sets_list[page_start:page_end]
            common_job_parameters['pagination']['compute']['hasNextPage'] = has_next_page

    load_vm_scale_sets(neo4j_session, subscription_id, vm_scale_sets_list, update_tag)
    cleanup_vm_scale_sets(neo4j_session, common_job_parameters)
    sync_virtual_machine_scale_sets_extensions(
        neo4j_session, client, vm_scale_sets_list, update_tag, common_job_parameters,
    )


def get_vm_scale_sets_extensions_list(vm_scale_sets_list: List[Dict], client: ComputeManagementClient, common_job_parameters: Dict) -> List[Dict]:
    try:
        vm_scale_sets_extensions_list: List[Dict] = []
        for set in vm_scale_sets_list:
            extensions_list = list(
                map(
                    lambda x: x.as_dict(), client.virtual_machine_scale_set_extensions.list(
                        resource_group_name=set['resource_group'], vm_scale_set_name=set['name'],
                    ),
                ),
            )
            for extension in extensions_list:
                extension["location"] = set.get("location", "global")
                x = extension['id'].split('/')
                extension['resource_group'] = x[x.index('resourceGroups') + 1]
                extension['set_id'] = extension['id'][:extension['id'].index("/extensions")]
                extension['consolelink'] = azure_console_link.get_console_link(
                    id=extension['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'])

            vm_scale_sets_extensions_list.extend(extensions_list)

        return vm_scale_sets_extensions_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving virtual machine scale set extensions- {e}")
        return []


def _load_vm_scale_sets_extensions_tx(
    tx: neo4j.Transaction, vm_scale_sets_extensions_list: List[Dict], update_tag: int,
) -> None:
    ingest_vm_scale_sets_extension = """
    UNWIND $vm_scale_sets_extensions_list AS extension
    MERGE (v:AzureVirtualMachineScaleSetExtension{id: extension.id})
    ON CREATE SET v.firstseen = timestamp()
    SET v.lastupdated = $update_tag, v.name = extension.name,
    v.location = extension.location,
    v.region = extension.location,
    v.consolelink = extension.consolelink,
    v.type = extension.type
    WITH v,extension
    MATCH (owner:AzureVirtualMachineScaleSet{id: extension.set_id})
    MERGE (owner)-[r:CONTAIN]->(v)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_vm_scale_sets_extension,
        vm_scale_sets_extensions_list=vm_scale_sets_extensions_list,
        update_tag=update_tag,
    )
    for vm_scale_sets_extension in vm_scale_sets_extensions_list:
        resource_group = get_azure_resource_group_name(vm_scale_sets_extension.get('id'))    
        _attach_resource_group_vm_scale_sets_extension(tx,vm_scale_sets_extension['id'],resource_group,update_tag)

    
def  _attach_resource_group_vm_scale_sets_extension(tx: neo4j.Transaction, vm_scale_sets_extension_id:str,resource_group: str, update_tag: int) -> None:
    ingest_vm_scale_sets_extension_resource_group = """
    MATCH (v:AzureVirtualMachineScaleSetExtension{id: $extension_id})
    WITH v
    MATCH(rg:AzureResourceGroup{name: $resource_group})
        MERGE (v)-[res:RESOURCE_GROUP]->(rg)
        ON CREATE SET res.firstseen = timestamp()
        SET res.lastupdated = $update_tag
    """
    tx.run(
        ingest_vm_scale_sets_extension_resource_group,
        extension_id=vm_scale_sets_extension_id,
        resource_group=resource_group,
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
    vm_scale_sets_extensions_list = get_vm_scale_sets_extensions_list(vm_list, client, common_job_parameters)
    load_vm_scale_sets_extensions(neo4j_session, vm_scale_sets_extensions_list, update_tag)
    cleanup_virtual_machine_scale_sets_extensions(neo4j_session, common_job_parameters)


def load_vm_data_disks(neo4j_session: neo4j.Session, vm_id: str, data_disks: List[Dict], update_tag: int) -> None:
    ingest_data_disk = """
    UNWIND $disks AS disk
    MERGE (d:AzureDataDisk{id: disk.managed_disk.id})
    ON CREATE SET d.firstseen = timestamp(), d.lun = disk.lun
    SET d.lastupdated = $update_tag, d.name = disk.name,
    d.vhd = disk.vhd.uri, d.image = disk.image.uri,
    d.location = disk.location,
    d.region = disk.location,
    d.size = disk.disk_size_gb, d.caching = disk.caching,
    d.createoption = disk.create_option, d.write_accelerator_enabled=disk.write_accelerator_enabled,
    d.managed_disk_storage_type=disk.managed_disk.storage_account_type
    WITH d
    MATCH (owner:AzureVirtualMachine{id: $VM_ID})
    MERGE (owner)-[r:ATTACHED_TO]->(d)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
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


def get_disks(credentials: Credentials, subscription_id: str, regions: list, common_job_parameters: Dict) -> List[Dict]:
    try:
        client = get_client(credentials, subscription_id)
        disk_list = list(map(lambda x: x.as_dict(), client.disks.list()))
        disk_data = []
        for disk in disk_list:
            x = disk['id'].split('/')
            disk['resource_group'] = x[x.index('resourceGroups') + 1]
            disk['consolelink'] = azure_console_link.get_console_link(
                id=disk['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'])
            if regions is None:
                disk_data.append(disk)
            else:
                if disk.get('location') in regions or disk.get('location') == 'global':
                    disk_data.append(disk)
        return disk_data

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving disks - {e}")
        return []


def load_disks(neo4j_session: neo4j.Session, subscription_id: str, disk_list: List[Dict], update_tag: int) -> None:
    ingest_disks = """
    UNWIND $disks AS disk
    MERGE (d:AzureDisk{id: disk.id})
    ON CREATE SET d.firstseen = timestamp(),
    d.type = disk.type, d.location = disk.location,
    d.region = disk.location,
    d.consolelink = disk.consolelink,
    d.resourcegroup = disk.resource_group
    SET d.lastupdated = $update_tag, d.name = disk.name,
    d.createoption = disk.creation_data.create_option, d.disksizegb = disk.disk_size_gb,
    d.encryption = disk.encryption_settings_collection.enabled, d.maxshares = disk.max_shares,
    d.network_access_policy = disk.network_access_policy,
    d.ostype = disk.os_type, d.tier = disk.tier,
    d.sku = disk.sku.name, d.zones = disk.zones
    WITH d
    MATCH (owner:AzureSubscription{id: $SUBSCRIPTION_ID})
    MERGE (owner)-[r:RESOURCE]->(d)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag"""

    neo4j_session.run(
        ingest_disks,
        disks=disk_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )
    for disk in disk_list:
        resource_group = get_azure_resource_group_name(disk.get('id'))
        _attach_resource_group_disk(neo4j_session,disk['id'],resource_group,update_tag)
            
def _attach_resource_group_disk(neo4j_session: neo4j.Session, disk_id: str,resource_group:str , update_tag: int) -> None:
    ingest_disks = """
    MATCH (d:AzureDisk{id: $disk_id})
    WITH d
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (d)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    neo4j_session.run(
        ingest_disks,
        disk_id=disk_id,
        resource_group=resource_group,
        update_tag=update_tag,
    )

def cleanup_disks(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_disks_cleanup.json', neo4j_session, common_job_parameters)


def get_snapshots_list(credentials: Credentials, subscription_id: str, regions: list, common_job_parameters: Dict) -> List[Dict]:
    try:
        client = get_client(credentials, subscription_id)
        snapshots = list(map(lambda x: x.as_dict(), client.snapshots.list()))
        snapshot_list = []
        for snapshot in snapshots:
            x = snapshot['id'].split('/')
            snapshot['resource_group'] = x[x.index('resourceGroups') + 1]
            snapshot['consolelink'] = azure_console_link.get_console_link(
                id=snapshot['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'])
            if regions is None:
                snapshot_list.append(snapshot)
            else:
                if snapshot.get('location') in regions or snapshot.get('location') == 'global':
                    snapshot_list.append(snapshot)
        return snapshot_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving snapshots - {e}")
        return []


def load_snapshots(neo4j_session: neo4j.Session, subscription_id: str, snapshots: List[Dict], update_tag: int) -> None:
    ingest_snapshots = """
    UNWIND $snapshots as snapshot
    MERGE (s:AzureSnapshot{id: snapshot.id})
    ON CREATE SET s.firstseen = timestamp(),
    s.resourcegroup = snapshot.resource_group,
    s.type = snapshot.type, s.location = snapshot.location,
    s.consolelink = snapshot.consolelink,
    s.region = snapshot.location
    SET s.lastupdated = $update_tag, s.name = snapshot.name,
    s.createoption = snapshot.creation_data.create_option, s.disksizegb = snapshot.disk_size_gb,
    s.encryption = snapshot.encryption_settings_collection.enabled, s.incremental = snapshot.incremental,
    s.network_access_policy = snapshot.network_access_policy, s.ostype = snapshot.os_type,
    s.tier = snapshot.tier, s.sku = snapshot.sku.name
    WITH s
    MATCH (owner:AzureSubscription{id: $SUBSCRIPTION_ID})
    MERGE (owner)-[r:RESOURCE]->(s)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag"""

    neo4j_session.run(
        ingest_snapshots,
        snapshots=snapshots,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )
    for snapshot in snapshots:
        resource_group = get_azure_resource_group_name(snapshot.get('id'))
        _attach_resource_group_disk_snapshot(neo4j_session,snapshot['id'],resource_group,update_tag)

def _attach_resource_group_disk_snapshot(neo4j_session: neo4j.Session, snapshot_id: str, resource_group:str, update_tag: int) -> None:
    ingest_snapshots = """
    MATCH (s:AzureSnapshot{id: $snapshot_id})
    WITH s
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (s)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    neo4j_session.run(
        ingest_snapshots,
        snapshot_id=snapshot_id,
        resource_group=resource_group,
        update_tag=update_tag,
    )

def cleanup_snapshot(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_snapshots_cleanup.json', neo4j_session, common_job_parameters)


def sync_virtual_machine(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict, regions: list
) -> None:
    client = get_client(credentials, subscription_id)
    vm_list = get_vm_list(credentials, subscription_id, regions, common_job_parameters)

    if common_job_parameters.get('pagination', {}).get('compute', None):
        pageNo = common_job_parameters.get("pagination", {}).get("compute", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("compute", None)["pageSize"]
        totalPages = len(vm_list) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1
        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for compute vm {pageNo}/{totalPages} pageSize is {pageSize}')
        page_start = (common_job_parameters.get('pagination', {}).get('compute', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('compute', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('compute', {})['pageSize']
        if page_end > len(vm_list) or page_end == len(vm_list):
            vm_list = vm_list[page_start:]
        else:
            has_next_page = True
            vm_list = vm_list[page_start:page_end]
            common_job_parameters['pagination']['compute']['hasNextPage'] = has_next_page

    load_vms(neo4j_session, subscription_id, vm_list, update_tag)
    cleanup_virtual_machine(neo4j_session, common_job_parameters)
    sync_virtual_machine_extensions(neo4j_session, client, vm_list, update_tag, common_job_parameters)
    # sync_virtual_machine_available_sizes(neo4j_session, client, vm_list, update_tag, common_job_parameters)


def sync_disk(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict, regions: list
) -> None:
    disk_list = get_disks(credentials, subscription_id, regions, common_job_parameters)

    if common_job_parameters.get('pagination', {}).get('compute', None):
        pageNo = common_job_parameters.get("pagination", {}).get("compute", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("compute", None)["pageSize"]
        totalPages = len(disk_list) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1
        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for compute disk {pageNo}/{totalPages} pageSize is {pageSize}')
        page_start = (common_job_parameters.get('pagination', {}).get('compute', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('compute', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('compute', {})['pageSize']
        if page_end > len(disk_list) or page_end == len(disk_list):
            disk_list = disk_list[page_start:]
        else:
            has_next_page = True
            disk_list = disk_list[page_start:page_end]
            common_job_parameters['pagination']['compute']['hasNextPage'] = has_next_page

    load_disks(neo4j_session, subscription_id, disk_list, update_tag)
    cleanup_disks(neo4j_session, common_job_parameters)


def sync_snapshot(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict, regions: list
) -> None:
    snapshots = get_snapshots_list(credentials, subscription_id, regions, common_job_parameters)

    if common_job_parameters.get('pagination', {}).get('compute', None):
        pageNo = common_job_parameters.get("pagination", {}).get("compute", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("compute", None)["pageSize"]
        totalPages = len(snapshots) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1
        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for compute snapshots {pageNo}/{totalPages} pageSize is {pageSize}')
        page_start = (common_job_parameters.get('pagination', {}).get('compute', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('compute', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('compute', {})['pageSize']
        if page_end > len(snapshots) or page_end == len(snapshots):
            snapshots = snapshots[page_start:]
        else:
            has_next_page = True
            snapshots = snapshots[page_start:page_end]
            common_job_parameters['pagination']['compute']['hasNextPage'] = has_next_page

    load_snapshots(neo4j_session, subscription_id, snapshots, update_tag)
    cleanup_snapshot(neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict, regions: list
) -> None:
    logger.info("Syncing VM for subscription '%s'.", subscription_id)

    sync_virtual_machine(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters, regions)
    sync_vm_scale_sets(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters, regions)
    sync_disk(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters, regions)
    sync_snapshot(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters, regions)
