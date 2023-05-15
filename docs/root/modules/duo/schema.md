## Duo Schema

.. _duo_schema:

### DuoApiHost

Represents a Duo API Host to conain Duo resources.

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The hostname |

#### Relationships

- An DuoApiHost contains DuoUsers

    ```
    (DuoApiHost)-[RESOURCE]->(DuoUser)
    ```

- An DuoApiHost contains DuoGroups

    ```
    (DuoApiHost)-[RESOURCE]->(DuoGroup)
    ```

- An DuoApiHost contains DuoEndpoints

    ```
    (DuoApiHost)-[RESOURCE]->(DuoEndpoint)
    ```

### DuoGroup

Represents a [group](https://duo.com/docs/adminapi#groups) in Duo.

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The user_id |
| desc | The group's description. |
| group_id | The group's ID. |
| mobile_otp_enabled | Legacy parameter; no effect if specified and always returns false. |
| name | The group's name. If managed by directory sync, then the name returned here also indicates the source directory. |
| push_enabled | Legacy parameter; no effect if specified and always returns false. |
| sms_enabled | Legacy parameter; no effect if specified and always returns false |
| status | The group's authentication status. May be one of: "Active", "Bypass", "Disabled" |
| voice_enabled | Legacy parameter; no effect if specified and always returns false |

#### Relationships

- An DuoApiHost contains DuoGroups

    ```
    (DuoApiHost)-[RESOURCE]->(DuoGroup)
    ```

- A DuoUser is part of multiple DuoGroups.

    ```
    (DuoGroup)-[MEMBER_OF_DUO_GROUP]->(DuoUser)
    ```


### DuoUser

Represents a [user](https://duo.com/docs/adminapi#users) in Duo.

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The user_id |
| alias1 | The user's username alias1. |
| alias2 | The user's username alias2. |
| alias3 | The user's username alias3. |
| alias4 | The user's username alias4. |
| aliases | Map of the user's username alias(es). Up to eight aliases may exist. |
| created | The user's creation date as a UNIX timestamp. |
| email | The user's email address. |
| firstname | The user's given name. |
| groups | List of groups to which this user belongs. See Retrieve Groups for response info. |
| is_enrolled | Is true if the user has a phone, hardware token, U2F token, WebAuthn security key, or other WebAuthn method available for authentication. Otherwise, false. |
| last_directory_sync | An integer indicating the last update to the user via directory sync as a Unix timestamp, or null if the user has never synced with an external directory or if the directory that originally created the user has been deleted from Duo. |
| last_login | An integer indicating the last time this user logged in, as a Unix timestamp, or null if the user has not logged in. |
| lastname | The user's surname. |
| notes | Notes about this user. Viewable in the Duo Admin Panel. |
| phones | A list of phones that this user can use. See Retrieve Phones for descriptions of the phone response values. |
| realname | The user's real name (or full name). |
| status | The user's status. One of: "active", "bypass", "disabled", "locked out", "pending deletion". |
| tokens | A list of tokens that this user can use. A list of JSON strings |
| u2f_tokens | A list of U2F tokens that this user can use. A list of JSON strings |
| user_id | The user's ID. |
| username | The user's username. |
| webauthncredentials | A list of WebAuthn authenticators that this user can use. A list of JSON strings |

#### Relationships

- An DuoApiHost contains DuoUsers

    ```
    (DuoApiHost)-[RESOURCE]->(DuoUser)
    ```

- A DuoUser is part of multiple DuoGroups.

    ```
    (DuoGroup)-[MEMBER_OF_DUO_GROUP]->(DuoUser)
    ```

- A DuoUser has multiple DuoEndpoints

    ```
    (DuoUser)-[ENDPOINT_DUO]->(DuoEndpoint)
    ```

- A DuoUser is an identity to a Human

    ```
    (DuoUser)<-[IDENTITY_DUO]-(Human)
    ```

### DuoEndpoint

Represents a [endpoint](https://duo.com/docs/adminapi#endpoints) in Duo.

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The epkey |
| browsers | Collected information about all detected browsers on an individual endpoint. A list of JSON strings |
| computer_sid | The machine security identifier of a Windows endpoint. |
| cpu_id | The CPU ID of a Windows endpoint. |
| device_id | Custom device identifier of a Meraki-managed iOS endpoint. Returned for Duo Premier customers only. |
| device_identifier | The unique device attribute value that identifies the endpoint. Returned for Duo Premier customers only. This property will be deprecated in a future release. |
| device_identifier_type | The device attribute used to identify a unique endpoint. One of "hardware_uuid", "fqdn", "hardware_serial", "device_udid", or none. This property will be deprecated in a future release. |
| device_name | The endpoint's hostname. |
| device_udid | The unique device identifier for iOS endpoints managed by Workspace ONE, MobileIron Cloud or Core, or Sophos Mobile via certificates. Returned for Duo Premier customers only. |
| device_username | The unique attribute value that identifies the endpoint's associated user in the management system. Returned for Duo Premier customers only. |
| device_username_type | The management system attribute used to identify the user associated with the unique endpoint. One of "os_username", "upn", "username", "email", or none. Returned for Duo Premier customers only. |
| disk_encryption_status | The hard drive encryption status of the endpoint as detected by the Duo Device Health app. One of "On", "Off", or "Unknown". |
| domain_sid | The Active Directory domain security identifier for a domain-joined Windows endpoint. Empty if the Windows endpoint is not joined to a domain. |
| email | The email address, if present, of the user associated with an endpoint. |
| epkey | The endpoint's unique identifier. |
| firewall_status | Status of the endpoint's local firewall as detected by the Duo Device Health app. One of "On", "Off", or "Unknown". |
| hardware_uuid | The universally unique identifier for a Mac endpoint. |
| health_app_client_version | The version of the Duo Device Health app installed on the endpoint. |
| health_data_last_collected | The last time the Duo Device Health app performed a device health check, as a Unix timestamp. |
| last_updated | The last time the endpoint accessed Duo, as a Unix timestamp. |
| machine_guid | The globally unique identifier for a Windows endpoint. |
| model | The device model of a 2FA endpoint. |
| os_build | The endpoint's operating system build number. |
| os_family | The endpoint's operating system platform. |
| os_version | The endpoint's operating system version. |
| password_status | Whether the local admin password is set on the endpoint as detected by the Duo Device Health app. One of "Set", "Unset", or "Unknown" |
| security_agents | Information about security agents present on the endpoint as detected by the Duo Device Health app. Returned for Duo Premier customers only. a list of JSON strings |
| trusted_endpoint | Whether the endpoint is a Duo managed endpoint. One of "yes", "no", or "unknown". Returned for Duo Premier customers only. |
| type | The endpoint's device class. |
| username | The Duo username of the user associated with an endpoint. |


#### Relationships

- An DuoApiHost contains DuoEndpoints

    ```
    (DuoApiHost)-[RESOURCE]->(DuoEndpoint)
    ```

- A DuoUser has multiple DuoEndpoints

    ```
    (DuoUser)-[ENDPOINT_DUO]->(DuoEndpoint)
    ```
