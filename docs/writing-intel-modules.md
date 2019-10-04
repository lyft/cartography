# How to write a new intel module
<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Sync = Get, Transform, Load, Cleanup](#sync--get-transform-load-cleanup)
  - [Get](#get)
  - [Transform](#transform)
  - [Load](#load)
  - [Cleanup](#cleanup)
  - [The _attach pattern](#the-_attach-pattern)
- [Error handling principles](#error-handling-principles)
- [Schema](#schema)
- [Making tests](#making-tests)
- [Other](#other)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

This doc contains guidelines on creating a Cartography intel module.  If you want to add a new data type to Cartography,
this is guide for you!  It is fairly straightforward to copy the structure of an existing intel module and test it,
but we'll share some best practices and nuances in this doc to save you some time.  We look forward to receiving your PR!


## Sync = Get, Transform, Load, Cleanup

A cartography intel module consists of one `sync` function.  `sync` should then call `get` followed by `load`, which is
then concluded with `cleanup`.

We'll use the example of [ingesting GCP VPCs](https://github.com/lyft/cartography/blob/9607b0835928e8195f9b8d601c4f32a37d17de96/cartography/intel/gcp/compute.py#L875)
to walk through how this works.

### Get

The `get*` function [retrieves necessary data](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/intel/gcp/compute.py#L98)
from a resource provider API, in this case GCP.

`get` should be "dumb".  Our current guidance is that a `get` function should not handle retry logic or data
manipulation. (⚠️At the time of this writing we are aware of issues with not having retry logic, and we are holding off
on implementing a solution immediately to better understand problems with different APIs)

### Transform

The `transform*` function [performs transformations](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/intel/gcp/compute.py#L193)
on the data to make it easier to ingest to the graph.  We have some best practices on handling transforms:

- Use `my_dict['someField']` when accessing important fields, and use `my_dict.get('someField')` for less important ones.

    We should directly access dicts in cases where not having the data should cause a sync to fail.
    For example, if we are transforming AWS data, we definitely need an AWS object's ARN field because it uniquely
    identifies the object.  Therefore, we should access an object's ARN using `data['arn']` as opposed to
    using `data.get('arn')` (the former will raise a `KeyError` if `arn` does not exist and the latter will just return
    `None` without an exception).

    We _want_ the sync to fail if an important field is not present in our data.  The idea here is that
    it is better to fail a sync than to add malformed data.

    On the other hand, we should use `data.get('SomeField')` if `SomeField` is something optional that can afford to be `None`.


### Load

The `load*` function [ingests the processed data to neo4j](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/intel/gcp/compute.py#L442).
There are several practices that we employ with `load*`:

- What is the cartography `update_tag`?

    `cartography`'s global [config object carries around an `update_tag` property](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/cli.py#L91-L98) which is
    [set to the time that the CLI is run](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/sync.py#L131-L134).
    All `cartography` intel modules need to set the `lastupdated` property on all nodes and all relationships to this
    `update_tag`.  You can see a couple examples of this in our
    [AWS ingestion code](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/intel/aws/__init__.py#L106) and our
    [GCP ingestion code](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/intel/gcp/__init__.py#L134).


- At minimum, set these fields on all nodes:
    - `id`
        Set this to a field that uniquely identifies the node.  For our example of GCP VPCs, we will use the `partial_uri`
        as an unique identifier for `id` - this is shown in our
        [schema docs](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/docs/schema/gcp.md#gcpvpc).
        For an AWS node, it would make sense to set `id` to an ARN.

        If possible, we should always use API-provided fields for IDs and not create derived IDs based on multiple fields.
        In some cases though this is unavoidable -
        see [GCPNetworkTag](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/docs/schema/gcp.md#gcpnetworktag).

        When setting an `id`, ensure that you also include the field name that it came from.  For example, since we've
        decided to use `partial_uri`s as GCPVpc `id`,  we should include both `partial_uri` _and_ `id`.  This way,
        a user can tell what fields were used to derive the `id`.  This is accomplished [here](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/intel/gcp/compute.py#L455-L457).

    - `lastupdated` - See the special section below on how to set this.
    - `firstseen` - See the special section below on how to set this.

- At minimum, set these fields on all relationships:
    - `lastupdated` - See the special section below on how to set this.
    - `firstseen` - See the special section below on how to set this.

- For best performance, ensure that you `MERGE` on fields that are indexed.

    In this example of ingesting GCP VPCs, we connect VPCs with GCPProjects
    [based on GCPProject `id`s and GCPVpc `id`s](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/intel/gcp/compute.py#L451).
    These are both indexed fields, as seen [here](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/data/indexes.cypher#L45)
    and [here](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/data/indexes.cypher#L42).

- On that note, ensure that you [update the indexes.cypher file](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/data/indexes.cypher)
  with your new node type.


- Make sure to set the `lastupdated` and `firstseen` fields on both nodes and relationships.

    Suppose we are creating the following chain:

    ```cypher
    MERGE (n:NodeType)-[r:RELATIONSHIP]->(n2:NodeType2)
    ```

    - To handle nodes in this case,

        - Every `MERGE` query that creates a new node should look like this

            ```cypher
            ON CREATE SET n.firstseen = {UpdateTag}
            SET
            n.lastupdated = {UpdateTag},
            node.field1 = {value1},
            node.field2 = {value2},
            ...
            node.fieldN = {valueN}
            ```

    - To handle relationships in this case,

        - Every `MERGE` query that creates a new relationship should look like this

            ```cypher
            ON CREATE SET r.firstseen = {UpdateTag}
            SET
            r.lastupdated = {UpdateTag}
            ```



### Cleanup

We have just added new nodes and relationships to the graph, and we have also updated previously-added ones
by using `MERGE`.  We now need to delete nodes and relationships that no longer exist, and we do this by simply removing
all nodes and relationships that have `lastupdated` NOT set to the `update_tag` of this current run.

- Delete all old nodes

    You can see this in our [GCP VPCs example](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/data/jobs/cleanup/gcp_compute_vpc_cleanup.json#L4).
    We run `DETACH DELETE` to delete an old node and disconnect it from all other nodes.

 - Delete all old relationships

    You can see this in the GCP VPC example [here](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/data/jobs/cleanup/gcp_compute_vpc_cleanup.json#L10)
    and [here](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/data/jobs/cleanup/gcp_compute_vpc_cleanup.json#L16).

    - FAQ: But we just `DETACH DELETE`'d the node, why do we need to delete the relationships?
        There are cases where the node may continue to exist but the relationships between it and other nodes have changed.
        Explicitly deleting stale relationships accounts for this case.
        See this [short discussion](https://github.com/lyft/cartography/pull/124/files#r312277725).


### The _attach pattern

Node connections can be complex.  In this GCP VPC example, we need to connect GCP instances to the VPCs that
they belong to.  We can do this with the `_attach` pattern, as seen [here](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/intel/gcp/compute.py#L439).

In this case, we create a [helper function](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/intel/gcp/compute.py#L660)
that accepts the instance's `id` and connects the instance to the VPC using a `MERGE` query.

This pattern can also be seen when [attaching AWS RDS instances to EC2 security groups](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/intel/aws/rds.py#L108).


## Error handling principles

- Don't catch the base Exception class when error handling because it makes it difficult to trace.


## Schema

- Update the [schema](https://github.com/lyft/cartography/tree/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/docs/schema)
with every change!

## Making tests

- Before making tests, read through [these docs](developer-guide.md).

- Add fake data for testing at `tests/data`.  We can see
the GCP VPC example here: https://github.com/lyft/cartography/blob/0652c2b6dede589e805156925353bffc72da6c2b/tests/data/gcp/compute.py#L2.

- Add unit tests to `tests/unit/cartography/intel`.  See this [example](https://github.com/lyft/cartography/blob/828ed600f2b14adae9d0b78ef82de0acaf24b86a/tests/unit/cartography/intel/gcp/test_compute.py).
  These tests ensure that `transform*` manipulates the data in expected ways.

- Add integration tests to  `tests/integration/cartography/intel`.  See this [example](https://github.com/lyft/cartography/blob/828ed600f2b14adae9d0b78ef82de0acaf24b86a/tests/integration/cartography/intel/gcp/test_compute.py).
  These tests assume that you have neo4j running at localhost:7687 with no password, and ensure that nodes loaded to the
  graph match your mock data.

## Other

- Smaller PRs are much better than larger PRs!  It's so much easier to review smaller chunks of work.
