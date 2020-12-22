import logging
from azure.mgmt.compute import ComputeManagementClient
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)




def get_client(credentials,subscription_id):
    client=ComputeManagementClient(credentials,subscription_id)
    return client


def get_vm_list(credentials,subscription_id):

    try:
    
        client = get_client(credentials,subscription_id)

        VM_List=client.virtual_machines.list_all()

        return VM_List
    
    except Exception as e:

            print(f'Failed to retrieve virtual machine: {e}')

            return []



def load_vm_data(neo4j_session,subscription_id,VM_group,azer_updated_tag,common_job_parameters):

    ingest_vm="""

    MERGE (Machines:VirtualMachine{id: {Vm_id}})
    ON CREATE SET Machines.firstseen = timestamp(), Machines.id = {id}, Machines.name = {name},
    Machines.location = {location},
    SET Machines.lastupdated = {azer_updated_tag}, Machines.type = {type}, Machines.size = {size},
    Machines.Vm_disk_OS_size = {osSize},
    Machines.Vm_disk_OS_type = {osType}
    WITH Machines
    MATCH (owner:AzureAccount{id: {AZURE_SUBSCRIPTION_ID}})
    MERGE (owner)-[r:RESOURCE]->(Machines)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azer_updated_tag}
    """

    for data in VM_group:
        neo4j_session.run( ingest_vm,
            osSize=data['properties']["storageProfile"]['osDisk']['diskSizeGB'],
            osType=data['properties']["storageProfile"]['osDisk']['osType'],
            size=data['properties']['hardwareProfile']["vmSize"],
            type=data['type'],
            location=data['location'],
            id=data['id'],
            name=data['name'],
            AZURE_SUBSCRIPTION_ID=subscription_id,
            azure_update_tag=azer_updated_tag,
        ).azure_update_tag=azer_updated_tag

def cleanup_virtual_machine(neo4j_session, common_job_parameters):
    run_cleanup_job('azure_import_virtual_machine_cleanup.json', neo4j_session, common_job_parameters)

    
def get_security_group_list(credentials,subscription_id):
    client = get_client(credentials,subscription_id)
    security_groups=list(client.network_security_group.list_all())
    return security_groups


def load_security_group_info(neo4j_session,subscription_id,groups,azure_update_tag,common_job_parameters):
    ingest_security_group = """
    MERGE (group:Network_SecurityGroup{id: {GroupId}})
    ON CREATE SET group.firstseen = timestamp(), group.groupid = {GroupId}
    SET group.name = {GroupName}, group.location = {location},
    group.lastupdated = {azure_update_tag}
    WITH group
    MATCH (aa:zureSubscription{id: {AZURE_SUBSCRIPTION_ID}})
    MERGE (aa)-[r:RESOURCE]->(group)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
   
    """

    for group in groups:
        group_id = group["id"]

        neo4j_session.run(
            ingest_security_group,
            GroupId=group_id,
            GroupName=group.get("name"),
            location=group.get('location'),
            AZURE_SUBSCRIPTION_ID=subscription_id,
           azure_update_tag=azure_update_tag,
        )
def cleanup_network_security_group(neo4j_session, common_job_parameters):
    run_cleanup_job('azure_import_network_security_group_cleanup.json', neo4j_session, common_job_parameters)

def get_virtual_network_group(credentials,subscription_id):
    client = get_client(credentials,subscription_id)
    virtual_networks=list(client.virtual_network.list_all())
    return virtual_networks

def load_virtual_network_data(neo4j_session,credentials,virtualNetworkList,subscription_id,azure_update_tag,common_job_parameters):
    ingest_virtual_network="""
    MERGE (virtualNetwork:Azure_virtualnetwork{id: {id}})
    ON CREATE SET virtualNetwork.firstseen = timestamp(), virtualNetwork.vpcid ={id}
    SET virtualNetwork.name= {name},
    virtualNetwork.type = {type},
    virtualNetwork.location = {location},
    virtualNetwork.etag= {etag},
    virtualNetwork.lastupdated = {azure_update_tag}
    WITH virtualNetwork
    MATCH (owner:AzureAccount{id: {subscription_id}})
    MERGE (owner)-[r:RESOURCE]->(virtualNetwork)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}"""


    for virtualNetwork in virtualNetworkList:

        neo4j_session.run(ingest_virtual_network,
        name=virtualNetwork.get('name'),
        id=virtualNetwork.get('id'),
        type=virtualNetwork.get('type'),
        location=virtualNetwork.get('location'),
        etag=virtualNetwork.get('etag'),
        virtualNetworkPeerings=virtualNetwork['properties']['virtualNetworkPeerings'],
        AZURE_SUBSCRIPTION_ID=subscription_id,
        azure_update_tag=azure_update_tag,      
        )
def cleanup_virtual_network(neo4j_session, common_job_parameters):
    run_cleanup_job('azure_import_virtual_network_cleanup.json', neo4j_session, common_job_parameters)


def get_network_interface_group(credentials,subscription_id):
    client = get_client(credentials,subscription_id)
    networkInterfaceList=list(client.network_interface.list_all())
    return networkInterfaceList

def load_network_interface_data(neo4j_session,subscription_id,networkInterfaceGroup,azure_update_tag,common_job_parameters):

    ingest_network_interface="""
    MERGE (NetworkInterface:Azure_networkInterface{id: {id}})
    ON CREATE SET NetworkInterface.firstseen = timestamp(), virtualNetwork.id ={id}
    SET NetworkInterface.name= {name},
    NetworkInterface.type = {type},
    NetworkInterface.location = {location},
    NetworkInterface.etag= {etag},
    NetworkInterface.macAddress= {macAddress},
    NetworkInterface.networkSecurityGroupId={networkSecurityGroupId}
    NetworkInterface.lastupdated = {azure_update_tag}
    WITH NetworkInterface
    MATCH (owner:AzureAccount{id: {subscription_id}})
    MERGE (owner)-[r:RESOURCE]->(NetworkInterface)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}"""


    for networkInterface in networkInterfaceGroup:
        
        neo4j_session.run(ingest_network_interface,
        name=networkInterface.get('name'),
        id=networkInterface.get('id'),
        type=networkInterface.get('type'),
        location=networkInterface.get('location'),
        etag=networkInterface.get('etag'),
        macAddress=networkInterface.get('macAddress'),
        networkSecurityGroupId=networkInterface['properties']['macAddress']['networkSecurityGroup']['id'],
        AZURE_SUBSCRIPTION_ID=subscription_id,
        azure_update_tag=azure_update_tag,      
     
        )
def cleanup_network_interface(neo4j_session, common_job_parameters):
    run_cleanup_job('azure_import_network_interface_cleanup.json', neo4j_session, common_job_parameters)

def get_disks(credentials,subscription_id):
    client = get_client(credentials,subscription_id)
    diskList=list(client.disks.list_all())
    return diskList

def loadDisksData(neo4j_session,subscription_id,diskList,azure_update_tag,common_job_parameters):

    ingest_compute_disks="""
    MERGE (Disks:Compute_disk{id: {id}})
    ON CREATE SET Disks.firstseen = timestamp(), Disks.id ={id}
    SET Disks.name= {name},
    Disks.type = {type},
    Disks.location = {location},
    Disks.lastupdated = {azure_update_tag},
    Disks.skuName={skuName},
    Disks.osType={osType},
    Disks.diskSize={diskSize},
    Disks.diskState={diskState},
    Disks.diskTier={diskTier}
    WITH Disks
    MATCH (owner:AzureAccount{id: {subscription_id}})
    MERGE (owner)-[r:RESOURCE]->(Disks)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}"""



    for disk in diskList:
        neo4j_session.run(ingest_compute_disks,
        name=disk.get('name'),
        id=disk.get('id'),
        type=disk.get('type'),
        location=disk.get('location'),
        skuName=disk['sku']['name'],
        osType=disk['properties']['osType'],
        diskSize=disk['properties']['diskSizeGB'],
        diskState=disk['properties']['diskState'],
        diskTier=disk['properties']['tier'],
        AZURE_SUBSCRIPTION_ID=subscription_id,
        azure_update_tag=azure_update_tag,      
     
        )

def cleanup_Disks(neo4j_session, common_job_parameters):
    run_cleanup_job('azure_import_compute_disks_cleanup.json', neo4j_session, common_job_parameters)


def getSnaoshotList(credentials,subscription_id):
    client = get_client(credentials,subscription_id)
    snapshotList=list(client.snapshots.list())
    return snapshotList

def load_snapshotData(neo4j_session,subscription_id,snapshotList,azure_update_tag,common_job_parameters):


    ingest_compute_disks="""
    MERGE (Snapshot:Compute_snapshot{id: {id}})
    ON CREATE SET Snapshot.firstseen = timestamp(), Disks.id ={id}
    SET Snapshot.name= {name},
    Snapshot.type = {type},
    Snapshot.location = {location},
    Snapshot.lastupdated = {azure_update_tag},
    Snapshot.osType={osType},
    Snapshot.diskSize={diskSize},
    Snapshot.timeCreated={timeCreated},
    WITH Disks
    MATCH (owner:AzureAccount{id: {subscription_id}})
    MERGE (owner)-[r:RESOURCE]->(Disks)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}"""



    for snapshot in snapshotList:
        neo4j_session.run(ingest_compute_disks,
        name=snapshot.get('name'),
        id=snapshot.get('id'),
        type=snapshot.get('type'),
        location=snapshot.get('location'),
        osType=snapshot['properties']['osType'],
        diskSize=snapshot['properties']['diskSizeGB'],
        timeCreated=snapshot['properties']['timeCreated'],
        AZURE_SUBSCRIPTION_ID=subscription_id,
        azure_update_tag=azure_update_tag,      
     
        )

def cleanup_snapshot(neo4j_session, common_job_parameters):
    run_cleanup_job('azure_import_snapshot_cleanup.json', neo4j_session, common_job_parameters)

def sync_snapshot(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters):

    snapshotList=getSnaoshotList(credentials,subscription_id)
    load_snapshotData(neo4j_session,subscription_id,snapshotList,sync_tag,common_job_parameters)
    cleanup_snapshot(neo4j_session, common_job_parameters)
    
def sync_disk(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters):

    diskList=get_disks(credentials,subscription_id)
    loadDisksData(neo4j_session,subscription_id,diskList,sync_tag,common_job_parameters)
    cleanup_network_interface(neo4j_session, common_job_parameters)
   


def sync_network_interface(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters):
    networkInterfaceGroup=get_network_interface_group(credentials,subscription_id)
    load_network_interface_data(neo4j_session,subscription_id,networkInterfaceGroup,sync_tag,common_job_parameters)
    cleanup_network_interface(neo4j_session, common_job_parameters)

def sync_virtual_network(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters):

    virtualNetworkList=get_virtual_network_group(credentials,subscription_id)
    load_virtual_network_data(neo4j_session,credentials,virtualNetworkList,subscription_id,sync_tag,common_job_parameters)
    cleanup_virtual_network(neo4j_session, common_job_parameters)


def sync_network_security_group(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters):
    groups=get_security_group_list(credentials,subscription_id)
    load_security_group_info(neo4j_session,subscription_id,groups,sync_tag,common_job_parameters)
    cleanup_network_security_group(neo4j_session, common_job_parameters)
  
    


def sync_virtual_machine(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters):
    vm_list=get_vm_list(credentials,subscription_id)
    load_vm_data(neo4j_session, subscription_id, vm_list,sync_tag, common_job_parameters)
    cleanup_virtual_machine(neo4j_session, common_job_parameters)


    


def sync(neo4j_session, credentials,location, subscription_id, sync_tag, common_job_parameters):
    # TODO: start Azure VM's sync
    #print('inside azure vm sync')
    logger.info("Syncing VM for subscription '%s'.", subscription_id)

    sync_virtual_machine(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters)
    sync_virtual_network(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters)
    sync_network_interface(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters)
    sync_network_security_group(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters)
    sync_disk(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters)
    sync_snapshot(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters)


