'''
Implement the Moneky Patching described in
https://github.com/lyft/cartography/issues/838 and in
https://docs.google.com/document/d/1DR-XPzEpd5o_aqvgH28mdIJG-2WSeektx2V9hETFXuM/edit#heading=h.cqtqxkjjli6n

The driver patch can also auto-detect the database version,
and determine if the query upgrades are needed.
By default, the driver patches apply automatically.
But for your own forks of cartography, you can directly driver patch like this:
experimental neo4j 4.x support

```
from cartography import patch_session_obj
patch_session_obj(neo4j_session)
```

You can also use the decorator `disable_syntax_upgrade` to disable the upgrade temporarily,
for the duration of the function being docerated. Use it if you have your own sync modules or synbc methods
that already have upgraded syntax. For example:

```
@disable_syntax_upgrade
def my_sync_function(ne4j_session, commong_job_params, ...):
   ...
```
'''
import logging
import re
from functools import wraps
from typing import Callable

import neo4j.exceptions

# Enable these patches, by default
EXPERIMENTAL_NEO4J_4X_SUPPORT = True

# Detect the database version
USING_4x_DATABASE = None

# Upgrade the syntax
UPGRADE_SYNTAX = None

# Log the queries
LOG_QUERIES = False


logger = logging.getLogger(__name__)

# Helper functions that patch the neo4j.GraphDatabase.driver().session().run()
# codepath to include the query conversions:


# decorator to disable the syntax upgrader for the duration of any specific function decorated
def disable_syntax_upgrade(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        global UPGRADE_SYNTAX
        original = UPGRADE_SYNTAX
        UPGRADE_SYNTAX = False
        try:
            return_value = func(*args, **kwargs)
            UPGRADE_SYNTAX = original
            return return_value
        except Exception:
            UPGRADE_SYNTAX = original
            raise
    return wrapper


def convert_index_statement(old_statement: str) -> str:
    label_expr = r'(?<=CREATE INDEX ON :).+(?=\()'
    prop_expr = r'(?<=\().+(?=\))'
    label = re.findall(label_expr, old_statement)[0]
    prop = re.findall(prop_expr, old_statement)[0]
    new_statement = f'CREATE INDEX IF NOT EXISTS FOR (n:{label}) ON (n.{prop});'
    return new_statement


def convert_params(old_query: str) -> str:
    expr = r'\{[^{}:\s]+\}'

    def match_handler(group_match):
        '''{characters} -> $characters'''
        s = group_match.group(0)
        # print(f'match_handler found: {s}')
        return '$' + s[1:-1]
    new_query = re.sub(expr, match_handler, old_query)
    # if old_query != new_query:
    if LOG_QUERIES:
        logger.debug('[OLD]\n', old_query)
        logger.debug('[NEW]\n', new_query)
    return new_query


def converted_query_str(old_query: str) -> str:
    if 'CREATE INDEX ON' in old_query:
        return convert_index_statement(old_query)
    else:
        return convert_params(old_query)


def patched_run_func(run_func: Callable) -> Callable:
    @wraps(run_func)
    def wrapper(query, *args, **kwargs):
        global UPGRADE_SYNTAX
        if UPGRADE_SYNTAX:
            query = converted_query_str(query)
        return run_func(query, *args, **kwargs)
    return wrapper


def patched_read_write_transaction_func(read_write_transaction_func: Callable) -> Callable:
    @wraps(read_write_transaction_func)
    def transaction_wrapper(transaction_func, *args, **kwargs):
        @wraps(transaction_func)
        def transaction_func_wrapper(tx, *args, **kwargs):
            tx.run = patched_run_func(tx.run)
            return transaction_func(tx, *args, **kwargs)
        return read_write_transaction_func(transaction_func_wrapper, *args, **kwargs)
    return transaction_wrapper


def patched_begin_transaction_func(begin_transaction_func: Callable) -> Callable:
    @wraps(begin_transaction_func)
    def begin_transaction_wrapper(*args, **kwargs):
        tx = begin_transaction_func(*args, **kwargs)
        tx.run = patched_run_func(tx.run)
        return tx
    return begin_transaction_wrapper


def detect_neo4j_version(neo4j_session: neo4j.Session) -> None:
    result = neo4j_session.run(
        'call dbms.components() yield name, versions, edition unwind versions as version return version;',
    )
    global USING_4x_DATABASE
    global UPGRADE_SYNTAX
    neo4j_version = result.single().value()
    if neo4j_version >= '4.0.0':
        USING_4x_DATABASE = True
        UPGRADE_SYNTAX = True


def patch_session_obj(neo4j_session: neo4j.Session) -> None:
    detect_neo4j_version(neo4j_session)
    neo4j_session.run = patched_run_func(neo4j_session.run)
    neo4j_session.write_transaction = patched_read_write_transaction_func(neo4j_session.write_transaction)
    neo4j_session.read_transaction = patched_read_write_transaction_func(neo4j_session.read_transaction)
    neo4j_session.begin_transaction = patched_begin_transaction_func(neo4j_session.begin_transaction)


def patch_driver_obj(neo4j_driver: neo4j.Driver) -> None:
    def session_converter(session_func):
        @wraps(session_func)
        def wrapper(*args, **kwargs):
            neo4j_session = session_func(*args, **kwargs)
            patch_session_obj(neo4j_session)
            return neo4j_session
        return wrapper
    neo4j_driver.session = session_converter(neo4j_driver.session)


def patched_driver_func(driver_func: Callable) -> Callable:
    @wraps(driver_func)
    def wrapper(*args, **kwargs) -> neo4j.Driver:
        neo4j_driver = driver_func(*args, **kwargs)
        patch_driver_obj(neo4j_driver)
        return neo4j_driver
    return wrapper


def patch_driver():
    neo4j.GraphDatabase.driver = patched_driver_func(neo4j.GraphDatabase.driver)


if EXPERIMENTAL_NEO4J_4X_SUPPORT:
    patch_driver()
