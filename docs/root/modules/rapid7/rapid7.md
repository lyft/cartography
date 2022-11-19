# Cartography - Rapid7 InsightVM Schema

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Table of contents

- [Rapid7Host](#rapid7host)

## Rapid7Host

Placeholder representation of a single [Rapid7 Host or asset](https://help.rapid7.com/insightvm/en-us/api/index.html#operation/getAssets). This node is the minimal data necessary to map an asset.

For report, you can use [SQL Query Export](https://docs.rapid7.com/insightvm/creating-reports-based-on-sql-queries/) like
```
select da.asset_id,da.mac_address,da.ip_address,da.host_name,da.operating_system_id,da.sites,da.last_assessed_for_vulnerabilities,fa.scan_started,fa.scan_finished,fa.vulnerabilities,fa.critical_vulnerabilities,fa.moderate_vulnerabilities,fa.vulnerability_instances,fa.riskscore,fa.pci_status,dos.asset_type,dos.description,dos.vendor,dos.family,dos.name,dos.version,dos.architecture,dos.system,dos.cpe,daui.source,daui.unique_id
FROM dim_asset da
JOIN fact_asset fa USING (asset_id)
JOIN dim_operating_system dos USING (operating_system_id)
JOIN dim_asset_unique_id daui USING (asset_id)
```

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| r7_id | id |
| r7_assessedForPolicies | assessedForPolicies |
| r7_assessedForVulnerabilities | assessedForVulnerabilities |
| hostname | hostName |
| short_hostname | short hostname, lowercase|
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
| r7_architecture | osFingerprint_architecture |
| r7_os_product | osFingerprint_product |
| r7_os_version | osFingerprint_version |
| r7_vulnerabilities_critical | vulnerabilities_critical |
| r7_vulnerabilities_exploits | vulnerabilities_exploits |
| r7_vulnerabilities_malwareKits | vulnerabilities_malwareKits |
| r7_vulnerabilities_moderate | vulnerabilities_moderate |
| r7_vulnerabilities_severe | vulnerabilities_severe |
| r7_vulnerabilities_total | vulnerabilities_total |
| r7_type | type |
| r7_sites | sites |
| cloud_provider | cloud_provider |
| instance_id | instance_id |
| subscription_id | subscription_id |
| resource_id | resource_id |
| resource_group | resource_group |

### Relationships

* Azure Virtual Machine is one single Rapid7 Host, based on resource_id if available.
```
(AzureVirtualMachine-[PRESENT_IN]->(Rapid7Host)
```
