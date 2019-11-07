# Cartography
Cartography is a Python tool that consolidates infrastructure assets and the relationships between them in an intuitive graph view powered by a [Neo4j](https://www.neo4j.com) database.

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Why Cartography?](#why-cartography)
- [Installation](#installation)
- [Usage Tutorial](#usage-tutorial)
  - [ℹ️ Already know how to query Neo4j?  You can skip to our reference material!](#-already-know-how-to-query-neo4j--you-can-skip-to-our-reference-material)
  - [What RDS instances are installed in my AWS accounts?](#what-rds-instances-are-installed-in-my-aws-accounts)
    - [ℹ️ Protip - customizing your view](#-protip---customizing-your-view)
  - [Which RDS instances have encryption turned off?](#which-rds-instances-have-encryption-turned-off)
  - [Which EC2 instances are directly exposed to the internet?](#which-ec2-instances-are-directly-exposed-to-the-internet)
  - [Which S3 buckets have a policy granting any level of anonymous access to the bucket?](#which-s3-buckets-have-a-policy-granting-any-level-of-anonymous-access-to-the-bucket)
  - [How many unencrypted RDS instances do I have in all my AWS accounts?](#how-many-unencrypted-rds-instances-do-i-have-in-all-my-aws-accounts)
  - [Learning more](#learning-more)
- [Extending Cartography with Analysis Jobs](#extending-cartography-with-analysis-jobs)
- [Contributing](#contributing)
  - [Code of conduct](#code-of-conduct)
  - [Contributing code](#contributing-code)
    - [How to test your code contributions](#how-to-test-your-code-contributions)
    - [Sign the Contributor License Agreement (CLA)](#sign-the-contributor-license-agreement-cla)
    - [File issues in Github](#file-issues-in-github)
    - [Submit pull requests](#submit-pull-requests)
- [Reference](#reference)
  - [Schema](#schema)
  - [Sample queries](#sample-queries)
    - [What RDS instances are installed in my AWS accounts?](#what-rds-instances-are-installed-in-my-aws-accounts-1)
    - [Which RDS instances have encryption turned off?](#which-rds-instances-have-encryption-turned-off-1)
    - [Which EC2 instances are exposed (directly or indirectly) to the internet?](#which-ec2-instances-are-exposed-directly-or-indirectly-to-the-internet)
    - [Which ELB LoadBalancers are internet accessible?](#which-elb-loadbalancers-are-internet-accessible)
    - [Which ELBv2 LoadBalancerV2s (Application Load Balancers) are internet accessible?](#which-elbv2-loadbalancerv2s-application-load-balancers-are-internet-accessible)
    - [Which S3 buckets have a policy granting any level of anonymous access to the bucket?](#which-s3-buckets-have-a-policy-granting-any-level-of-anonymous-access-to-the-bucket-1)
    - [How many unencrypted RDS instances do I have in all my AWS accounts?](#how-many-unencrypted-rds-instances-do-i-have-in-all-my-aws-accounts-1)
    - [What users have the TotallyFake extension installed?](#what-users-have-the-totallyfake-extension-installed)
    - [What users have installed extensions that are risky based on CRXcavator scoring?](#what-users-have-installed-extensions-that-are-risky-based-on-crxcavator-scoring)
  - [Data Enrichment](#data-enrichment)
- [Multiple AWS Account Setup](#multiple-aws-account-setup)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Why Cartography?
Cartography aims to enable a broad set of exploration and automation scenarios.  It is particularly good at exposing otherwise hidden dependency relationships between your service's assets so that you may validate assumptions about security risks.

Service owners can generate asset reports, Red Teamers can discover attack paths, and Blue Teamers can identify areas for security improvement.   All can benefit from using the graph for manual exploration through a web frontend interface, or in an automated fashion by calling the APIs.

Cartography is not the only [security](https://github.com/dowjones/hammer) [graph](https://github.com/BloodHoundAD/BloodHound) [tool](https://github.com/Netflix/security_monkey) [out](https://github.com/vysecurity/ANGRYPUPPY) [there](https://github.com/duo-labs/cloudmapper), but it differentiates itself by being fully-featured yet generic and [extensible](docs/writing-analysis-jobs.md) enough to help make anyone better understand their risk exposure, regardless of what platforms they use.  Rather than being focused on one core scenario or attack vector like the other linked tools, Cartography focuses on flexibility and exploration.

You can learn more about the story behind Cartography in our [presentation at BSidesSF 2019](https://www.youtube.com/watch?v=ZukUmZSKSek).


## Installation

Time to set up the server that will run Cartography.  Cartography _should_ work on both Linux and Windows servers, but bear in mind we've only tested it in Linux so far.  Cartography requires Python 3.6 or greater.

1. **Get and install the Neo4j graph database** on your server.

	1. Go to the [Neo4j download page](https://neo4j.com/download-center/#releases), click "Community Server" and download Neo4j Community Edition 3.5.\*.

			⚠️ At this time we run our automated tests on Neo4j version 3.5.\*.  Other versions may work but are not explicitly supported. ⚠️

	1. [Install](https://neo4j.com/docs/operations-manual/current/installation/) Neo4j on the server you will run Cartography on.

1. If you're an AWS user, **prepare your AWS account(s)**

	- **If you only have a single AWS account**

		1. Set up an AWS identity (user, group, or role) for Cartography to use.  Ensure that this identity has the built-in AWS [SecurityAudit policy](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_job-functions.html#jf_security-auditor) (arn:aws:iam::aws:policy/SecurityAudit) attached.  This policy grants access to read security config metadata.
		1. Set up AWS credentials to this identity on your server, using a `config` and 	`credential` file.  For details, see AWS' [official guide](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html).

 	- **If you want to pull from multiple AWS accounts**, see [here](#multiple-aws-account-setup).

 1. If you're a GCP user, **prepare your GCP credential(s)**

    1. Create an identity - either a User Account or a Service Account - for Cartography to run as
    1. Ensure that this identity has the [securityReviewer](https://cloud.google.com/iam/docs/understanding-roles) role attached to it.
    1. Ensure that the machine you are running Cartography on can authenticate to this identity.
        - **Method 1**: You can do this by setting your `GOOGLE_APPLICATION_CREDENTIALS` environment variable to point to a json file containing your credentials.  As per SecurityCommonSense™️, please ensure that only the user account that runs Cartography has read-access to this sensitive file.
        - **Method 2**: If you are running Cartography on a GCE instance or other GCP service, you can make use of the credential management provided by the default service accounts on these services.  See the [official docs](https://cloud.google.com/docs/authentication/production) on Application Default Credentials for more details.

1. If you're a CRXcavator user, **prepare your CRXcavator API key**

    1. Generate an API key from your CRXcavator [user page](https://crxcavator.io/user/settings#)
    1. Populate the following environment variables in the shell running Cartography
        1. CRXCAVATOR_URL - the full URL to the CRXcavator API. https://api.crxcavator.io/v1 as of 07/09/19
        1. CREDENTIALS_CRXCAVATOR_API_KEY - your API key generated in the previous step. Note this is a credential and should be stored in an appropriate secret store to be populated securely into your runtime environment.
    1. If the credentials are configured, the CRXcavator module will run automatically on the next sync

1.  If you're using GSuite, **prepare your GSuite Credential**

    Ingesting GSuite Users and Groups utilizes the [Google Admin SDK](https://developers.google.com/admin-sdk/).

    1. [Enable Google API access](https://support.google.com/a/answer/60757?hl=en)
    1. Create a new G Suite user account and accept the Terms of Service. This account will be used as the domain-wide delegated access.
    1. [Perform G Suite Domain-Wide Delegation of Authority](https://developers.google.com/admin-sdk/directory/v1/guides/delegation)
    1.  Download the service account's credentials
    1.  Export the environmental variables:
        1. `GSUITE_GOOGLE_APPLICATION_CREDENTIALS` - location of the credentials file.
        1. `GSUITE_DELEGATED_ADMIN` - email address that you created in step 2

1. If you're using Okta intel module, **prepare your Okta API token**
    1. Generate your API token by following the steps from [Okta Create An API Token documentation](https://developer.okta.com/docs/guides/create-an-api-token/overview/)
    1. Populate an environment variable with the API token. You can pass the environment variable name via the cli --okta-api-key-env-var parameter
    1. Use the cli --okta-org-id parameter with the organization id you want to query. The organization id is the first part of the Okta url for your organization.
	1. If you are using Okta to [administer AWS as a SAML provider](https://saml-doc.okta.com/SAML_Docs/How-to-Configure-SAML-2.0-for-Amazon-Web-Service#scenarioC) then the module will automatically match OktaGroups to the AWSRole they control access for
		- If you are using a regex other than the standard okta group to role regex `^aws\#\S+\#(?{{role}}[\w\-]+)\#(?{{accountid}}\d+)$` defined in [Step 5: Enabling Group Based Role Mapping in Okta](https://saml-doc.okta.com/SAML_Docs/How-to-Configure-SAML-2.0-for-Amazon-Web-Service#scenarioC)  then you can specify your regex with the --okta-saml-role-regex parameter.

1. **Get and run Cartography**

	1. Run `pip install cartography` to install our code.

	1. Finally, to sync your data:

		- If you have one AWS account, run

			```
			cartography --neo4j-uri <uri for your neo4j instance; usually bolt://localhost:7687>
			```

		- If you have more than one AWS account, run

			```
			AWS_CONFIG_FILE=/path/to/your/aws/config cartography --neo4j-uri <uri for your neo4j instance; usually bolt://localhost:7687> --aws-sync-all-profiles
			```

		The sync will pull data from your configured accounts and ingest data to Neo4j!  This process might take a long time if your account has a lot of assets.


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

#### How to test your code contributions

See [these docs](docs/developer-guide.md).

#### Sign the Contributor License Agreement (CLA)

We require a CLA for code contributions, so before we can accept a pull request
we need to have a signed CLA. Please [visit our CLA service](https://oss.lyft.com/cla)
and follow the instructions to sign the CLA.

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
Detailed view of [our schema and all data types](docs/schema/index.md) 😁.


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

#### Which [EC2](https://aws.amazon.com/ec2/) instances are exposed (directly or indirectly) to the internet?
```
MATCH (instance:EC2Instance{exposed_internet: true})
RETURN instance.instanceid, instance.publicdnsname
```

#### Which [ELB](https://aws.amazon.com/elasticloadbalancing/) LoadBalancers are internet accessible?
```
MATCH (elb:LoadBalancer{exposed_internet: true})—->(listener:ELBListener)
RETURN elb.dnsname, listener.port
ORDER by elb.dnsname, listener.port
```

#### Which [ELBv2](https://aws.amazon.com/elasticloadbalancing/) LoadBalancerV2s (Application Load Balancers) are internet accessible?
```
MATCH (elbv2:LoadBalancerV2{exposed_internet: true})—->(listener:ELBV2Listener)
RETURN elbv2.dnsname, listener.port
ORDER by elbv2.dnsname, listener.port
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

#### What users have the TotallyFake extension installed?
```
MATCH (u:GSuiteUser)-[r:INSTALLS]->(ext:ChromeExtension)
WHERE ext.name CONTAINS 'TotallyFake'
return ext.name, ext.version, u.email
```

#### What users have installed extensions that are risky based on [CRXcavator scoring](https://crxcavator.io/docs#/risk_breakdown)?
Risk > 200 is evidence of 3 or more critical risks or many high risks in the extension.
```
MATCH (u:GSuiteUser)-[r:INSTALLS]->(ext:ChromeExtension)
WHERE ext.risk_total > 200
return ext.name, ext.version, u.email
```

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
