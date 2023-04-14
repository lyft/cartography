## Azure Resource Graph Schema

.. _azureresourcegraph_schema:

### Azure Resource Graph platform

Representation of a virtualmachines type resource from [Azure Resource Graph](https://learn.microsoft.com/en-us/azure/governance/resource-graph/overview).

| Field | Description |
|-------|-------------|
|tool_first_seen| Timestamp of when first available logs for host is available since first sync|
|tool_last_seen| Timestamp of when last available logs for host is available per last sync|
|lastupdated| Timestamp of the last time the node was updated|
|**hostname**| The Hostname Computer name|
|short_hostname| The short hostname, lowercase|
|instance_id| Azure instance_id|
|resource_id| Azure resource_id|
|subscription_id| Azure subscription_id|
|subscription_name| Azure subscription_name|
|resource_group| Azure resource_group|
|type| Azure type|
|osname| Azure osname|
|ostype| Azure ostype|
|vm_status| Azure vm_status|
|image_publisher| Azure image_publisher|
|image_offer| Azure image_offer|
|image_sku| Azure image_sku|
|image_galleryid| Azure image_galleryid|
|public_ip_name| Azure public_ip_name|
|public_ip_allocation_method| Azure public_ip_allocation_method|
|public_ip| Azure public_ip|
|nsg_id| Azure nsg_id|
|tags_costcenter| Azure tag costcenter|
|tags_engcontact| Azure tag engcontact|
|tags_businesscontact| Azure tag businesscontact|
|tags_environment| Azure tag environment|
