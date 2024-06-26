from typing import Dict

from . import compute
from . import cosmosdb
from . import sql
from . import storage


RESOURCE_FUNCTIONS: Dict = {
    'cosmosdb': cosmosdb.sync,
    'compute': compute.sync,
    'sql': sql.sync,
    'storage': storage.sync,
}
