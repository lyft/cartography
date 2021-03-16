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
- [AzureStorageAccount](#azurestorageaccount)
  - [Relationships](#relationships-7)
- [AzureStorageQueueService](#azurestoragequeueservice)
  - [Relationships](#relationships-8)
- [AzureStorageTableService](#azurestoragetableservice)
  - [Relationships](#relationships-9)
- [AzureStorageFileService](#azurestoragefileservice)
  - [Relationships](#relationships-10)
- [AzureStorageBlobService](#azurestorageblobservice)
  - [Relationships](#relationships-11)
- [AzureStorageQueue](#azurestoragequeue)
  - [Relationships](#relationships-12)
- [AzureStorageTable](#azurestoragetable)
  - [Relationships](#relationships-13)
- [AzureStorageFileShare](#azurestoragefileshare)
  - [Relationships](#relationships-14)
- [AzureStorageBlobContainer](#azurestorageblobcontainer)
  - [Relationships](#relationships-15)

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

## AzureStorageAccount

Representation of an [AzureStorageAccount](https://docs.microsoft.com/en-us/rest/api/storagerp/storageaccounts).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| Fully qualified resource ID for the resource.|
|type | The type of the resource.|
|location | The geo-location where the resource lives.|
|resourcegroup | The Resource Group where the storage account is created|
|name | The name of the resource.|
|kind | Gets the Kind of the resource.|
|creationtime | Gets the creation date and time of the storage account in UTC.|
|hnsenabled | Specifies if the Account HierarchicalNamespace is enabled.|
|primarylocation | Gets the location of the primary data center for the storage account.|
|secondarylocation | Gets the location of the geo-replicated secondary for the storage account.|
|provisioningstate | Gets the status of the storage account at the time the operation was called.|
|statusofprimary | Gets the status availability status of the primary location of the storage account.|
|statusofsecondary | Gets the status availability status of the secondary location of the storage account.|
|supportshttpstrafficonly | Allows https traffic only to storage service if sets to true.|

### Relationships

- Azure Subscription contains one or more Storage Accounts.

        ```
        (AzureSubscription)-[RESOURCE]->(AzureStorageAccount)
        ```
- Azure Storage Accounts uses one or more Queue Services.

        ```
        (AzureStorageAccount)-[USES]->(AzureStorageQueueService)
        ```
- Azure Storage Accounts uses one or more Table Services.

        ```
        (AzureStorageAccount)-[USES]->(AzureStorageTableService)
        ```
- Azure Storage Accounts uses one or more File Services.

        ```
        (AzureStorageAccount)-[USES]->(AzureStorageFileService)
        ```
- Azure Storage Accounts uses one or more Blob Services.

        ```
        (AzureStorageAccount)-[USES]->(AzureStorageBlobService)
        ```

## AzureStorageQueueService

Representation of an [AzureStorageQueueService](https://docs.microsoft.com/en-us/rest/api/storagerp/queueservices).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| Fully qualified resource ID for the resource.|
|type | The type of the resource.|
|name | The name of the queue service.|

### Relationships

- Azure Storage Accounts uses one or more Queue Services.

        ```
        (AzureStorageAccount)-[USES]->(AzureStorageQueueService)
        ```
- Queue Service contains one or more queues.

        ```
        (AzureStorageQueueService)-[CONTAINS]->(AzureStorageQueue)
        ```

## AzureStorageTableService

Representation of an [AzureStorageTableService](https://docs.microsoft.com/en-us/rest/api/storagerp/tableservices).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| Fully qualified resource ID for the resource.|
|type | The type of the resource.|
|name | The name of the table service.|

### Relationships

- Azure Storage Accounts uses one or more Table Services.

        ```
        (AzureStorageAccount)-[USES]->(AzureStorageTableService)
        ```
- Table Service contains one or more tables.

        ```
        (AzureStorageTableService)-[CONTAINS]->(AzureStorageTable)
        ```

## AzureStorageFileService

Representation of an [AzureStorageFileService](https://docs.microsoft.com/en-us/rest/api/storagerp/fileservices).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| Fully qualified resource ID for the resource.|
|type | The type of the resource.|
|name | The name of the file service.|

### Relationships

- Azure Storage Accounts uses one or more File Services.

        ```
        (AzureStorageAccount)-[USES]->(AzureStorageFileService)
        ```
- Table Service contains one or more file shares.

        ```
        (AzureStorageFileService)-[CONTAINS]->(AzureStorageFileShare)
        ```

## AzureStorageBlobService

Representation of an [AzureStorageBlobService](https://docs.microsoft.com/en-us/rest/api/storagerp/blobservices).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| Fully qualified resource ID for the resource.|
|type | The type of the resource.|
|name | The name of the blob service.|

### Relationships

- Azure Storage Accounts uses one or more Blob Services.

        ```
        (AzureStorageAccount)-[USES]->(AzureStorageBlobService)
        ```
- Blob Service contains one or more blob containers.

        ```
        (AzureStorageBlobService)-[CONTAINS]->(AzureStorageBlobContainer)
        ```

## AzureStorageQueue

Representation of an [AzureStorageQueue](https://docs.microsoft.com/en-us/rest/api/storagerp/queue).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| Fully qualified resource ID for the resource.|
|type | The type of the resource.|
|name | The name of the queue.|

### Relationships

- Queue Service contains one or more queues.

        ```
        (AzureStorageQueueService)-[CONTAINS]->(AzureStorageQueue)
        ```

## AzureStorageTable

Representation of an [AzureStorageTable](https://docs.microsoft.com/en-us/rest/api/storagerp/table).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| Fully qualified resource ID for the resource.|
|type | The type of the resource.|
|name | The name of the table resource.|
|tablename | Table name under the specified account.|

### Relationships

- Table Service contains one or more tables.

        ```
        (AzureStorageTableService)-[CONTAINS]->(AzureStorageTable)
        ```

## AzureStorageFileShare

Representation of an [AzureStorageFileShare](https://docs.microsoft.com/en-us/rest/api/storagerp/fileshares).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| Fully qualified resource ID for the resource.|
|type | The type of the resource.|
|name | The name of the resource.|
|lastmodifiedtime | Specifies the date and time the share was last modified.|
|sharequota | The maximum size of the share, in gigabytes.|
|accesstier | Specifies the access tier for the share.|
|deleted | Indicates whether the share was deleted.|
|accesstierchangetime | Indicates the last modification time for share access tier.|
|accesstierstatus | Indicates if there is a pending transition for access tier.|
|deletedtime | The deleted time if the share was deleted.|
|enabledprotocols | The authentication protocol that is used for the file share.|
|remainingretentiondays | Remaining retention days for share that was soft deleted.|
|shareusagebytes | The approximate size of the data stored on the share.|
|version | The version of the share.|

### Relationships

- File Service contains one or more file shares.

        ```
        (AzureStorageTableService)-[CONTAINS]->(AzureStorageFileShare)
        ```

## AzureStorageBlobContainer

Representation of an [AzureStorageBlobContainer](https://docs.microsoft.com/en-us/rest/api/storagerp/blobcontainers).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| Fully qualified resource ID for the resource.|
|type | The type of the resource.|
|name | The name of the resource.|
|deleted | Indicates whether the blob container was deleted.|
|deletedtime | Blob container deletion time.|
|defaultencryptionscope | Default the container to use specified encryption scope for all writes.|
|publicaccess | Specifies whether data in the container may be accessed publicly and the level of access.|
|leasestatus | The lease status of the container.|
|leasestate | Lease state of the container.|
|lastmodifiedtime | Specifies the date and time the container was last modified.|
|remainingretentiondays | Specifies the remaining retention days for soft deleted blob container.|
|version | The version of the deleted blob container.|
|hasimmutabilitypolicy | Specifies the if the container has an ImmutabilityPolicy or not.|
|haslegalhold | Specifies if the container has any legal hold tags.|
|leaseduration | Specifies whether the lease on a container is of infinite or fixed duration, only when the container is leased.|

### Relationships

- Blob Service contains one or more blob containers.

        ```
        (AzureStorageBlobService)-[CONTAINS]->(AzureStorageBlobContainer)
        ```
