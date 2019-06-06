# Cartography - Google Cloud Platform Schema

## Table of contents

- [GCPOrganization](#gcporganization)
- [GCPFolder](#gcpfolder)
- [GCPProject](#gcpproject)
- [GCPInstance](#gcpinstance)
- [GCPNetworkInterface](#gcpnetworkinterface)
- [GCPVpc](#gcpvpc) 
- [GCPNicAccessConfig](#gcpnicaccessconfig)
- [GCPSubnet](#gcpsubnet)


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
    
- GCPVpcs are part of GCPProjects 

    ```
    (GCPProject)-[RESOURCE]->(GCPVpc)
    ```

    
 ## GCPInstance
 
 Representation of a GCP [Instance](https://cloud.google.com/compute/docs/reference/rest/v1/instances).  Additional references can be found in the [official documentation]( https://cloud.google.com/compute/docs/concepts).
 
 | Field | Description |
|-------|--------------| 
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated | 
| id | The partial resource URI representing this instance. Has the form `projects/{project_name}/zones/{zone_name}/instances/{instance_name}`. |
| partial_uri | Same as `id` above. |
| self_link | The full resource URI representing this instance. Has the form `https://www.googleapis.com/compute/v1/{partial_uri}` |
| instancename | The name of the instance, e.g. "my-instance" |
| zone_name | The zone that the instance is installed on |
| hostname | If present, the hostname of the instance |

### Relationships

- GCPInstances are resources of GCPProjects.

    ```
    (GCPProject)-[RESOURCE]->(GCPInstance)
    ```
    
- GCPNetworkInterfaces are attached to GCPInstances

    ```
    (GCPInstance)-[NETWORK_INTERFACE]->(GCPNetworkInterface)
    ```
 
    
## GCPVpc

Representation of a GCP [VPC](https://cloud.google.com/compute/docs/reference/rest/v1/networks/).  In GCP documentation this is also known simply as a "Network" object.

| Field | Description |
|-------|--------------| 
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated | 
| id | The partial resource URI representing this VPC.  Has the form `projects/{project_name}/global/networks/{vpc name}`.
| partial_uri | Same as `id` |
| self_link | The full resource URI representing this VPC. Has the form `https://www.googleapis.com/compute/v1/{partial_uri}` |
| name | The name of the VPC |
| project_id | The project ID that this VPC belongs to |
| auto_create_subnetworks | When set to true, the VPC network is created in "auto" mode. When set to false, the VPC network is created in "custom" mode.  An auto mode VPC network starts with one subnet per region. Each subnet has a predetermined range as described in [Auto mode VPC network IP ranges](https://cloud.google.com/vpc/docs/vpc#ip-ranges). |
| routing_confg_routing_mode | The network-wide routing mode to use. If set to REGIONAL, this network's Cloud Routers will only advertise routes with subnets of this network in the same region as the router. If set to GLOBAL, this network's Cloud Routers will advertise routes with all subnets of this network, across regions. |
| description | A description for the VPC |

### Relationships

- GCPVpcs are part of projects 

    ```
    (GCPProject)-[RESOURCE]->(GCPVpc)
    ```

- GCPVpcs contain GCPSubnets 

    ```
    (GCPVpc)-[RESOURCE]->(GCPSubnet)
    ```

- GCPSubnets are part of GCP VPCs

    ```
    (GCPVpc)-[RESOURCE]->(GCPSubnet)
    ```

    
## GCPNetworkInterface

Representation of a GCP Instance's [network interface](https://cloud.google.com/compute/docs/reference/rest/v1/instances/list) (scroll down to the fields on "networkInterface").

| Field | Description |
|-------|--------------| 
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated | 
| id | A partial resource URI representing this network interface.  Note: GCP does not define a partial resource URI for network interfaces, so we create one so we can uniquely identify GCP network interfaces.  Has the form `projects/{project_name}/zones/{zone_name}/instances/{instance_name}/networkinterfaces/{network interface name}`.
| partial_uri | Same as `id` |
| name | The name of the network interface |
| private_ip | The private IP address of this network interface.  This IP is valid on the network interface's VPC. |

### Relationships

- GCPNetworkInterfaces are attached to GCPInstances

    ```
    (GCPInstance)-[NETWORK_INTERFACE]->(GCPNetworkInterface)
    ```

- GCPNetworkInterfaces are connected to GCPSubnets

    ```
    (GCPNetworkInterface)-[PART_OF_SUBNET]->(GCPSubnet)
    ```
    
- GCPNetworkInterfaces have GCPNicAccessConfig objects defined on them

    ```
    (GCPNetworkInterface)-[RESOURCE]->(GCPNicAccessConfig)
    ```


## GCPNicAccessConfig

Representation of the AccessConfig object on a GCP Instance's [network interface](https://cloud.google.com/compute/docs/reference/rest/v1/instances/list) (scroll down to the fields on "networkInterface").

| Field | Description |
|-------|--------------| 
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated | 
| id | A partial resource URI representing this AccessConfig.  Note: GCP does not define a partial resource URI for AccessConfigs, so we create one so we can uniquely identify GCP network interface access configs.  Has the form `projects/{project_name}/zones/{zone_name}/instances/{instance_name}/networkinterfaces/{network interface name}/accessconfigs/{access config type}`.
| partial_uri | Same as `id` |
| type | The type of configuration. GCP docs say: "The default and only option is ONE_TO_ONE_NAT." |
| name | The name of this access configuration. The default and recommended name is External NAT, but you can use any arbitrary string, such as My external IP or Network Access. |
| public_ip | The external IP associated with this instance |
| set_public_ptr | Specifies whether a public DNS 'PTR' record should be created to map the external IP address of the instance to a DNS domain name. |
| public_ptr_domain_name | The DNS domain name for the public PTR record. You can set this field only if the setPublicPtr field is enabled. |
| network_tier | This signifies the networking tier used for configuring this access configuration and can only take the following values: PREMIUM, STANDARD. |

### Relationships

- GCPNetworkInterfaces have GCPNicAccessConfig objects defined on them

    ```
    (GCPNetworkInterface)-[RESOURCE]->(GCPNicAccessConfig)
    ```

## GCPSubnet

Representation of a GCP [Subnetwork](https://cloud.google.com/compute/docs/reference/rest/v1/subnetworks).

| Field | Description |
|-------|--------------| 
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated | 
| id | A partial resource URI representing this Subnet.  Has the form `projects/{project}/regions/{region}/subnetworks/{subnet name}`.
| partial_uri | Same as `id` |
| self_link | The full resource URI representing this subnet. Has the form `https://www.googleapis.com/compute/v1/{partial_uri}` |
| project_id | The project ID that this Subnet belongs to | 
| name | The name of this Subnet |
| region | The region of this Subnet |
| gateway_address | Gateway IP address of this Subnet |
| ip_cidr_range | The CIDR range covered by this Subnet |
| vpc_partial_uri | The partial URI of the VPC that this Subnet is a part of | 
| private_ip_google_access | Whether the VMs in this subnet can access Google services without assigned external IP addresses. This field can be both set at resource creation time and updated using setPrivateIpGoogleAccess. |

### Relationships

- GCPSubnets are part of GCP VPCs

    ```
    (GCPVpc)-[RESOURCE]->(GCPSubnet)
    ```
    
- GCPNetworkInterfaces are connected to GCPSubnets

    ```
    (GCPNetworkInterface)-[PART_OF_SUBNET]->(GCPSubnet)
    ```
