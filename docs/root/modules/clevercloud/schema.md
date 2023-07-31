## CleverCloud Schema

.. _clevercloud_schema:


### Human

CleverCloud use Human node as pivot with other Identity Providers (GSuite, GitHub ...)

Human nodes are not created by CleverCloud module.


#### Relationships

- Human as an access to CleverCloud
    ```
    (Human)-[IDENTITY_CLEVERCLOUD]->(CleverCloudUser)
    ```

### CleverCloudOrganization

Representation of an Organization in CleverCloud

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | CleverCloud ID (fmt: orga_{UUID4} |
| name | Organization full name |
| description | Organization description |
| billing_email | Organization billing email |
| address | Organization postal address |
| city | Organization city |
| zipcode | Organization ZipCode |
| country | Organization Country |
| company | Company legal name |
| vat | Company VAT number |
| vat_state | Flag for VAT or without VAT billing |
| avatar | Organization avatar URL |
| customer_fullname | Main contact fullname |
| can_pay | Flag for enabled billing |
| clever_enterprise | Flag for partnership |
| emergency_number | Phone number of company emergency contact |
| can_sepa | Flag for enabled SEPA billing |
| is_trusted | Flag for verified organization |

#### Relationships
- Organization has users
    ```
    (CleverCloudUser)-[MEMBER_OF]->(CleverCloudOrganization)
    ```
- Organization has application
    ```
    (CleverCloudApplication)-[RESOURCE]->(CleverCloudOrganization)
    ```
- Organization has addons
    ```
    (CleverCloudAddon)-[RESOURCE]->(CleverCloudOrganization)
    ```

### CleverCloudUser

Representation of a single User in CleverCloud

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | CleverCloud ID (fmt: user_{UUID4} |
| email | User email |
| name | User full name |
| avatar | User avatar URL |
| preferred_mfa | User MFA status |
| role | User role |
| job | User job title |


#### Relationships
- User belongs to an Organization has users
    ```
    (CleverCloudUser)-[MEMBER_OF]->(CleverCloudOrganization)
    ```


### CleverCloudApplication

Representation of a single Application in CleverCloud

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | CleverCloud ID (fmt: app_{UUID4} |
| name | Application name |
| description | Application description |
| zone | Datacenter where application is deployed |
| instance_type | Kind of instance (eg. java) |
| instance_version | CleverCloud build version (eg. 20221027) |
| instance_slug | Instance ID (eg. gradle) |
| instance_name | Java or Groovy + Gradle |
| deployment_shutdownable | Flag for instance that could be shutdown |
| deployment_type | How the instance is deployed (eg. GIT) |
| creation_date | Instance creation date |
| state | Instance current state |
| archived | Flag for archived applications |
| separate_build | Flag for application that use a separater worker for build |
| git_commit | Git SHA1 commit for GIT deployment |
| git_branch | Git branch name for GIT deployment |
| force_https | Flag for application that enforce HTTPS traffic |

#### Relationships
- Application belongs to an Organization
    ```
    (CleverCloudApplication)-[RESOURCE]->(CleverCloudOrganization)
    ```
- Application uses Addons
    ```
    (CleverCloudApplication)<-[RESOURCE]-(CleverCloudApplication)
    ```
- Application uses VHost
    ```
    (CleverCloudApplication)<-[DNS_POINT_TO]-(CleverCloudDNSRecord)
    ```


### CleverCloudAddon

Representation of a single Addon in CleverCloud

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | CleverCloud ID (fmt: addon_{UUID4} |
| name | Addon name |
| real_id | CleverCloud typed ID (eg: postgresql_9643dfb9-4f46-46bf-9a6c-2ddbf3c5b750) |
| region | Datacenter where addon is deployed |
| provider_id | Provider ID (eg. postgresql-addon) |
| provider_name | Provider Name (eg. PostgreSQL) |
| plan_id | Pricing plan ID (eg. plan_23dd6346-2dda-4951-9c9d-9bba52ed9447) |
| plan_slug | Pricing plan slug (eg: xxs_sml) |
| plan_name | Pricing plan name (eg: XXS Small Space) |
| creation_date | Addon creation date |


#### Relationships
- Addon belongs to an Organization
    ```
    (CleverCloudApplication)-[RESOURCE]->(CleverCloudOrganization)
    ```
- Addons (can) be used by Application
    ```
    (CleverCloudApplication)<-[RESOURCE]-(CleverCloudApplication)
    ```
