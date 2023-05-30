## HiBob Schema

.. _hibob_schema:


### Human

HiBob use Human node as pivot with other Identity Providers (GSuite, GitHub ...)

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| name | Name of the person |
| family_name | Family name of the personn |
| given_name | Given name of the personn |
| gender | Gender of the personn |

#### Relationships

- Human is an HiBobEmployee

    ```
    (Human)-[IS_EMPLOYEE]->(HiBobEmployee)
    ```

### HiBobDepartment

HiBob use Departement as "Oranizational Unit".

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | Same as department name |
| name | Department name |

#### Relationships

- HiBobEmployee is a member of HiBobDepartment

    ```
    (HiBobEmployee)-[MEMBER_OF]->(HiBobDepartment)
    ```

### HiBobEmployee

Representation of a single Employee in HiBob

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | HiBob employee ID (global ID not company ID) |
| name | Name of the employee |
| family_name | Family name of the employee |
| given_name | Given name of the employee |
| gender | Gender of the employee |
| email | Email of the employee |
| private_mobile | Personal mobile |
| private_phone | Personal phone number |
| private_email | Personal email |
| start_date | First day in the company |
| is_manager | Is the employee managing other people |
| work_phone | Professional phone number |
| work_office | Name of the office where the employee is affected |

#### Relationships

- Human is an HiBobEmployee

    ```
    (Human)-[IS_EMPLOYEE]->(HiBobEmployee)
    ```

- HiBobEmployee is a member of HiBobDepartment

    ```
    (HiBobEmployee)-[MEMBER_OF]->(HiBobDepartment)
    ```

- HiBobEmployee is a managed by an other HiBobEmployee

    ```
    (HiBobEmployee)-[MANAGED_BY]->(HiBobEmployee)
    ```
