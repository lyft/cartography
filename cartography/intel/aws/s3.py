import hashlib
import json
import logging

from botocore.exceptions import ClientError
from policyuniverse.policy import Policy

from cartography.util import run_analysis_job
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_s3_bucket_list(boto3_session):
    client = boto3_session.client('s3')
    # NOTE no paginator available for this operation
    return client.list_buckets()


@timeit
def get_s3_bucket_details(boto3_session, bucket_data):
    """
    Iterates over all S3 buckets. Yields bucket name (string) and pairs of S3 bucket policies (JSON) and ACLs (JSON)
    """
    client = boto3_session.client('s3')
    for bucket in bucket_data['Buckets']:
        acl = get_acl(bucket, client)
        policy = get_policy(bucket, client)
        yield bucket['Name'], acl, policy


@timeit
def get_policy(bucket, client):
    """
    Gets the S3 bucket policy. Returns policy string or None if no policy
    """
    try:
        policy = client.get_bucket_policy(Bucket=bucket['Name'])
    except ClientError as e:
        # no policy is defined for this bucket
        if "NoSuchBucketPolicy" in e.args[0]:
            policy = None
        elif "AccessDenied" in e.args[0]:
            logger.warning("Access denied trying to retrieve S3 bucket {} policy".format(bucket['Name']))
            policy = None
        else:
            raise
    return policy


@timeit
def get_acl(bucket, client):
    """
    Gets the S3 bucket ACL. Returns ACL string
    """
    try:
        acl = client.get_bucket_acl(Bucket=bucket['Name'])
    except ClientError as e:
        if "AccessDenied" in e.args[0]:
            logger.warning("Failed to retrieve S3 bucket {} ACL - Access Denied".format(bucket['Name']))
            return None
        elif "NoSuchBucket" in e.args[0]:
            logger.warning("Failed to retrieve S3 bucket {} ACL - No Such Bucket".format(bucket['Name']))
            return None
        else:
            raise
    return acl


@timeit
def _load_s3_acls(neo4j_session, acls, aws_account_id, update_tag):
    """
    Ingest S3 ACL into neo4j.
    """
    ingest_acls = """
    UNWIND {acls} AS acl
    MERGE (a:S3Acl{id: acl.id})
    ON CREATE SET a.firstseen = timestamp(), a.owner = acl.owner, a.ownerid = acl.ownerid, a.type = acl.type,
    a.displayname = acl.displayname, a.granteeid = acl.granteeid, a.uri = acl.uri, a.permission = acl.permission
    SET a.lastupdated = {UpdateTag}
    WITH a,acl MATCH (s3:S3Bucket{id: acl.bucket})
    MERGE (a)-[r:APPLIES_TO]->(s3)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {UpdateTag}
    """

    neo4j_session.run(
        ingest_acls,
        acls=acls,
        UpdateTag=update_tag,
    )

    # implement the acl permission
    # https://docs.aws.amazon.com/AmazonS3/latest/dev/acl-overview.html#permissions
    run_analysis_job(
        'aws_s3acl_analysis.json',
        neo4j_session,
        {'AWS_ID': aws_account_id},
    )


@timeit
def _load_s3_policies(neo4j_session, policies, update_tag):
    """
    Ingest S3 policy results into neo4j.
    """
    # NOTE we use the coalesce function so appending works when the value is null initially
    ingest_policies = """
    UNWIND {policies} AS policy
    MATCH (s:S3Bucket) where s.name = policy.bucket
    SET s.anonymous_access = (coalesce(s.anonymous_access, false) OR policy.internet_accessible),
    s.anonymous_actions = coalesce(s.anonymous_actions, []) + policy.accessible_actions,
    s.lastupdated = {UpdateTag}
    """

    neo4j_session.run(
        ingest_policies,
        policies=policies,
        UpdateTag=update_tag,
    )


def _set_default_values(neo4j_session, aws_account_id):
    set_defaults = """
    MATCH (:AWSAccount{id: {AWS_ID}})-[:RESOURCE]->(s:S3Bucket) where NOT EXISTS(s.anonymous_actions)
    SET s.anonymous_access = false, s.anonymous_actions = []
    """

    neo4j_session.run(
        set_defaults,
        AWS_ID=aws_account_id,
    )


@timeit
def load_s3_details(neo4j_session, s3_details_iter, aws_account_id, update_tag):
    """
    Create dictionaries for all bucket ACLs and all bucket policies so we can import them in a single query for each
    """
    acls = []
    policies = []
    for bucket, acl, policy in s3_details_iter:
        if acl is None:
            continue
        parsed_acls = parse_acl(acl, bucket, aws_account_id)
        if parsed_acls:
            acls.extend(parsed_acls)
        else:
            continue
        parsed_policy = parse_policy(bucket, policy)
        if parsed_policy is not None:
            policies.append(parsed_policy)

    # cleanup existing policy properties set on S3 Buckets
    run_cleanup_job(
        'aws_s3_details.json',
        neo4j_session,
        {'UPDATE_TAG': update_tag, 'AWS_ID': aws_account_id},
    )

    _load_s3_acls(neo4j_session, acls, aws_account_id, update_tag)
    _load_s3_policies(neo4j_session, policies, update_tag)
    _set_default_values(neo4j_session, aws_account_id)


@timeit
def parse_policy(bucket, policy):
    """
    Uses PolicyUniverse to parse S3 policies and returns the internet accessibility results
    """
    # policy is not required, so may be None
    # policy JSON format. Note condition can be any JSON statement so will need to import as-is
    # policy is a very complex format, so the policyuniverse library will be used for parsing out important data
    # ...metadata...
    # "Policy" :
    # {
    #     "Version": "2012-10-17",
    #     {
    #         "Statement": [
    #             {
    #                 "Effect": "Allow",
    #                 "Principal": "*",
    #                 "Action": "s3:GetObject",
    #                 "Resource": "arn:aws:s3:::MyBucket/*"
    #             },
    #             {
    #                 "Effect": "Deny",
    #                 "Principal": "*",
    #                 "Action": "s3:GetObject",
    #                 "Resource": "arn:aws:s3:::MyBucket/MySecretFolder/*"
    #             },
    #             {
    #                 "Effect": "Allow",
    #                 "Principal": {
    #                     "AWS": "arn:aws:iam::123456789012:root"
    #                 },
    #                 "Action": [
    #                     "s3:DeleteObject",
    #                     "s3:PutObject"
    #                 ],
    #                 "Resource": "arn:aws:s3:::MyBucket/*"
    #             }
    #         ]
    #     }
    # }
    if policy is not None:
        # get just the policy element and convert to JSON because boto3 returns this as string
        policy = Policy(json.loads(policy['Policy']))
        if policy.is_internet_accessible():
            return {
                "bucket": bucket,
                "internet_accessible": True,
                "accessible_actions": list(policy.internet_accessible_actions()),
            }
        else:
            return None
    else:
        return None


@timeit
def parse_acl(acl, bucket, aws_account_id):
    """ Parses the AWS ACL object and returns a dict of the relevant data """
    # ACL JSON looks like
    # ...metadata...
    # {
    #     "Grants": [
    #         {
    #             "Grantee": {
    #                 "DisplayName": "string",
    #                 "EmailAddress": "string",
    #                 "ID": "string",
    #                 "Type": "CanonicalUser" | "AmazonCustomerByEmail" | "Group",
    #                 "URI": "string"
    #             },
    #             "Permission": "FULL_CONTROL" | "WRITE" | "WRITE_ACP" | "READ" | "READ_ACP"
    #         }
    #              ...
    #     ],
    #     "Owner": {
    #         "DisplayName": "string",
    #         "ID": "string"
    #     }
    # }
    acl_list = []
    for grant in acl['Grants']:
        parsed_acl = None
        if grant['Grantee']['Type'] == 'CanonicalUser':
            parsed_acl = {
                "bucket": bucket,
                "owner": acl['Owner'].get('DisplayName'),
                "ownerid": acl['Owner'].get('ID'),
                "type": grant['Grantee']['Type'],
                "displayname": grant['Grantee'].get('DisplayName'),
                "granteeid": grant['Grantee'].get('ID'),
                "uri": None,
                "permission": grant.get('Permission'),
            }
        elif grant['Grantee']['Type'] == 'Group':
            parsed_acl = {
                "bucket": bucket,
                "owner": acl['Owner'].get('DisplayName'),
                "ownerid": acl['Owner'].get('ID'),
                "type": grant['Grantee']['Type'],
                "displayname": None,
                "granteeid": None,
                "uri": grant['Grantee'].get('URI'),
                "permission": grant.get('Permission'),
            }
        else:
            logger.warning("Unexpected grant type: %s", grant['Grantee']['Type'])
            continue

        # TODO this can be replaced with a string join
        id_data = "{}:{}:{}:{}:{}:{}:{}:{}".format(
            aws_account_id,
            parsed_acl['owner'],
            parsed_acl['ownerid'],
            parsed_acl['type'],
            parsed_acl['displayname'],
            parsed_acl['granteeid'],
            parsed_acl['uri'],
            parsed_acl['permission'],
        )

        parsed_acl['id'] = hashlib.sha256(id_data.encode("utf8")).hexdigest()
        acl_list.append(parsed_acl)

    return acl_list


@timeit
def load_s3_buckets(neo4j_session, data, current_aws_account_id, aws_update_tag):
    ingest_bucket = """
    MERGE (bucket:S3Bucket{id:{BucketName}})
    ON CREATE SET bucket.firstseen = timestamp(), bucket.creationdate = {CreationDate}
    SET bucket.name = {BucketName}, bucket.arn = {Arn}, bucket.lastupdated = {aws_update_tag}
    WITH bucket
    MATCH (owner:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (owner)-[r:RESOURCE]->(bucket)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    # The owner data returned by the API maps to the aws account nickname and not the IAM user
    # there doesn't seem to be a way to retreive the mapping but we can get the current context account
    # so we map to that directly

    for bucket in data["Buckets"]:
        arn = "arn:aws:s3:::" + bucket["Name"]
        neo4j_session.run(
            ingest_bucket,
            BucketName=bucket["Name"],
            Arn=arn,
            CreationDate=str(bucket["CreationDate"]),
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        )


@timeit
def cleanup_s3_buckets(neo4j_session, common_job_parameters):
    run_cleanup_job('aws_import_s3_buckets_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def cleanup_s3_bucket_acl_and_policy(neo4j_session, common_job_parameters):
    run_cleanup_job('aws_import_s3_acl_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(neo4j_session, boto3_session, current_aws_account_id, aws_update_tag, common_job_parameters):
    logger.info("Syncing S3 for account '%s'.", current_aws_account_id)
    bucket_data = get_s3_bucket_list(boto3_session)

    load_s3_buckets(neo4j_session, bucket_data, current_aws_account_id, aws_update_tag)
    cleanup_s3_buckets(neo4j_session, common_job_parameters)

    acl_and_policy_data_iter = get_s3_bucket_details(boto3_session, bucket_data)
    load_s3_details(neo4j_session, acl_and_policy_data_iter, current_aws_account_id, aws_update_tag)
    cleanup_s3_bucket_acl_and_policy(neo4j_session, common_job_parameters)
