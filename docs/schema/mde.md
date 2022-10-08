# Cartography - MDE (Microsoft Defender for Endpoint) Schema

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Table of contents

- [MdeHost](#mdehost)

## MdeHost

Placeholder representation of a single [MDE Host or machine](https://docs.microsoft.com/en-us/microsoft-365/security/defender-endpoint/get-machines?view=o365-worldwide). This node is the minimal data necessary to map an asset.

Warning! Work In Progress.

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| mde_id | MDE id |
| instance_id | [Azure VM InstanceId](https://azure.microsoft.com/en-us/blog/accessing-and-using-azure-vm-unique-id/) if applicable (vmMetadata.vmId) |
| subscription_id | Azure subscriptionid (vmMetadata.subscriptionId) |
| resource_id | Azure resourceid (vmMetadata.resourceId) |
| status | MDE status |
| hostname | MDE computerDnsName |
| machine_domain | MDE machine_domain,
| mde_first_seen | host.firstSeen |
| mde_last_seen | MDE lastSeen |
| platform_name | MDE osPlatform |
| os_version | MDE osVersion |
| cpu_signature | MDE osProcessor |
| agent_version | MDE agentVersion |
| local_ip | MDE lastIpAddress |
| external_ip | MDE lastExternalIpAddress |
| mde_healthstatus | MDE healthStatus |
| mde_devicevalue | MDE deviceValue |
| mde_riskscore | MDE riskScore |
| mde_exposurelevel | MDE exposureLevel |
| mde_isadjoined | MDE isAadJoined |
| mde_aaddeviceid | MDE aadDeviceId |
| mde_machinetags | MDE machineTags |
| mde_defenderavstatus | MDE defenderAvStatus |
| mde_onboardingstatus | MDE onboardingStatus |
| mde_osarchitecture | MDE osArchitecture |
| mde_managedby | MDE managedBy |
| mde_managedbystatus | MDE managedByStatus |

### Relationships

TBD
* Azure Tenant contains one or more Mde Hosts.
```
(AzureTenant)-[RESOURCE]->(MdeHost)
```
* Azure Subscription contains one or more Mde Hosts.
```
(AzureSubscription)-[RESOURCE]->(MdeHost)
```
* Azure Virtual Machine is one single Mde Host.
* Similarly for other cloud providers and Onpremises.