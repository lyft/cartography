from . import pubsublite
from . import spanner
from . import cloudtasks
from typing import Dict

from . import apigateway
from . import bigtable
from . import cloud_logging
from . import cloudcdn
from . import cloudfunction
from . import cloudkms
from . import cloudmonitoring
from . import cloudrun
from . import compute
from . import dataproc
from . import dns
from . import firestore
from . import gke
from . import iam
from . import pubsub
from . import sql
from . import storage
from . import cloud_logging
from . import cloudmonitoring
from . import dataproc
from . import cloudcdn
from . import loadbalancer
from . import bigquery
<< << << < HEAD
== == == =
>>>>>> > ce5d7086e0711afa1dad6457719e58fef723f78b


RESOURCE_FUNCTIONS: Dict = {
    'iam': iam.sync,
    'bigtable': bigtable.sync,
    'cloudfunction': cloudfunction.sync,
    'cloudkms': cloudkms.sync,
    'cloudrun': cloudrun.sync,
    'compute': compute.sync,
    'dns': dns.sync,
    'firestore': firestore.sync,
    'gke': gke.sync,
    'sql': sql.sync,
    'storage': storage.sync,
    'apigateway': apigateway.sync,
    'pubsub': pubsub.sync,
    'cloud_logging': cloud_logging.sync,
    'cloudmonitoring': cloudmonitoring.sync,
    'dataproc': dataproc.sync,
    'cloudcdn': cloudcdn.sync,
    'loadbalancer': loadbalancer.sync,
    'bigquery': bigquery.sync,
    'cloudtasks': cloudtasks.sync,
    'spanner': spanner.sync,
    'pubsublite': pubsublite.sync,
}
