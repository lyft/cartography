# Cartography - Okta Schema

## Table of contents

- [OktaOrganization](#oktaorganization)
- [OktaUser](#oktauser)
- [OktaGroup](#oktagroup)
- [OktaApplication](#oktaapplication)
- [OktaUserFactor](#oktauserfactor)
- [OktaTrustedOrigin](#oktatrustedorigin)
- [OktaAdministrationRole](#oktaadministrationrole)


## OktaOrganization

Representation of a Okta [Organization](https://developer.okta.com/docs/concepts/okta-organizations/).


| Field | Description |
|-------|--------------| 
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated | 
| id | The name of the Okta Organization, e.g. "lyft" |
| name | The name of the Okta Organization, e.g. "lyft"

### Relationships

- OktaOrganization has OktaUser.

    ```
    (OktaOrganization)-[RESOURCE]->(OktaUser)
    ```
    
- OktaOrganization has OktaGroup.

    ```
    (OktaOrganization)-[RESOURCE]->(OktaGroup)
    ```
- OktaOrganization has OktaApplication.

    ```
    (OktaOrganization)-[RESOURCE]->(OktaApplication)
    ```
- OktaOrganization has OktaTrustedOrigin.

    ```
    (OktaOrganization)-[RESOURCE]->(OktaTrustedOrigin)
    ```
- OktaOrganization has OktaAdministrationRole.

    ```
    (OktaOrganization)-[RESOURCE]->(OktaAdministrationRole)
    ```
 ## OktaUser
 
 Representation of a Okta User (https://github.com/okta/okta-sdk-python/blob/master/okta/models/user/User.py).

| Field | Description |
|-------|--------------| 
| id | user id  |
| first_name | user first name  |
| last_name | user last name  |
| login | user usernmae used to login (usually email) |
| email | user email |
| second_email | user secondary email |
| mobile_phone | user mobile phone |
| created | date and time of creation |
| activated | date and time of activation |
| status_changed | date and time of the last state change |
| last_login | date and time of last login |
| okta_last_updated | date and time of last user property changes |
| password_changed | date and time of last password change |
| transition_to_status | date and time of last state transition change |
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated | 

 ### Relationships
 
 - OktaUser is a resource of an OktaOrganization
    ```
    (OktaUser)<-[RESOURCE]->(OkOrganization)
    ```
 - OktaUser is assigned OktaApplication
 
    ```
    (OktaUser)-[APPLICATION]->(OktaApplication)
    ```
 - OktaUser is an identity for a Human
 
    ```
    (OktaUser)<-[IDENTITY_OKTA]-(Human)
    ```
 - OktaUser can be a member of a OktaGroup
     ```
    (OktaUser)-[MEMBER_OF_OKTA_GROUP]->(OktaGroup)
    ```
 - OktaUser can be a member of an OktaAdministrationRole
     ```
    (OktaUser)-[MEMBER_OF_OKTA_ROLE]->(OktaAdministrationRole)
    ```
 - OktaUser can have authentication Factors
     ```
    (OktaUser)-[FACTOR]->(OktaUserFactor)
    ```
 
 ## OktaGroup
 Representation of a OktaGroup (https://github.com/okta/okta-sdk-python/blob/master/okta/models/usergroup/UserGroup.py).
 
| Field | Description |
|-------|--------------| 
| id | application id  |
| name | group name |
| description | group description |
| sam_account_name | windows SAM account name mapped
| dn | group dn |
| windows_domain_qualified_name | windows domain name |
| external_id | group foreign id |
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated | 

 ### Relationships
  - OktaGroup is a resource of an OktaOrganization
    ```
    (OktaGroup)<-[RESOURCE]->(OkOrganization)
    ```
 - OktaGroup is assigned OktaApplication
 
    ```
    (OktaGroup)-[APPLICATION]->(OktaApplication)
    ```
 - OktaGroup can have members of OktaUser
     ```
    (OktaUser)-[MEMBER_OF_OKTA_GROUP]->(OktaGroup)
    ```
 - OktaGroup can be a member of an OktaAdministrationRole
     ```
    (OktaGroup)-[MEMBER_OF_OKTA_ROLE]->(OktaAdministrationRole)
    ```
 ## OktaApplication
Representation of a Okta Application (https://developer.okta.com/docs/reference/api/apps/).

| Field | Description |
|-------|--------------| 
| id | application id |
| name | application name |
| label | application label |
| created | application creation date |
| okta_last_updated | date and time of last user property changes |
| status | application status |
| activated | application activation state |
| features | application features |
| sign_on_mode | application signon mode |
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated | 

### Relationships
  - OktaApplication is a resource of an OktaOrganization
    ```
    (OktaApplication)<-[RESOURCE]->(OkOrganization)
    ```
 - OktaGroup is assigned OktaApplication
 
    ```
    (OktaGroup)-[APPLICATION]->(OktaApplication)
    ```
 - OktaUser is assigned OktaApplication
 
    ```
    (OktaUser)-[APPLICATION]->(OktaApplication)
    ```
 ## OktaUserFactor
Representation of a Okta user authentication factors (https://developer.okta.com/docs/reference/api/factors/).

| Field | Description |
|-------|--------------| 
| id | factor id |
| factor_type | factor type |
| provider | factor provider |
| status | factor status |
| created | factor creation date and time |
| okta_last_updated | date and time of last property changes |
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated | 

### Relationships
 - OktaUser can have authentication Factors
     ```
    (OktaUser)-[FACTOR]->(OktaUserFactor)
    ```

## OktaTrustedOrigin
Representation of a Okta trusted origin for login/logout or recovery operations. For more information visit Okta documentation at https://developer.okta.com/docs/reference/api/trusted-origins

| Field | Description |
|-------|--------------| 
| id | trusted origin id |
| name | name |
| scopes | array of scope |
| status | status |
| created | date & time of creation in okta |
| create_by | id of user who created the trusted origin |
| okta_last_updated | date and time of last user property changes |
| okta_last_updated_by | id of user who last updated the trusted origin |
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |

### Relationships
- OktaOrganization has OktaTrustedOrigin.

    ```
    (OktaOrganization)-[RESOURCE]->(OktaTrustedOrigin)
    ```

## OktaAdministrationRole
Representation of Okta administration roles. For more information visa Okta documentation https://developer.okta.com/docs/reference/api/roles/

| Field | Description |
|-------|--------------| 
| id | role id mapped to the type |
| type | role type |
| label | role label |
| firstseen| Timestamp of when a sync job first discovered this node |
| lastupdated |  Timestamp of the last time the node was updated |

### Relationships
 - OktaUser can be a member of an OktaAdministrationRole
     ```
    (OktaUser)-[MEMBER_OF_OKTA_ROLE]->(OktaAdministrationRole)
    ```
 - OktaGroup can be a member of an OktaAdministrationRole
     ```
    (OktaGroup)-[MEMBER_OF_OKTA_ROLE]->(OktaAdministrationRole)
    ```
- OktaOrganization has OktaAdministrationRole.

    ```
    (OktaOrganization)-[RESOURCE]->(OktaAdministrationRole)
    ```