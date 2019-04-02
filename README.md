# Cartography
Cartography is a Python tool that consolidates infrastructure assets and the relationships between them in an intuitive graph view powered by a [Neo4j](https://www.neo4j.com) database.

## Why Cartography?
Cartography aims to enable a broad set of exploration and automation scenarios.  It is particularly good at exposing otherwise hidden dependency relationships between your service's assets so that you may validate assumptions about security risks.  

Service owners can generate asset reports, Red Teamers can discover attack paths, and Blue Teamers can identify areas for security improvement.   All can benefit from using the graph for manual exploration through a web frontend interface, or in an automated fashion by calling the APIs.

Cartography is not the only [security](https://github.com/dowjones/hammer) [graph](https://github.com/BloodHoundAD/BloodHound) [tool](https://github.com/Netflix/security_monkey) [out](https://github.com/vysecurity/ANGRYPUPPY) [there](https://github.com/duo-labs/cloudmapper), but it differentiates itself by being fully-featured yet generic and [extensible](docs/writing-analysis-jobs.md) enough to help make anyone better understand their risk exposure, regardless of what platforms they use.  Rather than being focused on one core scenario or attack vector like the other linked tools, Cartography focuses on flexibility and exploration.

You can learn more about the story behind Cartography in our [presentation at BSidesSF 2019](https://www.youtube.com/watch?v=ZukUmZSKSek).


## Installation

Time to set up the server that will run Cartography.  Cartography _should_ work on both Linux and Windows servers, but bear in mind we've only tested it in Linux so far.  Cartography requires Python 3.4 or greater.

1. **Get and install the Neo4j graph database** on your server.

	1. Go to the [Neo4j download page](https://neo4j.com/download-center/#releases), click "Community Server" and download Neo4j Community Edition 3.3.9.

			⚠️ At this time we only support version 3.3.*. ⚠️
			
	2. [Install](https://neo4j.com/docs/operations-manual/current/installation/) Neo4j on the server you will run Cartography on.


2. **Prepare your AWS account(s)** 

	- **If you only have a single AWS account**
		
		1. Set up an AWS identity (user, group, or role) for Cartography to use.  Ensure that this identity has the built-in AWS [SecurityAudit policy](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_job-functions.html#jf_security-auditor) (arn:aws:iam::aws:policy/SecurityAudit) attached.  This policy grants access to read security config metadata.
		2. Set up AWS credentials to this identity on your server, using a `config` and 	`credential` file.  For details, see AWS' [official guide](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html).
  
 	- **If you want to pull from multiple AWS accounts**, see [here](#multiple-aws-account-setup). 

	
5. **Get and run Cartography** 

	1. Run `pip install cartography` to install our code.

	2. Finally, to sync your data:

		- If you have one AWS account, run

			```
			cartography --neo4j-uri <uri for your neo4j instance; usually bolt://localhost:7687>
			```
		
		- If you have more than one AWS account, run

			```
			AWS_CONFIG_FILE=/path/to/your/aws/config cartography --neo4j-uri <uri for your neo4j instance; usually bolt://localhost:7687> --aws-sync-all-profiles
			```
		
		The sync will pull data from your AWS accounts and ingest data to Neo4j!  This process might take a long time if your account has a lot of assets.


## Usage Tutorial

Once everything has been installed and synced, you can view the Neo4j web interface at http://localhost:7474.  You can view the reference on this [here](https://neo4j.com/developer/guide-neo4j-browser/#_installing_and_starting_neo4j_browser).

### ℹ️ Already know [how to query Neo4j](https://neo4j.com/developer/cypher-query-language/)?  You can skip to our reference material!
If you already know Neo4j and just need to know what are the nodes, attributes, and graph relationships for our representation of infrastructure assets, you can skip this handholdy walkthrough and see our [quick canned queries](#sample-queries).  You can also view our [reference material](#reference). 


### What [RDS](https://aws.amazon.com/rds/) instances are installed in my [AWS](https://aws.amazon.com/) accounts?
```
MATCH (aws:AWSAccount)-[r:RESOURCE]->(rds:RDSInstance) 
return *
```
![Visualization of RDS nodes and AWS nodes](docs/images/accountsandrds.png)

In this query we asked Neo4j to find all `[:RESOURCE]` relationships from AWSAccounts to RDSInstances, and return the nodes and the `:RESOURCE` relationships.

We will do more interesting things with this result next.


#### ℹ️ Protip - customizing your view
You can adjust the node colors, sizes, and captions by clicking on the node type at the top of the query.  For example, to change the color of an AWSAccount node, first click the "AWSAccount" icon at the top of the view to select the node type 
![selecting an AWSAccount node](docs/images/selectnode.png) 

and then pick options on the menu that shows up at the bottom of the view like this: 
![customizations](docs/images/customizeview.png)


### Which RDS instances have [encryption](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Overview.Encryption.html) turned off?
```
MATCH (a:AWSAccount)-[:RESOURCE]->(rds:RDSInstance{storage_encrypted:false}) 
RETURN a.name, rds.id
```

![Unencrypted RDS instances](docs/images/unencryptedinstances.png)


The results show up in a table because we specified attributes like `a.name` and `rds.id` in our return statement (as opposed to having it `return *`).  We used the "{}" notation to have the query only return RDSInstances where `storage_encrypted` is set to `False`.

If you want to go back to viewing the graph and not a table, simply make sure you don't have any attributes in your return statement -- use `return *` to return all nodes decorated with a variable label in your `MATCH` statement, or just return the specific nodes and relationships that you want.

Let's look at some other AWS assets now.


### Which [EC2](https://aws.amazon.com/ec2/) instances are directly exposed to the internet? 
```
MATCH (instance:EC2Instance{exposed_internet: true}) 
RETURN instance.instanceid, instance.publicdnsname 
```
![EC2 instances open to the internet](docs/images/ec2-inet-open.png)

These instances are open to the internet either through permissive inbound IP permissions defined on their EC2SecurityGroups or their NetworkInterfaces. 

If you know a lot about AWS, you may have noticed that EC2 instances [don't actually have an exposed_internet field](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_Instance.html).  We're able to query for this because Cartography performs some [data enrichment](#data-enrichment) to add this field to EC2Instance nodes.


### Which [S3](https://aws.amazon.com/s3/) buckets have a policy granting any level of anonymous access to the bucket?
```
MATCH (s:S3Bucket) 
WHERE s.anonymous_access = true
RETURN s
```
![S3 buckets that allow anon access](docs/images/anonbuckets.png)

These S3 buckets allow for any user to read data from them anonymously.  Similar to the EC2 instance example above, S3 buckets returned by the S3 API [don't actually have an anonymous_access field](https://docs.aws.amazon.com/AmazonS3/latest/API/API_Bucket.html) and this field is added by one of Cartography's [data augmentation steps](#data-augmentation).

A couple of other things to notice: instead of using the "{}" notation to filter for anonymous buckets, we can use SQL-style `WHERE` clauses.  Also, we used the SQL-style `AS` operator to relabel our output header rows.


### How many unencrypted RDS instances do I have in all my AWS accounts?

Let's go back to analyzing RDS instances.  In an earlier example we queried for RDS instances that have encryption turned off.  We can aggregate this data by AWSAccount with a small change:

```
MATCH (a:AWSAccount)-[:RESOURCE]->(rds:RDSInstance) 
WHERE rds.storage_encrypted = false 
RETURN a.name as AWSAccount, count(rds) as UnencryptedInstances
```
![Table of unencrypted RDS instances by AWS account](docs/images/unencryptedcounts.png)


### Learning more
If you want to learn more in depth about Neo4j and Cypher queries you can look at [this tutorial](https://neo4j.com/developer/cypher-query-language/) and see this [reference card](https://neo4j.com/docs/cypher-refcard/current/).


## Extending Cartography with Analysis Jobs
You can add your own custom attributes and relationships without writing Python code!  Here's [how](docs/writing-analysis-jobs.md).


## Contributing

### Code of conduct

This project is governed by [Lyft's code of conduct](https://github.com/lyft/code-of-conduct).
All contributors and participants agree to abide by its terms.

### Contributing code

#### Sign the Contributor License Agreement (CLA)

We require a CLA for code contributions, so before we can accept a pull request
we need to have a signed CLA. Please [visit our CLA service](https://oss.lyft.com/cla)
follow the instructions to sign the CLA.

#### File issues in Github

In general all enhancements or bugs should be tracked via github issues before
PRs are submitted. We don't require them, but it'll help us plan and track.

When submitting bugs through issues, please try to be as descriptive as
possible. It'll make it easier and quicker for everyone if the developers can
easily reproduce your bug.

#### Submit pull requests

Our only method of accepting code changes is through Github pull requests.


## Reference

### Schema
Detailed view of [our schema and all data types](docs/schema.md) 😁.


### Sample queries
#### What [RDS](https://aws.amazon.com/rds/) instances are installed in my [AWS](https://aws.amazon.com/) accounts?
```
MATCH (aws:AWSAccount)-[r:RESOURCE]->(rds:RDSInstance) 
return *
```

#### Which RDS instances have [encryption](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Overview.Encryption.html) turned off?
```
MATCH (a:AWSAccount)-[:RESOURCE]->(rds:RDSInstance{storage_encrypted:false}) 
return a.name, rds.id
```

#### Which [EC2](https://aws.amazon.com/ec2/) instances are directly exposed to the internet? 
```
MATCH (instance:EC2Instance{exposed_internet: true}) 
RETURN instance.instanceid, instance.publicdnsname 
```

#### Which [S3](https://aws.amazon.com/s3/) buckets have a policy granting any level of anonymous access to the bucket?
```
MATCH (s:S3Bucket) 
WHERE s.anonymous_access = true
RETURN s
```

#### How many unencrypted RDS instances do I have in all my AWS accounts?

```
MATCH (a:AWSAccount)-[:RESOURCE]->(rds:RDSInstance) 
WHERE rds.storage_encrypted = false 
return a.name as AWSAccount, count(rds) as UnencryptedInstances
```

### Data Enrichment
Cartography adds custom attributes to nodes and relationships to point out security-related items of interest.  Unless mentioned otherwise these data augmentation jobs are stored in `cartography/data/jobs/analysis`.  Here is a summary of all of Cartography's custom attributes.

- `exposed_internet` indicates whether the asset is accessible to the public internet.

	- **Elastic Load Balancers**: The `exposed_internet` flag is set to `True` when the load balancer's `scheme` field is set to `internet-facing`.  This indicates that the load balancer has a public DNS name that resolves to a public IP address. 

	- **EC2 instances**: The `exposed_internet` flag on an EC2 instance is set to `True` when any of following apply:

		- The instance is part of an EC2 security group or is connected to a network interface connected to an EC2 security group that allows connectivity from the 0.0.0.0/0 subnet.

		- The instance is connected to an Elastic Load Balancer that has its own `exposed_internet` flag set to `True`.

	- **ElasticSearch domain**: `exposed_internet` is set to `True` if the ElasticSearch domain has a policy applied to it that makes it internet-accessible.  This policy determination is made by using the [policyuniverse](https://github.com/Netflix-Skunkworks/policyuniverse) library.  The code for this augmentation is implemented at `cartography.intel.aws.elasticsearch._process_access_policy()`.

- `anonymous_access` indicates whether the asset allows access without needing to specify an identity.

	- **S3 buckets**: `anonymous_access` is set to `True` on an S3 bucket if this bucket has an S3Acl with a policy applied to it that allows the [predefined AWS "Authenticated Users" or "All Users" groups](https://docs.aws.amazon.com/AmazonS3/latest/dev/acl-overview.html#specifying-grantee-predefined-groups) to access it.  These determinations are made by using the [policyuniverse](https://github.com/Netflix-Skunkworks/policyuniverse) library.


## Multiple AWS Account Setup
There are many ways to allow Cartography to pull from more than one AWS account.  We can't cover all of them, but we _can_ show you the way we have things set up at Lyft.  In this scenario we will assume that you are going to run Cartography on an EC2 instance.

1. Pick one of your AWS accounts to be the "**Hub**" account.  This Hub account will pull data from all of your other accounts - we'll call those "**Spoke**" accounts.

2. **Set up the IAM roles**: Create an IAM role named `cartography-read-only` on _all_ of your accounts.  Configure the role on all accounts as follows:
	1. Attach the built-in AWS [SecurityAudit IAM policy](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_job-functions.html#jf_security-auditor) (arn:aws:iam::aws:policy/SecurityAudit) to the role.  This grants access to read security config metadata.
	2. Set up a trust relationship so that the Spoke accounts will allow the Hub account to assume the `cartography-read-only` role.  The resulting trust relationship should look something like this:

		```	               
		{
		  "Version": "2012-10-17",
		  "Statement": [
		    {
		      "Effect": "Allow",
		      "Principal": {
		        "AWS": "arn:aws:iam::<Hub's account number>:root"
		      },
		      "Action": "sts:AssumeRole"
		    }
		  ]
		}
		```
	3. Allow a role in the Hub account to **assume the `cartography-read-only` role** on your Spoke account(s).
		
		- On the Hub account, create a role called `cartography-service`.
		- On this new `cartography-service` role, add an inline policy with the following JSON:

			```
			{
			  "Version": "2012-10-17",
			  "Statement": [
			    {
			      "Effect": "Allow",
			      "Resource": "arn:aws:iam::*:role/cartography-read-only",
			      "Action": "sts:AssumeRole"
			    }
			  ]
			}
			```
	
			This allows the Hub role to assume the `cartography-read-only` role on your Spoke accounts.  
		- When prompted to name the policy, you can name it anything you want - perhaps `CartographyAssumeRolePolicy`.

3. **Set up your EC2 instance to correctly access these AWS identities**

	1. Attach the `cartography-service` role to the EC2 instance that you will run Cartography on.  You can do this by following [these official AWS steps](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-roles-for-amazon-ec2.html#attach-iam-role).
		
	2. Ensure that the `[default]` profile in your `AWS_CONFIG_FILE` file (default `~/.aws/config` in Linux, and `%UserProfile%\.aws\config` in Windows) looks like this:

			[default]
			region=<the region of your Hub account, e.g. us-east-1>
			output=json


	3.  Add a profile for each AWS account you want Cartography to sync with to your `AWS_CONFIG_FILE`.  It will look something like this:
	
		```
		[profile accountname1]
		role_arn = arn:aws:iam::<AccountId#1>:role/cartography-read-only
		region=us-east-1
		output=json
		credential_source = Ec2InstanceMetadata
		
		[profile accountname2]
		role_arn = arn:aws:iam::<AccountId#2>:role/cartography-read-only
		region=us-west-1
		output=json
		credential_source = Ec2InstanceMetadata
		
		... etc ...
		```	
