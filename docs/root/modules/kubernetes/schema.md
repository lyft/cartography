## Kubernetes Schema

.. _kubernetes_schema:

### KubernetesCluster
Representation of a [Kubernetes Cluster.](https://kubernetes.io/docs/concepts/overview/what-is-kubernetes/)

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | Identifier for the cluster i.e. UID of `kube-system` namespace |
| name | Name assigned to the cluster which is derived from kubeconfig context |

#### Relationships
- KubernetesCluster has KubernetesNamespaces.
    ```
    (KubernetesCluster)-[HAS_NAMESPACE]->(KubernetesNamespace)
    ```

- KubernetesCluster can have KubernetesPods.
    ```
    (KubernetesCluster)-[HAS_POD]->(KubernetesPod)
    ```

### KubernetesNamespace
Representation of a [Kubernetes Namespace.](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/)

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | UID of the kubernetes namespace |
| name | Name of the kubernetes namespace |
| created\_at | Timestamp of the creation time of the kubernetes namespace |
| deleted\_at | Timestamp of the deletion time of the kubernetes namespace |

#### Relationships
- KubernetesNamespace can have KubernetesPods.
    ```
    (KubernetesNamespace)-[HAS_POD]->(KubernetesPod)
    ```

- KubernetesNamespace can have KubernetesServices.
    ```
    (KubernetesNamespace)-[HAS_SERVICE]->(KubernetesService)
    ```

- KubernetesNamespace can have KubernetesSecrets.
    ```
    (KubernetesNamespace)-[HAS_SECRET]->(KubernetesSecret)
    ```

- KubernetesNamespace can have KubernetesIngresses.
    ```
    (KubernetesNamespace)-[HAS_INGRESS]->(KubernetesIngress)
    ```

### KubernetesPod
Representation of a [Kubernetes Pod.](https://kubernetes.io/docs/concepts/workloads/pods/)

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | UID of the kubernetes pod |
| name | Name of the kubernetes pod |
| status\_phase | The phase of a Pod is a simple, high-level summary of where the Pod is in its lifecycle.  |
| created\_at | Timestamp of the creation time of the kubernetes pod |
| deleted\_at | Timestamp of the deletion time of the kubernetes pod |

#### Relationships
- KubernetesPod has KubernetesContainers.
    ```
    (KubernetesPod)-[HAS_CONTAINER]->(KubernetesContainer)
    ```

### KubernetesContainer
Representation of a [Kubernetes Container.](https://kubernetes.io/docs/concepts/workloads/pods/#how-pods-manage-multiple-containers)

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | Identifier for the container which is derived from the UID of pod and the name of container |
| name | Name of the container in kubernetes pod |
| image | Docker image used in the container |
| status\_image\_id | ImageID of the container's image. |
| status\_image\_sha | The SHA portion of the status\_image\_id |
| status\_ready | Specifies whether the container has passed its readiness probe. |
| status\_started | Specifies whether the container has passed its startup probe. |
| statys\_state | State of the container (running, terminated, waiting) |

#### Relationships
- KubernetesPod has KubernetesContainers.
    ```
    (KubernetesPod)-[HAS_CONTAINER]->(KubernetesContainer)
    ```

### KubernetesService
Representation of a [Kubernetes Service.](https://kubernetes.io/docs/concepts/services-networking/service/)

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | UID of the kubernetes service |
| name | Name of the kubernetes service |
| created\_at | Timestamp of the creation time of the kubernetes service |
| deleted\_at | Timestamp of the deletion time of the kubernetes service |
| type | Type of kubernetes service e.g. `ClusterIP` |
| load\_balancer\_ip | IP of the load balancer when service type is `LoadBalancer` |
| ingress\_host | Hostname of the ingress endpoint, if any |
| ingress\_ip | IP of the ingress endpoint, if any |

#### Relationships
- KubernetesService can serve KubernetesPods.
    ```
    (KubernetesService)-[SERVES_POD]->(KubernetesPod)
    ```

- KubernetesIngressRuleHttpPath can have a KubernetesService.
    ```
    (KubernetesIngressRuleHttpPath)-[HAS_PATH]->(KubernetesService)
    ```

### KubernetesSecret
Representation of a [Kubernetes Secret.](https://kubernetes.io/docs/concepts/configuration/secret/)

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | UID of the kubernetes secret |
| name | Name of the kubernetes secret |
| created\_at | Timestamp of the creation time of the kubernetes secret |
| deleted\_at | Timestamp of the deletion time of the kubernetes secret |
| type | Type of kubernetes secret e.g. `Opaque` |

#### Relationships
- KubernetesNamespace can have KubernetesSecrets.
    ```
    (KubernetesNamespace)-[HAS_SECRET]->(KubernetesSecret)
    ```

### KubernetesIngress
Representation of a [Kubernetes Ingress.](https://kubernetes.io/docs/concepts/services-networking/ingress/)

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | UID of the kubernetes ingress |
| name | Name of the kubernetes ingress |
| created\_at | Timestamp of the creation time of the kubernetes ingress |
| deleted\_at | Timestamp of the deletion time of the kubernetes ingress |
| tls | TLS data for ingress |

#### Relationships
- KubernetesNamespace can have KubernetesIngresses.
    ```
    (KubernetesNamespace)-[HAS_INGRESS]->(KubernetesIngress)
    ```

- KubernetesIngress can have KubernetesIngressRules.
    ```
    (KubernetesIngress)-[HAS_RULE]->(KubernetesIngressRule)
    ```

### KubernetesIngressRule
Representation of a [Kubernetes Ingress Rule.](https://kubernetes.io/docs/concepts/services-networking/ingress/#ingress-rules)

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| ingress_id | UID of the kubernetes ingress that has the rule |
| host | Name of the rule host |

#### Relationships
- KubernetesIngress can have KubernetesIngressRules.
    ```
    (KubernetesIngress)-[HAS_RULE]->(KubernetesIngressRule)
    ```

- KubernetesIngressRule can have KubernetesIngressRuleHttpPaths.
    ```
    (KubernetesIngressRule)-[HAS_PATH]->(KubernetesIngressRuleHttpPath)
    ```

### KubernetesIngressRuleHttpPath
Representation of a [Kubernetes Ingress Rule HTTP Path.](https://kubernetes.io/docs/concepts/services-networking/ingress/#path-types)

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| ingress_id | UID of the kubernetes ingress that has the rule |
| host | Name of the rule host |
| path | Name of the path |

#### Relationships
- KubernetesIngressRule can have KubernetesIngressRuleHttpPaths.
    ```
    (KubernetesIngressRule)-[HAS_PATH]->(KubernetesIngressRuleHttpPath)
    ```

- KubernetesIngressRuleHttpPath can have a KubernetesService.
    ```
    (KubernetesIngressRuleHttpPath)-[HAS_PATH]->(KubernetesService)
    ```
