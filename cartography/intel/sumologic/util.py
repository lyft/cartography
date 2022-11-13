"""
cartography/intel/sumologic/util
"""
# pylint: disable=invalid-name,broad-except
import datetime
import json
import logging
from array import array

from msticpy.data.data_providers import QueryProvider

logger = logging.getLogger(__name__)


def sumologic_hosts(
    authorization: tuple[str, str, str],
    timeout_max: int = 600,
) -> array:
    """
    Get Sumologic (Logging) coverage inventory

    Timeout should be adapted to context, mostly size of indexes and searched timeperiod.

    https://help.sumologic.com/docs/api/search-job/
    https://msticpy.readthedocs.io/en/latest/data_acquisition/DataProv-Sumologic.html
    """

    (
        sumologic_access_id,
        sumologic_access_key,
        sumologic_server_url,
    ) = authorization
    end_time = datetime.datetime.now()
    start_time = end_time - datetime.timedelta(hours=1)

    qry_prov = QueryProvider("Sumologic")
    qry_prov.connect(
        connection_str=sumologic_server_url,
        accessid=sumologic_access_id,
        accesskey=sumologic_access_key,
    )

    # _sourceCategory, _sourceHost and _collector will get multiple entries for same host...
    # Exact query depends on your context and how structured in your platform and
    # the existence of a hostname (through Field Extraction Rule for example)
    # or use Sumologic Cloud SIEMT Enterprise normalized schema if apply
    # | formatDate(_messageTime,"yyyy/dd/MM HH:mm:ss") as date
    # | formatDate(_messageTime,"yyyy/MM/dd'T'HH:mm:ss'Z'") as date - NOK
    # | formatDate(_messageTime,"yyyy-MM-dd HH:mm:ss") as date - NOK
    vm_assets_query = r"""(_sourceCategory=*/*/SERVER or _sourceCategory=*/*/NXLOG_*)
| formatDate(_messageTime,"yyyy-MM-dd'T'HH:mm:ss'Z'") as date
| tolowercase(replace(hostname, /\..*$/, "")) as short_hostname
| tolowercase(hostname) as hostname
| first(date) as lastseen, last(date) as firstseen by bu,dc,hostname,short_hostname
| count bu,dc,hostname,short_hostname,firstseen,lastseen
| fields bu,dc,hostname,short_hostname,firstseen,lastseen"""
    df_vm_assets = qry_prov.exec_query(
        vm_assets_query,
        start_time=start_time,
        end_time=end_time,
        timeout=timeout_max,
        verbosity=2,
    )

    df_vm_assets.columns = df_vm_assets.columns.str.lstrip("map.")
    df_vm_assets["instance"] = sumologic_server_url.replace(
        ".sumologic.com/api", "",
    ).replace("https://api.", "")

    logger.info("SumologicHosts count final: %s", df_vm_assets.shape[0])
    logger.warning("SumologicHosts count final: %s", df_vm_assets.shape[0])

    if df_vm_assets.shape[0]:
        flatten_data = json.loads(df_vm_assets.to_json(orient="records"))
        logger.debug("Example: %s", flatten_data[0])
        logger.warning("Example: %s", flatten_data[0])
        return flatten_data

    logger.warning("No data returned")
    return {}
