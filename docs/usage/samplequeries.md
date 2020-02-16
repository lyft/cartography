## Reference


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

