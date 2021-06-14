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
- [AWSLambda](#awslambda)
  - [Relationships](#relationships-3)
- [AWSLambdaFunctionAlias](#awslambdafunctionalias)
  - [Relationships](#relationships-4)
- [AWSLambdaEventSourceMapping](#awslambdaeventsourcemapping)
  - [Relationships](#relationships-5)
- [AWSLambdaLayer](#awslambdalayer)
  - [Relationships](#relationships-6)
- [AWSPolicy](#awspolicy)
  - [Relationships](#relationships-7)
- [AWSPolicyStatement](#awspolicystatement)
  - [Relationships](#relationships-8)
- [AWSPrincipal](#awsprincipal)
  - [Relationships](#relationships-9)
- [AWSPrincipal::AWSUser](#awsprincipalawsuser)
  - [Relationships](#relationships-10)
- [AWSPrincipal::AWSRole](#awsprincipalawsrole)
  - [Relationships](#relationships-11)
- [AWSTransitGateway](#awstransitgateway)
  - [Relationships](#relationships-12)
- [AWSTransitGatewayAttachment](#awstransitgatewayattachment)
  - [Relationships](#relationships-13)
- [AWSVpc](#awsvpc)
  - [Relationships](#relationships-14)
- [Tag::AWSTag](#tagawstag)
  - [Relationships](#relationships-15)
- [AccountAccessKey](#accountaccesskey)
  - [Relationships](#relationships-16)
- [DBSubnetGroup](#dbsubnetgroup)
  - [Relationships](#relationships-17)
- [DNSRecord](#dnsrecord)
  - [Relationships](#relationships-18)
- [DNSRecord::AWSDNSRecord](#dnsrecordawsdnsrecord)
  - [Relationships](#relationships-19)
- [DNSZone](#dnszone)
  - [Relationships](#relationships-20)
- [DNSZone::AWSDNSZone](#dnszoneawsdnszone)
  - [Relationships](#relationships-21)
- [DynamoDBTable](#dynamodbtable)
  - [Relationships](#relationships-22)
- [EC2Instance](#ec2instance)
  - [Relationships](#relationships-23)
- [EC2KeyPair](#ec2keypair)
  - [Relationships](#relationships-24)
- [EC2PrivateIp](#ec2privateip)
  - [Relationships](#relationships-25)
- [EC2Reservation](#ec2reservation)
  - [Relationships](#relationships-26)
- [EC2SecurityGroup](#ec2securitygroup)
  - [Relationships](#relationships-27)
- [EC2Subnet](#ec2subnet)
  - [Relationships](#relationships-28)
- [AWSInternetGateway](#awsinternetgateway)
  - [Relationships](#relationships-29)
- [ECRRepository](#ecrrepository)
  - [Relationships](#relationships-30)
- [ECRRepositoryImage](#ecrrepositoryimage)
  - [Relationships](#relationships-31)
- [ECRImage](#ecrimage)
  - [Relationships](#relationships-32)
- [Package](#package)
  - [Relationships](#relationships-33)
- [ECRScanFinding (:Risk:CVE)](#ecrscanfinding-riskcve)
  - [Relationships](#relationships-34)
- [EKSCluster](#ekscluster)
  - [Relationships](#relationships-35)
- [EMRCluster](#emrcluster)
  - [Relationships](#relationships-36)
- [ESDomain](#esdomain)
  - [Relationships](#relationships-37)
- [Endpoint](#endpoint)
  - [Relationships](#relationships-38)
- [Endpoint::ELBListener](#endpointelblistener)
  - [Relationships](#relationships-39)
- [Endpoint::ELBV2Listener](#endpointelbv2listener)
  - [Relationships](#relationships-40)
- [Ip](#ip)
  - [Relationships](#relationships-41)
- [IpRule](#iprule)
  - [Relationships](#relationships-42)
- [IpRule::IpPermissionInbound](#ipruleippermissioninbound)
  - [Relationships](#relationships-43)
- [LoadBalancer](#loadbalancer)
  - [Relationships](#relationships-44)
- [LoadBalancerV2](#loadbalancerv2)
  - [Relationships](#relationships-45)
- [Nameserver](#nameserver)
  - [Relationships](#relationships-46)
- [NetworkInterface](#networkinterface)
  - [Relationships](#relationships-47)
- [AWSPeeringConnection](#awspeeringconnection)
- [RedshiftCluster](#redshiftcluster)
  - [Relationships](#relationships-48)
- [RDSInstance](#rdsinstance)
  - [Relationships](#relationships-49)
- [S3Acl](#s3acl)
  - [Relationships](#relationships-50)
- [S3Bucket](#s3bucket)
  - [Relationships](#relationships-51)
- [KMSKey](#kmskey)
  - [Relationships](#relationships-52)
- [KMSAlias](#kmsalias)
  - [Relationships](#relationships-53)
- [KMSGrant](#kmsgrant)
  - [Relationships](#relationships-54)
- [APIGatewayRestAPI](#apigatewayrestapi)
  - [Relationships](#relationships-55)
- [APIGatewayStage](#apigatewaystage)
  - [Relationships](#relationships-56)
- [APIGatewayClientCertificate](#apigatewayclientcertificate)
  - [Relationships](#relationships-57)
- [APIGatewayResource](#apigatewayresource)
  - [Relationships](#relationships-58)

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
        (AWSAccount)-[RESOURCE]->(AWSPolicy)
        ```

- `AWSRole` nodes are defined in `AWSAccount` nodes.

        ```
        (AWSAccount)-[RESOURCE]->(AWSRole)
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
- Peering connection where `AWSCidrBlock` is an accepter or requester cidr.
  ```
  (AWSCidrBlock)<-[REQUESTER_CIDR]-(AWSPeeringConnection)
  (AWSCidrBlock)<-[ACCEPTER_CIDR]-(AWSPeeringConnection)
  ```

  Example of high level view of peering (without security group permissions)
  ```
  MATCH p=(:AWSAccount)-[:RESOURCE|BLOCK_ASSOCIATION*..]->(:AWSCidrBlock)<-[:ACCEPTER_CIDR]-(:AWSPeeringConnection)-[:REQUESTER_CIDR]->(:AWSCidrBlock)<-[:RESOURCE|BLOCK_ASSOCIATION*..]-(:AWSAccount)
  RETURN p
  ```

  Exploring detailed inbound peering rules
  ```
  MATCH (outbound_account:AWSAccount)-[:RESOURCE|BLOCK_ASSOCIATION*..]->(:AWSCidrBlock)<-[:ACCEPTER_CIDR]-(:AWSPeeringConnection)-[:REQUESTER_CIDR]->(inbound_block:AWSCidrBlock)<-[:BLOCK_ASSOCIATION]-(inbound_vpc:AWSVpc)<-[:RESOURCE]-(inbound_account:AWSAccount)
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

## AWSLambda

Representation of an AWS [Lambda Function](https://docs.aws.amazon.com/lambda/latest/dg/API_FunctionConfiguration.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The arn of the lambda function|
| name |  The name of the lambda function |
| modifieddate |  Timestamp of the last time the function was last updated |
| runtime |  The runtime environment for the Lambda function |
| description |  The description of the Lambda function |
| timeout |  The amount of time in seconds that Lambda allows a function to run before stopping it |
| memory |  The memory that's allocated to the function |
| codesize |  The size of the function's deployment package, in bytes. |
| handler |  The function that Lambda calls to begin executing your function. |
| version |  The version of the Lambda function. |
| tracingconfigmode | The function's AWS X-Ray tracing configuration mode. |
| revisionid | The latest updated revision of the function or alias. |
| state | The current state of the function. |
| statereason | The reason for the function's current state. |
| statereasoncode | The reason code for the function's current state. |
| lastupdatestatus | The status of the last update that was performed on the function. |
| lastupdatestatusreason |  The reason for the last update that was performed on the function.|
| lastupdatestatusreasoncode | The reason code for the last update that was performed on the function. |
| packagetype |  The type of deployment package. |
| signingprofileversionarn | The ARN of the signing profile version. |
| signingjobarn | The ARN of the signing job. |

### Relationships

- AWSLambda function are resources in an AWS Account.

        ```
        (AWSAccount)-[RESOURCE]->(AWSLambda)
        ```

- AWSLambda functions may act as AWSPrincipals via role assumption.

        ```
        (AWSLambda)-[STS_ASSUME_ROLE_ALLOW]->(AWSPrincipal)
        ```

- AWSLambda functions may also have aliases.

        ```
        (AWSLambda)-[KNOWN_AS]->(AWSLambdaFunctionAlias)
        ```

- AWSLambda functions may have the resource AWSLambdaEventSourceMapping.

        ```
        (AWSLambda)-[RESOURCE]->(AWSLambdaEventSourceMapping)
        ```

- AWSLambda functions has AWS Lambda Layers.

        ```
        (AWSLambda)-[HAS]->(AWSLambdaLayer)
        ```

## AWSLambdaFunctionAlias

Representation of an [AWSLambdaFunctionAlias](https://docs.aws.amazon.com/lambda/latest/dg/configuration-aliases.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The arn of the lambda function alias|
| name |  The name of the lambda function alias |
| functionversion | The function version that the alias invokes.|
| revisionid |  A unique identifier that changes when you update the alias. |
| description |  The description of the alias. |

### Relationships

- AWSLambda functions may also have aliases.

        ```
        (AWSLambda)-[KNOWN_AS]->(AWSLambdaFunctionAlias)
        ```

## AWSLambdaEventSourceMapping

Representation of an [AWSLambdaEventSourceMapping](https://docs.aws.amazon.com/lambda/latest/dg/API_ListEventSourceMappings.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The id of the event source mapping|
| batchsize | The maximum number of items to retrieve in a single batch. |
| startingposition | The position in a stream from which to start reading. |
| startingpositiontimestamp |  The time from which to start reading. |
| parallelizationfactor |  The number of batches to process from each shard concurrently. |
| maximumbatchingwindowinseconds | The maximum amount of time to gather records before invoking the function, in seconds.|
| eventsourcearn |The Amazon Resource Name (ARN) of the event source.|
| lastmodified |The date that the event source mapping was last updated, or its state changed.|
| state | The state of the event source mapping. |
| maximumrecordage | Discard records older than the specified age. |
| bisectbatchonfunctionerror | If the function returns an error, split the batch in two and retry. |
| maximumretryattempts | Discard records after the specified number of retries. |
| tumblingwindowinseconds | The duration in seconds of a processing window. |
| lastprocessingresult |The result of the last AWS Lambda invocation of your Lambda function. |

### Relationships

- AWSLambda functions may have the resource AWSLambdaEventSourceMapping.

        ```
        (AWSLambda)-[RESOURCE]->(AWSLambdaEventSourceMapping)
        ```

## AWSLambdaLayer

Representation of an [AWSLambdaLayer](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The arn of the lambda function layer|
| codesize | The size of the layer archive in bytes.|
| signingprofileversionarn | The Amazon Resource Name (ARN) for a signing profile version.|
| signingjobarn | The Amazon Resource Name (ARN) of a signing job. |

### Relationships

- AWSLambda functions has AWS Lambda Layers.

        ```
        (AWSLambda)-[HAS]->(AWSLambdaLayer)
        ```

## AWSPolicy

Representation of an [AWS Policy](https://docs.aws.amazon.com/IAM/latest/APIReference/API_Policy.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| name | The friendly name (not ARN) identifying the policy |
| createdate | ISO 8601 date-time when the policy was created|
| type | "inline" or "managed" - the type of policy it is|
| arn | The arn for this object |
| **id** | The unique identifer for a policy. If the policy is managed this will be the Arn. If the policy is inline this will calculated as _AWSPrincipal_/inline_policy/_PolicyName_|


### Relationships

- `AWSPrincipal` contains `AWSPolicy`

        ```
        (AWSPrincipal)-[POLICY]->(AWSPolicy)
        ```

- `AWSPolicy` contains `AWSPolicyStatement`

        ```
        (AWSPolicy)-[STATEMENTS]->(AWSPolicyStatement)
        ```

## AWSPolicyStatement

Representation of an [AWS Policy Statement](https://docs.aws.amazon.com/IAM/latest/APIReference/API_Statement.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated | Timestamp of the last time the node was updated |
| resources | (array) The resources the statement is applied to. Can contain wildcards |
| actions | (array) The permissions allowed or denied by the statement. Can contain wildcards |
| notactions | (array) The permission explicitly not matched by the statement |
| effect | "Allow" or "Deny" - the effect of this statement |
| **id** | The unique identifier for a statement. <br>If the statement has an Sid the id will be calculated as _AWSPolicy.id_/statements/_Sid_. <br>If the statement has no Sid the id will be calculated as  _AWSPolicy.id_/statements/_index of statement in statement list_ |


### Relationships

- `AWSPolicy` contains `AWSPolicyStatement`

        ```
        (AWSPolicy)-[STATEMENTS]->(AWSPolicyStatement)
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

- Redshift clusters may assume IAM roles. See [this article](https://docs.aws.amazon.com/redshift/latest/mgmt/authorizing-redshift-service.html).

    ```
    (RedshiftCluster)-[STS_ASSUMEROLE_ALLOW]->(AWSPrincipal)
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
    (AWSAccount)-[RESOURCE]->(AWSRole)
    ```

## AWSTransitGateway
Representation of an [AWS Transit Gateway](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_TransitGateway.html).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|owner\_id| The ID of the AWS account that owns the transit gateway|
|description| Transit Gateway description|
|state| Can be one of `pending | available | modifying | deleting | deleted`|
|tgw_id| Unique identifier of the Transit Gateway|
|**id**| Unique identifier of the Transit Gateway|
| **arn** | AWS-unique identifier for this object (same as `id`) |

### Relationships
- Transit Gateways belong to one `AWSAccount`...
```
(AWSAccount)-[RESOURCE]->(AWSTransitGateway)
```

- ... and can be shared with other accounts
```
(AWSAccount)<-[SHARED_WITH]-(AWSTransitGateway)
```

- `AWSTag`
```
(AWSTransitGateway)-[TAGGED]->(AWSTag)
```

## AWSTransitGatewayAttachment
Representation of an [AWS Transit Gateway Attachment](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_TransitGatewayAttachment.html).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|resource\_type| Can be one of `vpc | vpn | direct-connect-gateway | tgw-peering`
|state| Can be one of `initiating | pendingAcceptance | rollingBack | pending | available | modifying | deleting | deleted | failed | rejected | rejecting | failing`
|**id**| Unique identifier of the Transit Gateway Attachment

### Relationships
- `AWSAccount`
```
(AWSAccount)-[RESOURCE]->(AWSTransitGatewayAttachment)
```
- `AWSVpc` (for VPC attachments)
```
(AWSVpc)-[RESOURCE]->(AWSTransitGatewayAttachment {resource_type: 'vpc'})
```
- `AWSTransitGateway` attachment
```
(AWSTransitGateway)<-[ATTACHED_TO]-(AWSTransitGatewayAttachment)
```
- `AWSTag`
```
(AWSTransitGatewayAttachment)-[TAGGED]->(AWSTag)
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
-  AWS VPCs can be tagged with AWSTags.
    ```
        (AWSVpc)-[TAGGED]->(AWSTag)
        ```
- Redshift clusters can be members of AWSVpcs.
    ```
    (RedshiftCluster)-[MEMBER_OF_AWS_VPC]->(AWSVpc)
    ```
- Peering connection where `AWSVpc` is an accepter or requester vpc.
  ```
  (AWSVpc)<-[REQUESTER_VPC]-(AWSPeeringConnection)
  (AWSVpc)<-[ACCEPTER_VPC]-(AWSPeeringConnection)
  ```


## Tag::AWSTag

Representation of an AWS [Tag](https://docs.aws.amazon.com/resourcegroupstagging/latest/APIReference/API_Tag.html). AWS Tags can be applied to many objects.

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | This tag's unique identifier of the format `{TagKey}:{TagValue}`. We fabricated this ID. |
| key | One part of a key-value pair that makes up a tag.|
| value | One part of a key-value pair that makes up a tag. |
| region | The region where this tag was discovered.|

### Relationships
-  AWS VPCs, DB Subnet Groups, EC2 Instances, EC2 SecurityGroups, EC2 Subnets, EC2 Network Interfaces, RDS Instances, and S3 Buckets can be tagged with AWSTags.
    ```
        (AWSVpc, DBSubnetGroup, EC2Instance, EC2SecurityGroup, EC2Subnet, NetworkInterface, RDSInstance, S3Bucket)-[TAGGED]->(AWSTag)
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

-  DB Subnet Groups can be tagged with AWSTags.

        ```
        (DBSubnetGroup)-[TAGGED]->(AWSTag)
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
|**id**| The zoneid for the record, the value of the record, and the type concatenated together|
|type| The record type of the DNS record|
|value| The IP address that the DNSRecord points to|

### Relationships
- DNSRecords/AWSDNSRecords can point to each other.

        ```
        (AWSDNSRecord, DNSRecord)-[DNS_POINTS_TO]->(AWSDNSRecord, DNSRecord)
        ```


- AWSDNSRecords can point to LoadBalancers.

        ```
        (AWSDNSRecord)-[DNS_POINTS_TO]->(LoadBalancer, ESDomain)
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
- AWSDNSZone can have subzones hosted by another AWSDNSZone
        ```
        (AWSDNSZone)<-[SUBZONE]-(AWSDNSZone)
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
| **id** | Same as `instanceid` below. |
| instanceid | The instance id provided by AWS.  This is [globally unique](https://forums.aws.amazon.com/thread.jspa?threadID=137203) |
| publicdnsname | The public DNS name assigned to the instance |
| publicipaddress | The public IPv4 address assigned to the instance if applicable |
| privateipaddress | The private IPv4 address assigned to the instance |
| imageid | The ID of the [Amazon Machine Image](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AMIs.html) used to launch the instance |
| subnetid | The ID of the EC2Subnet associated with this instance |
| instancetype | The instance type.  See API docs linked above for specifics. |
| iaminstanceprofile | The IAM instance profile associated with the instance, if applicable. |
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

-  EC2 Instances can be tagged with AWSTags.

        ```
        (EC2Instance)-[TAGGED]->(AWSTag)
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
 id | same as `arn` |
| user_uploaded | `user_uploaded` is set to `True` if the the KeyPair was uploaded to AWS. Uploaded KeyPairs will have 128-bit MD5 hashed `keyfingerprint`, and KeyPiars from AWS will have 160-bit SHA-1 hashed `keyfingerprint`s.
| duplicate_keyfingerprint | `duplicate_keyfingerprint` is set to `True` if the KeyPair has the same `keyfingerprint` as another KeyPair.

### Relationships

- EC2 key pairs are contained in AWS Accounts.

        ```
        (AWSAccount)-[RESOURCE]->(EC2KeyPair)
        ```

- EC2 key pairs can be used to log in to AWS EC2 isntances.

        ```
        (EC2KeyPair)-[SSH_LOGIN_TO]->(EC2Instance)
        ```

- EC2 key pairs have matching `keyfingerprint`.

        ```
        (EC2KeyPair)-[MATCHING_FINGERPRINT]->(EC2KeyPair)
        ```
## EC2PrivateIp
Representation of an AWS EC2 [InstancePrivateIpAddress](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_InstancePrivateIpAddress.html)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| network_interface_id   | id of the network interface with which the IP is associated with  |
| primary   |  Indicates whether this IPv4 address is the primary private IP address of the network interface.  |
| private_ip_address   |  The private IPv4 address of the network interface. |
| public_ip   |  The public IP address or Elastic IP address bound to the network interface. |
| ip_owner_id  | Id of the owner, e.g. `amazon-elb` for ELBs  |

### Relationships

- EC2PrivateIps are connected with NetworkInterfaces.

        ```
        (NetworkInterface)-[PRIVATE_IP_ADDRESS]->(EC2PrivateIp)
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

-  EC2 SecurityGroups can be tagged with AWSTags.

        ```
        (EC2SecurityGroup)-[TAGGED]->(AWSTag)
        ```

- Redshift clusters can be members of EC2 Security Groups.

    ```
    (RedshiftCluster)-[MEMBER_OF_EC2_SECURITY_GROUP]->(EC2SecurityGroup)
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
| name | The IPv4 CIDR block assigned to the subnet|
| cidr_block | The IPv4 CIDR block assigned to the subnet|
| available_ip_address_count | The number of unused private IPv4 addresses in the subnet. The IPv4 addresses for any stopped instances are considered unavailable |
| default_for_az | Indicates whether this is the default subnet for the Availability Zone. |
| map_customer_owned_ip_on_launch | Indicates whether a network interface created in this subnet (including a network interface created by RunInstances ) receives a customer-owned IPv4 address |
| map_public_ip_on_launch | Indicates whether instances launched in this subnet receive a public IPv4 address |
| subnet_arn | The Amazon Resource Name (ARN) of the subnet |
| availability_zone | The Availability Zone of the subnet |
| availability_zone_id | The AZ ID of the subnet |


### Relationships

- A Network Interface can be part of an EC2 Subnet.

        ```
        (NetworkInterface)-[PART_OF_SUBNET]->(EC2Subnet)
        ```

- An EC2 Instance can be part of an EC2 Subnet.

        ```
        (EC2Instance)-[PART_OF_SUBNET]->(EC2Subnet)
        ```

- A LoadBalancer can be part of an EC2 Subnet.

        ```
        (LoadBalancer)-[SUBNET]->(EC2Subnet)

        ```

- A LoadBalancer can be part of an EC2 Subnet.

        ```
        (LoadBalancer)-[PART_OF_SUBNET]->(EC2Subnet)
        ```

- A LoadBalancerV2 can be part of an EC2 Subnet.

        ```
        (LoadBalancerV2)-[PART_OF_SUBNET]->(EC2Subnet)
        ```


- DB Subnet Groups consist of EC2 Subnets
    ```
    (DBSubnetGroup)-[RESOURCE]->(EC2Subnet)
    ```


-  EC2 Subnets can be tagged with AWSTags.

        ```
        (EC2Subnet)-[TAGGED]->(AWSTag)
        ```

-  EC2 Subnets are member of a VPC.

        ```
        (EC2Subnet)-[MEMBER_OF_AWS_VPC]->(AWSVpc)
        ```

-  EC2 Subnets belong to AWS Accounts

        ```
        (AWSAccount)-[RESOURCE]->(EC2Subnet)
        ```


## AWSInternetGateway

 Representation of an AWS [Interent Gateway](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_InternetGateway.html).

 | Field | Description |
 |--------|-----------|
 | **id** | Internet gateway ID |
 | arn | Amazon Resource Name |
 | region | The region of the gateway |


 ### Relationships

 -  Internet Gateways are attached to a VPC.

         ```
         (AWSInternetGateway)-[ATTACHED_TO]->(AWSVpc)
         ```

 -  Internet Gateways belong to AWS Accounts

         ```
         (AWSAccount)-[RESOURCE]->(AWSInternetGateway)
         ```

## ECRRepository

Representation of an AWS Elastic Container Registry [Repository](https://docs.aws.amazon.com/AmazonECR/latest/APIReference/API_Repository.html).

| Field | Description |
|--------|-----------|
| **id** | Same as ARN |
| arn | The ARN of the repository |
| name | The name of the repository |
| region | The region of the repository |
| created_at | Date and time when the repository was created |

### Relationships

- An ECRRepository contains ECRRepositoryImages:
    ```
    (:ECRRepository)-[:REPO_IMAGE]->(:ECRRepositoryImage)
    ```


## ECRRepositoryImage

An ECR image may be referenced and tagged by more than one ECR Repository. To best represent this, we've created an
`ECRRepositoryImage` node as a layer of indirection between the repo and the image.

More concretely explained, we run
[`ecr.list_images()`](https://docs.aws.amazon.com/AmazonECR/latest/APIReference/API_ImageIdentifier.html), and then
store the image tag on an `ECRRepositoryImage` node and the image digest hash on a separate `ECRImage` node.

This way, more than one `ECRRepositoryImage` can reference/be connected to the same `ECRImage`.

| Field | Description |
|--------|-----------|
| tag | The tag applied to the repository image, e.g. "latest" |
| uri | The URI where the repository image is stored |
| **id** | same as uri |

### Relationships

- An ECRRepository contains ECRRepositoryImages:
    ```
    (:ECRRepository)-[:REPO_IMAGE]->(:ECRRepositoryImage)
    ```

- ECRRepositoryImages reference ECRImages
    ```
    (:ECRRepositoryImage)-[:IMAGE]->(:ECRImage)
    ```


## ECRImage

Representation of an ECR image identified by its digest (e.g. a SHA hash). Specifically, this is the "digest part" of
[`ecr.list_images()`](https://docs.aws.amazon.com/AmazonECR/latest/APIReference/API_ImageIdentifier.html). Also see
ECRRepositoryImage.

| Field | Description |
|--------|-----------|
| digest | The hash of this ECR image |
| **id** | Same as digest |

### Relationships

- ECRRepositoryImages reference ECRImages
    ```
    (:ECRRepositoryImage)-[:IMAGE]->(:ECRImage)
    ```

- Software packages are a part of ECR Images
    ```
    (:Package)-[:DEPLOYED]->(:ECRImage)
    ```


## Package

Representation of a software package, as found by an AWS ECR vulnerability scan.

| Field | Description |
|-------|-------------|
| **id** | Concatenation of `{version}|{name}` |
| version | The version of the package, includes the Linux distro that it was built for |
| name | The name of the package |

### Relationships

- Software packages are a part of ECR Images
    ```
    (:Package)-[:DEPLOYED]->(:ECRImage)
    ```

- AWS ECR scans yield ECRScanFindings that affect software packages
    ```
    (:ECRScanFindings)-[:AFFECTS]->(:Package)
    ```


## ECRScanFinding (:Risk:CVE)

Representation of a scan finding from AWS ECR. This is the result output of [`ecr.describe_image_scan_findings()`](https://docs.aws.amazon.com/AmazonECR/latest/APIReference/API_DescribeImageScanFindings.html).

| Field | Description |
|--------|-----------|
| name | The name of the ECR scan finding, e.g. a CVE name |
| **id** | Same as name |
| severity | The severity of the risk |
| uri | A URI link to a descriptive article on the risk |

### Relationships

- AWS ECR scans yield ECRScanFindings that affect software packages
    ```
    (:ECRScanFindings)-[:AFFECTS]->(:Package)
    ```



## EKSCluster

Representation of an AWS [EKS Cluster](https://docs.aws.amazon.com/eks/latest/APIReference/API_Cluster.html).

| Field            | Description                                                                                                 |
| ---------------- | ----------------------------------------------------------------------------------------------------------- |
| firstseen        | Timestamp of when a sync job first discovered this node                                                     |
| lastupdated      | Timestamp of the last time the node was updated                                                             |
| created_at       | The date and time the cluster was created                                                                   |
| region           | The AWS region                                                                                              |
| **arn**          | AWS-unique identifier for this object                                                                       |
| id               | same as `arn`                                                                                               |
| name             | Name of the EKS Cluster                                                                                     |
| endpoint         | The endpoint for the Kubernetes API server.                                                                 |
| endpoint_public_access | Indicates whether the Amazon EKS public API server endpoint is enabled                                |
| exposed_internet | Set to True if the EKS Cluster public API server endpoint is enabled                                        |
| rolearn          | The ARN of the IAM role that provides permissions for the Kubernetes control plane to make calls to AWS API |
| version          | Kubernetes version running                                                                                  |
| platform_version | Version of EKS                                                                                              |
| status           | Status of the cluster. Valid Values: creating, active, deleting, failed, updating                           |
| audit_logging    | Whether audit logging is enabled                                                                            |


### Relationships

- EKS Clusters belong to AWS Accounts.
      ```
      (AWSAccount)-[RESOURCE]->(EKSCluster)
      ```



## EMRCluster

Representation of an AWS [EMR Cluster](https://docs.aws.amazon.com/emr/latest/APIReference/API_Cluster.html).

| Field            | Description                                                                                                 |
| ---------------- | ----------------------------------------------------------------------------------------------------------- |
| firstseen        | Timestamp of when a sync job first discovered this node                                                     |
| lastupdated      | Timestamp of the last time the node was updated                                                             |
| region           | The AWS region                                                                                              |
| **arn**          | AWS-unique identifier for this object                                                                       |
| id               | The Id of the EMR Cluster.                                                                                  |
| servicerole      | Service Role of the EMR Cluster                                                                             |


### Relationships

- EMR Clusters belong to AWS Accounts.
      ```
      (AWSAccount)-[RESOURCE]->(EMRCluster)
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

-       Elastic Search domains belong to AWS Accounts.

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
| policy\_names | A list of SSL policy names set on the listener.
| **id** | The ELB ID.  This is a concatenation of the DNS name, port, and protocol. |
| instance\_port | The port open on the EC2 instance that this listener is connected to |
| instance\_protocol | The protocol defined on the EC2 instance that this listener is connected to |


### Relationships

- A ELBListener is installed on a load balancer.

        ```
        (LoadBalancer)-[ELB_LISTENER]->(ELBListener)
        ```

## Endpoint::ELBV2Listener

Representation of an AWS Elastic Load Balancer V2 [Listener](https://docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_Listener.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| protocol | The protocol of this endpoint - One of `'HTTP''HTTPS''TCP''TLS''UDP''TCP_UDP'` |
| port | The port of this endpoint |
| ssl\_policy | Only set for HTTPS or TLS listener. The security policy that defines which protocols and ciphers are supported. |
| targetgrouparn | The ARN of the Target Group, if the Action type is `forward`. |


### Relationships

- A ELBV2Listener is installed on a LoadBalancerV2.

        ```
        (elbv2)-[r:ELBV2_LISTENER]->(ELBV2Listener)
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


- LoadBalancers can be part of EC2 Subnets

        ```
        (LoadBalancer)-[PART_OF_SUBNET]->(EC2Subnet)
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

## LoadBalancerV2

Represents an Elastic Load Balancer V2 ([Application Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html) or [Network Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/introduction.html).)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| scheme|  The type of load balancer.  If scheme is `internet-facing`, the load balancer has a public DNS name that resolves to a public IP address.  If scheme is `internal`, the load balancer has a public DNS name that resolves to a private IP address. |
| name| The name of the load balancer|
| **dnsname** | The DNS name of the load balancer. |
| exposed_internet | The `exposed_internet` flag is set to `True` when the load balancer's `scheme` field is set to `internet-facing`.  This indicates that the load balancer has a public DNS name that resolves to a public IP address. |
| **id** |  Currently set to the `dnsname` of the load balancer. |
| type | Can be `application` or `network` |
| region| The region of the load balancer |
|createdtime | The date and time the load balancer was created. |
|canonicalhostedzonenameid| The ID of the Amazon Route 53 hosted zone for the load balancer. |


### Relationships


- LoadBalancerV2's can be connected to EC2Instances and therefore expose them.

        ```
        (LoadBalancerV2)-[EXPOSE]->(EC2Instance)
        ```

- LoadBalancerV2's can be part of EC2SecurityGroups.

        ```
        (LoadBalancerV2)-[MEMBER_OF_EC2_SECURITY_GROUP]->(EC2SecurityGroup)
        ```

- LoadBalancerV2's can be part of EC2 Subnets

        ```
        (LoadBalancerV2)-[SUBNET]->(EC2Subnet)
        ```

- LoadBalancerV2's can be part of EC2 Subnets

        ```
        (LoadBalancerV2)-[PART_OF_SUBNET]->(EC2Subnet)
        ```

- LoadBalancerV2's have [listeners](https://docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_Listener.html):

        ```
        (LoadBalancerV2)-[ELBV2_LISTENER]->(ELBV2Listener)
        ```
## Nameserver

Represents a DNS nameserver.
| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | The address of the nameserver|
| name |  The name or address of the nameserver|

### Relationships

- Nameservers are nameservers for to DNSZone.

        ```
        (Nameserver)-[NAMESERVER]->(DNSZone)
        ```

## NetworkInterface

Representation of a generic Network Interface.  Currently however, we only create NetworkInterface nodes from AWS [EC2 Instances](#ec2instance).  The spec for an AWS EC2 network interface is [here](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_InstanceNetworkInterface.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| mac\_address| The MAC address of the network interface|
| description |  Description of the network interface|
| private\_ip\_address| The primary IPv4 address of the network interface within the subnet |
| **id** | The ID of the network interface.  (known as `networkInterfaceId` in EC2) |
| private\_dns\_name| The private DNS name |
| status | Status of the network interface.  Valid Values: `available | associated | attaching | in-use | detaching ` |
| subnetid | The ID of the subnet |
| interface_type  |  Describes the type of network interface. Valid values: ` interface | efa ` |
| requester_id  | Id of the requester, e.g. `amazon-elb` for ELBs |
| requester_managed  |  Indicates whether the interface is managed by the requester |
| source_dest_check   | Indicates whether to validate network traffic to or from this network interface.  |
| public_ip   | Public IPv4 address attached to the interface  |


### Relationships

-  EC2 Network Interfaces belong to AWS accounts.

        (NetworkInterface)<-[:RESOURCE]->(:AWSAccount)

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

- LoadBalancers can have NetworkInterfaces connected to them.

        ```
        (LoadBalancer)-[NETWORK_INTERFACE]->(NetworkInterface)
        ```

- LoadBalancerV2s can have NetworkInterfaces connected to them.

        ```
        (LoadBalancerV2)-[NETWORK_INTERFACE]->(NetworkInterface)
        ```
- EC2PrivateIps are connected to a NetworkInterface.

        ```
        (NetworkInterface)-[PRIVATE_IP_ADDRESS]->(EC2PrivateIp)
        ```
-  EC2 Network Interfaces can be tagged with AWSTags.

        ```
        (NetworkInterface)-[TAGGED]->(AWSTag)
        ```

## AWSPeeringConnection

Representation of an AWS [PeeringConnection](https://docs.aws.amazon.com/vpc/latest/peering/what-is-vpc-peering.html) implementing an AWS [VpcPeeringConnection](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_VpcPeeringConnection.html) object.

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | vpcPeeringConnectionId, The ID of the VPC peering connection. |
| allow_dns_resolution_from_remote_vpc | Indicates whether a local VPC can resolve public DNS hostnames to private IP addresses when queried from instances in a peer VPC. |
| allow_egress_from_local_classic_link_to_remote_vpc | Indicates whether a local ClassicLink connection can communicate with the peer VPC over the VPC peering connection.  |
| allow_egress_from_local_vpc_to_remote_classic_link | Indicates whether a local VPC can communicate with a ClassicLink connection in the peer VPC over the VPC peering connection. |
| requester_region | Peering requester region |
| accepter_region | Peering accepter region |
| status_code | The status of the VPC peering connection. |
| status_message | A message that provides more information about the status, if applicable. |

- `AWSVpc` is an accepter or requester vpc.
  ```
  (AWSVpc)<-[REQUESTER_VPC]-(AWSPeeringConnection)
  (AWSVpc)<-[ACCEPTER_VPC]-(AWSPeeringConnection)
  ```

- `AWSCidrBlock` is an accepter or requester cidr.
  ```
  (AWSCidrBlock)<-[REQUESTER_CIDR]-(AWSPeeringConnection)
  (AWSCidrBlock)<-[ACCEPTER_CIDR]-(AWSPeeringConnection)
  ```


## RedshiftCluster

Representation of an AWS [RedshiftCluster](https://docs.aws.amazon.com/redshift/latest/APIReference/API_Cluster.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **arn** | The Amazon Resource Name (ARN) for the Redshift cluster |
| **id** | Same as arn |
| availability\_zone | Specifies the name of the Availability Zone the cluster is located in |
| cluster\_create\_time | Provides the date and time the cluster was created |
| cluster\_identifier | The unique identifier of the cluster. |
| cluster_revision_number | The specific revision number of the database in the cluster. |
| db_name | The name of the initial database that was created when the cluster was created. This same name is returned for the life of the cluster. If an initial database was not specified, a database named devdev was created by default. |
| encrypted | Specifies whether the cluster has encryption enabled |
| cluster\_status | The current state of the cluster. |
| endpoint\_address | DNS name of the Redshift cluster endpoint |
| endpoint\_port | The port that the Redshift cluster's endpoint is listening on  |
| master\_username | The master user name for the cluster. This name is used to connect to the database that is specified in the DBName parameter. |
| node_type | The node type for the nodes in the cluster. |
| number\_of\_nodes | The number of compute nodes in the cluster. |
| publicly_accessible | A boolean value that, if true, indicates that the cluster can be accessed from a public network. |
| vpc_id | The identifier of the VPC the cluster is in, if the cluster is in a VPC. |


### Relationships

- Redshift clusters are part of AWS Accounts.

        ```
        (AWSAccount)-[RESOURCE]->(RedshiftCluster)
        ```

- Redshift clusters can be members of EC2 Security Groups.

    ```
    (RedshiftCluster)-[MEMBER_OF_EC2_SECURITY_GROUP]->(EC2SecurityGroup)
    ```

- Redshift clusters may assume IAM roles. See [this article](https://docs.aws.amazon.com/redshift/latest/mgmt/authorizing-redshift-service.html).

    ```
    (RedshiftCluster)-[STS_ASSUMEROLE_ALLOW]->(AWSPrincipal)
    ```

- Redshift clusters can be members of AWSVpcs.

    ```
    (RedshiftCluster)-[MEMBER_OF_AWS_VPC]->(AWSVpc)
    ```

## RDSInstance

Representation of an AWS Relational Database Service [DBInstance](https://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_DBInstance.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | Same as ARN |
| **arn** | The Amazon Resource Name (ARN) for the DB instance. |
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

-  RDS Instances can be tagged with AWSTags.

        ```
        (RDSInstance)-[TAGGED]->(AWSTag)
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
| **id** | Same as `name`, as seen below |
| name | The name of the bucket.  This is guaranteed to be [globally unique](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.list_buckets) |
| anonymous\_actions |  List of anonymous internet accessible actions that may be run on the bucket.  This list is taken by running [policyuniverse](https://github.com/Netflix-Skunkworks/policyuniverse#internet-accessible-policy) on the policy that applies to the bucket.   |
| anonymous\_access | True if this bucket has a policy applied to it that allows anonymous access or if it is open to the internet.  These policy determinations are made by using the [policyuniverse](https://github.com/Netflix-Skunkworks/policyuniverse) library.  |
| region | The region that the bucket is in. Only defined if the S3 bucket has a [location constraint](https://docs.aws.amazon.com/AmazonS3/latest/dev/UsingBucket.html#access-bucket-intro) |

### Relationships

- S3Buckets are resources in an AWS Account.

        ```
        (AWSAccount)-[RESOURCE]->(S3Bucket)
        ```

- S3 Access Control Lists apply to S3 buckets.

        ```
        (S3Acl)-[APPLIES_TO]->(S3Bucket)
        ```

-  S3 Buckets can be tagged with AWSTags.

        ```
        (S3Bucket)-[TAGGED]->(AWSTag)
        ```

## KMSKey

Representation of an AWS [KMS Key](https://docs.aws.amazon.com/kms/latest/APIReference/API_KeyListEntry.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The id of the key|
| name |  The name of the key |
| description |  The description of the key |
| enabled |  Whether the key is enabled |
| region | The region where key is created|
| anonymous\_actions |  List of anonymous internet accessible actions that may be run on the key. |
| anonymous\_access | True if this key has a policy applied to it that allows anonymous access or if it is open to the internet. |

### Relationships

- AWS KMS Keys are resources in an AWS Account.

        ```
        (AWSAccount)-[RESOURCE]->(KMSKey)
        ```

- AWS KMS Key may also be refered as KMSAlias via aliases.

        ```
        (KMSKey)-[KNOWN_AS]->(KMSAlias)
        ```

- AWS KMS Key may also have KMSGrant based on grants.

        ```
        (KMSGrant)-[APPLIED_ON]->(KMSKey)
        ```

## KMSAlias

Representation of an AWS [KMS Key Alias](https://docs.aws.amazon.com/kms/latest/APIReference/API_AliasListEntry.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The arn of the alias|
| aliasname |  The name of the alias |
| targetkeyid |  The kms key id associated via this alias |

### Relationships

- AWS KMS Key may also be refered as KMSAlias via aliases.

        ```
        (KMSKey)-[KNOWN_AS]->(KMSAlias)
        ```

## KMSGrant

Representation of an AWS [KMS Key Grant](https://docs.aws.amazon.com/kms/latest/APIReference/API_GrantListEntry.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The id of the key grant|
| name |  The name of the key grant |
| granteeprincipal |  The principal associated with the key grant |
| creationdate | ISO 8601 date-time string when the grant was created |

### Relationships

- AWS KMS Key may also have KMSGrant based on grants.

        ```
        (KMSGrant)-[APPLIED_ON]->(KMSKey)
        ```

## APIGatewayRestAPI

Representation of an AWS [API Gateway REST API](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-rest-api.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The id of the REST API|
| createddate |  The timestamp when the REST API was created |
| version |  The version identifier for the API |
| minimumcompressionsize | A nullable integer that is used to enable or disable the compression of the REST API |
| disableexecuteapiendpoint | Specifies whether clients can invoke your API by using the default `execute-api` endpoint |
| region | The region where the REST API is created |
| anonymous\_actions |  List of anonymous internet accessible actions that may be run on the API. |
| anonymous\_access | True if this API has a policy applied to it that allows anonymous access or if it is open to the internet. |

### Relationships

- AWS API Gateway REST APIs are resources in an AWS Account.

        ```
        (AWSAccount)-[RESOURCE]->(APIGatewayRestAPI)
        ```

- AWS API Gateway REST APIs may be associated with an API Gateway Stage.

        ```
        (APIGatewayRestAPI)-[ASSOCIATED_WITH]->(APIGatewayStage)
        ```

- AWS API Gateway REST APIs may also have API Gateway Resource resources.

        ```
        (APIGatewayRestAPI)-[RESOURCE]->(APIGatewayResource)
        ```

## APIGatewayStage

Representation of an AWS [API Gateway Stage](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-stages.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The name of the API Gateway Stage|
| createddate |  The timestamp when the stage was created |
| deploymentid |  The identifier of the Deployment that the stage points to. |
| clientcertificateid | The identifier of a client certificate for an API stage. |
| cacheclusterenabled | Specifies whether a cache cluster is enabled for the stage. |
| cacheclusterstatus | The status of the cache cluster for the stage, if enabled. |
| tracingenabled | Specifies whether active tracing with X-ray is enabled for the Stage |
| webaclarn | The ARN of the WebAcl associated with the Stage |

### Relationships

- AWS API Gateway REST APIs may be associated with an API Gateway Stage.

        ```
        (APIGatewayRestAPI)-[ASSOCIATED_WITH]->(APIGatewayStage)
        ```

- AWS API Gateway Stage may also contain a Client Certificate.

        ```
        (APIGatewayStage)-[HAS_CERTIFICATE]->(APIGatewayClientCertificate)
        ```

## APIGatewayClientCertificate

Representation of an AWS [API Gateway Client Certificate](https://docs.aws.amazon.com/apigateway/api-reference/resource/client-certificate/).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The identifier of the client certificate |
| createddate |  The timestamp when the client certificate was created |
| expirationdate |  The timestamp when the client certificate will expire |

### Relationships

- AWS API Gateway Stage may also contain a Client Certificate.

        ```
        (APIGatewayStage)-[HAS_CERTIFICATE]->(APIGatewayClientCertificate)
        ```

## APIGatewayResource

Representation of an AWS [API Gateway Resource](https://docs.aws.amazon.com/apigateway/api-reference/resource/resource/).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The id of the REST API|
| path |  The timestamp when the REST API was created |
| pathpart |  The version identifier for the API |
| parentid | A nullable integer that is used to enable or disable the compression of the REST API |

### Relationships

- AWS API Gateway REST APIs may also have API Gateway Resource resources.

        ```
        (APIGatewayRestAPI)-[RESOURCE]->(APIGatewayResource)
        ```
