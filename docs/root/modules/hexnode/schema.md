## Hexnode Schema

.. _hexnode_schema:


### Human

Hexnode use Human node as pivot with other Identity Providers (GSuite, GitHub ...)

Human nodes are not created by Hexnode module, link is made using analysis job.


#### Relationships

- Human as an access to Hexnode
    ```
    (Human)-[IDENTITY_HEXNODE]->(HexnodeUser)
    ```

### HexnodeUser

Representation of a single User in Hexnode

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | Hexnode ID |
| name | User full name |
| email | User email |
| phone | User phone number |
| domain | Source for the user (local, gsuite ...) |

#### Relationships

- HexnodeUser owns HexnodeDevice

    ```
    (HexnodeUser)-[OWNS_DEVICE]->(HexnodeDevice)
    ```

### HexnodeDevice

Representation of a single Employee in Hexnode

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | Hexnode device ID |
| name | Device name |
| model_name | Device model name |
| os_name | Device OS name |
| os_version | Device OS version |
| enrolled_time | Date when device was enrolled |
| last_reported | Date when agent last reported to MDM console |
| compliant | Device is compliant with all policies |
| serial_number | Device serial number |
| udid | Unique Device Identifier for Apple products |
| enrollment_status | Device status in enrollment process |
| imei | IMEI number for mobile devices |


#### Relationships

- HexnodeUser owns HexnodeDevice

    ```
    (HexnodeUser)-[OWNS_DEVICE]->(HexnodeDevice)
    ```

- HexnodeDevice is a member of HexnodeDeviceGroup

    ```
    (HexnodeDevice)-[MEMBER_OF]->(HexnodeDeviceGroup)
    ```

- HexnodeDevice applies a HexnodePolicy (added by analysis job)

    ```
    (HexnodeDevice)-[APPLIES_POLICY]->(HexnodePolicy)
    ```

### HexnodeDeviceGroup

Representation of a gourp of devices in Hexnode

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | Hexnode group ID |
| name | Group name |
| description | Group description |
| group_type | Type of group (automatic, custom ...) |
| modified_date | Timestamp of last time the group was edited |


#### Relationships

- HexnodeDevice is a member of HexnodeDeviceGroup

    ```
    (HexnodeDevice)-[MEMBER_OF]->(HexnodeDeviceGroup)
    ```

- HexnodeDeviceGroup applies a HexnodePolicy

    ```
    (HexnodeDeviceGroup)-[APPLIES_POLICY]->(HexnodePolicy)
    ```


### HexnodePolicy

Representation of a single Policy in Hexnode

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | Hexnode policy ID |
| name | Policy name |
| description | Policy description |
| version | Policy version (increased by 1 every update) |
| archived | Flag for archived policies |
| ios_configured | Flag for policy with iOS rules |
| android_configured | Flag for policy with android rules |
| windows_configured | Flag for policy with Windows rules |
| created_time | Timestamp of when the policy was created |
| modified_time | Timestamp of last time the policy was edited |


#### Relationships

- HexnodeDevice applies a HexnodePolicy (added by analysis job)

    ```
    (HexnodeDevice)-[APPLIES_POLICY]->(HexnodePolicy)
    ```

- HexnodeDeviceGroup applies a HexnodePolicy

    ```
    (HexnodeDeviceGroup)-[APPLIES_POLICY]->(HexnodePolicy)
    ```
