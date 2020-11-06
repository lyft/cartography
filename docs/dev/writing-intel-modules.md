# How to write a new intel module
<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Before getting started...](#before-getting-started)
- [Configuration and credential management](#configuration-and-credential-management)
  - [Supplying credentials and arguments to your module](#supplying-credentials-and-arguments-to-your-module)
  - [An important note on validating your commandline args](#an-important-note-on-validating-your-commandline-args)
- [Sync = Get, Transform, Load, Cleanup](#sync--get-transform-load-cleanup)
  - [Get](#get)
  - [Transform](#transform)
    - [Handling required versus optional fields](#handling-required-versus-optional-fields)
  - [Load](#load)
    - [Handling cartography's `update_tag`:](#handling-cartographys-update_tag)
    - [All nodes need these fields](#all-nodes-need-these-fields)
    - [All relationships need these fields](#all-relationships-need-these-fields)
    - [Run queries only on indexed fields for best performance](#run-queries-only-on-indexed-fields-for-best-performance)
    - [Create an index for new nodes](#create-an-index-for-new-nodes)
    - [lastupdated and firstseen](#lastupdated-and-firstseen)
    - [Connecting different node types with the `_attach` pattern](#connecting-different-node-types-with-the-_attach-pattern)
  - [Cleanup](#cleanup)
- [Error handling principles](#error-handling-principles)
- [Schema](#schema)
- [Making tests](#making-tests)
- [Other](#other)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

This doc contains guidelines on creating a Cartography intel module.  If you want to add a new data type to Cartography,
this is the guide for you!  It is fairly straightforward to copy the structure of an existing intel module and test it,
but we'll share some best practices in this doc to save you some time.  We look forward to receiving your PR!

## Before getting started...

Read through and follow the setup steps in [the Cartography developer guide](developer-guide.md).  Learn the basics of
running, testing, and linting your code there.


## Configuration and credential management

### Supplying credentials and arguments to your module

If you need to supply an API key or other credential to your Cartography module, we recommend adding a CLI argument.  An example of this can be seen [in our Okta module](https://github.com/lyft/cartography/blob/811990606c22a42791d213c7ca845b15f87e47f1/cartography/cli.py#L136) where we require the user to specify the name of an environment variable containing their Okta API key.  This credential will then be bound to Cartography's [Config object](https://github.com/lyft/cartography/blob/811990606c22a42791d213c7ca845b15f87e47f1/cartography/config.py#L3) which is present in all modules.  You can specify different arguments from the commandline for your module via the Config object.

### An important note on validating your commandline args

Note that it is your module's responsibility to validate arguments that you introduce.  For example with the Okta module, we [validate](https://github.com/lyft/cartography/blob/811990606c22a42791d213c7ca845b15f87e47f1/cartography/intel/okta/__init__.py#L37) that `config.okta_api_key` has been defined before attempting to continue.


## Sync = Get, Transform, Load, Cleanup

A cartography intel module consists of one `sync` function.  `sync` should call `get`, then `load`, and finally `cleanup`.


### Get

The `get` function [retrieves necessary data](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/intel/gcp/compute.py#L98)
from a resource provider API, which is GCP in this particular example.

`get` should be "dumb" in the sense that it should not handle retry logic or data
manipulation.  It should also raise an exception if it's not able to complete successfully.

### Transform

The `transform` function [manipulates data](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/intel/gcp/compute.py#L193)
to make it easier to ingest to the graph.  We have some best practices on handling transforms:

#### Handling required versus optional fields

We should directly access dicts in cases where not having the data should cause a sync to fail.
For example, if we are transforming AWS data, we definitely need an AWS object's ARN field because it uniquely
identifies the object.  Therefore, we should access an object's ARN using `data['arn']` as opposed to
using `data.get('arn')` (the former will raise a `KeyError` if `arn` does not exist and the latter will just return
`None` without an exception).

We _want_ the sync to fail if an important field is not present in our data.  The idea here is that
it is better to fail a sync than to add malformed data.

On the other hand, we should use `data.get('SomeField')` if `SomeField` is something optional that can afford to be
`None`.

For the sake of consistency, if a field does not exist, set it to `None` and not `""`.


### Load

The `load` function ingests the processed data to Neo4j, [as seen in this GCP VPC example](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/intel/gcp/compute.py#L442).
There are many best practices to consider here.

#### Handling cartography's `update_tag`:

`cartography`'s global [config object carries around an `update_tag` property](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/cli.py#L91-L98)
which is a tag/label associated with the current sync.  Cartography's CLI code [sets this to a Unix timestamp of when the CLI was run](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/sync.py#L131-L134),
but in theory could be anything provided that it is unique per sync.

All `cartography` intel modules need to set the `lastupdated` property on all nodes and all relationships to this
`update_tag`.  You can see a couple examples of this in our
[AWS ingestion code](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/intel/aws/__init__.py#L106) and our
    [GCP ingestion code](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/intel/gcp/__init__.py#L134).


#### All nodes need these fields

- <a name="id">`id`</a> - an ID should be a string that uniquely identifies the node.  In AWS, this is usually an
    ARN.  In GCP, this is usually a partial URI.

    If possible, we should use API-provided fields for IDs and not create our own.
    In some cases though this is unavoidable -
    see [GCPNetworkTag](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/docs/schema/gcp.md#gcpnetworktag).

    When setting an `id`, ensure that you also include the field name that it came from.  For example, since we've
    decided to use `partial_uri`s as an id for a GCPVpc,  we should include both `partial_uri` _and_ `id` on the node.
    This way, a user can tell what fields were used to derive the `id`.  This is accomplished [here](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/intel/gcp/compute.py#L455-L457).

- `lastupdated` - See [below](#lastupdated-and-firstseen) on how to set this.
- `firstseen` - See [below](#lastupdated-and-firstseen) on how to set this.

#### All relationships need these fields

Cartography currently does not create indexes on relationships, so we should keep relationships lightweight with only these two fields:

- `lastupdated` - See [below](#lastupdated-and-firstseen) on how to set this.
- `firstseen` - See [below](#lastupdated-and-firstseen) on how to set this.




#### Run queries only on indexed fields for best performance

In this example of ingesting GCP VPCs, we connect VPCs with GCPProjects
[based on GCPProject `id`s and GCPVpc `id`s](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/intel/gcp/compute.py#L451).
`id`s are indexed, as seen [here](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/data/indexes.cypher#L45)
and [here](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/data/indexes.cypher#L42).
All of these queries use indexes for faster lookup.


#### Create an index for new nodes

Be sure to [update the indexes.cypher file](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/data/indexes.cypher)
with your new node type.  Indexing on ID is required, and indexing on anything else that will be frequently queried is
encouraged.


#### lastupdated and firstseen

Set the `lastupdated` and `firstseen` fields on both nodes and relationships.  Suppose we are creating
the following chain:

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

#### Connecting different node types with the `_attach` pattern

Node connections can be complex.  In many cases we need to connect many different node types together, so we use an
`_attach` function to manage this.

The best way to explain `_attach` is through an example, like when [we connect GCP instances to their VPCs](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/intel/gcp/compute.py#L439).
In this case, we create a [helper `_attach` function](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/intel/gcp/compute.py#L660)
that accepts the instance's `id` and connects the instance to the VPC using a `MERGE` query.

This pattern can also be seen when [attaching AWS RDS instances to EC2 security groups](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/intel/aws/rds.py#L108).


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

    - Q: We just `DETACH DELETE`'d the node.  Why do we need to delete the relationships too?

    - A: There are cases where the node may continue to exist but the relationships between it and other nodes have changed.
        Explicitly deleting stale relationships accounts for this case.
        See this [short discussion](https://github.com/lyft/cartography/pull/124/files#r312277725).




## Error handling principles

- Don't catch the base Exception class when error handling because it makes problems difficult to trace.

- Do catch the narrowest possible class of exception.

- Only catch exceptions when your code can resolve the issue.  Otherwise, allow exceptions to bubble up.


## Schema

- Update the [schema](https://github.com/lyft/cartography/tree/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/docs/schema)
with every change!

## Making tests

- Before making tests, read through and follow the setup steps in [the Cartography developer guide](developer-guide.md).

- Add fake data for testing at `tests/data`.  We can see
the GCP VPC example here: https://github.com/lyft/cartography/blob/0652c2b6dede589e805156925353bffc72da6c2b/tests/data/gcp/compute.py#L2.

- Add unit tests to `tests/unit/cartography/intel`.  See this [example](https://github.com/lyft/cartography/blob/828ed600f2b14adae9d0b78ef82de0acaf24b86a/tests/unit/cartography/intel/gcp/test_compute.py).
  These tests ensure that `transform*` manipulates the data in expected ways.

- Add integration tests to  `tests/integration/cartography/intel`.  See this [example](https://github.com/lyft/cartography/blob/828ed600f2b14adae9d0b78ef82de0acaf24b86a/tests/integration/cartography/intel/gcp/test_compute.py).
  These tests assume that you have neo4j running at localhost:7687 with no password, and ensure that nodes loaded to the
  graph match your mock data.



## Other

- We prefer and will accept PRs which incrementally add information from a particular data source.  Incomplete
representations are OK provided they are consistent over time.  For example, we don't sync 100% of AWS resources but the
resources that exist in the graph don't change across syncs.

- Each intel module offers its own view of the graph

    ℹ️ This best practice is a little more less precise, so if you've gotten to this point and you need clarification, just
    submit your PR and ask us.

    As much as possible, each intel module should ingest data without assuming that a different module will ingest the
    same data.  Explained another way, each module should "offer its own perspective" on the data.  We believe doing this
    gives us a more complete graph.  Below are some key guidelines clarifying and justifying this design choice.

    - Use `MERGE` when connecting one node type to another node type.

    - It is possible (and encouraged) for more than one intel module to modify the same node type.

        For example, when we [connect RDS instances to their associated EC2 security
        groups](https://github.com/lyft/cartography/blob/6e060389fbeb14f4ccc3e58005230129f1c6962f/cartography/intel/aws/rds.py#L188)
        there are actually two different intel modules that retrieve EC2 security group data: the [RDS module](https://github.com/lyft/cartography/blob/6e060389fbeb14f4ccc3e58005230129f1c6962f/cartography/intel/aws/rds.py#L13)
        returns [partial group data](https://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_DBSecurityGroupMembership.html),
        and the EC2 module returns more complete data as it calls APIs specific for [retrieving and loading security groups](https://github.com/lyft/cartography/blob/6e060389fbeb14f4ccc3e58005230129f1c6962f/cartography/intel/aws/ec2.py#L166).
        Because both the RDS and EC2 modules `MERGE` on a unique ID, we don't need to worry about
        creating duplicate nodes in the graph.

        Another less obvious benefit of using `MERGE` across more than one intel module to connect nodes in this way is that
        in many cases, we've seen an intel module discover nodes that another module was not aware of!
