## Semgrep Schema

.. _semgrep_schema:

### SemgrepDeployment

Represents a Semgrep [Deployment](https://semgrep.dev/api/v1/docs/#tag/Deployment), a unit encapsulating a security organization inside Semgrep Cloud. Works as the parent of all other Semgrep resources.

| Field | Description |
|-------|--------------|
| firstseen | Timestamp of when a sync job first discovered this node  |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique integer id representing the deployment |
| **slug** | Lowercase string id representing the deployment to query the API |
| **name** | Name of security organization connected to the deployment |

#### Relationships

- A SemgrepDeployment contains SemgrepSCAFinding's

    ```
    (SemgrepDeployment)-[RESOURCE]->(SemgrepSCAFinding)
    ```

- A SemgrepDeployment contains SemgrepSCALocation's


    ```
    (SemgrepDeployment)-[RESOURCE]->(SemgrepSCALocation)
    ```

    ```

### SemgrepSCAFinding

Represents a [Semgre Supply Chain](https://semgrep.dev/docs/semgrep-supply-chain/overview/) finding. This is, a vulnerability in a dependency of a project discovered by Semgrep performing software composition analysis (SCA) and code reachability analysis. Before ingesting this node, make sure you have run Semgrep CI and that it's connected to Semgrep Cloud Platform [Running Semgrep CI with Semgrep Cloud Platform](https://semgrep.dev/docs/semgrep-ci/running-semgrep-ci-with-semgrep-cloud-platform/).

| Field | Description |
|-------|--------------|
| firstseen | Timestamp of when a sync job first discovered this node  |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | A composed id based using the repository path and the rule that triggered the finding |
| **rule_id** | The rule that triggered the finding |
| **repository** | The repository path where the finding was discovered |
| summary | A short title summarizing of the finding |
| description | Description of the vulnerability. |
| package_manager | The ecosystem of the dependency where the finding was discovered (e.g. pypi, npm, maven) |
| severity | Severity of the finding (e.g. CRITICAL, HIGH, MEDIUM, LOW) |
| cve_id | CVE id of the vulnerability from NVD. Check [cve_schema](../cve/schema.md) |
| reachability_check | Whether the vulnerability reachability is confirmed, not confirmed or needs to be manually confirmed |
| reachability_condition | Description of the reachability condition (e.g. reachable if code is used in X way) |
| reachability | Whether the vulnerability is reachable or not |
| transitivity | Whether the vulnerability is transitive or not (e.g. dependency, transitive) |
| dependency | Dependency where the finding was discovered. Includes dependency name and version |
| dependency_fix | Dependency version that fixes the vulnerability |
| ref_urls | List of reference urls for the finding |
| dependency_file | Path of the file where the finding was discovered (e.g. lock.json, requirements.txt) |
| dependency_file_url | URL of the file where the finding was discovered |
| scan_time | Date and time when the finding was discovered in UTC |


#### Relationships

- An SemgrepSCAFinding connected to a GithubRepository (optional)

    ```
    (SemgrepSCAFinding)-[FOUND_IN]->(GithubRepository)
    ```

- A SemgrepSCAFinding vulnerable dependency usage at SemgrepSCALocation (optional)

    ```
    (SemgrepSCAFinding)-[USAGE_AT]->(SemgrepSCALocation)
    ```


### SemgrepSCALocation

Represents the location in a repository where a vulnerable dependency is used in a way that can trigger the vulnerability.

| Field | Description |
|-------|--------------|
| firstseen | Timestamp of when a sync job first discovered this node  |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique id identifying the location of the finding |
| path | Path of the file where the usage was discovered |
| start_line | Line where the usage starts |
| start_col | Column where the usage starts |
| end_line | Line where the usage ends |
| end_col | Column where the usage ends |
| url | URL of the file where the usage was discovered |
