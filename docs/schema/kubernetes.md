<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Cartography - Kubernetes Schema](#cartography---kubernetes-schema)
  - [KubernetesCluster](#kubernetescluster)
    - [Relationships](#relationships)
  - [KubernetesNamespace](#kubernetesnamespace)
    - [Relationships](#relationships-1)
  - [KubernetesPod](#kubernetespod)
    - [Relationships](#relationships-2)
  - [KubernetesContainer](#kubernetescontainer)
    - [Relationships](#relationships-3)
  - [KubernetesService](#kubernetesservice)
    - [Relationships](#relationships-4)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Cartography - Kubernetes Schema

## KubernetesCluster
Representation of a [Kubernetes Cluster.](https://kubernetes.io/docs/concepts/overview/what-is-kubernetes/)

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | Identifier for the cluster i.e. UID of `kube-system` namespace |
| name | Name assigned to the cluster which is derived from kubeconfig context |

### Relationships
- KubernetesCluster has KubernetesNamespaces.
    ```
    (KubernetesCluster)-[HAS_NAMESPACE]->(KubernetesNamespace)
    ```

- KubernetesCluster can have KubernetesPods.
    ```
    (KubernetesCluster)-[HAS_POD]->(KubernetesPod)
    ```

## KubernetesNamespace
Representation of a [Kubernetes Namespace.](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/)

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | UID of the kubernetes namespace |
| name | Name of the kubernetes namespace |
| created_at | Timestamp of the creation time of the kubernetes namespace |
| deleted_at | Timestamp of the deletion time of the kubernetes namespace |

### Relationships
- KubernetesNamespace can have KubernetesPods.
    ```
    (KubernetesNamespace)-[HAS_POD]->(KubernetesPod)
    ```

- KubernetesNamespace can have KubernetesServices.
    ```
    (KubernetesNamespace)-[HAS_SERVICE]->(KubernetesService)
    ```

## KubernetesPod
Representation of a [Kubernetes Pod.](https://kubernetes.io/docs/concepts/workloads/pods/)

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | UID of the kubernetes pod |
| name | Name of the kubernetes pod |
| created_at | Timestamp of the creation time of the kubernetes pod |
| deleted_at | Timestamp of the deletion time of the kubernetes pod |

### Relationships
- KubernetesPod has KubernetesContainers.
    ```
    (KubernetesPod)-[HAS_CONTAINER]->(KubernetesContainer)
    ```

## KubernetesContainer
Representation of a [Kubernetes Container.](https://kubernetes.io/docs/concepts/workloads/pods/#how-pods-manage-multiple-containers)

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | Identifier for the container which is derived from the UID of pod and the name of container |
| name | Name of the container in kubernetes pod |
| image | Docker image used in the container |

### Relationships
- KubernetesPod has KubernetesContainers.
    ```
    (KubernetesPod)-[HAS_CONTAINER]->(KubernetesContainer)
    ```

## KubernetesService
Representation of a [Kubernetes Service.](https://kubernetes.io/docs/concepts/services-networking/service/)

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | UID of the kubernetes service |
| name | Name of the kubernetes service |
| created_at | Timestamp of the creation time of the kubernetes service |
| deleted_at | Timestamp of the deletion time of the kubernetes service |
| type | Type of kubernetes service e.g. `ClusterIP` |
| load_balancer_ip | IP of the load balancer when service type is `LoadBalancer` |
| ingress_host | Hostname of the ingress endpoint, if any |
| ingress_ip | IP of the ingress endpoint, if any |

### Relationships
- KubernetesService can serve KubernetesPods.
    ```
    (KubernetesService)-[SERVES_POD]->(KubernetesPod)
    ```
