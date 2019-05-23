# Cartography - Google Cloud Platform Schema

## Table of contents

- [GCPOrganization](#gcporganization)
- [GCPFolder](#gcpfolder)
- [GCPProject](#gcpproject)
- [GCPInstance](#gcpinstance)

## GCPOrganization

Representation of a GCP [Organization](https://cloud.google.com/resource-manager/reference/rest/v1/organizations) object.


| Field | Description |
|-------|--------------| 
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated | 
| id | The name of the GCP Organization, e.g. "organizations/1234" |
| displayname | The "friendly name", e.g. "My Company"
| lifecyclestate | The organization's current lifecycle state. Assigned by the server.  See the [official docs](https://cloud.google.com/resource-manager/reference/rest/v1/organizations#LifecycleState).

### Relationships

- GCPOrganizations contain GCPFolders.

    ```
    (GCPOrganization)-[RESOURCE]->(GCPFolder)
    ```
    
- GCPOrganizations can contain GCPProjects.

    ```
    (GCPOrganization)-[RESOURCE]->(GCPProjects)
    ```

 ## GCPFolder
 
 Representation of a GCP [Folder](https://cloud.google.com/resource-manager/reference/rest/v2/folders).  An additional helpful reference is the [Google Compute Platform resource hierarchy](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy).

| Field | Description |
|-------|--------------| 
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated | 
| id | The name of the folder, e.g. "folders/1234"|
| displayname | A friendly name of the folder, e.g. "My Folder".
| lifecyclestate | The folder's current lifecycle state. Assigned by the server.  See the [official docs](https://cloud.google.com/resource-manager/reference/rest/v2/folders#LifecycleState).
 
 
 ### Relationships
 
 - GCPOrganizations are parents of GCPFolders.

    ```
    (GCPOrganization)<-[PARENT]-(GCPFolder)
    ```
    
 - GCPFolders can contain GCPProjects
 
    ```
    (GCPFolder)-[RESOURCE]->(GCPProject)
    ```
    
 - GCPFolders can contain other GCPFolders.
 
    ```
    (GCPFolder)-[RESOURCE]->(GCPFolder)
    ```
 
 ## GCPProject
 
 Representation of a GCP [Project](https://cloud.google.com/resource-manager/reference/rest/v1/projects).  An additional helpful reference is the [Google Compute Platform resource hierarchy](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy).

| Field | Description |
|-------|--------------| 
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated | 
| id | The ID of the project, e.g. "sys-12345"|
| displayname | A friendly name of the project, e.g. "MyProject".
| lifecyclestate | The project's current lifecycle state. Assigned by the server.  See the [official docs](https://cloud.google.com/resource-manager/reference/rest/v1/projects#LifecycleState).
 
 ### Relationships
     
- GCPOrganizations contain GCPProjects.

    ```
    (GCPOrganization)-[RESOURCE]->(GCPProjects)
    ```
       
 - GCPFolders can contain GCPProjects
 
    ```
    (GCPFolder)-[RESOURCE]->(GCPProject)
    ```
    
 ## GCPInstance
 
 Representation of a GCP [Instance](https://cloud.google.com/compute/docs/reference/rest/v1/instances).  Additional references can be found in the [official documentation]( https://cloud.google.com/compute/docs/concepts).
 
 | Field | Description |
|-------|--------------| 
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated | 
| id | The server-defined unique identifier of the instance, usually all numbers
| displayname | The friendly name of the instance, e.g. "my-instance"
| hostname | If present, the hostname of the instance
| zone_name | The zone that the instance is installed on

### Relationships

- GCPInstances are resources of GCPProjects.

    ```
    (GCPProject)-[RESOURCE]->(GCPInstance)
    ``` 