# Okta intel module - Origins
import asyncio
import logging
from typing import Dict
from typing import List
from typing import Any
from collections import defaultdict

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from okta.client import Client as OktaClient
from cartography.models.okta.role import OktaRoleSchema
from cartography.util import timeit


logger = logging.getLogger(__name__)


@timeit
def sync_okta_roles(
    okta_client: OktaClient,
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync Okta roles
    :param okta_client: An Okta client object
    :param neo4j_session: Session with Neo4j server
    :param common_job_parameters: Settings used by all Okta modules
    :return: Nothing
    """
    logger.info("Syncing Okta roles")
    roles = asyncio.run(_get_okta_roles(okta_client))
    role_users = asyncio.run(_get_okta_role_users(okta_client))
    transformed_roles = _transform_okta_roles(roles, role_users)
    _load_okta_roles(neo4j_session, transformed_roles, common_job_parameters)
    _cleanup_okta_roles(neo4j_session, common_job_parameters)


@timeit
async def _get_okta_roles(okta_client: OktaClient) -> List[Dict[str, Any]]:
    """
    Get Okta origins list from Okta
    :param okta_client: An Okta client object
    :return: List of Okta origins
    """
    query_parameters = {"sort": "name", "order": "acs", "limit": 200}
    headers = {
        "Authorization": f"SSWS {okta_client._api_token}",
        "Content-Type": "application/json",
    }


    # This is undocumented and internal, don't do this at home
    url = f"{okta_client._base_url}api/internal/permissionSets"
    resp = requests.get(url, params=query_parameters, headers=headers)
    if resp.status_code != 200:
        logger.info("We didn't get the response expected")
        return []

    return resp.json()


    breakpoint()
    # url = f"{okta_client._base_url}api/v1/iam/roles"
    #  /api/v1/iam/roles/${roleIdOrLabel}/permissions
    # https://lyft-admin.oktapreview.com/api/internal/permissionSets?sort=name&order=asc&limit=20
    breakpoint()
    # https://lyft-admin.oktapreview.com/api/internal/v1/admin/capabilities
    # https://lyft-admin.oktapreview.com/api/internal/privileges/admins?q=
    # https://lyft-admin.oktapreview.com/api/internal/privileges/stats/users/00u10tk991qGuxcmF0h8
    # /api/v1/iam/resource-sets

    # /api/v1/iam/roles
    # origins, resp, _ = await okta_client.list_origins(query_parameters)

    # output_origins += origins
    # while resp.has_next():
    #     origins, _ = await resp.next()
    #     output_origins += origins
    #     logger.info(f"Fetched {len(origins)} origins")
    # return output_origins


@timeit
def _transform_okta_roles(
    okta_roles: List[Dict[str, Any]],
    role_users: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Convert a list of Okta okta_roles into a format for Neo4j
    :param okta_roles: List of Okta roles
    :param role_users: Dict of Okta role user assignments
    :return: List of origin dicts
    """
    transformed_roles: List[Dict] = []
    logger.info(f"Transforming {len(okta_roles)} Okta roles")
    for okta_role in okta_roles:
        roles_props = {}
        roles_props["id"] = okta_role['id']
        roles_props["name"] = okta_role['name']
        roles_props["description"] = okta_role['description']
        roles_props["type"] = okta_role['type']
        roles_props["permissions"] = okta_role['permissions']
        roles_props["conditions"] = okta_role['conditions']
        roles_props["isEditable"] = okta_role['isEditable']
        roles_props["cursor"] = okta_role['cursor']
        transformed_roles.append(roles_props)
        if okta_role['name'] in role_users.keys():
            for role_user_id in role_users[okta_role['name']]:
                match_role = {**roles_props, "user_id": role_user_id}
                transformed_roles.append(match_role)
    return transformed_roles


@timeit
def _load_okta_roles(
    neo4j_session: neo4j.Session,
    role_list: List[Dict],
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Load Okta roles information into the graph
    :param neo4j_session: session with neo4j server
    :param role_list: list of roles
    :param common_job_parameters: Settings used by all Okta modules
    :return: Nothing
    """

    logger.info(f"Loading {len(role_list)} Okta roles")

    load(
        neo4j_session,
        OktaRoleSchema(),
        role_list,
        OKTA_ORG_ID=common_job_parameters["OKTA_ORG_ID"],
        lastupdated=common_job_parameters["UPDATE_TAG"],
    )


@timeit
def _cleanup_okta_roles(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    """
    Cleanup origin nodes and relationships
    :param neo4j_session: session with neo4j server
    :param common_job_parameters: Settings used by all Okta modules
    :return: Nothing
    """
    GraphJob.from_node_schema(OktaRoleSchema(), common_job_parameters).run(
        neo4j_session
    )
####
### Get assignment to roles
####

@timeit
async def _get_okta_role_users(okta_client: OktaClient) -> List[Dict[str, Any]]:
    """
    Get Okta origins list from Okta
    :param okta_client: An Okta client object
    :return: List of Okta origins
    """
    # TODO: Technically this API is paginated by user ID
    # this is unlike any other API at Okta. I guess it assumes order?
    # api/internal/privileges/admins?after={user_id}&limit=15
    query_parameters = {"q": "", "limit": 200}
    headers = {
        "Authorization": f"SSWS {okta_client._api_token}",
        "Content-Type": "application/json",
    }

    # This is undocumented and internal, don't do this at home
    # This lists all admins (users only)
    url = f"{okta_client._base_url}api/internal/privileges/admins"
    resp = requests.get(url, params=query_parameters, headers=headers)
    if resp.status_code != 200:
        logger.info("We didn't get the response expected")
        return []
    all_admin_roles = defaultdict(lambda: [])
    # This is undocumented and internal, don't do this at home
    # This fetches the role that user has assigned
    for user in resp.json():
        user_url = f"{okta_client._base_url}api/internal/privileges/stats/users/{user['userId']}"
        group_url = f"{user_url}/groups"
        for url in [user_url, group_url]:
            resp = requests.get(url, params=query_parameters, headers=headers)
            if resp.status_code != 200:
                logger.info("We didn't get the response expected")
                continue
            # It seems that Okta uses the role name (which is supposed to be unique)
            # as the unique identifier, this is bad practice, as there are roleIDs
            # i.e Super Administrator vs SuperOrgAdmin
            for role in resp.json():
                all_admin_roles[role['roleName']].append(user['userId'])
    return dict(all_admin_roles)

