# Cartography - Microsoft Azure Schema

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [AzureTenant](#azuretenant)
  - [Relationships](#relationships)
- [AzurePrincipal](#azureprincipal)
  - [Relationships](#relationships-1)
- [AzureSubscription](#azuresubscription)
  - [Relationships](#relationships-2)
- [VirtualMachine](#virtualmachine)
  - [Relationships](#relationships-3)
- [AzureDataDisk](#azuredatadisk)
  - [Relationships](#relationships-4)
- [AzureDisk](#azuredisk)
  - [Relationships](#relationships-5)
- [AzureSnapshot](#azuresnapshot)
  - [Relationships](#relationships-6)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->


## AzureTenant

Representation of an [Azure Tenant](https://docs.microsoft.com/en-us/rest/api/resources/Tenants/List).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The Azure Tenant ID number|

### Relationships

- Azure Principal is part of the Azure Account.

        ```
        (AzureTenant)-[RESOURCE]->(AzurePrincipal)
        ```

## AzurePrincipal

Representation of an [Azure Principal](https://docs.microsoft.com/en-us/graph/api/resources/user?view=graph-rest-1.0)..

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**email**| Email of the Azure Principal|

### Relationships

- Azure Principal is part of the Azure Account.

        ```
        (AzurePrincipal)-[RESOURCE]->(AzureTenant)
        ```

## AzureSubscription

Representation of an [Azure Subscription](https://docs.microsoft.com/en-us/rest/api/resources/subscriptions)..

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The Azure Subscription ID number|
|name | The friendly name that identifies the subscription|
|path | The full ID for the Subscription|
|state| Can be one of `Enabled | Disabled | Deleted | PastDue | Warned`|

### Relationships

- Azure Tenant contains one or more Subscriptions.

        ```
        (AzureTenant)-[RESOURCE]->(AzureSubscription)
        ```

## VirtualMachine

Representation of an [Azure Virtual Machine](https://docs.microsoft.com/en-us/rest/api/compute/virtualmachines).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The Azure Virtual Machine ID number|
|type | The type of the resource|
|location | The location where Virtual Machine is created|
|resourcegroup | The Resource Group where Virtual Machine is created|
|name | The friendly name that identifies the Virtual Machine|
|plan | The plan associated with the Virtual Machine|
|size | The size of the Virtual Machine|
|license_type | The type of license|
|computer_name | The computer name|
|identity_type | The type of identity used for the virtual machine|
|zones | The Virtual Machine zones|
|ultra_ssd_enabled | Enables or disables a capability on the virtual machine or virtual machine scale set.|
|priority | Specifies the priority for the virtual machine|
|eviction_policy | Specifies the eviction policy for the Virtual Machine|

### Relationships

- Azure Subscription contains one or more Virtual Machines.

        ```
        (AzureSubscription)-[RESOURCE]->(VirtualMachine)
        ```

## AzureDataDisk

Representation of an [Azure Data Disk](https://docs.microsoft.com/en-us/rest/api/compute/virtualmachines/get#datadisk).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The Azure Data Disk ID number|
|lun | Specifies the logical unit number of the data disk|
|name | The data disk name|
|vhd | The virtual hard disk associated with data disk|
|image | The source user image virtual hard disk|
|size | The size of the disk in GB|
|caching | Specifies the caching requirement|
|createoption | Specifies how the disk should be created|
|write_accelerator_enabled | Specifies whether writeAccelerator should be enabled or disabled on the data disk|
|managed_disk_storage_type | The data disk storage type|

### Relationships

- Azure Virtual Machines are attached to Data Disks.

        ```
        (VirtualMachine)-[ATTACHED_TO]->(AzureDataDisk)
        ```

## AzureDisk

Representation of an [Azure Disk](https://docs.microsoft.com/en-us/rest/api/compute/disks).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The Azure Disk ID number|
|type | The type of the resource|
|location | The location where Disk is created|
|resourcegroup | The Resource Group where Disk is created|
|name | The friendly name that identifies the Disk|
|createoption | Specifies how the disk should be created|
|disksizegb | The size of the disk in GB|
|encryption | Specifies whether the disk has encryption enabled |
|maxshares | Specifies how many machines can share the disk|
|ostype | The operating system type of the disk|
|tier | Performance Tier associated with the disk|
|sku | The disk sku name|
|zones | The logical zone list for disk|

### Relationships

- Azure Subscription contains one or more Disks.

        ```
        (AzureSubscription)-[RESOURCE]->(AzureDisk)
        ```

## AzureSnapshot

Representation of an [Azure Snapshot](https://docs.microsoft.com/en-us/rest/api/compute/snapshots).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The Azure Snapshot ID number|
|type | The type of the resource|
|location | The location where snapshot is created|
|resourcegroup | The Resource Group where snapshot is created|
|name | The friendly name that identifies the snapshot|
|createoption | Specifies how the disk should be created|
|disksizegb | The size of the snapshot in GB|
|encryption | Specifies whether the snapshot has encryption enabled |
|incremental | Indicates whether a snapshot is incremental or not |
|network_access_policy | Policy for accessing the snapshot via network|
|ostype | The operating system type of the snapshot|
|tier | Performance Tier associated with the snapshot|
|sku | The snapshot sku name|
|zones | The logical zone list for snapshot|

### Relationships

- Azure Subscription contains one or more Snapshots.

        ```
        (AzureSubscription)-[RESOURCE]->(AzureSnapshot)
        ```

## AzureDatabaseAccount

Representation of an [AzureDatabaseAccount](https://docs.microsoft.com/en-us/rest/api/cosmos-db-resource-provider/2020-04-01/databaseaccounts).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The unique resource identifier of the ARM resource.|
|location | The location of the resource group to which the resource belongs.|
|resourcegroup | The Resource Group where the database account is created.|
|name | The name of the ARM resource.|
|kind | Indicates the type of database account.|
|type | The type of Azure resource.|
|ipranges | List of IpRules.|
|capabilities | List of Cosmos DB capabilities for the account.|
|documentendpoint | The connection endpoint for the Cosmos DB database account.|
|virtualnetworkfilterenabled | Flag to indicate whether to enable/disable Virtual Network ACL rules.|
|enableautomaticfailover | Enables automatic failover of the write region in the rare event that the region is unavailable due to an outage.|
|provisioningstate | The status of the Cosmos DB account at the time the operation was called.|
|multiplewritelocations | Enables the account to write in multiple locations.|
|accountoffertype | The offer type for the Cosmos DB database account.|
|publicnetworkaccess | Whether requests from Public Network are allowed.|
|enablecassandraconnector | Enables the cassandra connector on the Cosmos DB C* account.|
|connectoroffer | The cassandra connector offer type for the Cosmos DB database C* account.|
|disablekeybasedmetadatawriteaccess | Disable write operations on metadata resources (databases, containers, throughput) via account keys.|
|keyvaulturi | The URI of the key vault.|
|enablefreetier | Flag to indicate whether Free Tier is enabled.|
|enableanalyticalstorage | Flag to indicate whether to enable storage analytics.|
|defaultconsistencylevel | The default consistency level and configuration settings of the Cosmos DB account.|
|maxstalenessprefix | When used with the Bounded Staleness consistency level, this value represents the number of stale requests tolerated.|
|maxintervalinseconds | When used with the Bounded Staleness consistency level, this value represents the time amount of staleness (in seconds) tolerated.|

### Relationships

- Azure Subscription contains one or more database accounts.

        ```
        (AzureSubscription)-[RESOURCE]->(AzureDatabaseAccount)
        ```
- Azure Database Account has write permissions from, read permissions from and is associated with Azure CosmosDB 
  Locations.

        ```
        (AzureDatabaseAccount)-[WRITE_PERMISSIONS_FROM]->(AzureCosmosDBLocation)
        ```
        (AzureDatabaseAccount)-[READ_PERMISSIONS_FROM]->(AzureCosmosDBLocation)
        ```
        (AzureDatabaseAccount)-[ASSOCIATED_WITH]->(AzureCosmosDBLocation)
        ```
- Azure Database Account contains one or more Cors Policy.

        ```
        (AzureDatabaseAccount)-[CONTAINS]->(AzureCosmosDBCorsPolicy)
        ```
- Azure Database Account contains one or more failover policies.

        ```
        (AzureDatabaseAccount)-[CONTAINS]->(AzureDatabaseAccountFailoverPolicy)
        ```
- Azure Database Account is configured with one or more private endpoint connections.

        ```
        (AzureDatabaseAccount)-[CONFIGURED_WITH]->(AzureCDBPrivateEndpointConnection)
        ```
- Azure Database Account is configured with one or more virtual network rules.

        ```
        (AzureDatabaseAccount)-[CONFIGURED_WITH]->(AzureCosmosDBVirtualNetworkRule)
        ```
- Azure Database Account contains one or more SQL databases.

        ```
        (AzureDatabaseAccount)-[CONTAINS]->(AzureCosmosDBSqlDatabase)
        ```
- Azure Database Account contains one or more Cassandra keyspace.

        ```
        (AzureDatabaseAccount)-[CONTAINS]->(AzureCosmosDBCassandraKeyspace)
        ```
- Azure Database Account contains one or more MongoDB Database.

        ```
        (AzureDatabaseAccount)-[CONTAINS]->(AzureCosmosDBMongoDBDatabase)
        ```
- Azure Database Account contains one or more table resource.

        ```
        (AzureDatabaseAccount)-[CONTAINS]->(AzureCosmosDBTableResource)
        ```

## AzureCosmosDBLocation

Representation of an Azure CosmosDB Location.

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The unique identifier of the region within the database account.|
|locationname | The name of the region.|
|documentendpoint | The connection endpoint for the specific region.|
|provisioningstate | The status of the Cosmos DB account at the time the operation was called.|
|failoverpriority | The failover priority of the region.|
|iszoneredundant | Flag to indicate whether or not this region is an AvailabilityZone region.|

### Relationships

- Azure Database Account has write permissions from, read permissions from and is associated with Azure CosmosDB 
  Locations.

        ```
        (AzureDatabaseAccount)-[WRITE_PERMISSIONS_FROM]->(AzureCosmosDBLocation)
        ```
        (AzureDatabaseAccount)-[READ_PERMISSIONS_FROM]->(AzureCosmosDBLocation)
        ```
        (AzureDatabaseAccount)-[ASSOCIATED_WITH]->(AzureCosmosDBLocation)
        ```

## AzureCosmosDBCorsPolicy

Representation of an Azure Cosmos DB Cors Policy.

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The unique resource identifier for Cors Policy.|
|allowedorigins | The origin domains that are permitted to make a request against the service via CORS.|
|allowedmethods | The methods (HTTP request verbs) that the origin domain may use for a CORS request.|
|allowedheaders | The request headers that the origin domain may specify on the CORS request.|
|exposedheaders | The response headers that may be sent in the response to the CORS request and exposed by the browser to the request issuer.|
|maxageinseconds | The maximum amount time that a browser should cache the preflight OPTIONS request.|

### Relationships

- Azure Database Account contains one or more Cors Policy.

        ```
        (AzureDatabaseAccount)-[CONTAINS]->(AzureCosmosDBCorsPolicy)
        ```

## AzureDatabaseAccountFailoverPolicy

Representation of an Azure Database Account Failover Policy.

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The unique identifier of the region in which the database account replicates to.|
|locationname | The name of the region in which the database account exists.|
|failoverpriority | The failover priority of the region. A failover priority of 0 indicates a write region.|

### Relationships

- Azure Database Account contains one or more failover policies.

        ```
        (AzureDatabaseAccount)-[CONTAINS]->(AzureDatabaseAccountFailoverPolicy)
        ```

## AzureCDBPrivateEndpointConnection

Representation of an Azure Cosmos DB Private Endpoint Connection.

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| Fully qualified resource Id for the resource.|
|name | The name of the resource.|
|privateendpointid | Resource id of the private endpoint.|
|status | The private link service connection status.|
|actionrequired | Any action that is required beyond basic workflow (approve/ reject/ disconnect).|

### Relationships

- Azure Database Account is configured with one or more private endpoint connections.

        ```
        (AzureDatabaseAccount)-[CONFIGURED_WITH]->(AzureCDBPrivateEndpointConnection)
        ```

## AzureCosmosDBVirtualNetworkRule

Representation of an Azure Cosmos DB Virtual Network Rule.

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| Resource ID of a subnet.|
|ignoremissingvnetserviceendpoint | Create firewall rule before the virtual network has vnet service endpoint enabled.|

### Relationships

- Azure Database Account is configured with one or more virtual network rules.

        ```
        (AzureDatabaseAccount)-[CONFIGURED_WITH]->(AzureCosmosDBVirtualNetworkRule)
        ```

## AzureCosmosDBSqlDatabase

Representation of an [AzureCosmosDBSqlDatabase](https://docs.microsoft.com/en-us/rest/api/cosmos-db-resource-provider/2020-04-01/sqlresources).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The unique resource identifier of the ARM resource.|
|name | The name of the ARM resource.|
|type| The type of Azure resource.|
|location| The location of the resource group to which the resource belongs.|
|throughput| Value of the Cosmos DB resource throughput or autoscaleSettings.|
|maxthroughput| Represents maximum throughput, the resource can scale up to.|

### Relationships

- Azure Database Account contains one or more SQL databases.

        ```
        (AzureDatabaseAccount)-[CONTAINS]->(AzureCosmosDBSqlDatabase)
        ```
- SQL Databases contain one or more SQL containers.

        ```
        (AzureCosmosDBSqlDatabase)-[CONTAINS]->(AzureCosmosDBSqlContainer)
        ```

## AzureCosmosDBCassandraKeyspace

Representation of an [AzureCosmosDBCassandraKeyspace](https://docs.microsoft.com/en-us/rest/api/cosmos-db-resource-provider/2020-04-01/cassandraresources).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The unique resource identifier of the ARM resource.|
|name | The name of the ARM resource.|
|type| The type of Azure resource.|
|location| The location of the resource group to which the resource belongs.|
|throughput| Value of the Cosmos DB resource throughput or autoscaleSettings.|
|maxthroughput| Represents maximum throughput, the resource can scale up to.|

### Relationships

- Azure Database Account contains one or more Cassandra keyspace.

        ```
        (AzureDatabaseAccount)-[CONTAINS]->(AzureCosmosDBCassandraKeyspace)
        ```
- Cassandra Keyspace contains one or more Cassandra tables.

        ```
        (AzureCosmosDBCassandraKeyspace)-[CONTAINS]->(AzureCosmosDBCassandraTable)
        ```

## AzureCosmosDBMongoDBDatabase

Representation of an [AzureCosmosDBMongoDBDatabase](https://docs.microsoft.com/en-us/rest/api/cosmos-db-resource-provider/2020-04-01/mongodbresources).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The unique resource identifier of the ARM resource.|
|name | The name of the ARM resource.|
|type| The type of Azure resource.|
|location| The location of the resource group to which the resource belongs.|
|throughput| Value of the Cosmos DB resource throughput or autoscaleSettings.|
|maxthroughput| Represents maximum throughput, the resource can scale up to.|

### Relationships

- Azure Database Account contains one or more MongoDB Database.

        ```
        (AzureDatabaseAccount)-[CONTAINS]->(AzureCosmosDBMongoDBDatabase)
        ```
- MongoDB database contains one or more MongoDB collections.

        ```
        (AzureCosmosDBMongoDBDatabase)-[CONTAINS]->(AzureCosmosDBMongoDBCollection)
        ```

## AzureCosmosDBTableResource

Representation of an [AzureCosmosDBTableResource](https://docs.microsoft.com/en-us/rest/api/cosmos-db-resource-provider/2020-04-01/tableresources).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The unique resource identifier of the ARM resource.|
|name | The name of the ARM resource.|
|type| The type of Azure resource.|
|location| The location of the resource group to which the resource belongs.|
|throughput| Value of the Cosmos DB resource throughput or autoscaleSettings.|
|maxthroughput| Represents maximum throughput, the resource can scale up to.|

### Relationships

- Azure Database Account contains one or more table resource.

        ```
        (AzureDatabaseAccount)-[CONTAINS]->(AzureCosmosDBTableResource)
        ```

## AzureCosmosDBSqlContainer

Representation of an [AzureCosmosDBSqlContainer](https://docs.microsoft.com/en-us/rest/api/cosmos-db-resource-provider/2020-04-01/sqlresources).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The unique resource identifier of the ARM resource.|
|name | The name of the ARM resource.|
|type| The type of Azure resource.|
|location| The location of the resource group to which the resource belongs.|
|throughput| Value of the Cosmos DB resource throughput or autoscaleSettings.|
|maxthroughput| Represents maximum throughput, the resource can scale up to.|
|container| Name of the Cosmos DB SQL container.|
|defaultttl| Default time to live.|
|analyticalttl| Specifies the Analytical TTL.|
|isautomaticindexingpolicy| Indicates if the indexing policy is automatic.|
|indexingmode|  Indicates the indexing mode.|
|conflictresolutionpolicymode| Indicates the conflict resolution mode.|

### Relationships

- SQL Databases contain one or more SQL containers.

        ```
        (AzureCosmosDBSqlDatabase)-[CONTAINS]->(AzureCosmosDBSqlContainer)
        ```

## AzureCosmosDBCassandraTable

Representation of an [AzureCosmosDBCassandraTable](https://docs.microsoft.com/en-us/rest/api/cosmos-db-resource-provider/2020-04-01/cassandraresources).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The unique resource identifier of the ARM resource.|
|name | The name of the ARM resource.|
|type| The type of Azure resource.|
|location| The location of the resource group to which the resource belongs.|
|throughput| Value of the Cosmos DB resource throughput or autoscaleSettings.|
|maxthroughput| Represents maximum throughput, the resource can scale up to.|
|container| Name of the Cosmos DB Cassandra table.|
|defaultttl| Time to live of the Cosmos DB Cassandra table.|
|analyticalttl| Specifies the Analytical TTL.|

### Relationships

- Cassandra Keyspace contains one or more Cassandra tables.

        ```
        (AzureCosmosDBCassandraKeyspace)-[CONTAINS]->(AzureCosmosDBCassandraTable)
        ```

## AzureCosmosDBMongoDBCollection

Representation of an [AzureCosmosDBMongoDBCollection](https://docs.microsoft.com/en-us/rest/api/cosmos-db-resource-provider/2020-04-01/mongodbresources).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The unique resource identifier of the ARM resource.|
|name | The name of the ARM resource.|
|type| The type of Azure resource.|
|location| The location of the resource group to which the resource belongs.|
|throughput| Value of the Cosmos DB resource throughput or autoscaleSettings.|
|maxthroughput| Represents maximum throughput, the resource can scale up to.|
|collectionname| Name of the Cosmos DB MongoDB collection.|
|analyticalttl| Specifies the Analytical TTL.|

### Relationships

- MongoDB database contains one or more MongoDB collections.

        ```
        (AzureCosmosDBMongoDBDatabase)-[CONTAINS]->(AzureCosmosDBMongoDBCollection)
        ```
