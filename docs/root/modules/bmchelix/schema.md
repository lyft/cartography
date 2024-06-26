## BMC Helix Schema

.. _bmchelix_schema:

### BMC Helix platform

Representation of a device identified in BMC Helix Discovery, either as [host node](https://docs.bmc.com/docs/discovery/daas/host-node-838555811.html) (credential scanning), either as a [VirtualMachine node](https://docs.bmc.com/docs/discovery/daas/virtualmachine-node-838555852.html) (API like Azure, Vmware ESX...).

| Field | Description |
|-------|-------------|
|tool_first_seen| Timestamp of when first available logs for host is available since first sync|
|tool_last_seen| Timestamp of when last available logs for host is available per last sync|
|lastupdated| Timestamp of the last time the node was updated|
|**hostname**| The Hostname Computer name|
|short_hostname| The short hostname, lowercase|
|bmchelix_uuid| UUID from BMC Helix, may differ from other UUID like Azure|
|platform_name| BMC Helix vm_os_type|
|os| BMC Helix vm_os|
|hw_vendor| BMC Helix hw_vendor|
|virtual| BMC Helix virtual|
|cloud| BMC Helix cloud|
|vm_power_state| BMC Helix vm_power_state|
|instance_id| BMC Helix instance_id (for ex, Azure)|
|subscription_id| BMC Helix subscription_id|
|resource_group| BMC Helix resource_group|
|resource_id| BMC Helix resource_id|
|tags_costcenter| BMC Helix tags_costcenter|
|tags_engcontact| BMC Helix tags_engcontact|
|tags_businesscontact| BMC Helix tags_businesscontact|
