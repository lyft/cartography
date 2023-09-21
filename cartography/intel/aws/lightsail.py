import json
import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import botocore
from botocore.config import Config
from datetime import date
from datetime import datetime
import neo4j

# from cartography.intel.aws.util.misc import discover_service_regions
from cartography.util import timeit
# from datetime import datetime
from cartography.util import aws_handle_regions
# from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)

config = Config(
    connect_timeout=300, 
    read_timeout=300,
    retries = {
      'max_attempts': 1,
      'mode': 'standard'
   }
)

@timeit
@aws_handle_regions
def get_lightsails_instances(boto3_session: boto3.session.Session, region: str) -> List[Any]:
    logger.info("Getting Lightsails instances: %s", region)
    
    client = boto3_session.client('lightsail', region_name=region)
    data: List[Any] = []
    try:
        paginator = client.get_paginator('get_instances')
        for page in paginator.paginate():
            data.extend(page['instances'])
    except botocore.exceptions.ClientError as e:
        logger.warning("{} in this region. Skipping...".format(e.response['Error']['Message']))
        return []
    return data


@timeit
@aws_handle_regions
def get_lightsails_active_names(boto3_session: boto3.session.Session, region: str) -> List[Any]:
    logger.info("Getting Lightsails Active Names: %s", region)
    
    client = boto3_session.client('lightsail', region_name=region)
    paginator = client.get_paginator('get_active_names')
    data: List[Any] = []
    for page in paginator.paginate():
        data.extend(page['activeNames'])
    return data


@timeit
@aws_handle_regions
def get_lightsails_domains(boto3_session: boto3.session.Session, region: str) -> List[Any]:
    # domains are only available in us-east-1
    if region != 'us-east-1':
        return []
    
    logger.info("Getting Lightsails domains: %s", region)
    client = boto3_session.client('lightsail', config=config, region_name=region)
    data: List[Any] = []
    try:
        paginator = client.get_paginator('get_domains')
        for page in paginator.paginate():
            data.extend(page['domains'])
    except botocore.exceptions.ClientError as e:
        logger.warning("{} in this region. Skipping...".format(e.response['Error']['Message']))
        return []

    return data


    # paginator = client.get_paginator('get_instance_snapshots')
    # for page in paginator.paginate():
    #     meta['instance_snapshots']=page['instance_snapshots']
    # TODO: all other services

@timeit
def load_lightsail_instances(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    org_id: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_instances = """
        MERGE (ls:LightsailInstance{id: $arn})
        ON CREATE SET ls.firstseen = $RECORD_TIMESTAMP, ls.org_id = $ORG_ID, ls.account_id = $AWS_ACCOUNT_ID
        SET
            ls.arn = $arn,
            ls.name = $name,
            ls.createdAt = $createdAt,
            ls.ipAddressType = $ipAddressType,
            ls.resourceType = $resourceType
        WITH ls
        MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
        MERGE (owner)-[r:RESOURCE]->(instance)
        ON CREATE SET r.firstseen = $RECORD_TIMESTAMP, r.org_id = $ORG_ID, r.account_id = $AWS_ACCOUNT_ID
        SET r.lastupdated = $aws_update_tag
    """
    
    for instance in data:
        # printObj(instance)
        neo4j_session.run(
            ingest_instances,
            arn = instance.get('arn'),
            name = instance.get('name'),
            createdAt = instance.get('createdAt'),
            ipAddressType = instance.get('ipAddressType'),
            # ipv6Address = instance.get('ipv6Address'),
            # metadataOptions = instance.get('metadataOptions'),
            # networking = instance.get('networking'),
            # publicIpAddress = instance.get('publicIpAddress'),
            # privateIpAddress = instance.get('privateIpAddress'),
            resourceType = instance.get('resourceType'),
            # tags = instance.get('tags'),
            Region=region,
            ORG_ID=org_id,
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
            RECORD_TIMESTAMP=datetime.timestamp(datetime.now()),
        )

@timeit
def sync(
        neo4j_session: neo4j.Session,
        boto3_session: boto3.session.Session,
        regions: List[str],
        current_aws_account_id: str,
        update_tag: int,
        common_job_parameters: Dict,
) -> None:
    # client = boto3_session.client('lightsail')
    service_regions = ["us-west-2","us-east-1"]

    logger.info("Syncing AWS Lightsail in account '%s'.", current_aws_account_id)
    org_id = common_job_parameters.get('target_org_id', '')
    
    for region in regions:
        if region not in service_regions:
           continue
        data = get_lightsails_instances(boto3_session, region)
        # meta["instances"] = data
        # printObj(data)
        load_lightsail_instances(neo4j_session, data, region, org_id, current_aws_account_id, update_tag)
        

def printObj(data: Any) -> None:
    json_formatted_str = json.dumps(data, indent=4, sort_keys=True, default=str)
    print(json_formatted_str)
    
    
testData = """
{
*    "arn": "arn:aws:lightsail:us-west-2:832698950836:Instance/b03e7647-87b5-441a-91db-0c7473231b7d",
    "blueprintId": "wordpress",
    "blueprintName": "WordPress",
    "bundleId": "nano_3_0",
*    "createdAt": "2023-08-01 12:10:46.194000-07:00",
    "hardware": {
        "cpuCount": 2,
        "disks": [
            {
                "attachedTo": "test-1",
                "attachmentState": "attached",
                "createdAt": "2023-08-01 12:10:46.194000-07:00",
                "iops": 100,
                "isSystemDisk": true,
                "path": "/dev/xvda",
                "sizeInGb": 20
            }
        ],
        "ramSizeInGb": 0.5
    },
*    "ipAddressType": "dualstack",
*    "ipv6Addresses": [
        "2600:1f14:2153:4b00:7220:92c2:1c41:1f0f"
    ],
    "isStaticIp": false,
*    "location": {
        "availabilityZone": "us-west-2a",
        "regionName": "us-west-2"
    },
*    "metadataOptions": {
        "httpEndpoint": "enabled",
        "httpProtocolIpv6": "disabled",
        "httpPutResponseHopLimit": 1,
        "httpTokens": "optional",
        "state": "applied"
    },
*    "name": "test-1",
*    "networking": {
        "monthlyTransfer": {
            "gbPerMonthAllocated": 1024
        },
        "ports": [
            {
                "accessDirection": "inbound",
                "accessFrom": "Anywhere (0.0.0.0/0 and ::/0)",
                "accessType": "public",
                "cidrListAliases": [],
                "cidrs": [
                    "0.0.0.0/0"
                ],
                "commonName": "",
                "fromPort": 80,
                "ipv6Cidrs": [
                    "::/0"
                ],
                "protocol": "tcp",
                "toPort": 80
            },
            {
                "accessDirection": "inbound",
                "accessFrom": "Anywhere (0.0.0.0/0 and ::/0)",
                "accessType": "public",
                "cidrListAliases": [],
                "cidrs": [
                    "0.0.0.0/0"
                ],
                "commonName": "",
                "fromPort": 22,
                "ipv6Cidrs": [
                    "::/0"
                ],
                "protocol": "tcp",
                "toPort": 22
            },
            {
                "accessDirection": "inbound",
                "accessFrom": "Anywhere (0.0.0.0/0 and ::/0)",
                "accessType": "public",
                "cidrListAliases": [],
                "cidrs": [
                    "0.0.0.0/0"
                ],
                "commonName": "",
                "fromPort": 443,
                "ipv6Cidrs": [
                    "::/0"
                ],
                "protocol": "tcp",
                "toPort": 443
            }
        ]
    },
*    "privateIpAddress": "172.26.12.13",
*    "publicIpAddress": "54.200.150.66",
*    "resourceType": "Instance",
    "sshKeyName": "LightsailDefaultKeyPair",
    "state": {
        "code": 16,
        "name": "running"
    },
    "supportCode": "801007670468/i-0800f9ba0b65e48d3",
*    "tags": [],
    "username": "bitnami"
}
"""