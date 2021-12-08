<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Kubernetes Configuration](#kubernetes-configuration)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Kubernetes Configuration

Follow these steps to analyze Kubernetes objects in Cartography.

1. Configure a [kubeconfig file](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/) specifying access to one or mulitple clusters.
    - Access to mutliple K8 clusters can be organized in a single kubeconfig file. Intel module of Kubernetes will automatically detect that and attempt to sync each cluster.
2. Note down the path of configured kubeconfig file and pass it to cartography CLI with `--k8s-kubeconfig` parameter.
