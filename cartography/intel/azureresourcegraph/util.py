"""
cartography/intel/azureresourcegraph/util
"""
# pylint: disable=invalid-name,broad-except
import json
import logging
import re
from array import array
from typing import Dict

import azure.mgmt.resourcegraph as arg
import pandas
from azure.identity import ChainedTokenCredential
from azure.identity import ClientSecretCredential
from azure.identity import ManagedIdentityCredential
from azure.mgmt.resource import SubscriptionClient


logger = logging.getLogger(__name__)


def get_authorization(
    client_id: str,
    client_secret: str,
    tenant_id: str,
    logging_enable: bool = True,
    managedidentity_enable: str = "False",
) -> str:
    """
    Get Authentication token

    https://learn.microsoft.com/en-us/python/api/overview/azure/identity-readme?view=azure-python
    """
    logger.warning(
        "get_authorization inputs: client_id %s, tenant_id %s, logging_enabled %s, managedidentity_enable %s",
        client_id,
        tenant_id,
        logging_enable,
        managedidentity_enable,
    )
    azure_token = None
    if managedidentity_enable.lower() == "true":
        try:
            # Azure Resource Managed Identity
            managed_identity = ManagedIdentityCredential(logging_enable=logging_enable)
            logger.warning("Using Managed identity: %s", managed_identity)
            return managed_identity
        except TypeError as exc:
            logger.exception("Exception: %s", exc)
    # try:
    #     # Get your credentials from Azure CLI (development only!) and get your subscription list
    #     # `az login` first
    #     azure_cli = AzureCliCredential()
    #     logger.warning("Using Azure CLI identity: %s", azure_cli)
    #     return azure_cli
    # except TypeError as exc:
    #     logger.exception("Exception: %s", exc)
    try:
        # App registration token
        logger.info(
            "ClientSecretCredential: tenant %s, client %s",
            tenant_id,
            client_id,
        )
        azure_token = ClientSecretCredential(tenant_id, client_id, client_secret)
        logger.warning("Using App registration identity: %s", azure_token)
        return azure_token
    except TypeError as exc:
        logger.exception("Exception: %s", exc)

    try:
        credential_chain = ChainedTokenCredential(managed_identity, azure_token)
        # credential_chain = ChainedTokenCredential(managed_identity, azure_cli)
        logger.warning("Using ChainedTokenCredential identity: %s", credential_chain)
        return credential_chain
    except TypeError as exc:
        logger.exception("Exception: %s", exc)

    return ""


def get_short_hostname(row: Dict) -> str:
    """
    Get short_hostname
    With extra restrictions
    if ostype Windows, 15 characters max
    if others, 64 characters max
    """
    short = re.sub(r"\..*$", "", row["name"].lower())
    if row["ostype"] == "Windows":
        return short[:15]
    return short[:64]


def azureresourcegraph_hosts(
    authorization: str,
    timeout_max: int = 300,
) -> array:
    """
    Get Azure Resource Graph coverage inventory

    https://docs.microsoft.com/en-us/azure/governance/resource-graph/first-query-python
    """

    vm_query = (
        r"""resources
| where type =~ 'Microsoft.Compute/virtualMachines'
| join kind=inner (resourcecontainers
    | where type == 'microsoft.resources/subscriptions'
    | project subscriptionId, subscriptionName = name, subproperties = properties
    ) on subscriptionId
| extend instance_id = properties.vmId
| extend resourceid = id
| extend vmStatus = properties.extended.instanceView.powerState.displayStatus
| extend osname = properties.osProfile.computerName
| extend ostype = properties.storageProfile.osDisk.osType
| extend image_publisher = properties.storageProfile.imageReference.publisher
| extend image_offer = properties.storageProfile.imageReference.offer
| extend image_sku = properties.storageProfile.imageReference.sku
| extend image_galleryid = properties.storageProfile.imageReference.id
| join kind=leftouter (
    Resources
    | where type =~ "Microsoft.Network/networkInterfaces"
    | mv-expand properties.ipConfigurations
    | where isnotempty(properties_ipConfigurations.properties.publicIPAddress.id)
    | extend publicIpId = tostring(properties_ipConfigurations.properties.publicIPAddress.id)
    | join (
        Resources
        | where type =~ "microsoft.network/publicipaddresses"
        ) on $left.publicIpId == $right.id
    | extend ipAddress = tostring(properties1.ipAddress)
    | extend publicIPAllocationMethod = tostring(properties1.publicIPAllocationMethod)
    | extend publicIpName = tostring(name1)
    | extend vmId = tostring(properties.virtualMachine.id)
    | extend nsgId = tostring(properties.networkSecurityGroup.id)
    | project publicIpName,publicIPAllocationMethod,ipAddress,vmId,nsgId
    ) on $left.id == $right.vmId
| project resourceid,instance_id,subscriptionId,subscriptionName, resourceGroup, name, type, """
        "osname, ostype, vmStatus, tags.environment, tags.costcenter, tags.contact, "
        "tags.businessproduct, tags.businesscontact, tags.engproduct, tags.engcontact, "
        "tags.lob, tags.compliance, tags.ticket, subproperties,publicIpName,"
        "publicIPAllocationMethod,ipAddress,nsgId,"
        "image_publisher,image_offer,image_sku,image_galleryid"
    )

    subsClient = SubscriptionClient(authorization)
    subsRaw = []
    for sub in subsClient.subscriptions.list():
        subsRaw.append(sub.as_dict())
    subsList = []
    for sub in subsRaw:
        subsList.append(sub.get("subscription_id"))

    # Create Azure Resource Graph client and set options
    argClient = arg.ResourceGraphClient(authorization)
    # https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/resources/
    #   azure-mgmt-resourcegraph/azure/mgmt/resourcegraph/models/_models_py3.py#L543
    # argQueryOptions = arg.models.QueryRequestOptions(result_format="objectArray")
    argQueryOptions = arg.models.QueryRequestOptions(result_format="table")

    # Create query
    argQuery = arg.models.QueryRequest(
        subscriptions=subsList,
        query=vm_query,
        options=argQueryOptions,
    )

    # Run query
    argResults = argClient.resources(argQuery)

    # Show Python object
    # return argResults

    # https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/resources/
    #   azure-mgmt-resourcegraph/azure/mgmt/resourcegraph/models/_models_py3.py#L612
    df_resourcegraph = pandas.DataFrame(
        argResults.data["rows"],
        columns=[item["name"] for item in argResults.data["columns"]],
    )

    while argResults.total_records - 1 > df_resourcegraph.shape[0] + 100:
        logger.info("Paging %s/%s", df_resourcegraph.shape[0], argResults.total_records)
        argQueryOptions2 = arg.models.QueryRequestOptions(
            result_format="table",
            skip_token=argResults.skip_token,
            skip=df_resourcegraph.shape[0],
        )
        argQuery2 = arg.models.QueryRequest(
            subscriptions=subsList,
            query=vm_query,
            options=argQueryOptions2,
        )
        argResults2 = argClient.resources(argQuery2)
        df_resourcegraph_tmp = pandas.DataFrame(
            argResults2.data["rows"],
            columns=[item["name"] for item in argResults2.data["columns"]],
        )
        if not df_resourcegraph_tmp.empty:
            df_resourcegraph = pandas.concat([df_resourcegraph, df_resourcegraph_tmp])

    logger.info(
        "ARG Final count %s/%s",
        df_resourcegraph.shape[0],
        argResults.total_records,
    )
    logger.warning(
        "ARG Final count %s/%s",
        df_resourcegraph.shape[0],
        argResults.total_records,
    )

    df_resourcegraph["short_hostname"] = df_resourcegraph.apply(
        get_short_hostname,
        axis=1,
    )

    flatten_data = json.loads(df_resourcegraph.to_json(orient="records"))
    logger.debug("Example: %s", flatten_data[0])
    logger.warning("Example: %s", flatten_data[0])

    # save to local csv for debugging?
    # df_resourcegraph.to_csv("/tmp/cartography-resourcegraph.csv")

    return flatten_data
