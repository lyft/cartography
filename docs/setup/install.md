<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Cartography Installation](#cartography-installation)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Cartography Installation

Time to set up the server that will run Cartography.  Cartography _should_ work on both Linux and Windows servers, but bear in mind we've only tested it in Linux so far.  Cartography requires Python 3.6 or greater.

1. **Get and install the Neo4j graph database** on your server.
    1. Neo4j requires a JVM (JDK/JRE 11 or higher) to be installed. One option is to install [Amazon Coretto 11](https://docs.aws.amazon.com/corretto/latest/corretto-11-ug/what-is-corretto-11.html).

            ⚠️ Make sure you have `JAVA_HOME` environment variable set. The following works for Mac OS: `export JAVA_HOME=$(/usr/libexec/java_home)`

    1. Go to the [Neo4j download page](https://neo4j.com/download-center/#releases), click "Community Server" and download Neo4j Community Edition 3.5.\*.

            ⚠️ At this time we run our automated tests on Neo4j version 3.5.\*.  Other versions may work but are not explicitly supported. ⚠️

    1. [Install](https://neo4j.com/docs/operations-manual/current/installation/) Neo4j on the server you will run Cartography on.

            ⚠️ For local testing, you might want to turn off authentication via property `dbms.security.auth_enabled` in file /NEO4J_PATH/conf/neo4j.conf

1. [Configure your data sources](config).

1. **Get and run Cartography**

    1. Run `pip install cartography` to install our code.

    1. Finally, to sync your data:

        - For one account using the `default` profile defined in your AWS config file, run

            ```
            cartography --neo4j-uri <uri for your neo4j instance; usually bolt://localhost:7687>
            ```

        - Or for a specific account defined as a separate profile in your AWS config file, set the `AWS_PROFILE` environment variable, for example

            ```
            AWS_PROFILE=other-profile cartography --neo4j-uri <uri for your neo4j instance; usually bolt://localhost:7687>
            ```

        - For more than one AWS account, run

            ```
            AWS_CONFIG_FILE=/path/to/your/aws/config cartography --neo4j-uri <uri for your neo4j instance; usually bolt://localhost:7687> --aws-sync-all-profiles
            ```

        You can view a full list of Cartography's CLI arguments by running `cartography --help`

        The sync will pull data from your configured accounts and ingest data to Neo4j!  This process might take a long time if your account has a lot of assets.

    1. See our [Operations Guide](ops.md) for tips on running Cartography in production.
