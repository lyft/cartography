from typing import Dict

from . import aks
from . import compute
from . import cosmosdb
from . import function_app
from . import iam
from . import key_vaults
from . import monitor
from . import network
from . import securitycenter
from . import sql
from . import storage

RESOURCE_FUNCTIONS: Dict = {
    'iam': iam.sync,
    'network': network.sync,
    'aks': aks.sync,
    'cosmosdb': cosmosdb.sync,
    'function_app': function_app.sync,
    'key_vaults': key_vaults.sync,
    'compute': compute.sync,
    'sql': sql.sync,
    'storage': storage.sync,
    'monitor': monitor.sync,
    'securitycenter': securitycenter.sync,
}
