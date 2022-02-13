## Crxcavtor Schema

### GSuiteUser

Placeholder representation of a single G Suite [user object](https://developers.google.com/admin-sdk/directory/v1/reference/users). This node is the minimal data necessary to map who has extensions installed until full G Suite data is imported.


| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | The user's email address, will change to actual G Suite id in future |
| email | The user's email address

#### Relationships

- GSuiteUsers install ChromeExtensions.

    ```
    (GSuiteUser)-[INSTALLS]->(ChromeExtension)
    ```

### ChromeExtension

 Representation of a CRXcavator Chrome Extension [Report](https://crxcavator.io/apidocs#tag/report).

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | The combined extension name and version e.g. ``"Docs\|1.0"`` |
| extension\_id | CRXcavator id for extension. |
| version | The versions of the extension in this report |
| risk\_total | CRXcavator risk score for the extension |
| risk\_metadata | Additional data provided by CRXcavator on the risk score |
| risk\_permissions\_score | Sum of the permissions component of the risk score |
| risk\_webstore\_score | Sum of the webstore component of the risk score |
| risk\_csp\_score | Sum of the CSP component of the risk score |
| risk\_optional\_permissions\_score | Sum of the optional permissions component of the risk score |
| risk\_extcalls\_score | Sum of the external calls component of the risk score |
| risk\_vuln\_score | Sum of the RetireJS vulnerability component of the risk score |
| address | Physical address of extension developer |
| email | Email address of extension developer |
| icon | URL of the extension icon |
| crxcavator\_last\_updated | Date the extension was last updated in the webstore |
| name | Full name of the extension |
| offered\_by | Name of the extension developer |
| permissions\_warnings | Concatenated list of permissions warnings for the extension |
| privacy\_policy | URL of privacy policy for extension |
| rating | Current webstore rating for extension |
| rating\_users | How many users have provided a rating for the extension |
| short\_description | Summary of what extension does |
| size | Size of extension download |
| support\_site | URL of developer support site |
| users | Webstore count of extension users |
| website | Developer URL for extension |
| type | Extension categorization |
| price | Extension price in webstore if applicable |
| report\_link | URL of full extension report on crxcavator.io |

 ### Relationships

- GSuiteUsers install ChromeExtensions.

    ```
    (GSuiteUser)-[INSTALLS]->(ChromeExtension)
    ```
