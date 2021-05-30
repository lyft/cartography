from cartography.graph.loader import build_node_ingestion_query
from cartography.graph.loader import build_relationship_ingestion_query


def test_build_node_ingestion_query():
    query = build_node_ingestion_query(
        'EC2Instance',
        'instanceid',
        [
            ('publicdnsname', 'PublicDnsName'),
            ('privateipaddress', 'PrivateIpAddress'),
            ('publicipaddress', 'PublicIpAddress'),
            ('imageid', 'ImageId'),
            ('instancetype', 'InstanceType'),
            ('monitoringstate', 'MonitoringState'),
            ('state', 'State'),
            ('launchtime', 'LaunchTime'),
            ('launchtimeunix', 'LaunchTimeUnix'),
            ('region', 'Region'),
            ('iaminstanceprofile', 'IamInstanceProfile'),
        ],
    )
    assert query == """
    UNWIND {DictList} AS item
        MERGE (i:EC2Instance{instanceid:{IdValue}})
        ON CREATE SET i.firstseen = timestamp(),
        SET i.lastupdated = {UpdateTag},
        i.publicdnsname = item.PublicDnsName,
        i.privateipaddress = item.PrivateIpAddress,
        i.publicipaddress = item.PublicIpAddress,
        i.imageid = item.ImageId,
        i.instancetype = item.InstanceType,
        i.monitoringstate = item.MonitoringState,
        i.state = item.State,
        i.launchtime = item.LaunchTime,
        i.launchtimeunix = item.LaunchTimeUnix,
        i.region = item.Region,
        i.iaminstanceprofile = item.IamInstanceProfile"""


def test_build_relationship_ingestion_query():
    query = build_relationship_ingestion_query(
        'AWSAccount',
        ('id', 'Id'),
        'EC2Instance',
        ('instanceid', 'InstanceId'),
        'RESOURCE',
        [],
    )
    assert query == """
    UNWIND {DictList} AS item
        MATCH (a:AWSAccount{id:item.Id})
        MATCH (b:EC2Instance{instanceid:item.InstanceId})
        MERGE (a)-[r:RESOURCE]->(b)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {UpdateTag}"""


def test_build_relationship_with_attributes_query():
    query = build_relationship_ingestion_query(
        'Service',
        ('id', 'Id'),
        'GoLibrary',
        ('id', 'Id'),
        'REQUIRES',
        [
            ('libraryspecifier', 'LibrarySpecifier'),
            ('someotherrelfield', 'SomeOtherRelField'),
        ],
    )
    assert query == """
    UNWIND {DictList} AS item
        MATCH (a:Service{id:item.Id})
        MATCH (b:GoLibrary{id:item.Id})
        MERGE (a)-[r:REQUIRES]->(b)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {UpdateTag},
        r.libraryspecifier = item.LibrarySpecifier,
        r.someotherrelfield = item.SomeOtherRelField"""
