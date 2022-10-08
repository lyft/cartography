# Cartography - Rapid7 InsightVM Schema

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Table of contents

- [Rapid7Host](#rapid7host)

## Rapid7Host

Placeholder representation of a single [Rapid7 Host or asset](https://help.rapid7.com/insightvm/en-us/api/index.html#operation/getAssets). This node is the minimal data necessary to map an asset.

Warning! Work In Progress.


| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| r7_id | id |
| r7_assessedForPolicies | assessedForPolicies |
| r7_assessedForVulnerabilities | assessedForVulnerabilities |
| hostname | hostName |
| r7_ip | ip |
| r7_mac | mac address |
| r7_os | os |
| r7_rawriskscore | rawRiskScore |
| r7_riskscore | riskScore |
| r7_type | type |
| r7_addresses | addresses |
| r7_configurations | configurations |
| r7_databases | databases |
| r7_files | files |
| r7_history | history |
| r7_hostnames | hostNames |
| r7_ids | ids |
| r7_links | links |
| r7_osfingerprint | osFingerprint |
| r7_services | services |
| r7_software | software |
| r7_usergroups | userGroups |
| r7_users | users |
| r7_vulnerabilities | vulnerabilities |

### Relationships

TBD
* Azure Tenant contains one or more Rapid7 Hosts.
```
(AzureTenant)-[RESOURCE]->(Rapid7Host)
```
* Azure Subscription contains one or more Rapid7 Hosts.
```
(AzureSubscription)-[RESOURCE]->(Rapid7Host)
```
* Azure Virtual Machine is one single Rapid7 Host.
* Similarly for other cloud providers and Onpremises.
