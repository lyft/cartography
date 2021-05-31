from cartography.graph.querybuilder import build_node_ingestion_query
from cartography.graph.querybuilder import build_relationship_ingestion_query


def test_build_node_ingestion_query():
    query = build_node_ingestion_query(
        'EC2Instance',
        {
            'id': 'Arn',
            'arn': 'Arn',
            'publicdnsname': 'PublicDnsName',
            'privateipaddress': 'PrivateIpAddress',
            'publicipaddress': 'PublicIpAddress',
            'imageid': 'ImageId',
            'instancetype': 'InstanceType',
            'monitoringstate': 'MonitoringState',
            'state': 'State',
            'launchtime': 'LaunchTime',
            'launchtimeunix': 'LaunchTimeUnix',
            'region': 'Region',
            'iaminstanceprofile': 'IamInstanceProfile',
        },
    )
    assert query == """
    UNWIND {DictList} AS item
        MERGE (i:EC2Instance{id:item.Arn})
        ON CREATE SET i.firstseen = timestamp()
        SET i.lastupdated = {UpdateTag},
        i.arn = item.Arn,
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


def test_build_node_ingestion_query_only_id():
    query = build_node_ingestion_query(
        'SomeNodeWithOnlyAnId',
        {
            'id': 'IdOnTheDictObject',
        },
    )
    assert query == """
    UNWIND {DictList} AS item
        MERGE (i:SomeNodeWithOnlyAnId{id:item.IdOnTheDictObject})
        ON CREATE SET i.firstseen = timestamp()
        SET i.lastupdated = {UpdateTag}"""


def test_build_relationship_ingestion_query():
    query = build_relationship_ingestion_query(
        'AWSAccount', 'id', 'Id',
        'EC2Instance', 'instanceid', 'InstanceId',
        'RESOURCE',
    )
    assert query == """
    UNWIND {RelMappingList} AS item
        MATCH (a:AWSAccount{id:item.Id})
        MATCH (b:EC2Instance{instanceid:item.InstanceId})
        MERGE (a)-[r:RESOURCE]->(b)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {UpdateTag}"""


def test_build_relationship_with_attributes_query():
    query = build_relationship_ingestion_query(
        'Service', 'name', 'Name',
        'GoLibrary', 'id', 'Id',
        'REQUIRES',
        {
            'libraryspecifier': 'LibrarySpecifier',
            'someotherrelfield': 'SomeOtherRelField',
        },
    )
    assert query == """
    UNWIND {RelMappingList} AS item
        MATCH (a:Service{name:item.Name})
        MATCH (b:GoLibrary{id:item.Id})
        MERGE (a)-[r:REQUIRES]->(b)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {UpdateTag},
        r.libraryspecifier = item.LibrarySpecifier,
        r.someotherrelfield = item.SomeOtherRelField"""
