import logging
from typing import Dict
from typing import List

import boto3
import neo4j

from .util import get_botocore_config
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit
logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_route_tables_data(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('ec2', region_name=region, config=get_botocore_config())
    paginator = client.get_paginator('describe_route_tables')
    route_tables: List[Dict] = []
    for page in paginator.paginate():
        route_tables.extend(page['RouteTables'])
    # logger.debug(json.dumps(route_tables))
    return route_tables


@timeit
def load_route_tables(
    neo4j_session: neo4j.Session, data: List[Dict], region: str,
    aws_account_id: str, update_tag: int,
) -> None:

    ingest_route_tables = """
    UNWIND {route_tables} AS route_table

    MERGE (rt:EC2RouteTable{id: route_table.RouteTableId})
    ON CREATE SET rt.firstseen = timestamp()
    SET rt.lastupdated = {update_tag},
    rt.route_table_id = route_table.RouteTableId

    MERGE (vpc:AWSVpc{id: route_table.VpcId})
    ON CREATE SET vpc.firstseen = timestamp()
    SET vpc.lastupdated = {update_tag}, vpc.vpcid = route_table.VpcId

    MERGE (account:AWSAccount{id: route_table.OwnerId})
    ON CREATE SET account.firstseen = timestamp()
    SET account.lastupdated = {update_tag}

    MERGE (account)-[ar:RESOURCE]->(rt)
    ON CREATE SET ar.firstseen = timestamp()
    SET ar.lastupdated = {update_tag}

    MERGE (vpc)-[vr:RESOURCE]->(rt)
    ON CREATE SET vr.firstseen = timestamp()
    SET vr.lastupdated = {update_tag}


    """

    neo4j_session.run(
        ingest_route_tables, route_tables=data, update_tag=update_tag,
        region=region, aws_account_id=aws_account_id,
    )


@timeit
def load_associations(
    neo4j_session: neo4j.Session, data: List[Dict], region: str,
    aws_account_id: str, update_tag: int,
) -> None:
    ingest_subnet_associations = """
    UNWIND {route_tables} AS route_table
    UNWIND route_table.Associations AS assoc

    MERGE (rt:EC2RouteTable{id: route_table.RouteTableId})
    ON CREATE SET rt.firstseen = timestamp()
    SET rt.lastupdated = {update_tag},
    rt.route_table_id = route_table.RouteTableId

    MERGE (rta:EC2RouteTableAssociation{id: assoc.RouteTableAssociationId})
    ON CREATE SET rta.firstseen = timestamp()
    SET rta.state = assoc.AssociationState.state,
    rta.subnet_id = assoc.SubnetId,
    rta.main = assoc.Main,
    rta.lastupdated = {update_tag}

    MERGE (rta)-[rta_a:ASSOCIATED]->(rt)
    ON CREATE SET rta_a.firstseen = timestamp()
    SET rta_a.lastupdated = {update_tag}


    FOREACH(runMe IN CASE WHEN assoc.SubnetId IS NOT NULL THEN [1] ELSE [] END |

        MERGE (rt:EC2RouteTable{id: route_table.RouteTableId})
        ON CREATE SET rt.firstseen = timestamp()
        SET rt.lastupdated = {update_tag},
        rt.route_table_id = route_table.RouteTableId

        MERGE (subnet:EC2Subnet{subnetid: assoc.SubnetId})
        ON CREATE SET subnet.firstseen = timestamp()
        SET subnet.lastupdated = {update_tag}

        MERGE (subnet)-[r:ASSOCIATED]->(rt)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {update_tag}, r.main = assoc.Main,
        r.state = assoc.AssociationState.State,
        r.id = assoc.RouteTableAssociationId

        MERGE (subnet)-[s_rta:ASSOCIATED]->(rta)
        ON CREATE SET s_rta.firstseen = timestamp()
        SET s_rta.lastupdated = {update_tag}

    )


    """

    neo4j_session.run(
        ingest_subnet_associations, route_tables=data, update_tag=update_tag,
        region=region, aws_account_id=aws_account_id,
    )


@timeit
def load_default_associations(
    neo4j_session: neo4j.Session, data: List[Dict], region: str,
    aws_account_id: str, update_tag: int,
) -> None:
    ingest_default_associations = """

    MATCH (a:AWSAccount{id:{aws_account_id}})-[:RESOURCE]-(snet:EC2Subnet)-[]-(vpc:AWSVpc)-
    [:RESOURCE]-(rtb:EC2RouteTable)-[:ASSOCIATED]-(rtba:EC2RouteTableAssociation{main:true})
    WHERE NOT (snet)-[:ASSOCIATED]-(:EC2RouteTable)

    MERGE (snet)-[r_m:ASSOCIATED]->(rtb)
    ON CREATE SET r_m.firstseen = timestamp()
    SET r_m.lastupdated = {update_tag}, r_m.main = rtba.Main,
    r_m.state = rtba.AssociationState.State,
    r_m.id = rtba.RouteTableAssociationId

    MERGE (subnet)-[s_rta_m:ASSOCIATED]->(rtba)
    ON CREATE SET s_rta_m.firstseen = timestamp()
    SET s_rta_m.lastupdated = {update_tag}
    """

    neo4j_session.run(
        ingest_default_associations, route_tables=data, update_tag=update_tag,
        region=region, aws_account_id=aws_account_id,
    )


@timeit
def load_routes(
    neo4j_session: neo4j.Session, data: List[Dict], region: str,
    aws_account_id: str, update_tag: int,
) -> None:

    ingest_routes = """
    UNWIND {route_tables} AS route_table
    UNWIND route_table.Routes AS route

    MERGE (rt:EC2RouteTable{id: route_table.RouteTableId})
    ON CREATE SET rt.firstseen = timestamp()
    SET rt.lastupdated = {update_tag}

    MERGE (account:AWSAccount{id: route_table.OwnerId})
    ON CREATE SET account.firstseen = timestamp()
    SET account.lastupdated = {update_tag}

    MERGE (account)-[ar:RESOURCE]->(r)
    ON CREATE SET ar.firstseen = timestamp()
    SET ar.lastupdated = {update_tag}




    FOREACH(runMe IN CASE WHEN route.GatewayId IS NOT NULL AND
        route.GatewayId CONTAINS 'local' AND
        route.DestinationCidrBlock  IS NOT NULL THEN [1] ELSE [] END |

        MERGE (r:EC2Route:Route{id: route_table.RouteTableId + '|' + route.DestinationCidrBlock})
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {update_tag},
        r.gateway_id  =  route.GatewayId

        MERGE (rt)-[ra:ROUTE]->(r)
        ON CREATE SET ra.firstseen = timestamp()
        SET ra.lastupdated = {update_tag}
    )

    FOREACH(runMe IN CASE WHEN route.GatewayId IS NOT NULL AND
        route.GatewayId CONTAINS 'igw-' AND
        route.DestinationCidrBlock  IS NOT NULL THEN [1] ELSE [] END |

        MERGE (r:EC2Route:Route{id: route_table.RouteTableId + '|' + route.DestinationCidrBlock})
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {update_tag},
        r.gateway_id  =  route.GatewayId

        MERGE (rt)-[ra:ROUTE]->(r)
        ON CREATE SET ra.firstseen = timestamp()
        SET ra.lastupdated = {update_tag}


        MERGE (igw:AWSInternetGateway{id: route.GatewayId})
        ON CREATE SET igw.firstseen = timestamp()
        SET igw.lastupdated = {update_tag}

        MERGE (igw)-[rg:ASSOCIATED]->(r)
        ON CREATE SET rg.firstseen = timestamp()
        SET rg.lastupdated = {update_tag}

    )

    FOREACH(runMe IN CASE WHEN route.GatewayId IS NOT NULL AND
        route.GatewayId CONTAINS 'vgw-' AND
        route.DestinationCidrBlock  IS NOT NULL THEN [1] ELSE [] END |

        MERGE (r:EC2Route:Route{id: route_table.RouteTableId + '|' + route.DestinationCidrBlock})
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {update_tag},
        r.vgw_id  =  route.GatewayId

        MERGE (rt)-[ra:ROUTE]->(r)
        ON CREATE SET ra.firstseen = timestamp()
        SET ra.lastupdated = {update_tag}


        MERGE (vgw:AWSVPNGateway{id: route.GatewayId})
        ON CREATE SET vgw.firstseen = timestamp()
        SET vgw.lastupdated = {update_tag}

        MERGE (vgw)-[rg:ASSOCIATED]->(r)
        ON CREATE SET rg.firstseen = timestamp()
        SET rg.lastupdated = {update_tag}

    )

    FOREACH(runMe IN CASE WHEN route.VpcPeeringConnectionId IS NOT NULL AND
        route.DestinationCidrBlock  IS NOT NULL THEN [1] ELSE [] END |

        MERGE (r:EC2Route:Route{id: route_table.RouteTableId + '|' + route.DestinationCidrBlock})
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {update_tag},
        r.peeringconnection_id  =  route.VpcPeeringConnectionId

        MERGE (rt)-[ra:ROUTE]->(r)
        ON CREATE SET ra.firstseen = timestamp()
        SET ra.lastupdated = {update_tag}

        MERGE (pcx:AWSPeeringConnection{id: route.VpcPeeringConnectionId})
        ON CREATE SET pcx.firstseen = timestamp()
        SET pcx.lastupdated = {update_tag}

        MERGE (pcx)-[rg:ASSOCIATED]->(r)
        ON CREATE SET rg.firstseen = timestamp()
        SET rg.lastupdated = {update_tag}

    )

    FOREACH(runMe IN CASE WHEN route.NatGatewayId  IS NOT NULL AND
        route.DestinationCidrBlock  IS NOT NULL THEN [1] ELSE [] END |

        MERGE (r:EC2Route:Route{id: route_table.RouteTableId + '|' + route.DestinationCidrBlock})
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {update_tag},
        r.ngw_id  =  route.NatGatewayId

        MERGE (rt)-[ra:ROUTE]->(r)
        ON CREATE SET ra.firstseen = timestamp()
        SET ra.lastupdated = {update_tag}

        MERGE (ngw:NatGateway{id: route.NatGatewayId})
        ON CREATE SET ngw.firstseen = timestamp()
        SET ngw.lastupdated = {update_tag}

        MERGE (ngw)-[rg:ASSOCIATED]->(r)
        ON CREATE SET rg.firstseen = timestamp()
        SET rg.lastupdated = {update_tag}
    )


    FOREACH(runMe IN CASE WHEN route.TransitGatewayId  IS NOT NULL AND
        route.DestinationCidrBlock  IS NOT NULL THEN [1] ELSE [] END |

        MERGE (r:EC2Route:Route{id: route_table.RouteTableId + '|' + route.DestinationCidrBlock})
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {update_tag},
        r.tgw_id  =  route.TransitGatewayId

        MERGE (rt)-[ra:ROUTE]->(r)
        ON CREATE SET ra.firstseen = timestamp()
        SET ra.lastupdated = {update_tag}

        MERGE (tgw:AWSTransitGateway{tgw_id: route.TransitGatewayId})
        ON CREATE SET tgw.firstseen = timestamp()
        SET tgw.lastupdated = {update_tag}

        MERGE (tgw)-[rg:ASSOCIATED]->(r)
        ON CREATE SET rg.firstseen = timestamp()
        SET rg.lastupdated = {update_tag}

    )

    FOREACH(runMe IN CASE WHEN route.CarrierGatewayId  IS NOT NULL AND
        route.DestinationCidrBlock  IS NOT NULL THEN [1] ELSE [] END |

        MERGE (r:EC2Route:Route{id: route_table.RouteTableId + '|' + route.DestinationCidrBlock})
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {update_tag},
        r.cgw_id  =  route.CarrierGatewayId

        MERGE (rt)-[ra:ROUTE]->(r)
        ON CREATE SET ra.firstseen = timestamp()
        SET ra.lastupdated = {update_tag}

        MERGE (cgw:CarrierGateway{id: route.CarrierGatewayId})
        ON CREATE SET cgw.firstseen = timestamp()
        SET cgw.lastupdated = {update_tag}

        MERGE (cgw)-[rg:ASSOCIATED]->(r)
        ON CREATE SET rg.firstseen = timestamp()
        SET rg.lastupdated = {update_tag}

    )




    FOREACH(runMe IN CASE WHEN route.GatewayId IS NOT NULL AND
        route.GatewayId CONTAINS 'local' AND
        route.DestinationPrefixListId  IS NOT NULL THEN [1] ELSE [] END |

        MERGE (r:EC2Route:Route{id: route_table.RouteTableId + '|' + route.DestinationPrefixListId})
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {update_tag},
        r.gateway_id  =  route.GatewayId

        MERGE (rt)-[ra:ROUTE]->(r)
        ON CREATE SET ra.firstseen = timestamp()
        SET ra.lastupdated = {update_tag}
    )

    FOREACH(runMe IN CASE WHEN route.GatewayId IS NOT NULL AND
        route.GatewayId CONTAINS 'igw-' AND
        route.DestinationPrefixListId  IS NOT NULL THEN [1] ELSE [] END |

        MERGE (r:EC2Route:Route{id: route_table.RouteTableId + '|' + route.DestinationPrefixListId})
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {update_tag},
        r.gateway_id  =  route.GatewayId

        MERGE (rt)-[ra:ROUTE]->(r)
        ON CREATE SET ra.firstseen = timestamp()
        SET ra.lastupdated = {update_tag}


        MERGE (igw:AWSInternetGateway{id: route.GatewayId})
        ON CREATE SET igw.firstseen = timestamp()
        SET igw.lastupdated = {update_tag}

        MERGE (igw)-[rg:ASSOCIATED]->(r)
        ON CREATE SET rg.firstseen = timestamp()
        SET rg.lastupdated = {update_tag}

    )

    FOREACH(runMe IN CASE WHEN route.GatewayId IS NOT NULL AND
        route.GatewayId CONTAINS 'vgw-' AND
        route.DestinationPrefixListId  IS NOT NULL THEN [1] ELSE [] END |

        MERGE (r:EC2Route:Route{id: route_table.RouteTableId + '|' + route.DestinationPrefixListId})
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {update_tag},
        r.vgw_id  =  route.GatewayId

        MERGE (rt)-[ra:ROUTE]->(r)
        ON CREATE SET ra.firstseen = timestamp()
        SET ra.lastupdated = {update_tag}


        MERGE (vgw:AWSVPNGateway{id: route.GatewayId})
        ON CREATE SET vgw.firstseen = timestamp()
        SET vgw.lastupdated = {update_tag}

        MERGE (vgw)-[rg:ASSOCIATED]->(r)
        ON CREATE SET rg.firstseen = timestamp()
        SET rg.lastupdated = {update_tag}

    )

    FOREACH(runMe IN CASE WHEN route.VpcPeeringConnectionId IS NOT NULL AND
        route.DestinationPrefixListId  IS NOT NULL THEN [1] ELSE [] END |

        MERGE (r:EC2Route:Route{id: route_table.RouteTableId + '|' + route.DestinationPrefixListId})
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {update_tag},
        r.peeringconnection_id  =  route.VpcPeeringConnectionId

        MERGE (rt)-[ra:ROUTE]->(r)
        ON CREATE SET ra.firstseen = timestamp()
        SET ra.lastupdated = {update_tag}

        MERGE (pcx:AWSPeeringConnection{id: route.VpcPeeringConnectionId})
        ON CREATE SET pcx.firstseen = timestamp()
        SET pcx.lastupdated = {update_tag}

        MERGE (pcx)-[rg:ASSOCIATED]->(r)
        ON CREATE SET rg.firstseen = timestamp()
        SET rg.lastupdated = {update_tag}

    )

    FOREACH(runMe IN CASE WHEN route.NatGatewayId  IS NOT NULL AND
        route.DestinationPrefixListId  IS NOT NULL THEN [1] ELSE [] END |

        MERGE (r:EC2Route:Route{id: route_table.RouteTableId + '|' + route.DestinationPrefixListId})
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {update_tag},
        r.ngw_id  =  route.NatGatewayId

        MERGE (rt)-[ra:ROUTE]->(r)
        ON CREATE SET ra.firstseen = timestamp()
        SET ra.lastupdated = {update_tag}

        MERGE (ngw:NatGateway{id: route.NatGatewayId})
        ON CREATE SET ngw.firstseen = timestamp()
        SET ngw.lastupdated = {update_tag}

        MERGE (ngw)-[rg:ASSOCIATED]->(r)
        ON CREATE SET rg.firstseen = timestamp()
        SET rg.lastupdated = {update_tag}
    )


    FOREACH(runMe IN CASE WHEN route.TransitGatewayId  IS NOT NULL AND
        route.DestinationPrefixListId  IS NOT NULL THEN [1] ELSE [] END |

        MERGE (r:EC2Route:Route{id: route_table.RouteTableId + '|' + route.DestinationPrefixListId})
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {update_tag},
        r.tgw_id  =  route.TransitGatewayId

        MERGE (rt)-[ra:ROUTE]->(r)
        ON CREATE SET ra.firstseen = timestamp()
        SET ra.lastupdated = {update_tag}

        MERGE (tgw:AWSTransitGateway{tgw_id: route.TransitGatewayId})
        ON CREATE SET tgw.firstseen = timestamp()
        SET tgw.lastupdated = {update_tag}

        MERGE (tgw)-[rg:ASSOCIATED]->(r)
        ON CREATE SET rg.firstseen = timestamp()
        SET rg.lastupdated = {update_tag}

    )

    FOREACH(runMe IN CASE WHEN route.CarrierGatewayId  IS NOT NULL AND
        route.DestinationPrefixListId  IS NOT NULL THEN [1] ELSE [] END |

        MERGE (r:EC2Route:Route{id: route_table.RouteTableId + '|' + route.DestinationPrefixListId})
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {update_tag},
        r.cgw_id  =  route.CarrierGatewayId

        MERGE (rt)-[ra:ROUTE]->(r)
        ON CREATE SET ra.firstseen = timestamp()
        SET ra.lastupdated = {update_tag}

        MERGE (cgw:CarrierGateway{id: route.CarrierGatewayId})
        ON CREATE SET cgw.firstseen = timestamp()
        SET cgw.lastupdated = {update_tag}

        MERGE (cgw)-[rg:ASSOCIATED]->(r)
        ON CREATE SET rg.firstseen = timestamp()
        SET rg.lastupdated = {update_tag}

    )



    FOREACH(runMe IN CASE WHEN route.DestinationCidrBlock IS NOT NULL THEN [1] ELSE [] END |
        MERGE (ec2r:EC2Route:Route{id: route_table.RouteTableId + '|' + route.DestinationCidrBlock})
        ON CREATE SET ec2r.firstseen = timestamp()
        SET ec2r.destination_cidr_block = route.DestinationCidrBlock,
        ec2r.origin = route.Origin, ec2r.state = route.State
    )

    FOREACH(runMe IN CASE WHEN route.DestinationPrefixListId IS NOT NULL THEN [1] ELSE [] END |
        MERGE (ec2r:EC2Route:Route{id: route_table.RouteTableId + '|' + route.DestinationPrefixListId})
        ON CREATE SET ec2r.firstseen = timestamp()
        SET ec2r.destination_prefix_list_id = route.DestinationPrefixListId,
        ec2r.origin = route.Origin, ec2r.state = route.State
    )

    """
    neo4j_session.run(
        ingest_routes, route_tables=data, update_tag=update_tag,
        region=region, aws_account_id=aws_account_id,
    )


@timeit
def cleanup_route_tables(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_route_tables_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_route_tables(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str],
    current_aws_account_id: str, update_tag: int, common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.debug("Syncing RouteTables for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_route_tables_data(boto3_session, region)
        load_route_tables(neo4j_session, data, region, current_aws_account_id, update_tag)
        load_associations(neo4j_session, data, region, current_aws_account_id, update_tag)
        load_default_associations(neo4j_session, data, region, current_aws_account_id, update_tag)
        load_routes(neo4j_session, data, region, current_aws_account_id, update_tag)
    cleanup_route_tables(neo4j_session, common_job_parameters)
