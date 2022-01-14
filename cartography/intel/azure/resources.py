from typing import Dict

from . import aks
from . import cosmosdb
from . import function_app
from . import key_vaults
from . import network
from . import compute
from . import iam
from . import sql
from . import storage


RESOURCE_FUNCTIONS: Dict = {
    'iam': iam.sync,
    'aks': aks.sync,
    'cosmosdb': cosmosdb.sync,
    'function_app': function_app.sync,
    'key_vaults': key_vaults.sync,
    'compute': compute.sync,
    'network': network.sync,
    'sql': sql.sync,
    'storage': storage.sync,
}
