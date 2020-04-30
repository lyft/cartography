## Usage Tutorial

Once everything has been installed and synced, you can view the Neo4j web interface at http://localhost:7474.  You can view the reference on this [here](https://neo4j.com/developer/guide-neo4j-browser/#_installing_and_starting_neo4j_browser).

### ℹ️ Already know [how to query Neo4j](https://neo4j.com/developer/cypher-query-language/)?  You can skip to our reference material!
If you already know Neo4j and just need to know what are the nodes, attributes, and graph relationships for our representation of infrastructure assets, you can skip this handholdy walkthrough and see our [sample queries](samplequeries.md).

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

  - [What RDS instances are installed in my AWS accounts?](#what-rds-instances-are-installed-in-my-aws-accounts)
    - [ℹ️ Protip - customizing your view](#-protip---customizing-your-view)
  - [Which RDS instances have encryption turned off?](#which-rds-instances-have-encryption-turned-off)
  - [Which EC2 instances are directly exposed to the internet?](#which-ec2-instances-are-directly-exposed-to-the-internet)
  - [Which S3 buckets have a policy granting any level of anonymous access to the bucket?](#which-s3-buckets-have-a-policy-granting-any-level-of-anonymous-access-to-the-bucket)
  - [How many unencrypted RDS instances do I have in all my AWS accounts?](#how-many-unencrypted-rds-instances-do-i-have-in-all-my-aws-accounts)
  - [Learning more](#learning-more)
  - [Data Enrichment](#data-enrichment)
- [Extending Cartography with Analysis Jobs](#extending-cartography-with-analysis-jobs)
- [Mapping AWS Access Permissions](#mapping-aws-access-permissions)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->


### What [RDS](https://aws.amazon.com/rds/) instances are installed in my [AWS](https://aws.amazon.com/) accounts?
```
MATCH (aws:AWSAccount)-[r:RESOURCE]->(rds:RDSInstance)
return *
```
![Visualization of RDS nodes and AWS nodes](../images/accountsandrds.png)

In this query we asked Neo4j to find all `[:RESOURCE]` relationships from AWSAccounts to RDSInstances, and return the nodes and the `:RESOURCE` relationships.

We will do more interesting things with this result next.


#### ℹ️ Protip - customizing your view
You can adjust the node colors, sizes, and captions by clicking on the node type at the top of the query.  For example, to change the color of an AWSAccount node, first click the "AWSAccount" icon at the top of the view to select the node type
![selecting an AWSAccount node](../images/selectnode.png)

and then pick options on the menu that shows up at the bottom of the view like this:
![customizations](../images/customizeview.png)


### Which RDS instances have [encryption](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Overview.Encryption.html) turned off?
```
MATCH (a:AWSAccount)-[:RESOURCE]->(rds:RDSInstance{storage_encrypted:false})
RETURN a.name, rds.id
```

![Unencrypted RDS instances](../images/unencryptedinstances.png)


The results show up in a table because we specified attributes like `a.name` and `rds.id` in our return statement (as opposed to having it `return *`).  We used the "{}" notation to have the query only return RDSInstances where `storage_encrypted` is set to `False`.

If you want to go back to viewing the graph and not a table, simply make sure you don't have any attributes in your return statement -- use `return *` to return all nodes decorated with a variable label in your `MATCH` statement, or just return the specific nodes and relationships that you want.

Let's look at some other AWS assets now.


### Which [EC2](https://aws.amazon.com/ec2/) instances are directly exposed to the internet?
```
MATCH (instance:EC2Instance{exposed_internet: true})
RETURN instance.instanceid, instance.publicdnsname
```
![EC2 instances open to the internet](../images/ec2-inet-open.png)

These instances are open to the internet either through permissive inbound IP permissions defined on their EC2SecurityGroups or their NetworkInterfaces.

If you know a lot about AWS, you may have noticed that EC2 instances [don't actually have an exposed_internet field](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_Instance.html).  We're able to query for this because Cartography performs some [data enrichment](#data-enrichment) to add this field to EC2Instance nodes.


### Which [S3](https://aws.amazon.com/s3/) buckets have a policy granting any level of anonymous access to the bucket?
```
MATCH (s:S3Bucket)
WHERE s.anonymous_access = true
RETURN s
```
![S3 buckets that allow anon access](../images/anonbuckets.png)

These S3 buckets allow for any user to read data from them anonymously.  Similar to the EC2 instance example above, S3 buckets returned by the S3 API [don't actually have an anonymous_access field](https://docs.aws.amazon.com/AmazonS3/latest/API/API_Bucket.html) and this field is added by one of Cartography's [data augmentation steps](#data-augmentation).

A couple of other things to notice: instead of using the "{}" notation to filter for anonymous buckets, we can use SQL-style `WHERE` clauses.  Also, we used the SQL-style `AS` operator to relabel our output header rows.


### How many unencrypted RDS instances do I have in all my AWS accounts?

Let's go back to analyzing RDS instances.  In an earlier example we queried for RDS instances that have encryption turned off.  We can aggregate this data by AWSAccount with a small change:

```
MATCH (a:AWSAccount)-[:RESOURCE]->(rds:RDSInstance)
WHERE rds.storage_encrypted = false
RETURN a.name as AWSAccount, count(rds) as UnencryptedInstances
```
![Table of unencrypted RDS instances by AWS account](../images/unencryptedcounts.png)


### Learning more
If you want to learn more in depth about Neo4j and Cypher queries you can look at [this tutorial](https://neo4j.com/developer/cypher-query-language/) and see this [reference card](https://neo4j.com/docs/cypher-refcard/current/).

### Data Enrichment
Cartography adds custom attributes to nodes and relationships to point out security-related items of interest.  Unless mentioned otherwise these data augmentation jobs are stored in `cartography/data/jobs/analysis`.  Here is a summary of all of Cartography's custom attributes.

- `exposed_internet` indicates whether the asset is accessible to the public internet.

	- **Elastic Load Balancers**: The `exposed_internet` flag is set to `True` when the load balancer's `scheme` field is set to `internet-facing`, and the load balancer has an attached source security group with rules allowing `0.0.0.0/0` ingress on ports or port ranges matching listeners on the load balancer.  This scheme indicates that the load balancer has a public DNS name that resolves to a public IP address.

	- **Application Load Balancers**: The `exposed_internet` flag is set to `True` when the load balancer's `scheme` field is set to `internet-facing`, and the load balancer has an attached security group with rules allowing `0.0.0.0/0` ingress on ports or port ranges matching listeners on the load balancer.  This scheme indicates that the load balancer has a public DNS name that resolves to a public IP address.

	- **EC2 instances**: The `exposed_internet` flag on an EC2 instance is set to `True` when any of following apply:

		- The instance is part of an EC2 security group or is connected to a network interface connected to an EC2 security group that allows connectivity from the 0.0.0.0/0 subnet.

		- The instance is connected to an Elastic Load Balancer that has its own `exposed_internet` flag set to `True`.

		- The instance is connected to a TargetGroup which is attached to a Listener on an Application Load Balancer (elbv2) that has its own `exposed_internet` flag set to `True`.

	- **ElasticSearch domain**: `exposed_internet` is set to `True` if the ElasticSearch domain has a policy applied to it that makes it internet-accessible.  This policy determination is made by using the [policyuniverse](https://github.com/Netflix-Skunkworks/policyuniverse) library.  The code for this augmentation is implemented at `cartography.intel.aws.elasticsearch._process_access_policy()`.

- `anonymous_access` indicates whether the asset allows access without needing to specify an identity.

	- **S3 buckets**: `anonymous_access` is set to `True` on an S3 bucket if this bucket has an S3Acl with a policy applied to it that allows the [predefined AWS "Authenticated Users" or "All Users" groups](https://docs.aws.amazon.com/AmazonS3/latest/dev/acl-overview.html#specifying-grantee-predefined-groups) to access it.  These determinations are made by using the [policyuniverse](https://github.com/Netflix-Skunkworks/policyuniverse) library.

## Extending Cartography with Analysis Jobs
You can add your own custom attributes and relationships without writing Python code!  Here's [how](../dev/writing-analysis-jobs.md).

## Mapping AWS Access Permissions
Cartography can map permissions between IAM Principals and resources in the graph. Here's [how](permissions-mapping.md).
