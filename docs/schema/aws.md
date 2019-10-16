# Cartography - Amazon Web Services Schema

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [AWSAccount](#awsaccount)
  - [Relationships](#relationships)
- [AWSCidrBlock](#awscidrblock)
  - [AWSIpv4CidrBlock](#awsipv4cidrblock)
  - [AWSIpv6CidrBlock](#awsipv6cidrblock)
  - [Relationships](#relationships-1)
- [AWSGroup](#awsgroup)
  - [Relationships](#relationships-2)
- [AWSPolicy](#awspolicy)
  - [Relationships](#relationships-3)
- [AWSPrincipal](#awsprincipal)
  - [Relationships](#relationships-4)
- [AWSPrincipal::AWSUser](#awsprincipalawsuser)
  - [Relationships](#relationships-5)
- [AWSPrincipal::AWSRole](#awsprincipalawsrole)
  - [Relationships](#relationships-6)
- [AWSVpc](#awsvpc)
  - [Relationships](#relationships-7)
- [AccountAccessKey](#accountaccesskey)
  - [Relationships](#relationships-8)
- [DBSubnetGroup](#dbsubnetgroup)
  - [Relationships](#relationships-9)
- [DNSRecord](#dnsrecord)
  - [Relationships](#relationships-10)
- [DNSRecord::AWSDNSRecord](#dnsrecordawsdnsrecord)
  - [Relationships](#relationships-11)
- [DNSZone](#dnszone)
  - [Relationships](#relationships-12)
- [DNSZone::AWSDNSZone](#dnszoneawsdnszone)
  - [Relationships](#relationships-13)
- [DynamoDBTable](#dynamodbtable)
  - [Relationships](#relationships-14)
- [EC2Instance](#ec2instance)
  - [Relationships](#relationships-15)
- [EC2KeyPair](#ec2keypair)
  - [Relationships](#relationships-16)
- [EC2Reservation](#ec2reservation)
  - [Relationships](#relationships-17)
- [EC2SecurityGroup](#ec2securitygroup)
  - [Relationships](#relationships-18)
- [EC2Subnet](#ec2subnet)
  - [Relationships](#relationships-19)
- [ESDomain](#esdomain)
  - [Relationships](#relationships-20)
- [Endpoint](#endpoint)
  - [Relationships](#relationships-21)
- [Endpoint::ELBListener](#endpointelblistener)
  - [Relationships](#relationships-22)
- [Ip](#ip)
  - [Relationships](#relationships-23)
- [IpRule](#iprule)
  - [Relationships](#relationships-24)
- [IpRule::IpPermissionInbound](#ipruleippermissioninbound)
  - [Relationships](#relationships-25)
- [LoadBalancer](#loadbalancer)
  - [Relationships](#relationships-26)
- [NetworkInterface](#networkinterface)
  - [Relationships](#relationships-27)
- [RDSInstance](#rdsinstance)
  - [Relationships](#relationships-28)
- [S3Acl](#s3acl)
  - [Relationships](#relationships-29)
- [S3Bucket](#s3bucket)
  - [Relationships](#relationships-30)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->


## AWSAccount

Representation of an AWS Account.

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|name| The name of the account|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The AWS Account ID number|

### Relationships
- Many node types belong to an `AWSAccount`.

	```
	(AWSAccount)-[RESOURCE]->(AWSDNSZone,
                              AWSGroup,
                              AWSPrincipal,
                              AWSUser,
                              AutoScalingGroup,
                              DNSZone,
                              DynamoDBTable,
                              EC2Instance,
                              EC2Reservation,
                              EC2SecurityGroup,
                              ESDomain,
                              LoadBalancer,
                              AWSVpc)
	```

- An `AWSPolicy` node is defined for an `AWSAccount`.

	```
	(AWSAccount)-[AWS_POLICY]->(AWSPolicy)
	```

- `AWSRole` nodes are defined in `AWSAccount` nodes.

	```
	(AWSAccount)-[AWS_ROLE]->(AWSRole)
	```

## AWSCidrBlock
### AWSIpv4CidrBlock
### AWSIpv6CidrBlock
Representation of an [AWS CidrBlock used in VPC configuration](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_VpcCidrBlockAssociation.html).
The `AWSCidrBlock` defines the base label
type for `AWSIpv4CidrBlock` and `AWSIpv6CidrBlock`

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|cidr\_block| The CIDR block|
|block\_state| The state of the block|
|association\_id| the association id if the block is associated to a VPC
|lastupdated| Timestamp of the last time the node was updated|
|**id**| Unique identifier defined with the VPC association and the cidr\_block

### Relationships
- `AWSVpc` association
  ```
  (AWSVpc)-[BLOCK_ASSOCIATION]->(AWSCidrBlock)
  ```
- VPC peering where two `AWSCidrBlock` have peering between them
  ```
  (AWSCidrBlock)<-[VPC_PEERING]-(AWSCidrBlock)
  ```
  Example of high level view of peering (without security group permissions)
  ```
  MATCH p=(:AWSAccount)-[:RESOURCE|BLOCK_ASSOCIATION*..]->(:AWSCidrBlock)<-[r:VPC_PEERING]->(:AWSCidrBlock)<-[:RESOURCE|BLOCK_ASSOCIATION*..]-(:AWSAccount)
  RETURN p
  ```

  Exploring detailed inbound peering rules
  ```
  MATCH (outbound_account:AWSAccount)-[:RESOURCE|BLOCK_ASSOCIATION*..]->(:AWSCidrBlock)<-[r:VPC_PEERING]->(inbound_block:AWSCidrBlock)<-[:BLOCK_ASSOCIATION]-(inbound_vpc:AWSVpc)<-[:RESOURCE]-(inbound_account:AWSAccount)
  WITH inbound_vpc, inbound_block, outbound_account, inbound_account
  MATCH (inbound_range:IpRange{id: inbound_block.cidr_block})-[:MEMBER_OF_IP_RULE]->(inbound_rule:IpPermissionInbound)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(inbound_group:EC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(inbound_vpc)
  RETURN outbound_account.name, inbound_account.name, inbound_range.range, inbound_rule.fromport, inbound_rule.toport, inbound_rule.protocol, inbound_group.name, inbound_vpc.id
  ```

## AWSGroup

Representation of AWS [IAM Groups](https://docs.aws.amazon.com/IAM/latest/APIReference/API_Group.html).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated|  Timestamp of the last time the node was updated |
|path | The path to the group (IAM identifier, see linked docs above for details)|
| groupid| Unique string identifying the group |
|name | The friendly name that identifies the group|
| createdate| ISO 8601 date-time string when the group was created|
|**arn** | The AWS-global identifier for this group|

### Relationships
- Objects part of an AWSGroup may assume AWSRoles.

	```
	(AWSGroup)-[STS_ASSUMEROLE_ALLOW]->(AWSRole)
	```

- AWSUsers and AWSPrincipals can be members of AWSGroups.

	```
	(AWSUser, AWSPrincipal)-[MEMBER_AWS_GROUP]->(AWSGroup)
	```

- AWSGroups belong to AWSAccounts.

	```
	(AWSAccount)-[RESOURCE]->(AWSGroup)
	```


## AWSPolicy

Representation of an [AWS Policy](https://docs.aws.amazon.com/IAM/latest/APIReference/API_Policy.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
|path | The path to the policy |
| defaultversionid| The identifier for the version of the policy that is set as the default version |
| isattachable | Specifies whether the policy can be attaced to an IAM user, group, or role |
|updatedate | ISO 8601 date-time when the policy was last updated |
| policyid | The stable and unique string identifying the policy, see the API docs above for specifics|
| attachmentcount | Number of entities (users, groups, and roles) that the policy is attached to|
| name | The friendly name (not ARN) identifying the policy |
| createdate | ISO 8601 date-time when the policy was created|
| **arn** | The AWS-unique identifier for this object |

### Relationships

- An `AWSPolicy` node is defined in an `AWSAccount`.

	```
	(AWSAccount)-[AWS_POLICY]->(AWSPolicy)
	```


## AWSPrincipal
Representation of an [AWSPrincipal](https://docs.aws.amazon.com/IAM/latest/APIReference/API_User.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| path | The path to the principal |
| name | The friendly name of the principal |
| createdate | ISO 8601 date-time when the principal was created |
| **arn** | AWS-unique identifier for this object |
| userid | The stable and unique string identifying the principal.  |
| passwordlastused | Datetime when this principal's password was last used


### Relationships

- AWS Principals can be members of AWS Groups.

	```
	(AWSPrincipal)-[MEMBER_AWS_GROUP]->(AWSGroup)
	```

- This AccountAccessKey is used to authenticate to this AWSPrincipal.

	```
	(AWSPrincipal)-[AWS_ACCESS_KEY]->(AccountAccessKey)
	```

- AWS Roles can trust AWS Principals.

    ```
    (AWSRole)-[TRUSTS_AWS_PRINCIPAL]->(AWSPrincipal)
    ```

- AWS Accounts contain AWS Principals.

	```
	(AWSAccount)-[RESOURCE]->(AWSPrincipal)
	```

## AWSPrincipal::AWSUser
Representation of an [AWSUser](https://docs.aws.amazon.com/IAM/latest/APIReference/API_User.html).  An AWS User is a type of AWS Principal.

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| path | The path to the user |
| name | The friendly name of the user |
| createdate | ISO 8601 date-time when the user was created |
| **arn** | AWS-unique identifier for this object |
| userid | The stable and unique string identifying the user.  |
| passwordlastused | Datetime when this user's password was last used

### Relationships
- AWS Users can be members of AWS Groups.

	```
	(AWSUser)-[MEMBER_AWS_GROUP]->(AWSGroup)
	```

- AWS Users can assume AWS Roles.

	```
	(AWSUser)-[STS_ASSUMEROLE_ALLOW]->(AWSRole)
	```

- This AccountAccessKey is used to authenticate to this AWSUser

	```
	(AWSUser)-[AWS_ACCESS_KEY]->(AccountAccessKey)
	```

- AWS Accounts contain AWS Users.

	```
	(AWSAccount)-[RESOURCE]->(AWSUser)
	```


## AWSPrincipal::AWSRole

Representation of an AWS [IAM Role](https://docs.aws.amazon.com/IAM/latest/APIReference/API_Role.html). An AWS Role is a type of AWS Principal.

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| roleid | The stable and unique string identifying the role.  |
| name | The friendly name that identifies the role.|
| createdate| The date and time, in ISO 8601 date-time format, when the role was created. |
| **arn** | AWS-unique identifier for this object |


### Relationships

- Some AWS Groups, Users, and Principals can assume AWS Roles.

    ```
    (AWSGroup, AWSUser)-[STS_ASSUMEROLE_ALLOW]->(AWSRole)
    ```

- Some AWS Roles can assume other AWS Roles.

    ```
    (AWSRole)-[STS_ASSUMEROLE_ALLOW]->(AWSRole)
    ```

- Some AWS Roles trust AWS Principals.

    ```
    (AWSRole)-[TRUSTS_AWS_PRINCIPAL]->(AWSPrincipal)
    ```

- AWS Roles are defined in AWS Accounts.

    ```
    (AWSAccount)-[AWS_ROLE]->(AWSRole)
    ```

## AWSVpc
Representation of an [AWS CidrBlock used in VPC configuration](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_VpcCidrBlockAssociation.html).
More information on https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-vpcs.html

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|vpcid| The VPC unique identifier|
|primary\_cidr\_block|The primary IPv4 CIDR block for the VPC.|
|instance\_tenancy| The allowed tenancy of instances launched into the VPC.|
|state| The current state of the VPC.|
|region| (optional) the region of this VPC.  This field is only available on VPCs in your account.  It is not available on VPCs that are external to your account and linked via a VPC peering relationship.
|**id**| Unique identifier defined VPC node (vpcid)

### Relationships
- `AWSAccount` resource
  ```
  (AWSAccount)-[RESOURCE]->(AWSVpc)
  ```
- `AWSVpc` and `AWSCidrBlock` association
  ```
  (AWSVpc)-[BLOCK_ASSOCIATION]->(AWSCidrBlock)
  ```
- `AWSVpc` and `EC2SecurityGroup` membership association
  ```
  (AWSVpc)<-[MEMBER_OF_EC2_SECURITY_GROUP]-(EC2SecurityGroup)
  ```

## AccountAccessKey

Representation of an AWS [Access Key](https://docs.aws.amazon.com/IAM/latest/APIReference/API_AccessKey.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated
| createdate | Date when access key was created |
| status | Active: valid for API calls.  Inactive: not valid for API calls|
| **accesskeyid** | The ID for this access key|

### Relationships
- Account Access Keys may authenticate AWS Users and AWS Principal objects.

	```
	(AWSUser, AWSPrincipal)-[AWS_ACCESS_KEY]->(AccountAccessKey)
	```


## DBSubnetGroup

Representation of an RDS [DB Subnet Group](https://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_DBSubnetGroup.html).  For more information on how RDS instances interact with these, please see [this article](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.WorkingWithRDSInstanceinaVPC.html).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job first discovered this node |
|id| The ARN of the DBSubnetGroup|
|name | The name of DBSubnetGroup |
|lastupdated| Timestamp of the last time the node was updated|
|description| Description of the DB Subnet Group|
|status| The status of the group |
|vpc\_id| The ID of the VPC (Virtual Private Cloud) that this DB Subnet Group is associated with.|
|value| The IP address that the DNSRecord points to|

### Relationships

- RDS Instances are part of DB Subnet Groups
    ```
    (RDSInstance)-[:MEMBER_OF_DB_SUBNET_GROUP]->(DBSubnetGroup)
    ```

- DB Subnet Groups consist of EC2 Subnets
    ```
    (DBSubnetGroup)-[:RESOURCE]->(EC2Subnet)
    ```


## DNSRecord

Representation of a generic DNSRecord.

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job first discovered this node |
|name| The name of the DNSRecord|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The name of the DNSRecord concatenated with the record type|
|type| The record type of the DNS record|
|value| The IP address that the DNSRecord points to|

### Relationships

- DNSRecords can point to IP addresses.

	```
	(DNSRecord)-[DNS_POINTS_TO]->(Ip)
	```


- DNSRecords/AWSDNSRecords can point to each other.

	```
	(AWSDNSRecord, DNSRecord)-[DNS_POINTS_TO]->(AWSDNSRecord, DNSRecord)
	```


- DNSRecords can point to LoadBalancers.

	```
	(DNSRecord)-[DNS_POINTS_TO]->(LoadBalancer)
	```


- DNSRecords can be members of DNSZones.

	```
	(DNSRecord)-[MEMBER_OF_DNS_ZONE]->(DNSZone)
	```


## DNSRecord::AWSDNSRecord

Representation of an AWS DNS [ResourceRecordSet](https://docs.aws.amazon.com/Route53/latest/APIReference/API_ResourceRecordSet.html).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job first discovered this node |
|name| The name of the DNSRecord|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The name of the DNSRecord concatenated with the record type|
|type| The record type of the DNS record|
|value| The IP address that the DNSRecord points to|

### Relationships
- DNSRecords/AWSDNSRecords can point to each other.

	```
	(AWSDNSRecord, DNSRecord)-[DNS_POINTS_TO]->(AWSDNSRecord, DNSRecord)
	```


- AWSDNSRecords can point to LoadBalancers.

	```
	(AWSDNSRecord)-[DNS_POINTS_TO]->(LoadBalancer)
	```


- AWSDNSRecords can be members of AWSDNSZones.

	```
	(AWSDNSRecord)-[MEMBER_OF_DNS_ZONE]->(AWSDNSZone)
	```


## DNSZone
Representation of a generic DNS Zone.

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated|  Timestamp of the last time the node was updated |
|**name**| the name of the DNS zone|
| comment | Comments about the zone |


### Relationships

- DNSRecords can be members of DNSZones.

	```
	(DNSRecord)-[MEMBER_OF_DNS_ZONE]->(DNSZone)
	```


## DNSZone::AWSDNSZone

Representation of an AWS DNS [HostedZone](https://docs.aws.amazon.com/Route53/latest/APIReference/API_HostedZone.html).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job first discovered this node  |
|**name**| the name of the DNS zone|
| zoneid| The zoneid defined by Amazon Route53|
| lastupdated|  Timestamp of the last time the node was updated |
| comment| Comments about the zone |
| privatezone | Whether or not this is a private DNS zone |

### Relationships

- AWSDNSZones and DNSZones can be part of AWSAccounts.

	```
	(AWSAccount)-[RESOURCE]->(AWSDNSZone)
	```

- AWSDNSRecords can be members of AWSDNSZones.

	```
	(AWSDNSRecord)-[MEMBER_OF_DNS_ZONE]->(AWSDNSZone)
	```



## DynamoDBTable

Representation of an AWS [DynamoDBTable](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_ListTables.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| name | The name of the table |
| **id** | The ARN of the table |
| region | The AWS region of the table |
| **arn** | The AWS-unique identifier

### Relationships
- DynamoDBTables belong to AWS Accounts.

	```
	(AWSAccount)-[RESOURCE]->(DynamoDBTable)
	```


## EC2Instance

Our representation of an AWS [EC2 Instance](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_Instance.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **instanceid**| The ID of the instance|
| **publicdnsname** | The public DNS name assigned to the instance |
| publicipaddress | The public IPv4 address assigned to the instance if applicable |
| privateipaddress | The private IPv4 address assigned to the instance |
| imageid | The ID of the [Amazon Machine Image](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AMIs.html) used to launch the instance |
| subnetid | The ID of the EC2Subnet associated with this instance |
| instancetype | The instance type.  See API docs linked above for specifics. |
| launchtime | The time the instance was launched |
| monitoringstate | Whether monitoring is enabled.  Valid Values: disabled, disabling, enabled,  pending. |
| state | The [current state](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_InstanceState.html) of the instance.
| launchtimeunix | The time the instance was launched in unix time |
| region | The AWS region this Instance is running in|
| exposed\_internet |  The `exposed_internet` flag on an EC2 instance is set to `True` when (1) the instance is part of an EC2 security group or is connected to a network interface connected to an EC2 security group that allows connectivity from the 0.0.0.0/0 subnet or (2) the instance is connected to an Elastic Load Balancer that has its own `exposed_internet` flag set to `True`. |


### Relationships

- EC2 Instances can be part of subnets

	```
	(EC2Instance)-[PART_OF_SUBNET]->(EC2Subnet)
	```

- EC2 Instances can have NetworkInterfaces connected to them

	```
	(EC2Instance)-[NETWORK_INTERFACE]->(NetworkInterface)
	```

- EC2 Instances may be members of EC2 Reservations

	```
	(EC2Instance)-[MEMBER_OF_EC2_RESERVATION]->(EC2Reservation)
	```

- EC2 Instances can be part of EC2 Security Groups

	```
	(EC2Instance)-[MEMBER_OF_EC2_SECURITY_GROUP]->(EC2SecurityGroup)
	```

- Load Balancers can expose (be connected to) EC2 Instances

	```
	(LoadBalancer)-[EXPOSE]->(EC2Instance)
	```

- Package and Dependency nodes can be deployed in EC2 Instances.

	```
	(Package, Dependency)-[DEPLOYED]->(EC2Instance)
	```

- AWS Accounts contain EC2 Instances.

	```
	(AWSAccount)-[RESOURCE]->(EC2Instance)
	```


## EC2KeyPair

Representation of an AWS [EC2 Key Pair](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_KeyPairInfo.html)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| keyname | The name of the key pair |
| keyfingerprint | The fingerprint of the public key |
| region| The AWS region |
| **arn** | AWS-unique identifier for this object |

### Relationships

- EC2 key pairs are contained in AWS Accounts.

	```
	(AWSAccount)-[RESOURCE]->(EC2KeyPair)
	```

- EC2 key pairs can be used to log in to AWS EC2 isntances.

	```
	(EC2KeyPair)-[SSH_LOGIN_TO]->(EC2Instance)
	```


## EC2Reservation
Representation of an AWS EC2 [Reservation](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_Reservation.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| requesterid | The ID of the requester that launched the instances on your behalf |
| **reservationid** | The ID of the reservation. |
| region| The AWS region |
| ownerid | The ID of the AWS account that owns the reservation. |

### Relationships

- EC2 reservations are contained in AWS Accounts.

	```
	(AWSAccount)-[RESOURCE]->(EC2Reservation)
	```

- EC2 Instances are members of EC2 reservations.

	```
	(EC2Instance)-[MEMBER_OF_EC2_RESERVATION]->(EC2Reservation)
	```


## EC2SecurityGroup
Representation of an AWS EC2 [Security Group](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_SecurityGroup.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| groupid | The ID of the security group|
| name | The name of the security group|
| description | A description of the security group|
| **id** | Same as `groupid` |
| region | The AWS region this security group is installed in|


### Relationships

- EC2 Instances, Network Interfaces, Load Balancers, Elastic Search Domains, IP Rules, IP Permission Inbound nodes, and RDS Instances can be members of EC2 Security Groups.

	```
	(EC2Instance,
	 NetworkInterface,
	 LoadBalancer,
	 ESDomain,
	 IpRule,
	 IpPermissionInbound,
	 RDSInstance,
	 AWSVpc)-[MEMBER_OF_EC2_SECURITY_GROUP]->(EC2SecurityGroup)
	```

- Load balancers can define inbound [Source Security Groups](https://docs.aws.amazon.com/elasticloadbalancing/latest/classic/elb-security-groups.html).

	```
	(LoadBalancer)-[SOURCE_SECURITY_GROUP]->(EC2SecurityGroup)
	```

- AWS Accounts contain EC2 Security Groups.

	```
	(AWSAccount)-[RESOURCE]->(EC2SecurityGroup)
	```


## EC2Subnet

Representation of an AWS EC2 [Subnet](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_Subnet.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **subnetid** | The ID of the subnet|
| **id** | same as subnetid |
| region| The AWS region the subnet is installed on|
|availability_zone| (If available) the AZ this subnet is installed on |


### Relationships

- A Network Interface can be part of an EC2 Subnet.

	```
	(NetworkInterface)-[PART_OF_SUBNET]->(EC2Subnet)
	```

- An EC2 Instance can be part of an EC2 Subnet.

	```
	(EC2Instance)-[PART_OF_SUBNET]->(EC2Subnet)
	```

- A load balancer can be part of an EC2 Subnet.

	```
	(LoadBalancer)-[SUBNET]->(EC2Subnet)
	```

- DB Subnet Groups consist of EC2 Subnets
    ```
    (DBSubnetGroup)-[:RESOURCE]->(EC2Subnet)
    ```



## ESDomain

Representation of an AWS [ElasticSearch Domain](https://docs.aws.amazon.com/elasticsearch-service/latest/developerguide/es-configuration-api.html#es-configuration-api-datatypes) (see ElasticsearchDomainConfig).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| elasticsearch\_cluster\_config\_instancetype | The instancetype |
| elasticsearch\_version | The version of elasticsearch |
| elasticsearch\_cluster\_config\_zoneawarenessenabled | Indicates whether multiple Availability Zones are enabled.  |
| elasticsearch\_cluster\_config\_dedicatedmasterenabled | Indicates whether dedicated master nodes are enabled for the cluster. True if the cluster will use a dedicated master node. False if the cluster will not.  |
| elasticsearch\_cluster\_config\_dedicatedmastercount |Number of dedicated master nodes in the cluster.|
| elasticsearch\_cluster\_config\_dedicatedmastertype | Amazon ES instance type of the dedicated master nodes in the cluster.|
| domainid | Unique identifier for an Amazon ES domain. |
| encryption\_at\_rest\_options\_enabled | Specify true to enable encryption at rest. |
| deleted | Status of the deletion of an Amazon ES domain. True if deletion of the domain is complete. False if domain deletion is still in progress. |
| **id** | same as `domainid` |
| **arn** |Amazon Resource Name (ARN) of an Amazon ES domain. |
| exposed\_internet | `exposed_internet` is set to `True` if the ElasticSearch domain has a policy applied to it that makes it internet-accessible.  This policy determination is made by using the [policyuniverse](https://github.com/Netflix-Skunkworks/policyuniverse) library.  The code for this augmentation is implemented at `cartography.intel.aws.elasticsearch._process_access_policy()`. |

### Relationships

- Elastic Search domains can be members of EC2 Security Groups.

	```
	(ESDomain)-[MEMBER_OF_EC2_SECURITY_GROUP]->(EC2SecurityGroup)
	```

-	Elastic Search domains belong to AWS Accounts.

	```
	(AWSAccount)-[RESOURCE]->(ESDomain)
	```

- DNS Records can point to Elastic Search domains.

	```
	(DNSRecord)-[DNS_POINTS_TO]->(ESDomain)
	```

## Endpoint

Representation of a generic network endpoint.

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| protocol | The protocol of this endpoint |
| port | The port of this endpoint |


### Relationships

- Endpoints can be installed load balancers, though more specifically we would refer to these Endpoint nodes as [ELBListeners](#endpoint::elblistener).

	```
	(LoadBalancer)-[ELB_LISTENER]->(Endpoint)
	```


## Endpoint::ELBListener

Representation of an AWS Elastic Load Balancer [Listener](https://docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_LoadBalancer.html).  Here, an ELBListener is a more specific type of Endpoint.  Here'a [good introduction](https://docs.aws.amazon.com/elasticloadbalancing/2012-06-01/APIReference/Welcome.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| protocol | The protocol of this endpoint |
| port | The port of this endpoint |
| **id** | The ELB ID.  This is a concatenation of the DNS name, port, and protocol. |
| instance\_port | The port open on the EC2 instance that this listener is connected to |
| instance\_protocol | The protocol defined on the EC2 instance that this listener is connected to |


### Relationships

- A ELBListener is installed on a load balancer.

	```
	(LoadBalancer)-[ELB_LISTENER]->(ELBListener)
	```


## Ip

Represents a generic IP address.

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **ip** | The IPv4 address |
| **id** | Same as `ip` |


### Relationships

- DNSRecords can point to IP addresses.

	```
	(DNSRecord)-[DNS_POINTS_TO]->(Ip)
	```


## IpRule

Represents a generic IP rule.  The creation of this node is currently derived from ingesting AWS [EC2 Security Group](#ec2securitygroup) rules.

| Field | Description |
|-------|-------------|
| **ruleid** | `{group_id}/{rule_type}/{from_port}{to_port}{protocol}` |
| groupid | The groupid of the EC2 Security Group that this was derived from |
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| protocol | The protocol this rule applies to |
| fromport | Lowest port in the range defined by this rule|
| toport | Highest port in the range defined by this rule|


### Relationships

- IpRules are defined from EC2SecurityGroups.

	```
	(IpRule, IpPermissionInbound)-[MEMBER_OF_EC2_SECURITY_GROUP]->(EC2SecurityGroup)
	```


## IpRule::IpPermissionInbound

An IpPermissionInbound node is a specific type of IpRule.  It represents a generic inbound IP-based rules.  The creation of this node is currently derived from ingesting AWS [EC2 Security Group](#ec2securitygroup) rules.

| Field | Description |
|-------|-------------|
| **ruleid** | `{group_id}/{rule_type}/{from_port}{to_port}{protocol}` |
| groupid |  The groupid of the EC2 Security Group that this was derived from |
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| protocol | The protocol this rule applies to |
| fromport | Lowest port in the range defined by this rule|
| toport | Highest port in the range defined by this rule|

### Relationships

- IpPermissionInbound rules are defined from EC2SecurityGroups.

	```
	(IpRule, IpPermissionInbound)-[MEMBER_OF_EC2_SECURITY_GROUP]->(EC2SecurityGroup)
	```


## LoadBalancer

Represents an AWS Elastic Load Balancer.  See [spec for details](https://docs.aws.amazon.com/elasticloadbalancing/2012-06-01/APIReference/API_LoadBalancerDescription.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| scheme|  The type of load balancer. Valid only for load balancers in a VPC. If scheme is `internet-facing`, the load balancer has a public DNS name that resolves to a public IP address.  If scheme is `internal`, the load balancer has a public DNS name that resolves to a private IP address. |
| name| The name of the load balancer|
| **dnsname** | The DNS name of the load balancer. |
| canonicalhostedzonename| The DNS name of the load balancer |
| **id** |  Currently set to the `dnsname` of the load balancer. |
| region| The region of the load balancer |
|createdtime | The date and time the load balancer was created. |
|canonicalhostedzonenameid| The ID of the Amazon Route 53 hosted zone for the load balancer. |
| exposed\_internet | The `exposed_internet` flag is set to `True` when the load balancer's `scheme` field is set to `internet-facing`.  This indicates that the load balancer has a public DNS name that resolves to a public IP address. |


### Relationships

- LoadBalancers can be connected to EC2Instances and therefore expose them.

	```
	(LoadBalancer)-[EXPOSE]->(EC2Instance)
	```

- LoadBalancers can have [source security groups](https://docs.aws.amazon.com/elasticloadbalancing/latest/classic/elb-security-groups.html) configured.

	```
	(LoadBalancer)-[SOURCE_SECURITY_GROUP]->(EC2SecurityGroup)
	```

- LoadBalancers can be part of EC2SecurityGroups.

	```
	(LoadBalancer)-[MEMBER_OF_EC2_SECURITY_GROUP]->(EC2SecurityGroup)
	```

- LoadBalancers can be part of EC2 Subnets

	```
	(LoadBalancer)-[SUBNET]->(EC2Subnet)
	```

- LoadBalancers can have listeners configured to accept connections from clients ([good introduction](https://docs.aws.amazon.com/elasticloadbalancing/2012-06-01/APIReference/Welcome.html)).

	```
	(LoadBalancer)-[ELB_LISTENER]->(Endpoint, ELBListener)
	```

- LoadBalancers are part of AWSAccounts.

	```
	(AWSAccount)-[RESOURCE]->(LoadBalancer)
	```

- AWSDNSRecords and DNSRecords point to LoadBalancers.

	```
	(AWSDNSRecord, DNSRecord)-[DNS_POINTS_TO]->(LoadBalancer)
	```

## NetworkInterface

Representation of a generic Network Interface.  Currently however, we only create NetworkInterface nodes from AWS [EC2 Instances](#ec2instance).  The spec for an AWS EC2 network interface is [here](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_InstanceNetworkInterface.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| mac\_address| The MAC address of the network interface|
| description |  Description of the network interface|
| private\_ip\_address| The IPv4 address of the network interface within the subnet |
| **id** | The ID of the network interface.  (known as `networkInterfaceId` in EC2) |
| private\_dns\_name| The private DNS name |
| status | Status of the network interface.  Valid Values: `available | associated | attaching | in-use | detaching ` |


### Relationships

- Network interfaces can be connected to EC2Subnets.

	```
	(NetworkInterface)-[PART_OF_SUBNET]->(EC2Subnet)
	```

- Network interfaces can be members of EC2SecurityGroups.

	```
	(NetworkInterface)-[MEMBER_OF_EC2_SECURITY_GROUP]->(EC2SecurityGroup)
	```

- EC2Instances can have NetworkInterfaces connected to them.

	```
	(EC2Instance)-[NETWORK_INTERFACE]->(NetworkInterface)
	```


## RDSInstance

Representation of an AWS Relational Database Service [DBInstance](https://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_DBInstance.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id**                               | The Amazon Resource Name (ARN) for the DB instance. |
| **db\_instance_identifier**           | Contains a user-supplied database identifier. This identifier is the unique key that identifies a DB instance.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| availability\_zone                | Specifies the name of the Availability Zone the DB instance is located in.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| backup\_retention\_period          | Specifies the number of days for which automatic DB snapshots are retained.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| preferred\_backup\_window          | Specifies the daily time range during which automated backups are created if automated backups are enabled, as determined by the BackupRetentionPeriod.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ca\_certificate\_identifier        | The identifier of the CA certificate for this DB instance.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| db\_cluster\_identifier            | If the DB instance is a member of a DB cluster, contains the name of the DB cluster that the DB instance is a member of.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| db\_instance\_class                | Contains the name of the compute and memory capacity class of the DB instance.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| db\_instance\_port                 | Specifies the port that the DB instance listens on.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| dbi\_resource\_id                  | The AWS Region-unique, immutable identifier for the DB instance. This identifier is found in AWS CloudTrail log entries whenever the AWS KMS key for the DB instance is accessed.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| db\_name                          | The meaning of this parameter differs according to the database engine you use. For example, this value returns MySQL, MariaDB, or PostgreSQL information when returning values from CreateDBInstanceReadReplica since Read Replicas are only supported for these engines.<br><br>**MySQL, MariaDB, SQL Server, PostgreSQL:** Contains the name of the initial database of this instance that was provided at create time, if one was specified when the DB instance was created. This same name is returned for the life of the DB instance.<br><br>**Oracle:** Contains the Oracle System ID (SID) of the created DB instance. Not shown when the returned parameters do not apply to an Oracle DB instance. |
| engine                           | Provides the name of the database engine to be used for this DB instance.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| engine\_version                   | Indicates the database engine version.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| enhanced\_monitoring\_resource\_arn | The Amazon Resource Name (ARN) of the Amazon CloudWatch Logs log stream that receives the Enhanced Monitoring metrics data for the DB instance.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| instance\_create\_time             | Provides the date and time the DB instance was created.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| kms\_key\_id                       | If StorageEncrypted is true, the AWS KMS key identifier for the encrypted DB instance.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| master\_username                  | Contains the master username for the DB instance.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| monitoring\_role\_arn              | The ARN for the IAM role that permits RDS to send Enhanced Monitoring metrics to Amazon CloudWatch Logs.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| multi\_az                         | Specifies if the DB instance is a Multi-AZ deployment.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| performance\_insights\_enabled     | True if Performance Insights is enabled for the DB instance, and otherwise false.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| preferred\_maintenance\_window     | Specifies the weekly time range during which system maintenance can occur, in Universal Coordinated Time (UTC).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| publicly\_accessible              | Specifies the accessibility options for the DB instance. A value of true specifies an Internet-facing instance with a publicly resolvable DNS name, which resolves to a public IP address. A value of false specifies an internal instance with a DNS name that resolves to a private IP address.                                                                                                                                                                                                                                                                                                                                                                                    |
| storage\_encrypted                | Specifies whether the DB instance is encrypted.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| endpoint\_address                 | DNS name of the RDS instance|
| endpoint\_port                    | The port that the RDS instance is listening on |
| endpoint\_hostedzoneid            | The AWS DNS Zone ID that is associated with the RDS instance's DNS entry |
| auto\_minor\_version\_upgrade       | Specifies whether minor version upgrades are applied automatically to the DB instance during the maintenance window |
| iam\_database\_authentication\_enabled       | Specifies if mapping of AWS Identity and Access Management (IAM) accounts to database accounts is enabled |



### Relationships

- RDS Instances are part of AWS Accounts.

	```
	(AWSAccount)-[RESOURCE]->(RDSInstance)
	```

- Some RDS instances are Read Replicas.

    ```
    (replica:RDSInstance)-[IS_READ_REPLICA_OF]->(source:RDSInstance)
    ```

- RDS Instances can be members of EC2 Security Groups.

    ```
    (RDSInstance)-[m:MEMBER_OF_EC2_SECURITY_GROUP]->(EC2SecurityGroup)
    ```

- RDS Instances are connected to DB Subnet Groups.

    ```
    (RDSInstance)-[:MEMBER_OF_DB_SUBNET_GROUP]->(DBSubnetGroup)
    ```

## S3Acl

Representation of an AWS S3 [Access Control List](https://docs.aws.amazon.com/AmazonS3/latest/API/API_control_S3AccessControlList.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| granteeid | The ID of the grantee as defined [here](https://docs.aws.amazon.com/AmazonS3/latest/API/API_control_S3Grantee.html) |
| displayname | Optional display name for the ACL |
| permission | Valid values: `FULL_CONTROL | READ | WRITE | READ_ACP | WRITE_ACP` (ACP = Access Control Policy)|
| **id** | The ID of this ACL|
| type |  The type of the [grantee](https://docs.aws.amazon.com/AmazonS3/latest/API/API_Grantee.html).  Either `CanonicalUser | AmazonCustomerByEmail | Group`. |
| ownerid| The ACL's owner ID as defined [here](https://docs.aws.amazon.com/AmazonS3/latest/API/API_control_S3ObjectOwner.html)|


### Relationships


- S3 Access Control Lists apply to S3 buckets.

	```
	(S3Acl)-[APPLIES_TO]->(S3Bucket)
	```

## S3Bucket

Representation of an AWS S3 [Bucket](https://docs.aws.amazon.com/AmazonS3/latest/API/API_Bucket.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| creationdate | Date-time when the bucket was created |
| **name** | The friendly name of the bucket |
| anonymous\_actions |  List of anonymous internet accessible actions that may be run on the bucket.  This list is taken by running [policyuniverse](https://github.com/Netflix-Skunkworks/policyuniverse#internet-accessible-policy) on the policy that applies to the bucket.   |
| anonymous\_access | True if this bucket has a policy applied to it that allows anonymous access or if it is open to the internet.  These policy determinations are made by using the [policyuniverse](https://github.com/Netflix-Skunkworks/policyuniverse) library.  |

### Relationships

- S3Buckets are resources in an AWS Account.

	```
	(AWSAccount)-[RESOURCE]->(S3Bucket)
	```

- S3 Access Control Lists apply to S3 buckets.

	```
	(S3Acl)-[APPLIES_TO]->(S3Bucket)
	```
