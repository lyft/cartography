from typing import Dict

from . import apigateway
from . import bigtable
from . import cloudfunction
from . import cloudkms
from . import cloudrun
from . import compute
from . import dns
from . import firestore
from . import gke
from . import iam
from . import sql
from . import storage


RESOURCE_FUNCTIONS: Dict = {
    'iam': iam.sync,
    'bigtable': bigtable.sync_bigtable,
    'cloudfunction': cloudfunction.sync,
    'cloudkms': cloudkms.sync_kms,
    'cloudrun': cloudrun.sync_cloudrun,
    'compute': compute.sync,
    'dns': dns.sync,
    'firestore': firestore.sync_firestore,
    'gke': gke.sync_gke_clusters,
    'sql': sql.sync_sql,
    'storage': storage.sync_gcp_buckets,
    'apigateway': apigateway.sync_apigateways,
}
