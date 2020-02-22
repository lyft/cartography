## Reference
<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Sample queries](#sample-queries)
  - [What RDS instances are installed in my AWS accounts?](#what-rds-instances-are-installed-in-my-aws-accounts)
  - [Which RDS instances have encryption turned off?](#which-rds-instances-have-encryption-turned-off)
  - [Which EC2 instances are exposed (directly or indirectly) to the internet?](#which-ec2-instances-are-exposed-directly-or-indirectly-to-the-internet)
  - [Which ELB LoadBalancers are internet accessible?](#which-elb-loadbalancers-are-internet-accessible)
  - [Which ELBv2 LoadBalancerV2s (Application Load Balancers) are internet accessible?](#which-elbv2-loadbalancerv2s-application-load-balancers-are-internet-accessible)
  - [Which S3 buckets have a policy granting any level of anonymous access to the bucket?](#which-s3-buckets-have-a-policy-granting-any-level-of-anonymous-access-to-the-bucket)
  - [How many unencrypted RDS instances do I have in all my AWS accounts?](#how-many-unencrypted-rds-instances-do-i-have-in-all-my-aws-accounts)
  - [What users have the TotallyFake Chrome extension installed?](#what-users-have-the-totallyfake-chrome-extension-installed)
  - [What users have installed extensions that are risky based on CRXcavator scoring?](#what-users-have-installed-extensions-that-are-risky-based-on-crxcavator-scoring)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->
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

#### What users have the TotallyFake Chrome extension installed?
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
