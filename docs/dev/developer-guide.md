# Cartography Developer Guide

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Testing](#testing)
  - [Running from source](#running-from-source)
  - [Manually testing individual intel modules](#manually-testing-individual-intel-modules)
  - [Automated testing](#automated-testing)
- [Implementing custom sync commands](#implementing-custom-sync-commands)
- [How to write a new intel module](#how-to-write-a-new-intel-module)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Testing

### Running from source

1. **Install**

    Follow steps 1 and 2 in [Installation](https://github.com/lyft/cartography/blob/master/docs/setup/install.md#cartography-installation).  Ensure that you have JVM 11 installed and Neo4j Community Edition 3.5 is running on your local machine.
2. **Clone the source code**

    Run `cd {path-where-you-want-your-source-code}`.  Get the source code with `git clone git://github.com/lyft/cartography.git`

3. **Install from source**

    Run `cd cartography` and then `pip install -e .` (yes, actually type the period into the command line) to install Cartography from source.

    ℹ️You may find it beneficial to use Python [virtualenvs](https://packaging.python.org/guides/installing-using-pip-and-virtualenv/) (or the  [virutalenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/command_ref.html#managing-environments)) so that packages installed via `pip` are easier to manage.

4. **Run from source**

    After this finishes you should be able to run Cartography from source with `cartography --neo4j-uri <uri for your neo4j instance; usually bolt://localhost:7687>`.  Any changes to the source code in `{path-where-you-want-your-source-code}/cartography` are now locally testable by running `cartography` from the command line.

### Manually testing individual intel modules

After completing the section above, you are now able to manually test intel modules.

1. **If needed, comment out unnecessary lines**

    See `cartography.intel.aws._sync_one_account()`[here](https://github.com/lyft/cartography/blob/master/cartography/intel/aws/__init__.py).  This function syncs different AWS objects with your Neo4j instance.  Comment out the lines that you don't want to test for.

    For example, IAM can take a long time to ingest so if you're testing an intel module that doesn't require IAM nodes to already exist in the graph, then you can comment out all of the `iam.sync_*` lines.

2. Save your changes and run `cartography` from a terminal as you normally would.

### Automated testing

1. **Install test requirements**

    `pip install -r test-requirements.txt`

2. **(OPTIONAL) Setup environment variables for integration tests**

    The integration tests expect Neo4j to be running locally, listening on default ports, with auth disabled:

    To disable auth, edit your `neo4j.conf` file with `dbms.security.auth_enabled=false`.  Additional details on [neo4j.com](    https://neo4j.com/docs/operations-manual/current/authentication-authorization/enable/).

    To run the integration tests on a specific Neo4j instance, add the following environment variable:

    `export "NEO4J_URL=<your_neo4j_instance_bolt_url:your_neo4j_instance_port>"`

3. **Run tests using `make`**
    - `make test_lint` can be used to run [pre-commit](https://pre-commit.com) linting against the codebase.  We use [pre-commit](https://pre-commit.com) to standardize our linting across our code-base at Lyft.
    - `make test_unit` can be used to run the unit test suite.

    ⚠️ Important!  The below commands will **DELETE ALL NODES** on your local Neo4j instance as part of our testing procedure.  Only run any of the below commands if you are ok with this. ⚠️

    - `make test_integration` can be used to run the integration test suite.
    For more granular testing, you can invoke `pytest` directly:
      - `pytest ./tests/integration/cartography/intel/aws/test_iam.py`
      - `pytest ./tests/integration/cartography/intel/aws/test_iam.py::test_load_groups`
    - `make test` can be used to run all of the above.

## Implementing custom sync commands

By default, cartography will try to sync every intel module included as part of the default sync. If you're not using certain intel modules you can create a custom sync script and invoke it using the cartography CLI. For example, if you're only interested in the AWS intel module you can create a sync script, `custom_sync.py`, that looks like this:

```python
from cartography import cli
from cartography import sync
from cartography.intel import aws
from cartography.intel import create_indexes

def build_custom_sync():
    s = sync.Sync()
    s.add_stages([
        ('create-indexes', create_indexes.run),
        ('aws', aws.start_aws_ingestion),
    ])
    return s

def main(argv):
    return cli.CLI(build_custom_sync(), prog='cartography').main(argv)

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv[1:]))
```

Which can then be invoked using `python custom_sync.py` and will have all the features of the cartography CLI while only including the intel modules you are specifically interested in using. For example:

```
cartography$ python custom_sync.py
INFO:cartography.sync:Starting sync with update tag '1569022981'
INFO:cartography.sync:Starting sync stage 'create-indexes'
INFO:cartography.intel.create_indexes:Creating indexes for cartography node types.
INFO:cartography.sync:Finishing sync stage 'create-indexes'
INFO:cartography.sync:Starting sync stage 'aws'
INFO:botocore.credentials:Found credentials in shared credentials file: ~/.aws/credentials
...
```

## How to write a new intel module
See [here](writing-intel-modules.md).
